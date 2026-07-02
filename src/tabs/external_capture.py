"""탭: 🌐 외부응답 — GPT/Gemini/Claude 등 외부 LLM 응답을 *보이는 그대로* 박는 자리.

설계 원칙 (사용자 합의, 2026-06-15):
  - 본문 변형 X. 카피→붙여넣기 그대로 보존.
  - 관리 단위 = "이벤트" (출처 + 이벤트명 + 본문 + 시각).
  - 분류는 *사후* 작업이라 본 탭에서 강요하지 않음 — 단 저장 시 자동 추천.
  - 기존 `📥 입력` 탭은 손대지 않음 — 본 탭은 *별도 자리*.

저장 위치:
  iris-system/knowledge/raw/_external/<source>/<slug>_<ts>.md

저장 후 흐름 (사용자 합의 2026-06-15):
  1. raw .md 파일 박기 (frontmatter + body)
  2. classify.suggest_classification() 으로 industry/area/level 추천
  3. raw_intake 헬퍼 함수로 documents/chunks/FTS 박기 (1건만)
  4. classify 결과를 documents UPDATE (industry/area/level)
"""
from __future__ import annotations

import datetime as dt
import re
import sqlite3
from pathlib import Path

import streamlit as st

from src.config import IRIS_DB_PATH, IRIS_KNOWLEDGE_EXTERNAL
from src.ui_kit import hub_kpi_grid, hub_pagebar

# V2.6.3.3: iris-knowledge로 경로 단일화. legacy IRIS_SYSTEM·sys.path hack 제거.
EXTERNAL_DIR = IRIS_KNOWLEDGE_EXTERNAL
DB_PATH = IRIS_DB_PATH

SOURCES = [
    "chatgpt",
    "gemini",
    "claude",
    "perplexity",
    "grok",
    "copilot",
    "mistral",
    "openwebui-chat",
    "manual-note",
    "meeting-memo",
    "other",
]


_CSS = """
<style>
.external-capture-grid {
  display:grid;
  grid-template-columns:minmax(0, 1.28fr) minmax(300px, 0.72fr);
  gap:14px;
  align-items:start;
  margin-top:12px;
}
.external-panel {
  border:1px solid rgba(47,128,196,0.16);
  border-radius:14px;
  background:linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
  box-shadow:0 8px 22px rgba(16,24,40,0.045);
  overflow:hidden;
  margin-bottom:14px;
}
.external-panel-head {
  display:flex;
  justify-content:space-between;
  align-items:flex-start;
  gap:12px;
  padding:12px 14px;
  border-bottom:1px solid rgba(47,128,196,0.10);
  background:rgba(47,128,196,0.035);
}
.external-panel-title {
  color:#172033;
  font-size:0.9rem;
  font-weight:850;
}
.external-panel-subtitle {
  margin-top:3px;
  color:#667085;
  font-size:0.76rem;
  line-height:1.4;
}
.external-panel-body {
  padding:14px;
}
.external-pill {
  display:inline-flex;
  align-items:center;
  padding:4px 8px;
  border-radius:999px;
  background:rgba(47,128,196,0.10);
  color:#2f80c4;
  font-size:0.7rem;
  line-height:1;
  font-weight:850;
  white-space:nowrap;
}
.external-path-box,
.external-note-box {
  padding:10px 12px;
  border:1px solid rgba(47,128,196,0.14);
  border-radius:11px;
  background:rgba(47,128,196,0.045);
  color:#475467;
  font-size:0.8rem;
  line-height:1.5;
  overflow-wrap:anywhere;
}
.external-recent-row {
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:12px;
  padding:10px 12px;
  border:1px solid rgba(47,128,196,0.12);
  border-radius:11px;
  background:linear-gradient(180deg, #ffffff 0%, #f9fbfd 100%);
  margin-bottom:8px;
}
.external-recent-title {
  color:#172033;
  font-size:0.84rem;
  font-weight:800;
}
.external-recent-meta {
  color:#667085;
  font-size:0.74rem;
  margin-top:3px;
}
.hub-pagebar {
  min-height:82px;
  overflow:visible !important;
  margin-top:10px !important;
  margin-bottom:14px !important;
  padding-top:16px !important;
  padding-bottom:16px !important;
  border-color:rgba(47,128,196,0.18) !important;
  background:linear-gradient(135deg, #ffffff 0%, #f7fbff 100%) !important;
  box-shadow:0 10px 28px rgba(16,24,40,0.055);
}
.hub-pagebar-title {
  font-size:1.32rem !important;
  line-height:1.28 !important;
  color:#101828 !important;
}
.hub-pagebar-desc {
  line-height:1.5 !important;
  overflow:visible !important;
}
.hub-pagebar-title-row {
  align-items:center !important;
  min-height:28px;
}
.hub-kpi-card,
div[data-testid="stMetric"] {
  border-color:rgba(47,128,196,0.16) !important;
  background:linear-gradient(180deg, #ffffff 0%, #f8fbfe 100%) !important;
  box-shadow:0 8px 22px rgba(16,24,40,0.045);
}
@media (max-width: 980px) {
  .external-capture-grid,
  .hub-kpi-grid {
    grid-template-columns:1fr !important;
  }
}
</style>
"""


