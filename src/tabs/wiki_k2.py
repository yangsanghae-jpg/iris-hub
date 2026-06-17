"""탭: 📚 위키 — 3-파트 분류 뷰 (V2.6.2.5 한국어화 + 시각화).

3 파트 (자료 1건은 여러 파트에 동시 노출, 의도된 중복):
  파트1. 산업 × 자동화 (8 산업 + 일반행) × (auto1/auto2/auto3/aiplus)
  파트2. 시스템 도메인 (APS/MES/ERP/WMS/QMS/SCM)
  파트3. 관리 (조직 · 거버넌스 · 실행)

UI 정책 (데이터 탭과 동일):
  - 한 줄 요약 → 3 파트 progress bar
  - 그리드 셀 카운트 → 강도(opacity)로 시각화
  - 파트2/3 분포 → 가로 stacked bar
  - 한국어 우선, 오역 우려 시 한국어(영어) 병기
"""
from __future__ import annotations

import html
import json
import sqlite3
from pathlib import Path

import streamlit as st

DB_PATH = Path("/Users/iris/Documents/0Dev/iris-system/knowledge/_index.db")

# ─── 분류축 정의 + 한국어 라벨 ────────────────────────────────────────
# ─── 분류축 정의 + 한국어 라벨 (V2.6.2.7 진단툴 IND_A~I 정합) ──────────
INDUSTRIES = ["A", "B", "C", "D", "E", "F", "G", "H", "I"]
INDUSTRY_LABELS = {
    "A": "A 프로젝트형 제조",
    "B": "B 반도체",
    "C": "C 전자 조립",
    "D": "D 디스플레이·신에너지",
    "E": "E 프로세스·화학",
    "F": "F 소비재·식품",
    "G": "G 의약품·바이오",
    "H": "H 자동차·장비",
    "I": "I 정밀 소재·부품",
}

AUTOMATION = ["auto1", "auto2", "auto3", "aiplus"]
AUTOMATION_LABELS = {
    "auto1":  ("auto1", "수작업"),
    "auto2":  ("auto2", "부분도입"),
    "auto3":  ("auto3", "통합"),
    "aiplus": ("aiplus", "AI/예측"),
}

SYSTEMS = [
    # 계획·실행
    "APS", "MES", "MOM", "WES",
    # 전사
    "ERP", "PLM", "EAM",
    # 품질·추적
    "QMS", "LIMS", "Historian",
    # 물류·공급망
    "WMS", "TMS", "SCM",
    # 데이터·자동화
    "SCADA", "HMI", "BI", "RPA",
    # MES 보조
    "EAP", "FDC", "SPC",
]
SYSTEM_LABELS = {
    "APS": "APS (생산계획)",
    "MES": "MES (실행)",
    "MOM": "MOM (운영관리)",
    "WES": "WES (창고실행)",
    "ERP": "ERP (전사자원)",
    "PLM": "PLM (수명주기)",
    "EAM": "EAM (설비자산)",
    "QMS": "QMS (품질)",
    "LIMS": "LIMS (실험실)",
    "Historian": "Historian (이력)",
    "WMS": "WMS (창고)",
    "TMS": "TMS (운송)",
    "SCM": "SCM (공급망)",
    "SCADA": "SCADA (감시제어)",
    "HMI": "HMI (인터페이스)",
    "BI": "BI (분석)",
    "RPA": "RPA (자동화)",
    "EAP": "EAP (장비자동화)",
    "FDC": "FDC (결함분류)",
    "SPC": "SPC (공정관리)",
}

