"""V2.6.3.10 — 비-마크다운 → 마크다운 변환기.

목적: PDF/PPTX/DOCX 등 비-텍스트 포맷도 archive 우선 파이프라인에 박을 수 있게.
      original.<ext>는 그대로 보존, content.md는 변환된 마크다운.

지원 포맷:
  .md, .txt     → passthrough (frontmatter 제거)
  .pdf          → pdfplumber 추출 (페이지 단위)
  .pptx, .ppt   → python-pptx (슬라이드 단위)
  .docx, .doc   → mammoth (마크다운 직접 변환)

설계 원칙:
  - 변환 실패 시 raise ConversionError → 호출자(folder_load)가 skip 처리
  - 본문이 비면 ("") 반환 → 호출자가 skip-empty로 카운트
  - 각 변환기는 *최대한 텍스트 추출*, 표/이미지 등 손실 가능 (manifest에 표식)
  - 외부 의존이 없는 포맷(.md/.txt)은 import 없이 작동
"""
from __future__ import annotations

from pathlib import Path


SUPPORTED_SUFFIXES = {".md", ".txt", ".pdf", ".pptx", ".ppt", ".docx", ".doc"}
LOSSLESS_SUFFIXES = {".md", ".txt"}   # 마크다운/텍스트 = original==content


class ConversionError(Exception):
    """변환 실패. 메시지에 원인 박힘."""


def convert_to_markdown(src: Path) -> str:
    """src 파일을 마크다운 문자열로 변환.

    raise ConversionError: 라이브러리 부재, 파싱 실패, 파일 없음.
    빈 결과 ("") 정상 — 호출자가 skip-empty.
    """
    if not src.exists():
        raise ConversionError(f"파일 없음: {src}")

    suf = src.suffix.lower()
    if suf in {".md", ".txt"}:
        return _convert_text(src)
    elif suf == ".pdf":
        return _convert_pdf(src)
    elif suf in {".pptx", ".ppt"}:
        return _convert_pptx(src)
    elif suf in {".docx", ".doc"}:
        return _convert_docx(src)
    else:
        raise ConversionError(f"지원 안 함: {suf}")


# ─── 포맷별 변환기 ────────────────────────────────────────────────────
def _convert_text(src: Path) -> str:
    """마크다운/텍스트 — frontmatter만 제거."""
    text = src.read_text(encoding="utf-8")
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end > 0:
            return text[end + 5:]
        end = text.find("\n---", 4)
        if end > 0:
            return text[end + 4:].lstrip("\n")
    return text


def _convert_pdf(src: Path) -> str:
    """PDF — pdfplumber로 페이지 단위 추출. 표는 마크다운 표로 변환."""
    try:
        import pdfplumber
    except ImportError as e:
        raise ConversionError(f"pdfplumber 미설치: {e}")

    out: list[str] = []
    try:
        with pdfplumber.open(src) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""
                tables = page.extract_tables() or []
                page_md = []
                if text.strip():
                    page_md.append(text.strip())
                for t in tables:
                    md_table = _list_table_to_markdown(t)
                    if md_table:
                        page_md.append(md_table)
                if page_md:
                    out.append(f"## 페이지 {i}\n\n" + "\n\n".join(page_md))
    except Exception as e:
        raise ConversionError(f"PDF 파싱 실패: {type(e).__name__}: {e}")
    return "\n\n".join(out)


def _convert_pptx(src: Path) -> str:
    """PPTX — python-pptx로 슬라이드 단위 추출."""
    try:
        from pptx import Presentation
    except ImportError as e:
        raise ConversionError(f"python-pptx 미설치: {e}")

    out: list[str] = []
    try:
        prs = Presentation(str(src))
        for i, slide in enumerate(prs.slides, 1):
            slide_lines = [f"## 슬라이드 {i}"]
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for para in shape.text_frame.paragraphs:
                        txt = "".join(run.text for run in para.runs).strip()
                        if txt:
                            slide_lines.append(txt)
                if getattr(shape, "has_table", False):
                    tbl = shape.table
                    rows = [
                        [cell.text.strip() for cell in row.cells]
                        for row in tbl.rows
                    ]
                    md_table = _list_table_to_markdown(rows)
                    if md_table:
                        slide_lines.append(md_table)
            # 노트
            try:
                if slide.has_notes_slide:
                    notes = slide.notes_slide.notes_text_frame.text.strip()
                    if notes:
                        slide_lines.append(f"\n> **노트**: {notes}")
            except Exception:
                pass
            if len(slide_lines) > 1:
                out.append("\n\n".join(slide_lines))
    except Exception as e:
        raise ConversionError(f"PPTX 파싱 실패: {type(e).__name__}: {e}")
    return "\n\n".join(out)


def _convert_docx(src: Path) -> str:
    """DOCX — mammoth로 마크다운 직접 변환."""
    try:
        import mammoth
    except ImportError as e:
        raise ConversionError(f"mammoth 미설치: {e}")

    try:
        with src.open("rb") as f:
            result = mammoth.convert_to_markdown(f)
        return result.value or ""
    except Exception as e:
        raise ConversionError(f"DOCX 파싱 실패: {type(e).__name__}: {e}")


# ─── 유틸 ────────────────────────────────────────────────────────────
def _list_table_to_markdown(rows: list[list]) -> str:
    """2D 리스트 → 마크다운 표. None/빈 셀은 공백으로."""
    if not rows:
        return ""
    # 행 정리
    cleaned = [
        [(str(c) if c is not None else "").replace("\n", " ").strip() for c in row]
        for row in rows
    ]
    cleaned = [r for r in cleaned if any(r)]  # 빈 줄 제거
    if not cleaned:
        return ""
    ncols = max(len(r) for r in cleaned)
    # 패딩
    for r in cleaned:
        while len(r) < ncols:
            r.append("")
    header = cleaned[0]
    out = ["| " + " | ".join(header) + " |"]
    out.append("| " + " | ".join("---" for _ in header) + " |")
    for r in cleaned[1:]:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


__all__ = [
    "SUPPORTED_SUFFIXES", "LOSSLESS_SUFFIXES",
    "ConversionError", "convert_to_markdown",
]