def _format_count(value: int) -> str:
    return f"{value:,}"


def _render_panel_header(title: str, subtitle: str, pill: str | None = None) -> None:
    pill_html = f"<span class='external-pill'>{pill}</span>" if pill else ""
    st.markdown(
        f"""
<div class="external-panel-head">
  <div>
    <div class="external-panel-title">{title}</div>
    <div class="external-panel-subtitle">{subtitle}</div>
  </div>
  {pill_html}
</div>
""",
        unsafe_allow_html=True,
    )


def _render_last_saved_panel() -> None:
    _render_panel_header(
        "저장 결과",
        "직전 저장 이벤트의 K2 분석과 인제스트 상태를 즉시 확인합니다.",
    )
    if "ext_last_saved" not in st.session_state:
        st.markdown(
            "<div class='external-panel-body'><div class='external-note-box'>아직 이 세션에서 저장한 이벤트가 없습니다. 저장 후 K2 분석 결과가 여기에 표시됩니다.</div></div>",
            unsafe_allow_html=True,
        )
        return

    last = st.session_state["ext_last_saved"]
    with st.container():
        st.success(
            f"저장 완료 — `{last['filename']}` · {last['source']} · {last['size']:,} bytes"
        )
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        metric_col1.metric("industry", last.get("industry") or "—")
        metric_col2.metric("area", last.get("area") or "—")
        metric_col3.metric("level", last.get("level") or "—")
        metric_col4.metric("chunks", last.get("ingest_chunks", 0))

        if last.get("summary"):
            st.caption(f"요약: {last['summary']}")

        tag_lines = []
        for label, values in [
            ("주제", last.get("topics", [])),
            ("고유명사", last.get("entities", [])),
            ("개념", last.get("concepts", [])),
        ]:
            if values:
                tag_lines.append(f"**{label}:** " + " · ".join(f"`{value}`" for value in values))
        for tag_line in tag_lines:
            st.caption(tag_line)

        version = last.get("k2_version", "")
        fallback_label = "fallback" if last.get("k2_fallback", False) else "LLM"
        st.caption(f"K2: {version} · {fallback_label} · {last.get('k2_ms', 0)} ms")

        if last.get("ingest_ok"):
            st.caption("documents/chunks/FTS + document_meta 반영 완료")
        else:
            st.warning(f"인제스트 실패(raw .md는 보존됨): {last.get('ingest_error') or '알 수 없음'}")


def _render_storage_panel() -> None:
    _render_panel_header(
        "저장 위치",
        "외부 응답은 source별 폴더에 원문 markdown으로 보존됩니다.",
    )
    st.markdown(
        f"<div class='external-panel-body'><div class='external-path-box'>{EXTERNAL_DIR}</div></div>",
        unsafe_allow_html=True,
    )
    if st.button("폴더 열기", key="ext_open_folder", use_container_width=True):
        import subprocess
        subprocess.Popen(["open", str(EXTERNAL_DIR)])


