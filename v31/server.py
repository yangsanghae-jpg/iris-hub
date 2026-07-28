"""V3.1 Shell FastAPI — 진단툴 V3.1 디자인 포트용 서비스.

port 8767 구동:
  uvicorn v31.server:app --port 8767 --reload

기존 시스템(8765 Streamlit / 8766 PPT)과는 분리.
"""
from __future__ import annotations

import datetime as _dt
import mimetypes
import shutil
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Optional

from fastapi import FastAPI, HTTPException, UploadFile as _UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

app = FastAPI(title="iris-hub-v31", version="0.1")

# -- backend config -------------------------------------------------------
from src.config import IRIS_KNOWLEDGE_RAW, IRIS_VAULT_DB

# -- intake state ---------------------------------------------------------
_state: dict[str, Any] = {
    "scan_list": None,
    "scan_dir": None,
    # PPT state
    "expand_md": None,
    "expand_meta": None,
    "expand_contract": None,
    "deck": None,
    "render_path": None,
    "render_meta": None,
    "preview_id": None,
    "preview_dir": None,
}


def _clear_previews() -> None:
    old = _state.get("preview_dir")
    if old:
        shutil.rmtree(old, ignore_errors=True)
    _state["preview_id"] = None
    _state["preview_dir"] = None


# -- helpers ---------------------------------------------------------------

def _raw_files() -> list[str]:
    if not IRIS_KNOWLEDGE_RAW.is_dir():
        return []
    return sorted(f.name for f in IRIS_KNOWLEDGE_RAW.iterdir() if f.is_file())


def _save_file(filename: str, content: bytes) -> Path:
    target = IRIS_KNOWLEDGE_RAW / filename
    if target.exists():
        stem, suffix = target.stem, target.suffix
        ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        target = IRIS_KNOWLEDGE_RAW / f"{stem}_{ts}{suffix}"
    target.write_bytes(content)
    return target


def _build_md(*, title: str, source: str = "manual",
              body: str, industry: str = "", area: str = "",
              level: str = "") -> str:
    lines = ["---", f"title: {title}", f"source: {source}",
             f"captured_at: {_dt.datetime.now().isoformat(timespec='seconds')}"]
    if industry: lines.append(f"industry: {industry}")
    if area: lines.append(f"area: {area}")
    if level: lines.append(f"level: {level}")
    lines += ["---", "", body.strip(), ""]
    return "\n".join(lines)


def _run_intake(filename: str) -> tuple[bool, str]:
    from io import StringIO
    from contextlib import redirect_stdout, redirect_stderr
    try:
        from src.engine.intake import raw_intake
    except Exception as e:
        return False, f"import 실패: {e}"
    buf_out, buf_err = StringIO(), StringIO()
    try:
        with redirect_stdout(buf_out), redirect_stderr(buf_err):
            rc = raw_intake.main()
        log = buf_out.getvalue() + buf_err.getvalue()
        return (rc == 0), log
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def _default_meta(lang: str) -> dict:
    """PPT default metadata generator."""
    return {
        "company": "赛美特",
        "title": "",
        "subtitle": "",
        "date": "",
        "lang": lang,
    }


def _resolve_style_from_req(template_id: str, master_style: dict, page_number: dict):
    from src.engine.output.deck.theme import resolve_deck_style
    return resolve_deck_style(template_id, master_style=master_style, page_number=page_number)


def _build_slide_previews(deck, style) -> dict[str, Any]:
    """ 프리뷰 HTML 슬라이드별 생성 — iframe 프리뷰용. """
    from src.engine.output.deck.renderer import render_slide_html

    old_dir = _state.get("preview_dir")  # 새 폴더로 덮어쓰기 전에 먼저 확보

    preview_id = uuid.uuid4().hex[:12]
    root = Path(tempfile.mkdtemp(prefix=f"iris_prev_{preview_id}_"))
    total = len(deck.slides)
    previews: list[dict[str, Any]] = []
    try:
        for i, slide in enumerate(deck.slides):
            html = render_slide_html(
                slide.pattern, slide.data, deck,
                pageno=i + 1, total_pages=total, style=style,
            )
            (root / f"slide-{i}.html").write_text(html, encoding="utf-8")
            title = slide.data.get("title") or slide.data.get("company") or slide.pattern
            previews.append({
                "slide_index": i,
                "page_number": i + 1,
                "html_url": f"/api/preview/{preview_id}/{i}",
                "title": str(title)[:120],
                "pattern": slide.pattern,
            })
    except Exception:
        shutil.rmtree(root, ignore_errors=True)
        raise

    # 새 폴더가 전부 완성된 뒤에만 state를 갱신하고 이전 폴더를 정리한다.
    _state["preview_id"] = preview_id
    _state["preview_dir"] = str(root)
    if old_dir:
        shutil.rmtree(old_dir, ignore_errors=True)
    return {"preview_id": preview_id, "previews": previews, "page_count": total}


