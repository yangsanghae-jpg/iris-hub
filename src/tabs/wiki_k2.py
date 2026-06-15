"""탭: 📚 위키 — K2 분류 결과 뷰 (도메인 그리드 + 자료 테이블 + 상세 패널).

설계:
  - 도메인 그리드: industry × area 자료 카운트. 셀 클릭으로 필터.
  - 자료 테이블: 선택된 분면의 documents + document_meta JOIN.
  - 상세 패널: 행 클릭 시 우측에 summary/topics/entities/concepts + 원문.

기존 위키 placeholder (K5 wiki server 상태)는 placeholders.render_wiki()에 보존.
본 모듈은 *그 위에 K2 결과 시각화*만 박는다.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import streamlit as st

DB_PATH = Path("/Users/iris/Documents/0Dev/iris-system/knowledge/_index.db")


def _grid_counts() -> dict[tuple[str, str], int]:
    """industry × area 그리드 카운트."""
    if not DB_PATH.exists():
        return {}
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            "SELECT industry, area, COUNT(*) "
            "FROM documents "
            "WHERE industry IS NOT NULL OR area IS NOT NULL "
            "GROUP BY industry, area"
        ).fetchall()
        return {(ind or "—", area or "—"): n for ind, area, n in rows}
    finally:
        conn.close()


def _list_in_cell(industry: str, area: str) -> list[dict]:
    """selected industry/area 분면의 자료 목록 (documents + document_meta JOIN)."""
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        # document_meta 테이블 존재 확인
        has_meta = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='document_meta'"
        ).fetchone() is not None

        if has_meta:
            sql = """
              SELECT d.doc_id, d.title, d.path, d.level, d.fetched_at,
                     m.summary, m.topics_json, m.entities_json, m.concepts_json,
                     m.confidence, m.classifier_version, m.fallback_used, m.k2_at
              FROM documents d
              LEFT JOIN document_meta m ON d.doc_id = m.doc_id
              WHERE d.industry = ? AND d.area = ?
              ORDER BY COALESCE(m.k2_at, d.fetched_at) DESC
            """
        else:
            sql = """
              SELECT d.doc_id, d.title, d.path, d.level, d.fetched_at,
                     '' AS summary, '[]' AS topics_json, '[]' AS entities_json,
                     '[]' AS concepts_json, 0 AS confidence,
                     '' AS classifier_version, 0 AS fallback_used, '' AS k2_at
              FROM documents d
              WHERE d.industry = ? AND d.area = ?
              ORDER BY d.fetched_at DESC
            """

        rows = conn.execute(sql, (industry, area)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _doc_detail(doc_id: str) -> dict | None:
    """1건 상세 — JOIN + path."""
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            """SELECT d.*, m.summary, m.topics_json, m.entities_json,
                      m.concepts_json, m.confidence, m.reason, m.k2_at,
                      m.k2_ms, m.fallback_used, m.classifier_version
               FROM documents d
               LEFT JOIN document_meta m ON d.doc_id = m.doc_id
               WHERE d.doc_id = ?""",
            (doc_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def render() -> None:
    st.markdown("## 📚 위키 — K2 분류 뷰")
    st.caption(
        "K1→K2→K3을 거친 자료를 *도메인 그리드*로 본다. 셀을 클릭하면 자료 목록, "
        "행을 클릭하면 상세 패널."
    )

    counts = _grid_counts()
    if not counts:
        st.info("아직 분류된 자료가 없습니다. 📦 데이터 탭의 [🔄 재처리]로 분석을 돌리세요.")
        return

    # 그리드 축 — 실제 박힌 industry/area 합집합
    industries = sorted({ind for (ind, _), _ in counts.items()})
    areas = sorted({area for (_, area), _ in counts.items()})

    # ─── 도메인 그리드 ────────────────────────────────────────────────────
    st.markdown("### 📊 도메인 그리드 (industry × area)")
    st.caption("셀 클릭 시 해당 분면 자료가 아래에 표시됨.")

    # 헤더 행 (area)
    header_cols = st.columns([1] + [1] * len(areas))
    header_cols[0].markdown("**industry / area**")
    for i, area in enumerate(areas):
        header_cols[i + 1].markdown(f"**{area}**")

    # 데이터 행
    for ind in industries:
        row_cols = st.columns([1] + [1] * len(areas))
        row_cols[0].markdown(f"**{ind}**")
        for i, area in enumerate(areas):
            n = counts.get((ind, area), 0)
            label = f"{n}" if n else "·"
            if n > 0:
                if row_cols[i + 1].button(label, key=f"cell_{ind}_{area}",
                                          use_container_width=True):
                    st.session_state["wiki_sel_ind"] = ind
                    st.session_state["wiki_sel_area"] = area
            else:
                row_cols[i + 1].markdown(f"<div style='text-align:center;color:#aaa;'>{label}</div>",
                                          unsafe_allow_html=True)

    # ─── 선택된 분면 자료 목록 ────────────────────────────────────────────
    sel_ind = st.session_state.get("wiki_sel_ind")
    sel_area = st.session_state.get("wiki_sel_area")
    if not (sel_ind and sel_area):
        st.divider()
        st.caption("👆 그리드의 셀을 클릭해서 분면을 선택하세요.")
        return

    st.divider()
    st.markdown(f"### 📁 자료 — `industry={sel_ind}` × `area={sel_area}`")

    docs = _list_in_cell(sel_ind, sel_area)
    if not docs:
        st.info("이 분면에 자료가 없습니다.")
        return

    # 자료 목록 — 펼침 형식 (테이블보다 markdown 친화)
    for doc in docs:
        topics = []
        try:
            topics = json.loads(doc.get("topics_json") or "[]")
        except Exception:
            pass

        confidence = doc.get("confidence") or 0
        is_fb = bool(doc.get("fallback_used"))
        badge = " 🟡 fallback" if is_fb else (" 🟢 LLM" if confidence > 0 else " ⚪ 미분석")

        title = doc.get("title") or doc["doc_id"]
        summary = doc.get("summary") or "(K2 분석 미완)"

        with st.expander(f"**{title}**{badge}  ·  conf {confidence:.2f}", expanded=False):
            st.caption(f"📝 {summary}")
            if topics:
                st.caption("🏷 " + " · ".join(f"`{t}`" for t in topics))

            # 상세 펼침
            entities, concepts = [], []
            try:
                entities = json.loads(doc.get("entities_json") or "[]")
                concepts = json.loads(doc.get("concepts_json") or "[]")
            except Exception:
                pass

            if entities:
                st.caption("👥 entities: " + " · ".join(f"`{e}`" for e in entities))
            if concepts:
                st.caption("💡 concepts: " + " · ".join(f"`{c}`" for c in concepts))

            cc1, cc2, cc3 = st.columns(3)
            cc1.caption(f"level: `{doc.get('level') or '—'}`")
            cc2.caption(f"k2: `{doc.get('classifier_version') or '—'}`")
            cc3.caption(f"k2_at: `{doc.get('k2_at') or '—'}`")

            # 원문 펼침
            path = doc.get("path", "")
            with st.expander("📄 원문 보기", expanded=False):
                try:
                    p = Path(path)
                    if p.exists():
                        text = p.read_text(encoding="utf-8")
                        # frontmatter 잘라내고 본문만
                        if text.startswith("---\n"):
                            parts = text[4:].split("\n---\n", 1)
                            if len(parts) == 2:
                                text = parts[1]
                        # 마크다운 렌더링
                        tab_render, tab_raw = st.tabs(["✨ 미리보기", "📝 원본"])
                        with tab_render:
                            st.markdown(text.strip())
                        with tab_raw:
                            st.code(text.strip(), language="markdown")
                    else:
                        st.warning(f"원문 파일 없음: {path}")
                except Exception as e:
                    st.caption(f"읽기 실패: {e}")

            st.caption(f"경로: `{path}`")