def _render_recent_events() -> None:
    _render_panel_header(
        "최근 박힌 이벤트",
        "최근 저장된 외부 응답을 펼쳐서 미리보기와 원본으로 확인합니다.",
    )
    recent = _list_recent(n=10)
    if not recent:
        st.markdown(
            "<div class='external-panel-body'><div class='external-note-box'>아직 박힌 이벤트가 없습니다.</div></div>",
            unsafe_allow_html=True,
        )
        return

    st.caption(f"총 {len(recent)}건 (최근순)")
    for idx, item in enumerate(recent):
        st.markdown(
            f"""
<div class="external-recent-row">
  <div>
    <div class="external-recent-title">{item['title']}</div>
    <div class="external-recent-meta">{item['mtime'].strftime('%Y-%m-%d %H:%M')} · {item['size']:,} bytes</div>
  </div>
  <span class="external-pill">{item['source']}</span>
</div>
""",
            unsafe_allow_html=True,
        )
        with st.expander("미리보기 / 원본", expanded=False):
            try:
                full_text = item["path"].read_text(encoding="utf-8")
                meta_block, body_block = "", full_text
                if full_text.startswith("---\n"):
                    parts = full_text[4:].split("\n---\n", 1)
                    if len(parts) == 2:
                        meta_block, body_block = parts[0], parts[1]

                if meta_block:
                    with st.expander("메타 frontmatter", expanded=False):
                        st.code(meta_block, language="yaml")

                tab_render, tab_raw = st.tabs(["미리보기", "원본"])
                with tab_render:
                    st.markdown(body_block.strip())
                with tab_raw:
                    st.code(body_block.strip(), language="markdown")

                action_col, path_col = st.columns([1, 4])
                with action_col:
                    if st.button("폴더에서 열기", key=f"ext_open_{idx}", use_container_width=True):
                        import subprocess
                        subprocess.Popen(["open", "-R", str(item["path"])])
                with path_col:
                    st.caption(f"경로: `{item['path']}`")
            except Exception as error:
                st.caption(f"읽기 실패: {error}")


# ─── 유틸 ────────────────────────────────────────────────────────────────────

def _slug(s: str, maxlen: int = 50) -> str:
    """이벤트명 → 파일명 안전 슬러그. 공백·특수문자는 _, 한글·영숫자는 유지."""
    s = s.strip()
    s = re.sub(r"[^\w가-힣\-]+", "_", s, flags=re.UNICODE)
    s = re.sub(r"_+", "_", s).strip("_")
    return s[:maxlen] or "event"


