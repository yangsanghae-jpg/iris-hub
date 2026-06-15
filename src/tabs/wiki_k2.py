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


# ─── CSS — 컴팩트 그리드 + 칩 스타일 ─────────────────────────────────
_CSS = """
<style>
  /* 위키 탭 전용: 컬럼 간격·행 간격 줄임 */
  div[data-testid="stVerticalBlock"] div[data-testid="stHorizontalBlock"] { gap: 4px !important; margin-bottom: 0 !important; }
  div[data-testid="stVerticalBlock"] div[data-testid="column"] { padding: 0 !important; }
  /* 셀 버튼·placeholder 컴팩트 */
  div[data-testid="column"] button[kind="secondary"] {
    padding: 4px 0 !important; min-height: 32px !important;
    font-weight: 600; font-size: 0.95em;
    border: 1px solid rgba(255,255,255,0.08) !important;
  }
  /* 비어있는 칸 점 */
  .wiki-empty {
    text-align: center; color: #444; font-size: 0.9em;
    padding: 6px 0; min-height: 32px; line-height: 20px;
    border: 1px solid rgba(255,255,255,0.04); border-radius: 6px;
  }
  /* 행 라벨 */
  .wiki-row-lbl {
    padding: 7px 6px 0 0; color: #d0d0d0; font-weight: 500;
    font-size: 0.92em; white-space: nowrap;
  }
  /* 컬럼 헤더 (auto1~aiplus) */
  .wiki-col-hdr {
    text-align: center; font-size: 0.82em; line-height: 1.2;
    padding: 2px 0 6px 0; border-bottom: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 4px;
  }
  .wiki-col-hdr b { color: #e6e6e6; font-size: 1.05em; }
  .wiki-col-hdr span { color: #888; }
  /* 파트 헤더 */
  .wiki-part-h { font-size: 1.05em; font-weight: 600; color: #d8d8d8;
    margin: 18px 0 8px 0; padding-bottom: 6px;
    border-bottom: 1px solid rgba(255,255,255,0.06); }
  .wiki-part-h .sub { color: #777; font-weight: 400; font-size: 0.85em; margin-left: 8px; }
  /* 칩 라벨 (파트2/3) */
  .wiki-chip-lbl {
    text-align: center; color: #aaa; font-size: 0.85em;
    padding: 0 0 2px 0;
  }
  .wiki-mgmt-grp {
    color: #888; font-size: 0.82em; margin: 8px 0 2px 2px;
    text-transform: uppercase; letter-spacing: 0.5px;
  }
</style>
"""


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
    """셀 1개 — 카운트 있으면 버튼, 없으면 점 placeholder (높이 통일)."""
    if n > 0:
        if col.button(str(n), key=key, use_container_width=True):
            for k, v in on_click_state.items():
                st.session_state[k] = v
    else:
        col.markdown("<div class='wiki-empty'>·</div>", unsafe_allow_html=True)


# ─── 메인 render ──────────────────────────────────────────────────────
def render() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)

    docs = _all_docs()
    if not docs:
        st.info("아직 분류된 자료가 없습니다. 📦 데이터 탭의 [🔄 재처리]로 분석을 돌리세요.")
        return

    p1 = _count_p1(docs)
    p2 = _count_p2(docs)
    p3 = _count_p3(docs)

    n_unclassified_auto = sum(
        1 for d in docs if not _parse(d.get("automation_levels_json"))
    )

    # 한 줄 요약
    st.caption(
        f"📚 **자료 {len(docs)}** · "
        f"파트1 {len(p1)}/{len(INDUSTRIES) * len(AUTOMATION)} · "
        f"파트2 {len(p2)}/{len(SYSTEMS)} · "
        f"파트3 {len(p3)}/{sum(len(g[1]) for g in MGMT_GROUPS)} · "
        f"미분류 {n_unclassified_auto}건"
    )

    with st.expander("📚 분류축 안내 (V2.5.3 §3.10 v2)", expanded=False):
        st.markdown("""
**3 파트 분류 — 자료 1건이 여러 파트에 동시 노출 (의도된 중복).**

- **파트1 산업 × 자동화**: 9 산업 × auto1/2/3/aiplus
- **파트2 시스템**: APS · MES · ERP · WMS · QMS · SCM
- **파트3 관리**: 조직 · 거버넌스 · 실행계획

라벨 비어 있는 자료는 📦 **데이터 탭 → [🔄 재처리]**로 K2 v2 재돌리면 채워짐.
        """)

    # ─── 파트 1: 산업 × 자동화 ───────────────────────────────────────
    p1_total = sum(len(v) for v in p1.values())
    with st.expander(
        f"🏭  파트 1 — 산업 × 자동화   ·   채워진 셀 {len(p1)}/36 · 매핑 {p1_total}건",
        expanded=True,
    ):
        # 헤더 행 (auto1~aiplus)
        header_cols = st.columns([1.4] + [1] * len(AUTOMATION))
        header_cols[0].markdown("&nbsp;", unsafe_allow_html=True)
        for i, lvl in enumerate(AUTOMATION):
            sub = AUTOMATION_LABELS[lvl].split("\n")[1]
            header_cols[i + 1].markdown(
                f"<div class='wiki-col-hdr'><b>{lvl}</b><br/><span>{sub}</span></div>",
                unsafe_allow_html=True,
            )

        # 데이터 행
        for ind in INDUSTRIES:
            cols = st.columns([1.4] + [1] * len(AUTOMATION))
            cols[0].markdown(
                f"<div class='wiki-row-lbl'>{INDUSTRY_LABELS[ind]}</div>",
                unsafe_allow_html=True,
            )
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
    p2_total = sum(len(v) for v in p2.values())
    with st.expander(
        f"💻  파트 2 — 시스템 (정보화)   ·   {len(p2)}/{len(SYSTEMS)} 도메인 · 매핑 {p2_total}건",
        expanded=True,
    ):
        sys_cols = st.columns(len(SYSTEMS))
        for i, sys in enumerate(SYSTEMS):
            n = len(p2.get(sys, []))
            sys_cols[i].markdown(f"<div class='wiki-chip-lbl'>{sys}</div>",
                                 unsafe_allow_html=True)
            _cell(
                sys_cols[i], n,
                key=f"p2_{sys}",
                on_click_state={"wiki_part": "2", "wiki_p2_sys": sys},
            )

    # ─── 파트 3: 관리 ────────────────────────────────────────────────
    p3_total = sum(len(v) for v in p3.values())
    with st.expander(
        f"🧭  파트 3 — 관리 (조직 · 거버넌스 · 실행)   ·   "
        f"{len(p3)}/{sum(len(g[1]) for g in MGMT_GROUPS)} 카테고리 · 매핑 {p3_total}건",
        expanded=True,
    ):
        grp_cols = st.columns([1, 1, 1, 1, 1, 1])
        cat_idx = 0
        for group_label, cats in MGMT_GROUPS:
            for cat in cats:
                with grp_cols[cat_idx]:
                    if cat == cats[0]:
                        st.markdown(
                            f"<div class='wiki-mgmt-grp'>{group_label}</div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown("<div class='wiki-mgmt-grp'>&nbsp;</div>",
                                    unsafe_allow_html=True)
                    st.markdown(f"<div class='wiki-chip-lbl'>{MGMT_LABELS[cat]}</div>",
                                unsafe_allow_html=True)
                    n = len(p3.get(cat, []))
                    _cell(
                        grp_cols[cat_idx], n,
                        key=f"p3_{cat}",
                        on_click_state={"wiki_part": "3", "wiki_p3_cat": cat},
                    )
                cat_idx += 1

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