def _save_to_exports(src_path: Path, prefix: str = "deck") -> Path:
    from src.config import IRIS_KNOWLEDGE_PROCESSED
    exports_dir = IRIS_KNOWLEDGE_PROCESSED / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    ext = src_path.suffix.lstrip(".") or "bin"
    target = exports_dir / f"{prefix}_{stamp}.{ext}"
    shutil.copy2(src_path, target)
    return target


# =========================================================================
# API Routes (정의 먼저 — StaticFiles mount 전)
# =========================================================================

@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "port": 8767}


# ---- Sources (intake + PPT) ----------------------------------------------

@app.get("/api/sources")
def list_sources() -> dict:
    """raw 폴더 파일 목록 + PPT용 archive/docs 목록."""
    files = _raw_files()
    # Try PPT-specific source listing
    try:
        from src.tabs.pptx import _list_archive_content_md, _list_docs_md
        archive = _list_archive_content_md()
        docs = _list_docs_md()
        return {
            "sources": [
                {"id": i + 1, "name": f, "size": (IRIS_KNOWLEDGE_RAW / f).stat().st_size if (IRIS_KNOWLEDGE_RAW / f).exists() else 0}
                for i, f in enumerate(files)
            ],
            "archive": [{"id": i, "label": label} for i, (label, _p) in enumerate(archive)],
            "docs": [{"id": i, "label": label} for i, (label, _p) in enumerate(docs)],
            "count": len(files),
        }
    except ImportError:
        return {"sources": [
            {"id": i + 1, "name": f, "size": (IRIS_KNOWLEDGE_RAW / f).stat().st_size if (IRIS_KNOWLEDGE_RAW / f).exists() else 0}
            for i, f in enumerate(files)
        ], "count": len(files)}


@app.get("/api/sources/content")
def source_content(kind: str = "raw", id: int = 0) -> dict:
    """raw 폴더 또는 PPT용 archive/docs 파일 본문 읽기."""
    files = _raw_files()
    # Try PPT mode first
    try:
        from src.tabs.pptx import _list_archive_content_md, _list_docs_md
        items = _list_archive_content_md() if kind == "archive" else (
            _list_docs_md() if kind == "docs" else None)
        if items is not None:
            if not (0 <= id < len(items)):
                raise HTTPException(404, "source not found")
            label, path = items[id]
            text = path.read_text(encoding="utf-8")
            return {"label": label, "text": text}
    except (ImportError, Exception):
        pass
    # Fallback to raw mode
    if id < 1 or id > len(files):
        raise HTTPException(404, "source not found")
    name = files[id - 1]
    path = IRIS_KNOWLEDGE_RAW / name
    if not path.exists():
        raise HTTPException(404, "file not found")
    return {
        "id": id, "name": name,
        "content": path.read_text(encoding="utf-8"),
        "mime": mimetypes.guess_type(str(path))[0] or "text/plain",
    }


# ---- Intake (Mode A/B/C) ------------------------------------------------

class FileUploadReq(BaseModel):
    filename: str = ""


@app.post("/api/intake/upload")
def intake_upload(file: _UploadFile = None, req: Optional[FileUploadReq] = None) -> dict:
    if file is None:
        raise HTTPException(400, "file required")
    content = file.file.read()
    name = file.filename or (req.filename if req else "unknown")
    if not any(name.endswith(ext) for ext in (".md", ".txt", ".pdf", ".pptx", ".docx")):
        name = name + ".md"
    target = _save_file(name, content)
    ok, log = _run_intake(name)
    if not ok:
        try: target.unlink()
        except Exception: pass
        raise HTTPException(500, f"intake failed: {log}")
    return {"status": "ok", "filename": name, "path": str(target)}


class PasteReq(BaseModel):
    title: str
    source: str = "manual"
    body: str
    industry: str = ""
    area: str = ""
    level: str = ""