def _now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def _build_frontmatter(*, title: str, source: str, prompt: str | None = None) -> str:
    """YAML frontmatter — 본문 보존이 본질이라 키는 최소만."""
    lines = ["---", f"title: {title}", f"source: {source}", f"captured_at: {_now_iso()}"]
    if prompt and prompt.strip():
        # 줄바꿈 있는 prompt는 YAML block 스타일로
        if "\n" in prompt:
            lines.append("prompt: |")
            for ln in prompt.splitlines():
                lines.append(f"  {ln}")
        else:
            lines.append(f"prompt: {prompt.strip()}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def _save_event(*, title: str, source: str, body: str, prompt: str | None = None) -> Path:
    """raw/_external/<source>/<slug>_<ts>.md 로 저장."""
    target_dir = EXTERNAL_DIR / source
    target_dir.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"{_slug(title)}_{ts}.md"
    target = target_dir / fname
    md = _build_frontmatter(title=title, source=source, prompt=prompt) + body.rstrip() + "\n"
    target.write_text(md, encoding="utf-8")
    return target


def _ingest_one(path: Path, *, industry: str | None, area: str | None,
                level: str | None) -> dict:
    """1건 인제스트 — raw_intake 내부 함수 직접 사용.

    raw_intake.main()은 RAW_DIR 루트만 읽기 때문에 _external/<source>/ 하위
    파일은 자동으로 안 들어감. 본 헬퍼가 1건만 정확히 박아준다.

    반환: {"ok": bool, "doc_id": str | None, "chunks": int, "error": str | None}
    """
    try:
        from src.ingest.raw_intake import (
            doc_id_for, parse_frontmatter, split_chunks, upsert_raw_doc,
        )
        from src.ingest.fts_sync import rebuild_all
    except Exception as e:
        return {"ok": False, "doc_id": None, "chunks": 0,
                "error": f"raw_intake import 실패: {e}"}

    if not DB_PATH.exists():
        return {"ok": False, "doc_id": None, "chunks": 0,
                "error": f"DB 없음: {DB_PATH}"}

    try:
        text = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)
        title = meta.get("title") or path.stem
        chunks = split_chunks(body)
        if not chunks:
            return {"ok": False, "doc_id": None, "chunks": 0,
                    "error": "본문 chunk 0개"}

        doc_id = doc_id_for(path)
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            upsert_raw_doc(conn, doc_id, path, title, chunks)

            # classify 결과 UPDATE — raw_intake가 박아준 NULL을 덮어씀
            if any(v is not None for v in (industry, area, level)):
                conn.execute(
                    "UPDATE documents SET industry=?, area=?, level=? "
                    "WHERE doc_id=?",
                    (industry, area, level, doc_id),
                )

            # FTS 동기 (raw_intake.main이 끝에 호출하던 것)
            rebuild_all(conn)
            conn.commit()
        finally:
            conn.close()

        return {"ok": True, "doc_id": doc_id, "chunks": len(chunks),
                "error": None}
    except Exception as e:
        return {"ok": False, "doc_id": None, "chunks": 0,
                "error": f"{type(e).__name__}: {e}"}


def _list_recent(n: int = 10) -> list[dict]:
    """최근 박힌 이벤트 N개 — mtime 내림차순."""
    if not EXTERNAL_DIR.exists():
        return []
    files: list[Path] = []
    for src_dir in EXTERNAL_DIR.iterdir():
        if not src_dir.is_dir():
            continue
        for p in src_dir.glob("*.md"):
            files.append(p)
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
                "path": p,
                "title": title or p.stem,
                "source": source,
                "mtime": dt.datetime.fromtimestamp(p.stat().st_mtime),
                "size": p.stat().st_size,
            })
        except Exception:
            continue
    return out


# ─── UI ──────────────────────────────────────────────────────────────────────

def _form_keys() -> dict[str, str]:
    """위젯 키 — 저장마다 reset_counter 증가로 새 키 생성.

    Streamlit은 위젯 인스턴스화 후 같은 key의 session_state를 직접 수정 못 함.
    저장 후 폼을 비우려면 *새 위젯*을 만들어야 하므로 키 자체를 바꾼다.
    """
    n = st.session_state.get("ext_reset_counter", 0)
    return {
        "title":  f"ext_title_{n}",
        "prompt": f"ext_prompt_{n}",
        "body":   f"ext_body_{n}",
        "source": f"ext_source_{n}",
    }


def _bump_form() -> None:
    """저장 직후 호출 — 다음 rerun에서 위젯 키가 새로 만들어져 빈 상태."""
    st.session_state["ext_reset_counter"] = st.session_state.get("ext_reset_counter", 0) + 1