MGMT_GROUPS = [
    ("조직",        ["org_design", "org_role"]),
    ("거버넌스",    ["gov_committee", "gov_kpi", "gov_policy", "gov_audit"]),
    ("실행계획",    ["exec_phase", "exec_milestone", "exec_resource"]),
    ("변화·리스크", ["change_management", "risk_mitigation", "stakeholder_alignment"]),
    ("커뮤니케이션", ["comm_reporting", "comm_escalation"]),
]
MGMT_LABELS = {
    "org_design":     "조직설계",
    "org_role":       "역할·책임 (R&R)",
    "gov_committee":  "위원회",
    "gov_kpi":        "KPI",
    "gov_policy":     "정책·표준",
    "gov_audit":      "감사 (audit)",
    "exec_phase":     "단계계획",
    "exec_milestone": "마일스톤",
    "exec_resource":  "자원·예산",
    "change_management":      "변화관리",
    "risk_mitigation":        "리스크 완화",
    "stakeholder_alignment":  "이해관계자 정렬",
    "comm_reporting":         "보고",
    "comm_escalation":        "에스컬레이션",
}

# 산업 색상 팔레트 (데이터 탭과 일관)
_INDUSTRY_COLORS = {
    "A": "#5fa8ff", "B": "#7ed6a3", "C": "#ffb86b", "D": "#c596ff",
    "E": "#f08585", "F": "#ffd166", "G": "#a0e7e5", "H": "#fbb1bd",
    "I": "#b8b8b8",
}
# 시스템 색상 팔레트
# 시스템 색상 팔레트 (20개 — 6 기본 + 14 확장)
_SYSTEM_COLORS = {
    # 6 기본 (V2.6.2.7 색상 유지)
    "APS": "#5fa8ff", "MES": "#7ed6a3", "ERP": "#ffb86b",
    "WMS": "#c596ff", "QMS": "#f08585", "SCM": "#ffd166",
    # 신규 14 — 무난한 톤
    "MOM": "#8b9dc3", "WES": "#9dc3a6",
    "PLM": "#ffaa7a", "EAM": "#a89dc7",
    "LIMS": "#f0a8a8", "Historian": "#d4c98a",
    "TMS": "#a3c4dc",
    "SCADA": "#7a9d7a", "HMI": "#c7a87a",
    "BI": "#9d7ac7", "RPA": "#dc7a9d",
    "EAP": "#7adcdc", "FDC": "#dca87a", "SPC": "#a8dc7a",
}
# 관리 카테고리 색상 (14개)
_MGMT_COLORS = {
    "org_design": "#5fa8ff", "org_role": "#7ed6a3",
    "gov_committee": "#c596ff", "gov_kpi": "#ffb86b",
    "gov_policy": "#a89dc7", "gov_audit": "#dc7a9d",
    "exec_phase": "#f08585", "exec_milestone": "#ffd166",
    "exec_resource": "#a3c4dc",
    "change_management": "#7a9d7a",
    "risk_mitigation": "#f0a8a8",
    "stakeholder_alignment": "#c7a87a",
    "comm_reporting": "#9dc3a6", "comm_escalation": "#d4c98a",
}