@app.post("/api/intake/paste")
def intake_paste(req: PasteReq) -> dict:
    md_content = _build_md(title=req.title, source=req.source,
                           body=req.body, industry=req.industry,
                           area=req.area, level=req.level)
    filename = f"{req.title[:50]}.md"
    counter = 1
    target = IRIS_KNOWLEDGE_RAW / filename
    while target.exists():
        filename = f"{req.title[:40]}_{counter}.md"
        target = IRIS_KNOWLEDGE_RAW / filename
        counter += 1
    target.write_text(md_content, encoding="utf-8")
    ok, log = _run_intake(filename)
    if not ok:
        try: target.unlink()
        except Exception: pass
        raise HTTPException(500, f"intake failed: {log}")
    return {"status": "ok", "filename": filename, "path": str(target)}


@app.post("/api/intake/folder")
def intake_folder(folder_path: str) -> dict:
    folder = Path(folder_path)
    if not folder.is_dir():
        raise HTTPException(404, "folder not found")
    files = []
    for ext in (".md", ".txt", ".pdf", ".pptx", ".docx"):
        files.extend(f.name for f in folder.iterdir() if f.is_file() and f.name.lower().endswith(ext))
    return {"status": "ok", "folder": str(folder), "files": sorted(files), "count": len(files)}



# ---- Intake Tree Scan (Folder Loading B) ----------------------------------

class FolderScanReq(BaseModel):
    folder_path: str
    recursive: bool = True



@app.post("/api/intake/scan_tree")
def intake_scan_tree(req: FolderScanReq) -> dict:
    """Folder scan with tree structure — returns directories with files and processed status."""
    from collections import defaultdict

    folder = Path(req.folder_path).resolve()
    if not folder.is_dir():
        raise HTTPException(404, f"folder not found: {req.folder_path}")

    scan = None
    scan_error = None
    try:
        from src.engine.intake.folder_load import scan_folder, FileEntry
        scan = scan_folder(str(folder), recursive=req.recursive)
    except Exception as e:
        # DB schema mismatch — fall back to listing files without processed status
        scan_error = str(e)

    if not scan or scan.total == 0:
        # Fallback: list files without processed status
        if folder.is_dir():
            files = []
            for ext in (".md", ".txt", ".pdf", ".pptx", ".docx"):
                for f in folder.rglob("*"):
                    if f.is_file() and f.name.lower().endswith(ext):
                        files.append({
                            "path": str(f),
                            "name": f.name,
                            "size": f.stat().st_size,
                            "mtime": f.stat().st_mtime,
                            "processed": False,
                            "last_doc_id": None,
                        })
            if files:
                by_dir = {}
                for f in files:
                    try:
                        rel_dir = str(Path(f["path"]).relative_to(folder))
                    except ValueError:
                        rel_dir = "."
                    if rel_dir not in by_dir:
                        by_dir[rel_dir] = []
                    by_dir[rel_dir].append(f)
                dirs_sorted = sorted(by_dir.keys(), key=lambda d: (d != ".", d))
                return {
                    "status": "ok",
                    "folder": str(folder),
                    "directories": [
                        {"path": d, "is_root": d == ".", "files": sorted(by_dir[d], key=lambda f: f["name"])}
                        for d in dirs_sorted
                    ],
                    "total": len(files),
                    "pending": len(files),
                    "processed": 0,
                }
        return {"status": "ok", "folder": str(folder), "directories": [],
                "total": 0, "pending": 0, "processed": 0}

    # Group by directory
    by_dir: dict[str, list] = defaultdict(list)
    for e in scan.entries:
        try:
            rel_dir = str(e.path.relative_to(folder))
        except ValueError:
            rel_dir = "."
        by_dir[rel_dir].append({
            "path": str(e.path),
            "name": e.path.name,
            "size": e.path.stat().st_size,
            "mtime": e.path.stat().st_mtime,
            "processed": e.processed,
            "last_doc_id": e.last_doc_id,
        })

    dirs_sorted = sorted(by_dir.keys(), key=lambda d: (d != ".", d))

    return {
        "status": "ok",
        "folder": str(folder),
        "directories": [
            {
                "path": d,
                "is_root": d == ".",
                "files": sorted(by_dir[d], key=lambda f: f["name"]),
            }
            for d in dirs_sorted
        ],
        "total": scan.total,
        "pending": scan.pending_count,
        "processed": scan.processed_count,
    }

    files: list[str]
    lane: str = "reference"
    force: bool = False
    archive_root: Optional[str] = None


