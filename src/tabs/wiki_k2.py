"""탭: 📚 위키 — 3-파트 분류 뷰 (V2.5.3 §3.10 v2).

3 파트 (자료 1건은 여러 파트에 동시 노출, 의도된 중복):
  파트1. 산업 × 자동화 (8 산업 + 일반행) × (auto1/auto2/auto3/aiplus)
  파트2. 시스템 도메인 (APS/MES/ERP/WMS/QMS/SCM)
  파트3. 관리 (조직 · 거버넌스 · 실행)

UI 정책 (그래프 탭과 동일):
  - 헤더/캡션 → 한 줄 요약
  - 컨트롤 → expander (기본 접힘)
  - 셀 클릭 → 자료 리스트 + 파트별 발췌 (blurb_*)
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import streamlit as st

DB_PATH = Path("/Users/iris/Documents/0Dev/iris-system/knowledge/_index.db")

INDUSTRIES = ["A", "B", "C", "D", "E", "F", "G", "H", "general"]
INDUSTRY_LABELS = {
    "A": "A 반도체", "B": "B 일반 제조", "C": "C 디스플레이", "D": "D 제약·바이오",
    "E": "E 기타", "F": "F", "G": "G", "H": "H", "general": "산업 무관",
}
AUTOMATION = ["auto1", "auto2", "auto3", "aiplus"]
AUTOMATION_LABELS = {
    "auto1": "auto1\n수작업", "auto2": "auto2\n부분도입",
    "auto3": "auto3\n통합", "aiplus": "aiplus\nAI/예측",
}
SYSTEMS = ["APS", "MES", "ERP", "WMS", "QMS", "SCM"]
MGMT_GROUPS = [
    ("조직",      ["org_design", "org_role"]),
    ("거버넌스",  ["gov_committee", "gov_kpi"]),
    ("실행계획",  ["exec_phase", "exec_milestone"]),
]
MGMT_LABELS = {
    "org_design": "조직설계", "org_role": "R&R",
    "gov_committee": "위원회", "gov_kpi": "KPI",
    "exec_phase": "단계계획", "exec_milestone": "마일스톤",
}


# ─── 데이터 로드 ──────────────────────────────────────────────────────
def _all_docs() -> list[dict]:
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        # document_meta 컬럼 존재 여부 (마이그레이션 전 안전)
        cols = {r[1] for r in conn.execute("PRAGMA table_info(document_meta)")}
        meta_extra = (
            ", m.automation_levels_json, m.system_domains_json, m.mgmt_categories_json,"
            " m.blurb_industry, m.blurb_system, m.blurb_mgmt"
            if "automation_levels_json" in cols else
            ", '[]' AS automation_levels_json, '[]' AS system_domains_json,"
            " '[]' AS mgmt_categories_json, '' AS blurb_industry,"
            " '' AS blurb_system, '' AS blurb_mgmt"
        )
        sql = f"""
          SELECT d.doc_id, d.title, d.path, d.industry, d.area, d.level,
                 d.fetched_at, d.lane,
                 m.summary, m.topics_json, m.confidence, m.fallback_used,
                 m.classifier_version, m.k2_at
                 {meta_extra}
            FROM documents d
            LEFT JOIN document_meta m ON d.doc_id = m.doc_id
           ORDER BY d.fetched_at DESC
        """
        return [dict(r) for r in conn.execute(sql).fetchall()]
    finally:
        conn.close()


def _parse(s: str | None) -> list[str]:
    if not s:
        return []
    try:
        v = json.loads(s)
        return [str(x) for x in v] if isinstance(v, list) else []
    except Exception:
        return []


def _industry_key(d: dict) -> str:
    """파트1 행 키 — industry가 없으면 'general' (산업 무관)."""
    return d["industry"] or "general"


# ─── 카운트/필터 ──────────────────────────────────────────────────────
def _count_p1(docs: list[dict]) -> dict[tuple[str, str], list[dict]]:
    """(industry, automation) → docs"""
    out: dict[tuple[str, str], list[dict]] = {}
    for d in docs:
        ind = _industry_key(d)
        levels = _parse(d.get("automation_levels_json"))
        if not levels:
            continue
        for lvl in levels:
            out.setdefault((ind, lvl), []).append(d)
    return out


def _count_p2(docs: list[dict]) -> dict[str, list[dict]]:
    """system → docs"""
    out: dict[str, list[dict]] = {}
    for d in docs:
        for sys in _parse(d.get("system_domains_json")):
            out.setdefault(sys, []).append(d)
    return out


def _count_p3(docs: list[dict]) -> dict[str, list[dict]]:
    """mgmt_category → docs"""
    out: dict[str, list[dict]] = {}
    for d in docs:
        for cat in _parse(d.get("mgmt_categories_json")):
            out.setdefault(cat, []).append(d)
    return out


# ─── 자료 리스트 렌더 ────────────────────────────────────────────────
def _render_docs(docs: list[dict], blurb_field: str) -> None:
    """선택된 셀의 자료를 펼침 카드로 표시."""
    if not docs:
        st.info("이 분면에 자료가 없습니다.")
        return

    for d in docs:
        title = d.get("title") or d["doc_id"]
        confidence = d.get("confidence") or 0
        is_fb = bool(d.get("fallback_used"))
        badge = " 🟡" if is_fb else (" 🟢" if confidence > 0 else " ⚪")
        blurb = (d.get(blurb_field) or "").strip() or (d.get("summary") or "(K2 분석 미완)")

        with st.expander(f"**{title}**{badge}  ·  conf {confidence:.2f}"):
            st.caption(f"📝 {blurb}")

            topics = _parse(d.get("topics_json"))
            if topics:
                st.caption("🏷 " + " · ".join(f"`{t}`" for t in topics))

            cc1, cc2, cc3 = st.columns(3)
            cc1.caption(f"산업: `{d.get('industry') or '—'}` · area `{d.get('area') or '—'}`")
            cc2.caption(f"자동화: `{', '.join(_parse(d.get('automation_levels_json'))) or '—'}`")
            cc3.caption(f"시스템: `{', '.join(_parse(d.get('system_domains_json'))) or '—'}`")

            path = d.get("path", "")
            with st.expander("📄 원문 보기", expanded=False):
                try:
                    p = Path(path)
                    if p.exists():
                        text = p.read_text(encoding="utf-8")
                        if text.startswith("---\n"):
                            parts = text[4:].split("\n---\n", 1)
                            if len(parts) == 2:
                                text = parts[1]
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


# ─── 그리드 셀 (버튼 또는 점) ─────────────────────────────────────────
def _cell(col, n: int, key: str, on_click_state: dict[str, str]) -> None:
    """셀 1개 — 카운트 있으면 버튼, 없으면 점."""
    if n > 0:
        if col.button(str(n), key=key, use_container_width=True):
            for k, v in on_click_state.items():
                st.session_state[k] = v
    else:
        col.markdown(
            "<div style='text-align:center;color:#555;padding:8px;'>·</div>",
            unsafe_allow_html=True,
        )


# ─── 메인 render ──────────────────────────────────────────────────────
def render() -> None:
    docs = _all_docs()
    if not docs:
        st.info("아직 분류된 자료가 없습니다. 📦 데이터 탭의 [🔄 재처리]로 분석을 돌리세요.")
        return

    p1 = _count_p1(docs)
    p2 = _count_p2(docs)
    p3 = _count_p3(docs)

    # 미분류 카운트 — 진단용
    n_unclassified_auto = sum(
        1 for d in docs if not _parse(d.get("automation_levels_json"))
    )

    # 한 줄 요약 (그래프 탭 스타일)
    st.caption(
        f"📚 **자료 {len(docs)}** · "
        f"파트1 채워진 셀 {len(p1)}/{len(INDUSTRIES) * len(AUTOMATION)} · "
        f"파트2 시스템 {len(p2)}/{len(SYSTEMS)} · "
        f"파트3 관리 {len(p3)}/{sum(len(g[1]) for g in MGMT_GROUPS)} · "
        f"자동화 미분류 {n_unclassified_auto}건"
    )

    with st.expander("📚 위키 — 분류축 안내 (V2.5.3 §3.10 v2)", expanded=False):
        st.markdown("""