# ─── CSS ──────────────────────────────────────────────────────────────
_CSS = """
<style>
.wiki-sec { font-size:0.78em; font-weight:600; color:#888;
            letter-spacing:.5px; margin:14px 0 6px 0; }

/* progress bar (데이터 탭과 동일) */
.wiki-prog-wrap {
  position:relative; height:28px; background:rgba(120,120,120,0.10);
  border:1px solid rgba(120,120,120,0.18); border-radius:6px; overflow:hidden;
}
.wiki-prog-fill {
  position:absolute; left:0; top:0; bottom:0;
  background: linear-gradient(90deg, #7ed6a3 0%, #5fa8ff 100%);
}
.wiki-prog-text {
  position:absolute; inset:0; display:flex; align-items:center;
  justify-content:center; font-size:0.85em; font-weight:600;
  color:#fff; text-shadow: 0 1px 2px rgba(0,0,0,0.6);
}

/* stacked bar */
.wiki-bar { display:flex; height:26px; border-radius:6px; overflow:hidden;
            background:rgba(120,120,120,0.10);
            border:1px solid rgba(120,120,120,0.18); }
.wiki-bar-seg {
  height:100%; display:flex; align-items:center; justify-content:flex-start;
  padding:0 9px; color:#fff; font-size:0.78em; font-weight:500;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
  text-shadow: 0 1px 1px rgba(0,0,0,0.45);
}
.wiki-zeros { font-size:0.78em; color:#888; margin-top:5px; }
.wiki-zeros span { margin-right:10px; }

/* 그리드 컴팩트 */
div[data-testid="stVerticalBlock"] div[data-testid="stHorizontalBlock"] {
  gap: 4px !important; margin-bottom: 0 !important;
}
div[data-testid="stVerticalBlock"] div[data-testid="column"] { padding: 0 !important; }

/* 셀 버튼 */
div[data-testid="column"] button[kind="secondary"] {
  padding: 5px 0 !important; min-height: 36px !important;
  font-weight: 600; font-size: 0.95em;
  border: 1px solid rgba(255,255,255,0.10) !important;
}
.wiki-empty {
  text-align: center; color: #444; font-size: 0.9em;
  padding: 8px 0; min-height: 36px; line-height: 20px;
  border: 1px solid rgba(255,255,255,0.04); border-radius: 6px;
}

/* 행/열 라벨 */
.wiki-row-lbl {
  padding: 10px 6px 0 0; color: #d0d0d0; font-weight: 500;
  font-size: 0.9em; white-space: nowrap;
}
.wiki-col-hdr {
  text-align: center; font-size: 0.82em; line-height: 1.2;
  padding: 4px 0 8px 0; border-bottom: 1px solid rgba(255,255,255,0.08);
  margin-bottom: 6px;
}
.wiki-col-hdr b { color: #e6e6e6; font-size: 1em; }
.wiki-col-hdr span { color: #888; }
.wiki-mgmt-grp {
  color: #888; font-size: 0.78em; margin: 4px 0 2px 2px;
  letter-spacing: 0.5px; font-weight: 600;
}
.wiki-chip-lbl {
  text-align: center; color: #c0c0c0; font-size: 0.85em;
  padding: 0 0 4px 0; font-weight: 500;
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


def _industry_key(d: dict) -> str | None:
    """파트1 행 키 — industry가 없으면 None (산업 분류 못한 자료는 그리드 제외)."""
    return d["industry"]


# ─── 카운트/필터 ──────────────────────────────────────────────────────
def _count_p1(docs: list[dict]) -> dict[tuple[str, str], list[dict]]:
    out: dict[tuple[str, str], list[dict]] = {}
    for d in docs:
        ind = _industry_key(d)
        if ind is None:
            continue  # 산업 미분류 자료는 파트1에서 제외
        for lvl in _parse(d.get("automation_levels_json")):
            out.setdefault((ind, lvl), []).append(d)
    return out


def _count_p2(docs: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for d in docs:
        for sys in _parse(d.get("system_domains_json")):
            out.setdefault(sys, []).append(d)
    return out


def _count_p3(docs: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for d in docs:
        for cat in _parse(d.get("mgmt_categories_json")):
            out.setdefault(cat, []).append(d)
    return out


# ─── 시각화 헬퍼 ──────────────────────────────────────────────────────
def _progress(numer: int, denom: int, label: str) -> str:
    pct = (numer / denom * 100) if denom else 0
    return (
        f"<div class='wiki-prog-wrap'>"
        f"<div class='wiki-prog-fill' style='width:{pct:.1f}%;'></div>"
        f"<div class='wiki-prog-text'>{html.escape(label)} · "
        f"<b>{numer:,}</b> / {denom:,} ({pct:.1f}%)</div>"
        f"</div>"
    )


def _stacked_bar(items: list[tuple[str, int, str]]) -> str:
    """items: [(label, count, color), ...]. 0인 카테고리는 zero-row."""
    nonzero = [(k, v, c) for k, v, c in items if v > 0]
    zeros = [k for k, v, _ in items if v == 0]
    total = sum(v for _, v, _ in nonzero) or 1

    segs = []
    for k, v, color in nonzero:
        pct = v / total * 100
        if pct >= 12:
            inner = f"{html.escape(k)} <b>{v:,}</b> · {pct:.0f}%"
        elif pct >= 5:
            inner = f"<b>{v:,}</b>"
        else:
            inner = "·"
        segs.append(
            f"<div class='wiki-bar-seg' "
            f"style='flex:{v} 0 0; background:{color};' "
            f"title='{html.escape(k)}: {v:,} ({pct:.1f}%)'>{inner}</div>"
        )

    bar = (f"<div class='wiki-bar'>{''.join(segs)}</div>" if nonzero else
           "<div class='wiki-bar'><div class='wiki-bar-seg' style='flex:1; color:#888;'>(분류 없음)</div></div>")

    if zeros:
        zlabels = " ".join(f"<span>○ {html.escape(k)}</span>" for k in zeros)
        bar += f"<div class='wiki-zeros'>{zlabels}</div>"
    return bar


def _heat_cell(col, n: int, max_n: int, key: str,
               on_click_state: dict[str, str]) -> None:
    """카운트가 있으면 강도(opacity)로 채운 버튼, 없으면 점."""
    if n > 0:
        # opacity = 0.25~1.0
        op = 0.25 + (n / max_n * 0.75) if max_n > 0 else 0.5
        # 셀 라벨에 카운트만 (배경은 inline style로 못 박으므로 button label에 의존)
        if col.button(f"{n}", key=key, use_container_width=True,
                      help=f"{n}건 — 클릭하여 자료 보기"):
            for k, v in on_click_state.items():
                st.session_state[k] = v
    else:
        col.markdown("<div class='wiki-empty'>·</div>", unsafe_allow_html=True)


# ─── 자료 리스트 렌더 ────────────────────────────────────────────────
def _render_docs(docs: list[dict], blurb_field: str) -> None:
    if not docs:
        st.info("이 분면에 자료가 없습니다.")
        return

    for d in docs:
        title = d.get("title") or d["doc_id"]
        confidence = d.get("confidence") or 0
        is_fb = bool(d.get("fallback_used"))
        badge = " 🟡 규칙 기반" if is_fb else (" 🟢 LLM" if confidence > 0 else " ⚪ 미분석")
        blurb = (d.get(blurb_field) or "").strip() or (d.get("summary") or "(K2 분석 미완)")

        with st.expander(f"**{title}** {badge}  ·  신뢰도 {confidence:.2f}"):
            st.caption(f"📝 {blurb}")

            topics = _parse(d.get("topics_json"))
            if topics:
                st.caption("🏷 주제(topics): " + " · ".join(f"`{t}`" for t in topics))

            cc1, cc2, cc3 = st.columns(3)
            cc1.caption(
                f"산업 `{d.get('industry') or '—'}` · 영역(area) `{d.get('area') or '—'}`"
            )
            cc2.caption(
                f"자동화 단계 `{', '.join(_parse(d.get('automation_levels_json'))) or '—'}`"
            )
            cc3.caption(
                f"시스템 `{', '.join(_parse(d.get('system_domains_json'))) or '—'}`"
            )

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

    n_p1_cells = len(INDUSTRIES) * len(AUTOMATION)
    n_p3_cells = sum(len(g[1]) for g in MGMT_GROUPS)
    p1_total = sum(len(v) for v in p1.values())
    p2_total = sum(len(v) for v in p2.values())
    p3_total = sum(len(v) for v in p3.values())
    n_unclassified = sum(
        1 for d in docs if not _parse(d.get("automation_levels_json"))
    )

    # ─── 한 줄 요약 ──────────────────────────────────────────────────
    cs1, cs2, cs3, cs4 = st.columns(4)
    cs1.metric("자료 (documents)", f"{len(docs):,}")
    cs2.metric("파트1 매핑", f"{p1_total:,}", help="산업×자동화 — 1자료가 여러 셀에 매핑 가능")
    cs3.metric("파트2 매핑", f"{p2_total:,}", help="시스템 — 1자료가 여러 시스템에 매핑 가능")
    cs4.metric("미분류 자료", f"{n_unclassified:,}",
               help="자동화(automation_levels) 라벨이 비어 있는 자료")

    st.caption("💡 K2 v2 멀티라벨 — 자료 1건이 3 파트에 동시 노출되는 의도된 중복")

    # 3 파트 채워진 셀 비율 (progress bar)
    st.markdown(
        "<div class='wiki-sec'>📐 3 파트 채워진 셀 비율 (분면 커버리지)</div>",
        unsafe_allow_html=True,
    )
    pc1, pc2, pc3 = st.columns(3)
    with pc1:
        st.markdown(_progress(len(p1), n_p1_cells, "파트1 산업×자동화"),
                    unsafe_allow_html=True)
    with pc2:
        st.markdown(_progress(len(p2), len(SYSTEMS), "파트2 시스템"),
                    unsafe_allow_html=True)
    with pc3:
        st.markdown(_progress(len(p3), n_p3_cells, "파트3 관리"),
                    unsafe_allow_html=True)

    with st.expander("📚 분류축 안내 (V2.5.3 §3.10 v2)", expanded=False):
        st.markdown("""