@app.post("/api/intake/index")
def intake_index(req: IndexReq) -> dict:
    """Index selected files from a previous scan."""
    from src.engine.intake.folder_load import ingest_paths

    paths = [Path(f).resolve() for f in req.files if Path(f).exists()]
    archive_root = Path(req.archive_root).resolve() if req.archive_root else None

    result = ingest_paths(
        paths, lane=req.lane, force=req.force, archive_root=archive_root,
        use_k2=False,  # K2 classification done in flow tab
    )

    files_out = []
    for fr in result.files:
        entry = {
            "name": fr.source.name,
            "doc_id": fr.doc_id,
            "chunks": fr.chunks,
            "archive_dir": str(fr.archive_dir) if fr.archive_dir else None,
            "classifier": fr.classifier,
            "industry": fr.industry,
            "area": fr.area,
            "level": fr.level,
            "error": fr.error,
            "skipped_reason": fr.skipped_reason,
        }
        files_out.append(entry)

    return {
        "status": "ok" if result.ok else "partial",
        "requested": result.requested,
        "upserted": result.upserted,
        "classified": result.classified,
        "skipped_empty": result.skipped_empty,
        "skipped_already": result.skipped_already,
        "archived": result.archived,
        "work_id": result.work_id,
        "files": files_out,
        "errors": [{"name": n, "error": e} for n, e in result.errors],
        "fts_counts": result.fts_counts,
    }


# ---- External Capture API -------------------------------------------------

class ExternalCaptureReq(BaseModel):
    title: str
    source: str = "manual-note"
    prompt: str = ""
    body: str


class OpenPathReq(BaseModel):
    path: str


@app.get("/api/intake/meta")
def intake_meta() -> dict:
    from src.config import IRIS_KNOWLEDGE_ARCHIVE, IRIS_KNOWLEDGE_EXTERNAL
    try:
        from src.tabs.external_capture import SOURCES
        source_count = len(SOURCES)
    except Exception:
        source_count = 11
    return {
        "archive_default": str(IRIS_KNOWLEDGE_ARCHIVE),
        "external_dir": str(IRIS_KNOWLEDGE_EXTERNAL),
        "external_sources": source_count,
    }


@app.post("/api/open_path")
def open_path(req: OpenPathReq) -> dict:
    import subprocess
    path = req.path.strip()
    if not path:
        raise HTTPException(400, "path required")
    try:
        subprocess.Popen(["open", path])
        return {"status": "ok", "path": path}
    except Exception as e:
        raise HTTPException(500, f"open failed: {e}")


@app.get("/api/external/content")
def external_content(path: str) -> dict:
    p = Path(path).resolve()
    from src.config import IRIS_KNOWLEDGE_EXTERNAL
    ext_root = IRIS_KNOWLEDGE_EXTERNAL.resolve()
    if not str(p).startswith(str(ext_root)):
        raise HTTPException(403, "path not allowed")
    if not p.is_file():
        raise HTTPException(404, "file not found")
    text = p.read_text(encoding="utf-8")
    body = text
    if text.startswith("---\n"):
        parts = text[4:].split("\n---\n", 1)
        if len(parts) == 2:
            body = parts[1]
    preview = body.strip()
    if len(preview) > 1200:
        preview = preview[:1200] + "\n…"
    return {"status": "ok", "body": body.strip(), "preview": preview}


# Recent external event format
@dataclass
class _RecentEvent:
    path: Path
    title: str
    source: str
    mtime: float
    size: int


def _external_list_recent(n: int = 20) -> list[dict]:
    """List recent external events."""
    from src.config import IRIS_KNOWLEDGE_EXTERNAL
    ext_dir = IRIS_KNOWLEDGE_EXTERNAL
    if not ext_dir.exists():
        return []

    files: list[Path] = []
    for src_dir in ext_dir.iterdir():
        if not src_dir.is_dir():
            continue
        files.extend(src_dir.glob("*.md"))

    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    out: list[dict] = []
    for p in files[:n]:
        try:
            head = p.read_text(encoding="utf-8")
            title = ""
            source = p.parent.name
            for line in head.splitlines()[:10]:
                if line.startswith("title:"):
                    title = line.split(":", 1)[1].strip()
                    break
            out.append({
                "path": str(p),
                "title": title or p.stem,
                "source": source,
                "mtime": p.stat().st_mtime,
                "size": p.stat().st_size,
            })
        except Exception:
            continue
    return out