**3 파트 분류 — 자료 1건이 여러 파트에 동시 노출 (의도된 중복).**

- **파트1 산업 × 자동화**: 산업 8종 + *산업 무관* 행 × auto1/2/3/aiplus
- **파트2 시스템**: APS · MES · ERP · WMS · QMS · SCM (정보화 시스템)
- **파트3 관리**: 조직·거버넌스·실행계획

K2 분류기 v2가 멀티라벨로 박는 자리. 라벨 비어 있는 자료는 📦 **데이터 탭 → [🔄 재처리]**로 K2 재돌리면 채워짐.
        """)

    # ─── 파트 1: 산업 × 자동화 ───────────────────────────────────────
    st.markdown("### 🏭 파트 1 — 산업 × 자동화")

    header_cols = st.columns([1.2] + [1] * len(AUTOMATION))
    header_cols[0].markdown("**산업 / 자동화**")
    for i, lvl in enumerate(AUTOMATION):
        header_cols[i + 1].markdown(
            f"<div style='text-align:center;font-size:0.85em;line-height:1.2;'>"
            f"<b>{lvl}</b><br/><span style='color:#888;'>"
            f"{AUTOMATION_LABELS[lvl].split(chr(10))[1]}</span></div>",
            unsafe_allow_html=True,
        )

    for ind in INDUSTRIES:
        cols = st.columns([1.2] + [1] * len(AUTOMATION))
        cols[0].markdown(f"**{INDUSTRY_LABELS[ind]}**")
        for i, lvl in enumerate(AUTOMATION):
            n = len(p1.get((ind, lvl), []))
            _cell(
                cols[i + 1], n,
                key=f"p1_{ind}_{lvl}",
                on_click_state={
                    "wiki_part": "1", "wiki_p1_ind": ind, "wiki_p1_lvl": lvl,
                },
            )

    # ─── 파트 2: 시스템 ──────────────────────────────────────────────
    st.markdown("### 💻 파트 2 — 시스템 (정보화)")
    sys_cols = st.columns(len(SYSTEMS))
    for i, sys in enumerate(SYSTEMS):
        n = len(p2.get(sys, []))
        with sys_cols[i]:
            st.markdown(f"<div style='text-align:center;color:#888;'>{sys}</div>",
                        unsafe_allow_html=True)
            _cell(
                sys_cols[i].container(), n,
                key=f"p2_{sys}",
                on_click_state={"wiki_part": "2", "wiki_p2_sys": sys},
            )

    # ─── 파트 3: 관리 ────────────────────────────────────────────────
    st.markdown("### 🧭 파트 3 — 관리 (조직 · 거버넌스 · 실행)")
    for group_label, cats in MGMT_GROUPS:
        st.markdown(f"<span style='color:#888;font-size:0.9em;'>{group_label}</span>",
                    unsafe_allow_html=True)
        cat_cols = st.columns(len(cats) * 2)  # 좁게
        for i, cat in enumerate(cats):
            n = len(p3.get(cat, []))
            with cat_cols[i * 2]:
                st.markdown(
                    f"<div style='text-align:center;color:#aaa;'>{MGMT_LABELS[cat]}</div>",
                    unsafe_allow_html=True,
                )
                _cell(
                    cat_cols[i * 2].container(), n,
                    key=f"p3_{cat}",
                    on_click_state={"wiki_part": "3", "wiki_p3_cat": cat},
                )

    # ─── 선택된 셀 자료 표시 ─────────────────────────────────────────
    st.divider()
    part = st.session_state.get("wiki_part")
    if not part:
        st.caption("👆 위 그리드의 셀을 클릭하면 해당 분면 자료가 여기에 표시됩니다.")
        return

    if part == "1":
        ind = st.session_state.get("wiki_p1_ind")
        lvl = st.session_state.get("wiki_p1_lvl")
        st.markdown(f"### 📁 파트1 — `{INDUSTRY_LABELS.get(ind, ind)}` × `{lvl}`")
        _render_docs(p1.get((ind, lvl), []), blurb_field="blurb_industry")
    elif part == "2":
        sys = st.session_state.get("wiki_p2_sys")
        st.markdown(f"### 📁 파트2 — `{sys}`")
        _render_docs(p2.get(sys, []), blurb_field="blurb_system")
    elif part == "3":
        cat = st.session_state.get("wiki_p3_cat")
        st.markdown(f"### 📁 파트3 — `{MGMT_LABELS.get(cat, cat)}`")
        _render_docs(p3.get(cat, []), blurb_field="blurb_mgmt")