def _render_capture_form() -> None:
    _render_panel_header(
        "새 이벤트 박기",
        "이벤트명, 출처, 원본 질의, 답변 본문을 한 화면에서 입력합니다.",
        "Primary",
    )

    keys = _form_keys()
    title_col, source_col = st.columns([3, 1])
    with title_col:
        title = st.text_input(
            "이벤트명 *",
            placeholder="예: MES 핵심 개념 정리 v3",
            key=keys["title"],
        )
    with source_col:
        source = st.selectbox("출처", SOURCES, index=0, key=keys["source"])

    prompt = st.text_input(
        "원본 질의 (선택)",
        placeholder="예: MES 핵심 개념을 7장 분량으로 정리해줘",
        key=keys["prompt"],
    )

    body = st.text_area(
        "답변 본문 * (markdown 그대로 붙여넣기)",
        height=520,
        placeholder="여기에 GPT/Gemini/Claude 답변을 그대로 붙여넣기...",
        key=keys["body"],
    )

    st.markdown(
        "<div class='external-note-box'>저장 시 raw markdown 생성 → K2 분석 → documents/chunks/FTS 반영 순서로 처리됩니다.</div>",
        unsafe_allow_html=True,
    )

    if st.button(
        "저장 실행",
        type="primary",
        disabled=not (title and body),
        use_container_width=True,
        key="ext_save_btn",
    ):
        try:
            target = _save_event(
                title=title.strip(),
                source=source,
                body=body,
                prompt=prompt.strip() if prompt else None,
            )

            k2_result = None
            from src.config import IRIS_LLM_DEEP
            with st.spinner(f"K2 분석 중 ({IRIS_LLM_DEEP} — 5~60초 예상)..."):
                try:
                    from src import k2
                    k2_result = k2.analyze(title.strip(), body, timeout=60.0)
                except Exception as e:
                    from src.classify import suggest_classification
                    rule = suggest_classification(title.strip(), body)
                    from src.k2 import K2Result
                    k2_result = K2Result(
                        industry=rule.get("industry"),
                        area=rule.get("area"),
                        level=rule.get("level"),
                        topics=rule.get("keywords", []),
                        summary="(K2 모듈 실패)",
                        reason=f"k2 import/call 실패: {type(e).__name__}: {e}",
                        confidence=0.2,
                        classifier_version="rule-emergency-fallback",
                        fallback_used=True,
                        error=str(e),
                    )

            ing = _ingest_one(
                target,
                industry=k2_result.industry,
                area=k2_result.area,
                level=k2_result.level,
            )

            if ing.get("ok") and ing.get("doc_id"):
                try:
                    from src import document_meta
                    document_meta.ensure_schema()
                    document_meta.upsert(
                        ing["doc_id"],
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
                except Exception as e:
                    st.warning(f"document_meta 저장 실패: {e}")

            st.session_state["ext_last_saved"] = {
                "filename": target.name,
                "source": source,
                "size": target.stat().st_size,
                "path": str(target),
                "industry": k2_result.industry,
                "area": k2_result.area,
                "level": k2_result.level,
                "summary": k2_result.summary,
                "topics": k2_result.topics,
                "entities": k2_result.entities,
                "concepts": k2_result.concepts,
                "k2_ms": k2_result.elapsed_ms,
                "k2_version": k2_result.classifier_version,
                "k2_fallback": k2_result.fallback_used,
                "k2_reason": k2_result.reason,
                "ingest_ok": ing.get("ok", False),
                "ingest_chunks": ing.get("chunks", 0),
                "ingest_error": ing.get("error"),
            }
            _bump_form()
            st.toast(f"{target.name} 저장됨")
            st.rerun()
        except Exception as e:
            st.error(f"저장 실패: {e}")


def render() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    hub_pagebar(
        "외부응답",
        "External Capture",
        "원문 보존을 우선하고, 분류·요약·인덱싱은 저장 후 자동 실행합니다.",
        "Capture Ready",
    )

    if not EXTERNAL_DIR.exists():
        try:
            EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            st.error(f"저장 자리 생성 실패: {e}")
            return

    recent = _list_recent(n=10)
    hub_kpi_grid([
        ("Storage", "raw", "_external"),
        ("Sources", _format_count(len(SOURCES)), "providers"),
        ("K2", "auto", "after save"),
        ("Recent", _format_count(len(recent)), "events"),
    ])

    left_column, right_column = st.columns([1.28, 0.72], gap="medium")
    with left_column:
        with st.container(border=True):
            _render_capture_form()

    with right_column:
        with st.container(border=True):
            _render_last_saved_panel()

        with st.container(border=True):
            _render_storage_panel()

    with st.container(border=True):
        _render_recent_events()