def _external_save_event(title: str, source: str, body: str, prompt: str = "") -> tuple[Path, str]:
    """Save external event and return (target_path, doc_id)."""
    from src.config import IRIS_KNOWLEDGE_EXTERNAL
    import re

    ext_dir = IRIS_KNOWLEDGE_EXTERNAL

    # Build safe filename
    slug = re.sub(r"[^\w가-힣\-]+", "_", title.strip(), flags=re.UNICODE)
    slug = re.sub(r"_+", "_", slug).strip("_")
    if not slug:
        slug = "event"
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"{slug}_{ts}.md"

    target_dir = ext_dir / source
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / fname

    # Build frontmatter + body
    lines = ["---", f"title: {title.strip()}", f"source: {source}",
             f"captured_at: {_dt.datetime.now().astimezone().isoformat(timespec='seconds')}"]
    if prompt and prompt.strip():
        lines.append(f"prompt: {prompt.strip()}")
    lines += ["---", "", body.rstrip(), ""]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target


def _external_ingest_one(path: Path) -> dict:
    """Ingest a single external event into DB."""
    from src.engine.intake.raw_intake import (
        doc_id_for, parse_frontmatter, split_chunks, upsert_raw_doc,
    )
    from src.engine.intake.fts_sync import rebuild_all
    import sqlite3

    from src.config import IRIS_DB_PATH

    if not IRIS_DB_PATH.exists():
        return {"ok": False, "error": f"DB 없음: {IRIS_DB_PATH}"}

    try:
        text = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)
        title = meta.get("title") or path.stem
        chunks = split_chunks(body)
        if not chunks:
            return {"ok": False, "error": "본문 chunk 0개"}

        doc_id = doc_id_for(path)
        conn = sqlite3.connect(str(IRIS_DB_PATH))
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            upsert_raw_doc(conn, doc_id, path, title, chunks)
            rebuild_all(conn)
            conn.commit()
        finally:
            conn.close()

        return {"ok": True, "doc_id": doc_id, "chunks": len(chunks), "error": None}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


@app.post("/api/external/capture")
def external_capture(req: ExternalCaptureReq) -> dict:
    """Save external response and run K2 + raw_intake."""
    try:
        target = _external_save_event(
            title=req.title, source=req.source,
            body=req.body, prompt=req.prompt,
        )

        # K2 analysis
        k2_result = None
        try:
            from src.engine.process import k2
            k2_result = k2.analyze(req.title.strip(), req.body, timeout=60.0)
        except Exception as e:
            from src.engine.process.classify import suggest_classification
            rule = suggest_classification(req.title.strip(), req.body)
            k2_result = type("K2Result", (), {
                "industry": rule.get("industry"), "area": rule.get("area"),
                "level": rule.get("level"), "topics": rule.get("keywords", []),
                "summary": "(K2 unavailable)", "reason": f"K2 error: {e}",
                "confidence": 0.2, "classifier_version": "rule-fallback",
                "elapsed_ms": 0, "fallback_used": True, "entities": [],
                "concepts": [], "error": str(e),
            })()

        # Ingest
        ing = _external_ingest_one(target)

        # document_meta upsert
        k2_meta = {}
        try:
            from src import document_meta
            document_meta.ensure_schema()
            document_meta.upsert(
                ing.get("doc_id"),
                summary=k2_result.summary,
                topics=k2_result.topics,
                entities=k2_result.entities,
                concepts=k2_result.concepts,
                classifier_version=k2_result.classifier_version,
                confidence=k2_result.confidence,
                reason=k2_result.reason,
                k2_ms=k2_result.elapsed_ms,
                fallback_used=k2_result.fallback_used,
            )
            k2_meta = {
                "industry": k2_result.industry,
                "area": k2_result.area,
                "level": k2_result.level,
                "summary": k2_result.summary,
                "topics": k2_result.topics,
                "entities": k2_result.entities,
                "concepts": k2_result.concepts,
                "k2_version": k2_result.classifier_version,
                "k2_ms": k2_result.elapsed_ms,
                "k2_fallback": k2_result.fallback_used,
            }
        except Exception:
            pass  # meta save failure doesn't block storage

        return {
            "status": "ok",
            "filename": target.name,
            "path": str(target),
            "size": target.stat().st_size,
            "ingest_ok": ing.get("ok"),
            "doc_id": ing.get("doc_id"),
            "chunks": ing.get("chunks", 0),
            "k2": k2_meta,
        }
    except Exception as e:
        raise HTTPException(500, f"capture failed: {e}")


@app.get("/api/external/recent")
def external_recent() -> dict:
    """List recent external events."""
    events = _external_list_recent(20)
    return {"status": "ok", "events": events}


@app.get("/api/intake/scan")
def intake_scan() -> dict:
    return _state

# ---- Folder Picker (macOS only) -------------------------------------------

