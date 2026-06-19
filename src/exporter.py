"""V2.7.5 — 마크다운 → PPTX 변환기.

Marp CLI를 subprocess로 호출. 사용자가 textarea에 박은 마크다운에 자동으로
frontmatter 박고 marp 실행. 결과 .pptx 경로 반환.

설계:
  - subprocess.run으로 marp 호출 (외부 의존: brew install marp-cli)
  - 테마는 iris.css (data/themes/iris.css) 또는 marp 기본 (default)
  - Chrome 경로는 macOS 표준 위치 + 환경변수 override
  - 변환 실패 시 ConversionError raise

호환:
  - Marp CLI 없으면: ConversionError("marp 미설치")
  - Chrome 없으면: Marp가 다운로드 시도 (시간 ↑) — Chrome 경로 명시 권장
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_THEME_PATH = REPO_ROOT / "data" / "themes" / "iris.css"

# macOS 표준 Chrome 경로
_CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/opt/homebrew/bin/chromium",
]


class ExportError(Exception):
    """변환 실패."""


@dataclass
class ExportResult:
    out_path: Path
    elapsed_ms: int
    size_bytes: int


def _find_chrome() -> str | None:
    env = os.environ.get("CHROME_PATH")
    if env and Path(env).exists():
        return env
    for p in _CHROME_CANDIDATES:
        if Path(p).exists():
            return p
    return None


def _ensure_marp() -> str:
    """marp 실행파일 찾기. 없으면 ExportError."""
    marp = shutil.which("marp")
    if not marp:
        raise ExportError(
            "marp 미설치. 설치: `brew install marp-cli` 또는 `npm i -g @marp-team/marp-cli`"
        )
    return marp


def _prep_markdown(md_text: str, *, theme: str = "iris", paginate: bool = True) -> str:
    """frontmatter가 없으면 박음. 있으면 그대로."""
    md_text = md_text.lstrip()
    if md_text.startswith("---"):
        # 이미 frontmatter 있음 — marp/theme 누락이면 박지 않음 (사용자 의도 존중)
        return md_text
    front = ["---", "marp: true"]
    if theme:
        front.append(f"theme: {theme}")
    if paginate:
        front.append("paginate: true")
    front.append("---")
    return "\n".join(front) + "\n\n" + md_text


def md_to_pptx(
    md_text: str,
    *,
    out_path: Path | None = None,
    theme_css: Path | None = None,
    theme_name: str = "iris",
    paginate: bool = True,
    timeout: int = 60,
) -> ExportResult:
    """마크다운 텍스트를 .pptx 파일로 변환.

    md_text:    마크다운 본문. frontmatter 없어도 자동 박음.
    out_path:   결과 .pptx 경로. None이면 tempfile.
    theme_css:  커스텀 CSS 파일 경로. None이면 DEFAULT_THEME_PATH 사용.
    theme_name: frontmatter `theme: <name>` 지정 (theme_css의 @theme 줄과 일치).
    """
    marp = _ensure_marp()

    if theme_css is None:
        theme_css = DEFAULT_THEME_PATH if DEFAULT_THEME_PATH.exists() else None

    if out_path is None:
        out_path = Path(tempfile.mkdtemp(prefix="iris_pptx_")) / "export.pptx"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    prepped = _prep_markdown(md_text, theme=theme_name, paginate=paginate)

    # 임시 .md 박음
    md_tmp = Path(tempfile.mkstemp(suffix=".md", prefix="iris_md_")[1])
    md_tmp.write_text(prepped, encoding="utf-8")

    cmd = [marp, str(md_tmp), "-o", str(out_path), "--no-config-file"]
    if theme_css:
        cmd += ["--theme", str(theme_css)]

    chrome = _find_chrome()
    if chrome:
        cmd += ["--chrome-path", chrome]

    env = os.environ.copy()

    started = datetime.now()
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, env=env,
        )
    except subprocess.TimeoutExpired:
        raise ExportError(f"marp 타임아웃 {timeout}s — Chrome 미설치 의심")
    finally:
        md_tmp.unlink(missing_ok=True)

    if proc.returncode != 0:
        raise ExportError(
            f"marp 실패 (code={proc.returncode}): {proc.stderr or proc.stdout}"
        )

    if not out_path.exists():
        raise ExportError("marp 종료됐지만 .pptx 파일 없음")

    elapsed_ms = int((datetime.now() - started).total_seconds() * 1000)
    return ExportResult(
        out_path=out_path,
        elapsed_ms=elapsed_ms,
        size_bytes=out_path.stat().st_size,
    )


def md_to_pdf(
    md_text: str,
    *,
    out_path: Path | None = None,
    theme_css: Path | None = None,
    theme_name: str = "iris",
    paginate: bool = True,
    timeout: int = 60,
) -> ExportResult:
    """마크다운 → PDF (Marp 같은 흐름, --pdf)."""
    marp = _ensure_marp()
    if theme_css is None:
        theme_css = DEFAULT_THEME_PATH if DEFAULT_THEME_PATH.exists() else None
    if out_path is None:
        out_path = Path(tempfile.mkdtemp(prefix="iris_pdf_")) / "export.pdf"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    prepped = _prep_markdown(md_text, theme=theme_name, paginate=paginate)
    md_tmp = Path(tempfile.mkstemp(suffix=".md", prefix="iris_md_")[1])
    md_tmp.write_text(prepped, encoding="utf-8")

    cmd = [marp, str(md_tmp), "-o", str(out_path), "--no-config-file", "--pdf"]
    if theme_css:
        cmd += ["--theme", str(theme_css)]
    chrome = _find_chrome()
    if chrome:
        cmd += ["--chrome-path", chrome]

    started = datetime.now()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise ExportError(f"marp 타임아웃 {timeout}s")
    finally:
        md_tmp.unlink(missing_ok=True)

    if proc.returncode != 0:
        raise ExportError(
            f"marp PDF 실패 (code={proc.returncode}): {proc.stderr or proc.stdout}"
        )

    elapsed_ms = int((datetime.now() - started).total_seconds() * 1000)
    return ExportResult(
        out_path=out_path,
        elapsed_ms=elapsed_ms,
        size_bytes=out_path.stat().st_size,
    )


__all__ = ["ExportError", "ExportResult", "md_to_pptx", "md_to_pdf"]
