"""PPT 탭 정적 셸 + API — 진단툴과 동일 기술(순수 HTML/CSS/JS + FastAPI JSON API).

Streamlit의 BaseWeb 위젯을 목업 디자인으로 리스킨하려던 시도가 3시간 넘게
CSS 특이도 싸움으로 끝나지 않았다(배경 누락 → 폰트 크기 → 스텝퍼 특이도 →
:has() 과매칭으로 패널이 220px로 짓눌림 → 포커스 링). 근본 원인은 Streamlit
컴포넌트 내부 스타일을 예측 없이 하나씩 덮어써야 하는 구조 자체였다.

이 서버는 그 문제를 우회한다: 화면은 client/dev/pptx_wizard_mock.html을
그대로 승격한 정적 HTML/CSS/JS이고(프레임워크 없음, diagnosis-tool의 v31
셸과 동일한 패턴), 실제 동작(소스 로딩·LLM 확장·설계·렌더)은 기존
src/tabs/pptx.py가 이미 쓰던 엔진 함수(expander/designer/renderer/
pptx_export)를 그대로 재사용하는 JSON API로 노출한다.

실행: uvicorn web.server:app --port 8766 --reload
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dataclasses import asdict
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="iris-hub-web", version="0.1")

CLIENT_DIR = Path(__file__).resolve().parent / "client"

# 단일 사용자 로컬 도구 — 세션 분리 없이 프로세스 전역 상태 하나로 충분
# (Streamlit의 st.session_state와 동일한 역할, 멀티유저 아님).
_STATE: dict[str, Any] = {
    "expand_md": None,
    "expand_meta": None,
    "deck": None,
    "render_path": None,
    "render_meta": None,
}


def _default_meta(lang: str) -> dict:
    return {
        "company": "赛美特",
        "title": "",
        "subtitle": "",
        "date": "",
        "lang": lang,
    }


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/sources")
def list_sources() -> dict:
    from src.tabs.pptx import _list_archive_content_md, _list_docs_md

    archive = _list_archive_content_md()
    docs = _list_docs_md()
    return {
        "archive": [{"id": i, "label": label} for i, (label, _p) in enumerate(archive)],
        "docs": [{"id": i, "label": label} for i, (label, _p) in enumerate(docs)],
    }


@app.get("/api/sources/content")
def source_content(kind: str, id: int) -> dict:
    from src.tabs.pptx import _list_archive_content_md, _list_docs_md

    items = _list_archive_content_md() if kind == "archive" else _list_docs_md()
    if not (0 <= id < len(items)):
        raise HTTPException(404, "source not found")
    label, path = items[id]
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        raise HTTPException(500, f"파일 읽기 실패: {e}")
    return {"label": label, "text": text}


@app.get("/api/models")
def list_models() -> dict:
    from src import llm
    from src.config import IRIS_LLM_DEEP

    names = [
        n for n in llm.list_models()
        if not any(k in n.lower() for k in ("bge-m3", "nomic-embed", "embed"))
    ]
    # 설정 deep이 미설치면 정책 우선순위로 fallback (embedding 제외).
    default = llm.resolve_available_model(IRIS_LLM_DEEP, installed=names) or IRIS_LLM_DEEP
    return {"models": names, "default": default, "configured": IRIS_LLM_DEEP}


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
        result = expander.expand_for_slides(
            req.md_text, meta, model=req.model, timeout=900,
            lang=req.lang, pages=pages,
        )
    except expander.ExpansionError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=422)

    _STATE["expand_md"] = result.md
    _STATE["expand_meta"] = meta
    _STATE["deck"] = None
    _STATE["render_path"] = None
    return {
        "ok": True, "md": result.md, "model": result.model,
        "elapsed": result.elapsed_ms / 1000,
        "in": result.original_chars, "out": result.output_chars,
    }


class DesignReq(BaseModel):
    model: Optional[str] = None
    lang: str = "한국어"
    target_slides: Optional[int] = None


@app.post("/api/design")
def run_design(req: DesignReq) -> dict:
    from src.engine.output.deck import designer

    md = _STATE.get("expand_md")
    if not md:
        raise HTTPException(400, "먼저 ②확장을 실행하세요")
    meta = _STATE.get("expand_meta") or _default_meta(req.lang)
    try:
        deck = designer.design_deck(
            md, meta, model=req.model, timeout=600,
            pre_expanded=True, target_slides=req.target_slides,
        )
    except designer.DesignError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=422)

    _STATE["deck"] = deck
    _STATE["render_path"] = None
    slides = [
        {"pattern": s.pattern, "title": s.data.get("title") or s.pattern}
        for s in deck.slides
    ]
    return {"ok": True, "slides": slides, "page_count": len(deck.slides)}


class RenderReq(BaseModel):
    format: str = "PDF"  # "PDF" | "PPTX"


@app.post("/api/render")
def run_render(req: RenderReq) -> dict:
    deck = _STATE.get("deck")
    if not deck:
        raise HTTPException(400, "먼저 ③설계를 실행하세요")

    try:
        if req.format.upper() == "PDF":
            from src.engine.output.deck.renderer import render_deck_to_pdf
            out_path = render_deck_to_pdf(deck)
            mime = "application/pdf"
        else:
            from src.engine.output.deck.pptx_export import render_deck_to_pptx
            out_path = render_deck_to_pptx(deck)
            mime = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    except Exception as e:
        return JSONResponse(
            {"ok": False, "error": f"{type(e).__name__}: {e}"}, status_code=500,
        )

    _STATE["render_path"] = out_path
    _STATE["render_meta"] = {"mime": mime, "fmt": req.format.upper()}
    size_kb = out_path.stat().st_size / 1024
    return {
        "ok": True, "fmt": req.format.upper(), "size_kb": size_kb,
        "page_count": len(deck.slides), "download_url": "/api/download",
    }


@app.get("/api/download")
def download() -> FileResponse:
    path = _STATE.get("render_path")
    meta = _STATE.get("render_meta")
    if not path or not meta:
        raise HTTPException(400, "아직 렌더된 파일이 없습니다")
    return FileResponse(path, media_type=meta["mime"], filename=Path(path).name)


# 정적 클라이언트 셸 — 반드시 API 라우트들 뒤에 mount (그렇지 않으면 /api/*가
# StaticFiles의 404 처리에 먼저 잡힘).
app.mount("/", StaticFiles(directory=str(CLIENT_DIR), html=True), name="client")