@app.post("/api/pick_folder")
def pick_folder(script: Optional[str] = None) -> dict:
    """Open macOS Finder folder picker dialog. Returns selected path."""
    import subprocess

    sel = script or 'POSIX path of (choose folder with prompt "폴더 선택")'
    try:
        out = subprocess.run(
            ["osascript", "-e", sel],
            capture_output=True, text=True, timeout=120,
        )
    except Exception as e:
        raise HTTPException(400, f"folder picker 실패: {e}")
    if out.returncode != 0:
        # Cancelled (-128) — return None
        return {"status": "ok", "path": None}
    path = out.stdout.strip()
    if not path:
        return {"status": "ok", "path": None}
    return {"status": "ok", "path": path}



# ---- PPT Engine ----------------------------------------------------------

class ExpandReq(BaseModel):
    md_text: str
    lang: str = "한국어"
    model: Optional[str] = None
    pages: Optional[str] = None
    target_slides: Optional[int] = None


@app.post("/api/expand")
def run_expand(req: ExpandReq) -> dict:
    from src.engine.output.deck import expander

    if not req.md_text.strip():
        raise HTTPException(400, "소스가 비어 있습니다")
    meta = _default_meta(req.lang)
    pages = req.pages
    if pages is None and req.target_slides is not None:
        pages = req.target_slides
    try:
        # Stage 0(재생성) — 원문을 읽고 형식 마커 없이 챕터로만, 최대한
        # 풍부하게 재구성한다. 콘텐츠 합성(여기)과 형식 판단(Stage 1)을
        # 분리해야 서로의 여력을 깎아먹지 않는다.
        regen = expander.regenerate_chapters(
            req.md_text, meta, model=req.model, timeout=900,
            lang=req.lang, pages=pages,
        )
        # Stage 1(확장) — 이미 풍부한 콘텐츠에 IRIS_BODY/PATTERN/ROLES만 판단.
        result = expander.expand_for_slides(
            regen.md, meta, model=req.model, timeout=900,
            lang=req.lang, pages=pages,
            contract_mode="required",
        )
    except expander.ExpansionError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=422)

    _state["expand_md"] = result.md
    _state["expand_meta"] = meta
    _state["expand_contract"] = result.contract
    _state["deck"] = None
    _state["render_path"] = None
    _clear_previews()
    return {
        "ok": True, "md": result.md, "model": result.model,
        "contract": result.contract,
        "elapsed": (regen.elapsed_ms + result.elapsed_ms) / 1000,
        "in": regen.original_chars, "out": result.output_chars,
    }


class DesignReq(BaseModel):
    model: Optional[str] = None
    lang: str = "한국어"
    target_slides: Optional[int] = None
    density: Literal["spacious", "standard", "dense"] = "standard"


@app.post("/api/design")
def run_design(req: DesignReq) -> dict:
    from src.engine.output.deck import designer
    from src import llm
    from src.config import IRIS_LLM_DEEP
    from src.engine.output.deck.pattern_contract import PatternContractError
    from src.engine.output.deck.theme import ThemeValidationError, validate_density

    md = _state.get("expand_md")
    if not md:
        raise HTTPException(400, "먼저 ②확장을 실행하세요")
    meta = _state.get("expand_meta") or _default_meta(req.lang)
    contract = _state.get("expand_contract")
    used_model = req.model or llm.resolve_available_model(IRIS_LLM_DEEP) or IRIS_LLM_DEEP
    try:
        density = validate_density(req.density)
        deck = designer.design_deck(
            md, meta, model=used_model, timeout=600,
            pre_expanded=True, target_slides=req.target_slides,
            density=density,
            contract_mode="required",
            contract=contract,
        )
    except ThemeValidationError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=422)
    except PatternContractError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=422)
    except designer.DesignError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=422)

    _state["deck"] = deck
    _state["render_path"] = None
    _clear_previews()
    slides = [
        {"pattern": s.pattern, "title": s.data.get("title") or s.pattern}
        for s in deck.slides
    ]
    return {
        "ok": True,
        "model": used_model,
        "density": density,
        "slides": slides,
        "page_count": len(deck.slides),
        "warnings": deck.warnings or [],
    }


class MasterStyleReq(BaseModel):
    title_font: Optional[str] = None
    title_size_pt: Optional[int] = None
    title_color: Optional[str] = None


class PageNumberReq(BaseModel):
    enabled: bool = True
    position: Literal["bottom-left", "bottom-center", "bottom-right"] = "bottom-right"