**3 파트 분류 — 자료 1건이 여러 파트에 동시 노출 (의도된 중복).**

- **파트1 산업 × 자동화**: 9 산업 × 4 자동화 단계 (auto1·auto2·auto3·aiplus)
- **파트2 시스템 (정보화)**: APS · MES · ERP · WMS · QMS · SCM
- **파트3 관리**: 조직 · 거버넌스 · 실행계획

라벨이 비어 있는 자료는 📦 **데이터 탭 → [🔄 재처리]** 로 K2 v2 재돌리면 채워짐.
        """)

    # ─── 파트 1: 산업 × 자동화 ───────────────────────────────────────
    st.markdown(
        "<div class='wiki-sec'>🏭 파트 1 — 산업 × 자동화 단계</div>",
        unsafe_allow_html=True,
    )

    # 자동화 단계 분포 (산업 색상으로 stacked)
    auto_industry: dict[str, dict[str, int]] = {lvl: {} for lvl in AUTOMATION}
    for (ind, lvl), ds in p1.items():
        auto_industry[lvl][ind] = len(ds)

    # 행 그리드
    with st.expander(
        f"산업×자동화 그리드 — 채워진 셀 {len(p1)}/{n_p1_cells} · 매핑 {p1_total:,}건",
        expanded=True,
    ):
        # 헤더
        header_cols = st.columns([1.6] + [1] * len(AUTOMATION))
        header_cols[0].markdown("&nbsp;", unsafe_allow_html=True)
        for i, lvl in enumerate(AUTOMATION):
            short, sub = AUTOMATION_LABELS[lvl]
            header_cols[i + 1].markdown(
                f"<div class='wiki-col-hdr'><b>{short}</b><br/><span>{sub}</span></div>",
                unsafe_allow_html=True,
            )

        # 데이터 행
        max_p1 = max((len(v) for v in p1.values()), default=1)
        for ind in INDUSTRIES:
            cols = st.columns([1.6] + [1] * len(AUTOMATION))
            cols[0].markdown(
                f"<div class='wiki-row-lbl'>{INDUSTRY_LABELS[ind]}</div>",
                unsafe_allow_html=True,
            )
            for i, lvl in enumerate(AUTOMATION):
                n = len(p1.get((ind, lvl), []))
                _heat_cell(
                    cols[i + 1], n, max_p1,
                    key=f"p1_{ind}_{lvl}",
                    on_click_state={
                        "wiki_part": "1", "wiki_p1_ind": ind, "wiki_p1_lvl": lvl,
                    },
                )

    # ─── 파트 2: 시스템 ──────────────────────────────────────────────
    st.markdown(
        "<div class='wiki-sec'>💻 파트 2 — 시스템 (정보화)  "
        "<span style='color:#777;font-weight:400;'>"
        f"카탈로그 {len(SYSTEMS)}개 · 박힌 자료 {p2_total:,}건</span></div>",
        unsafe_allow_html=True,
    )

    # Top-N 슬라이더 (세션 상태 유지)
    top_n_sys = st.slider(
        "Top-N 시스템 표시", min_value=4, max_value=len(SYSTEMS),
        value=st.session_state.get("wiki_p2_topn", 6),
        key="wiki_p2_topn",
        help="카운트 상위 N개만 그리드·bar에 표시. 나머지는 '기타' expander.",
    )

    # 시스템별 카운트 → 정렬 후 Top-N
    sys_counts = sorted(
        ((sys, len(p2.get(sys, []))) for sys in SYSTEMS),
        key=lambda x: (-x[1], x[0]),
    )
    top_sys = [s for s, _ in sys_counts[:top_n_sys]]
    rest_sys = [(s, n) for s, n in sys_counts[top_n_sys:] if n > 0]

    # Top-N stacked bar
    top_items = [(s, n, _SYSTEM_COLORS.get(s, "#888"))
                 for s, n in sys_counts[:top_n_sys]]
    st.markdown(_stacked_bar(top_items), unsafe_allow_html=True)

    # 기타 시스템 expander
    if rest_sys:
        rest_total = sum(n for _, n in rest_sys)
        with st.expander(
            f"➕ 기타 {len(rest_sys)}개 시스템 · 매핑 {rest_total:,}건",
            expanded=False,
        ):
            rest_items = [(s, n, _SYSTEM_COLORS.get(s, "#888")) for s, n in rest_sys]
            st.markdown(_stacked_bar(rest_items), unsafe_allow_html=True)
            # 기타 시스템도 클릭 가능 grid
            rest_cols = st.columns(len(rest_sys))
            max_rest = max((n for _, n in rest_sys), default=1)
            for i, (sys, n) in enumerate(rest_sys):
                rest_cols[i].markdown(
                    f"<div class='wiki-chip-lbl'>{SYSTEM_LABELS.get(sys, sys)}</div>",
                    unsafe_allow_html=True,
                )
                _heat_cell(
                    rest_cols[i], n, max_rest,
                    key=f"p2_rest_{sys}",
                    on_click_state={"wiki_part": "2", "wiki_p2_sys": sys},
                )

    # Top-N 시스템 grid
    with st.expander(
        f"🔝 Top-{top_n_sys} 시스템 그리드",
        expanded=True,
    ):
        sys_cols = st.columns(top_n_sys)
        max_p2 = max((len(v) for v in p2.values()), default=1)
        for i, sys in enumerate(top_sys):
            n = len(p2.get(sys, []))
            sys_cols[i].markdown(
                f"<div class='wiki-chip-lbl'>{SYSTEM_LABELS.get(sys, sys)}</div>",
                unsafe_allow_html=True,
            )
            _heat_cell(
                sys_cols[i], n, max_p2,
                key=f"p2_top_{sys}",
                on_click_state={"wiki_part": "2", "wiki_p2_sys": sys},
            )

    # ─── 파트 3: 관리 ────────────────────────────────────────────────
    st.markdown(
        "<div class='wiki-sec'>🧭 파트 3 — 관리  "
        "<span style='color:#777;font-weight:400;'>"
        f"카탈로그 {n_p3_cells}개 · 박힌 자료 {p3_total:,}건</span></div>",
        unsafe_allow_html=True,
    )

    # Top-N 슬라이더
    top_n_mgmt = st.slider(
        "Top-N 관리 카테고리 표시", min_value=4, max_value=n_p3_cells,
        value=st.session_state.get("wiki_p3_topn", 6),
        key="wiki_p3_topn",
        help="카운트 상위 N개만 표시. 나머지는 그룹별 bar에서 확인.",
    )

    # 전체 카테고리 → 카운트 → Top-N
    all_cats = [c for _, cats in MGMT_GROUPS for c in cats]
    cat_counts = sorted(
        ((c, len(p3.get(c, []))) for c in all_cats),
        key=lambda x: (-x[1], x[0]),
    )
    top_cats = [c for c, _ in cat_counts[:top_n_mgmt]]
    rest_cats = [(c, n) for c, n in cat_counts[top_n_mgmt:] if n > 0]

    # Top-N stacked bar
    top_mgmt_items = [(MGMT_LABELS.get(c, c), n, _MGMT_COLORS.get(c, "#888"))
                      for c, n in cat_counts[:top_n_mgmt]]
    st.markdown(_stacked_bar(top_mgmt_items), unsafe_allow_html=True)

    # 기타 카테고리 expander
    if rest_cats:
        rest_total = sum(n for _, n in rest_cats)
        with st.expander(
            f"➕ 기타 {len(rest_cats)}개 카테고리 · 매핑 {rest_total:,}건",
            expanded=False,
        ):
            rest_items = [(MGMT_LABELS.get(c, c), n, _MGMT_COLORS.get(c, "#888"))
                          for c, n in rest_cats]
            st.markdown(_stacked_bar(rest_items), unsafe_allow_html=True)
            rest_cols = st.columns(len(rest_cats))
            max_rest = max((n for _, n in rest_cats), default=1)
            for i, (cat, n) in enumerate(rest_cats):
                rest_cols[i].markdown(
                    f"<div class='wiki-chip-lbl'>{MGMT_LABELS.get(cat, cat)}</div>",
                    unsafe_allow_html=True,
                )
                _heat_cell(
                    rest_cols[i], n, max_rest,
                    key=f"p3_rest_{cat}",
                    on_click_state={"wiki_part": "3", "wiki_p3_cat": cat},
                )

    # Top-N 관리 grid
    with st.expander(
        f"🔝 Top-{top_n_mgmt} 관리 카테고리 그리드",
        expanded=True,
    ):
        top_cols = st.columns(top_n_mgmt)
        max_p3 = max((len(v) for v in p3.values()), default=1)
        for i, cat in enumerate(top_cats):
            n = len(p3.get(cat, []))
            top_cols[i].markdown(
                f"<div class='wiki-chip-lbl'>{MGMT_LABELS.get(cat, cat)}</div>",
                unsafe_allow_html=True,
            )
            _heat_cell(
                top_cols[i], n, max_p3,
                key=f"p3_top_{cat}",
                on_click_state={"wiki_part": "3", "wiki_p3_cat": cat},
            )

    # ─── 선택된 셀 자료 표시 ─────────────────────────────────────────
    st.divider()
    part = st.session_state.get("wiki_part")
    if not part:
        st.caption("👆 위 그리드의 셀(숫자 버튼)을 클릭하면 해당 분면 자료가 여기에 표시됩니다.")
        return

    if part == "1":
        ind = st.session_state.get("wiki_p1_ind")
        lvl = st.session_state.get("wiki_p1_lvl")
        st.markdown(
            f"### 📁 파트1 — {INDUSTRY_LABELS.get(ind, ind)} × "
            f"{AUTOMATION_LABELS.get(lvl, (lvl, ''))[0]} ({AUTOMATION_LABELS.get(lvl, ('',''))[1]})"
        )
        _render_docs(p1.get((ind, lvl), []), blurb_field="blurb_industry")
    elif part == "2":
        sys = st.session_state.get("wiki_p2_sys")
        st.markdown(f"### 📁 파트2 — {SYSTEM_LABELS.get(sys, sys)}")
        _render_docs(p2.get(sys, []), blurb_field="blurb_system")
    elif part == "3":
        cat = st.session_state.get("wiki_p3_cat")
        st.markdown(f"### 📁 파트3 — {MGMT_LABELS.get(cat, cat)}")
        _render_docs(p3.get(cat, []), blurb_field="blurb_mgmt")