class RenderReq(BaseModel):
    format: str = "PDF"
    save_disk: bool = False
    template_id: str = "clean-light"
    master_style: MasterStyleReq = Field(default_factory=MasterStyleReq)
    page_number: PageNumberReq = Field(default_factory=PageNumberReq)

    @field_validator("format")
    @classmethod
    def _format_ok(cls, v: str) -> str:
        fmt = (v or "").upper()
        if fmt not in ("PDF", "PPTX"):
            raise ValueError("format must be PDF or PPTX")
        return fmt


@app.post("/api/render")
def run_render(req: RenderReq) -> dict:
    from src.engine.output.deck.theme import ThemeValidationError

    deck = _state.get("deck")
    if not deck:
        raise HTTPException(400, "먼저 ③설계를 실행하세요")

    try:
        style = _resolve_style_from_req(req.template_id, req.master_style, req.page_number)
    except ThemeValidationError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=422)

    fmt = req.format.upper()
    try:
        if fmt == "PDF":
            from src.engine.output.deck.renderer import render_deck_to_pdf
            out_path = render_deck_to_pdf(deck, style=style)
            mime = "application/pdf"
        else:
            from src.engine.output.deck.pptx_export import render_deck_to_pptx
            out_path = render_deck_to_pptx(deck, style=style)
            mime = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    except Exception as e:
        return JSONResponse(
            {"ok": False, "error": f"{type(e).__name__}: {e}"}, status_code=500,
        )

    saved_to = None
    if req.save_disk:
        try:
            saved_to = str(_save_to_exports(out_path, prefix="deck"))
        except Exception as e:
            return JSONResponse(
                {"ok": False, "error": f"exports 저장 실패: {type(e).__name__}: {e}"},
                status_code=500,
            )

    try:
        preview_payload = _build_slide_previews(deck, style)
    except Exception as e:
        preview_payload = {
            "preview_id": None, "previews": [],
            "page_count": len(deck.slides),
            "error": f"preview failed: {type(e).__name__}",
        }

    _state["render_path"] = out_path
    _state["render_meta"] = {"mime": mime, "fmt": fmt}
    size_kb = out_path.stat().st_size / 1024
    return {
        "ok": True, "fmt": fmt, "size_kb": size_kb,
        "page_count": len(deck.slides), "download_url": "/api/download",
        "saved_to": saved_to,
        "template_id": style.template_id,
        "style": {
            "title_font": style.title_font,
            "title_size_pt": style.title_size_pt,
            "title_color": style.title_color,
            "page_number": {
                "enabled": style.page_number.enabled,
                "position": style.page_number.position,
            },
        },
        "preview_id": preview_payload.get("preview_id"),
        "previews": preview_payload.get("previews", []),
    }


class PreviewBuildReq(BaseModel):
    template_id: str = "clean-light"
    master_style: MasterStyleReq = Field(default_factory=MasterStyleReq)
    page_number: PageNumberReq = Field(default_factory=PageNumberReq)


@app.post("/api/preview/build")
def build_preview(req: PreviewBuildReq) -> dict:
    from src.engine.output.deck.theme import ThemeValidationError

    deck = _state.get("deck")
    if not deck:
        raise HTTPException(400, "먼저 ③설계를 실행하세요")
    try:
        style = _resolve_style_from_req(req.template_id, req.master_style, req.page_number)
        payload = _build_slide_previews(deck, style)
    except ThemeValidationError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=422)
    except Exception as e:
        return JSONResponse(
            {"ok": False, "error": f"{type(e).__name__}: {e}"}, status_code=500,
        )
    return {"ok": True, **payload}


@app.get("/api/preview/{preview_id}/{slide_index}")
def get_preview_html(preview_id: str, slide_index: int):
    if not preview_id.isalnum() or len(preview_id) > 32:
        raise HTTPException(400, "invalid preview id")
    if slide_index < 0:
        raise HTTPException(404, "slide not found")
    if _state.get("preview_id") != preview_id:
        raise HTTPException(404, "preview not found")
    root = _state.get("preview_dir")
    if not root:
        raise HTTPException(404, "preview not found")
    root_path = Path(root).resolve()
    path = (root_path / f"slide-{slide_index}.html").resolve()
    try:
        path.relative_to(root_path)
    except ValueError:
        raise HTTPException(404, "not found")
    if not path.is_file():
        raise HTTPException(404, "slide not found")
    return FileResponse(path, media_type="text/html; charset=utf-8")


@app.get("/api/download")
def download() -> FileResponse:
    path = _state.get("render_path")
    meta = _state.get("render_meta")
    if not path or not meta:
        raise HTTPException(400, "아직 렌더된 파일이 없습니다")
    return FileResponse(path, media_type=meta["mime"], filename=Path(path).name)


# ---- PPT metadata --------------------------------------------------------

@app.get("/api/models")
def list_models() -> dict:
    from src import llm
    from src.config import IRIS_LLM_DEEP

    names = [
        n for n in llm.list_models()
        if not any(k in n.lower() for k in ("bge-m3", "nomic-embed", "embed"))
    ]
    default = llm.resolve_available_model(IRIS_LLM_DEEP, installed=names) or IRIS_LLM_DEEP
    return {"models": names, "default": default, "configured": IRIS_LLM_DEEP}


@app.get("/api/ppt/templates")
def ppt_templates() -> dict:
    from src.engine.output.deck.theme import templates_api_payload
    return templates_api_payload()


# ---- PPT source upload (multi-format) ------------------------------------
# V2.9 — PPT 탭 ①소스에서 .md/.txt 외에 .pdf/.docx/.pptx/.xlsx도 서버 변환으로
# 받는다. intake_upload(/api/intake/upload)와는 별도 경로 — PPT 탭은 raw 폴더에
# 저장하지 않고 변환된 마크다운 텍스트만 클라이언트에 돌려준다.
PPT_UPLOAD_MAX_BYTES = 20 * 1024 * 1024  # 20MB
PPT_SOURCE_EXTENSIONS = [".md", ".txt", ".pdf", ".docx", ".pptx", ".xlsx"]

_LEGACY_UPGRADE_HINT = {".ppt": ".pptx", ".doc": ".docx", ".xls": ".xlsx"}


@app.get("/api/ppt/source/formats")
def ppt_source_formats() -> dict:
    """PPT 탭 소스 업로드가 허용하는 포맷 메타. 클라이언트 dropzone accept/label 배선용."""
    mb = PPT_UPLOAD_MAX_BYTES // (1024 * 1024)
    return {
        "ok": True,
        "extensions": PPT_SOURCE_EXTENSIONS,
        "accept": ",".join(PPT_SOURCE_EXTENSIONS),
        "max_bytes": PPT_UPLOAD_MAX_BYTES,
        "label": f"{' · '.join(PPT_SOURCE_EXTENSIONS)} · 최대 {mb}MB",
    }


@app.post("/api/ppt/source/convert")
def ppt_source_convert(file: _UploadFile = None):
    """업로드된 파일을 마크다운으로 변환해 반환. 파일은 디스크에 남기지 않는다."""
    from src.engine.intake import converter

    if file is None or not file.filename:
        return JSONResponse({"error": "file required"}, status_code=400)

    filename = file.filename
    suffix = Path(filename).suffix.lower()
    content = file.file.read()
    size = len(content)

    if size == 0:
        return JSONResponse({"error": "빈 파일은 업로드할 수 없습니다"}, status_code=400)
    if size > PPT_UPLOAD_MAX_BYTES:
        mb = PPT_UPLOAD_MAX_BYTES // (1024 * 1024)
        return JSONResponse(
            {"error": f"파일이 너무 큽니다 (최대 {mb}MB)"}, status_code=413,
        )
    if suffix in converter.LEGACY_BINARY_SUFFIXES:
        upgrade = _LEGACY_UPGRADE_HINT.get(suffix, "")
        return JSONResponse(
            {"error": f"레거시 포맷({suffix})은 지원하지 않습니다. {upgrade}로 저장한 뒤 다시 업로드하세요."},
            status_code=415,
        )
    if suffix not in PPT_SOURCE_EXTENSIONS:
        return JSONResponse(
            {"error": f"지원하지 않는 포맷입니다: {suffix or '(확장자 없음)'}"}, status_code=415,
        )

    tmp_path: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)
        result = converter.convert_with_meta(tmp_path, enable_ocr=True)
    except converter.ConversionError as e:
        return JSONResponse({"error": f"변환 실패: {e}"}, status_code=422)
    finally:
        if tmp_path is not None:
            try:
                tmp_path.unlink()
            except Exception:
                pass

    return {
        "ok": True,
        "filename": filename,
        "text": result.body,
        "extraction_method": result.extraction_method,
        "pages": result.pages,
        "ocr_pages": result.ocr_pages,
    }


# =========================================================================
# Static files mount — API routes AFTER (order matters in FastAPI)
# =========================================================================
V31_DIR = Path(__file__).resolve().parent
CLIENT_DIR = V31_DIR / "client"
if CLIENT_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(CLIENT_DIR), html=True), name="client")
