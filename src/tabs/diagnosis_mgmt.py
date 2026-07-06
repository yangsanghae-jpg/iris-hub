"""탭: 🔧 진단툴 — git 기준 마이그레이션 진도 자동 평가."""
from __future__ import annotations

from collections import defaultdict
from html import escape

import streamlit as st

from src import diagnosis_migration as dm
from src.config import DIAGNOSIS_TOOL_GITHUB
from src.diagnosis_git import format_git_date, resolve_diagnosis_repo
from src.diagnosis_eval import evaluate_all
from src.diagnosis_measurements import measure_diagnosis
from src.store import diag_sot as sot
from src.ui_kit import hub_kpi_grid, hub_pagebar, hub_section, sot_coverage_badge, sot_loader_badge

_CSS = """
<style>
.flow-row {
  display:grid;
  gap:8px;
  align-items:stretch;
  margin:12px 0 10px 0;
}
.flow-row.migration {
  grid-template-columns:minmax(0, 1fr) 22px minmax(0, 1fr) 22px minmax(0, 1fr) 22px minmax(0, 1fr);
}
.flow-card {
  position:relative;
  min-height:118px;
  border:1px solid rgba(47,128,196,0.18);
  border-radius:14px;
  padding:14px 15px 13px 15px;
  background:linear-gradient(180deg, #ffffff 0%, #f8fbfe 100%);
  box-shadow:0 8px 22px rgba(16,24,40,0.045);
  display:flex;
  flex-direction:column;
  justify-content:space-between;
  gap:8px;
  min-width:0;
  overflow:hidden;
}
.flow-card::before {
  content:"";
  position:absolute;
  top:0;
  left:0;
  right:0;
  height:3px;
  background:linear-gradient(90deg, #2f80c4, rgba(47,128,196,0.35));
}
.flow-card.alert {
  border-color:rgba(240,68,56,0.34);
  background:linear-gradient(180deg, #fffafa 0%, #fff5f5 100%);
}
.flow-card.alert::before { background:linear-gradient(90deg, #f04438, rgba(240,68,56,0.35)); }
.flow-card.empty {
  border-color:rgba(152,162,179,0.22);
  background:linear-gradient(180deg, #ffffff 0%, #fbfcfe 100%);
}
.flow-card.empty::before { background:linear-gradient(90deg, #98a2b3, rgba(152,162,179,0.18)); }
.flow-card.active {
  border-color:rgba(47,128,196,0.40);
  background:linear-gradient(180deg, #f7fbff 0%, #eef7ff 100%);
  box-shadow:0 10px 26px rgba(47,128,196,0.10);
}
.flow-card h4 {
  margin:0;
  font-size:0.88rem;
  line-height:1.25;
  font-weight:780;
  color:#172033;
  letter-spacing:-0.01em;
}
.flow-card .stage-id {
  display:inline-flex;
  width:max-content;
  max-width:100%;
  padding:3px 7px;
  border-radius:999px;
  background:rgba(47,128,196,0.08);
  color:#2f80c4;
  font-size:0.66rem;
  line-height:1;
  font-weight:800;
  letter-spacing:0.04em;
  text-transform:uppercase;
}
.flow-card.empty .stage-id { background:rgba(152,162,179,0.10); color:#667085; }
.flow-card.alert .stage-id { background:rgba(240,68,56,0.10); color:#d92d20; }
.flow-card .big {
  font-size:1.95rem;
  font-weight:850;
  line-height:1;
  color:#101828;
  letter-spacing:-0.045em;
}
.flow-card .unit {
  font-size:0.78rem;
  color:#667085;
  margin-left:5px;
  font-weight:750;
  letter-spacing:-0.01em;
}
.flow-card .sub {
  font-size:0.74rem;
  line-height:1.45;
  color:#667085;
}
.flow-arrow {
  display:flex;
  align-items:center;
  justify-content:center;
  font-size:1.25rem;
  color:#98a2b3;
  min-width:0;
}
.flow-console-note {
  display:flex;
  align-items:center;
  gap:10px;
  margin:6px 0 12px 0;
  padding:9px 11px;
  border:1px solid rgba(47,128,196,0.14);
  border-radius:11px;
  background:rgba(47,128,196,0.045);
  color:#475467;
  font-size:0.78rem;
  line-height:1.45;
}
.flow-console-note strong { color:#172033; font-weight:800; }
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
  white-space:normal !important;
}
.hub-pagebar-title-row {
  align-items:center !important;
  min-height:28px;
}
.hub-pill {
  border:1px solid rgba(18,183,106,0.18);
  box-shadow:0 4px 10px rgba(18,183,106,0.08);
}
div[data-testid="stButton"] > button {
  min-height:36px;
  border-radius:10px;
  border-color:rgba(47,128,196,0.20);
  box-shadow:0 3px 10px rgba(16,24,40,0.035);
  font-weight:760;
}
div[data-testid="stButton"] > button:hover {
  border-color:rgba(47,128,196,0.48);
  background:rgba(47,128,196,0.045);
}
.dt-toolbar {
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:12px;
  margin-bottom:10px;
}
.dt-source-line {
  color:var(--hub-muted);
  font-size:12px;
  margin:-4px 0 12px 0;
}
.dt-source-line a {
  color:var(--hub-accent);
  font-weight:700;
  text-decoration:none;
}
.dt-git-grid,
.dt-next-grid {
  display:grid;
  grid-template-columns:1.2fr 0.8fr;
  gap:12px;
  margin-bottom:12px;
}
.dt-git-panel,
.dt-next-panel,
.dt-items-panel {
  border:1px solid var(--hub-border);
  border-radius:12px;
  background:var(--hub-panel);
  overflow:hidden;
}
.dt-panel-head {
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:12px;
  padding:10px 12px;
  border-bottom:1px solid var(--hub-border-soft);
}
.dt-panel-title {
  color:var(--hub-ink);
  font-size:13px;
  font-weight:850;
}
.dt-panel-subtitle {
  margin-top:2px;
  color:var(--hub-muted-2);
  font-size:11px;
}
.dt-panel-body {
  padding:12px;
}
.dt-git-metrics {
  display:grid;
  grid-template-columns:repeat(3, minmax(0, 1fr));
  gap:8px;
}
.dt-git-metric,
.dt-next-card {
  padding:10px 11px;
  border:1px solid var(--hub-border-soft);
  border-radius:10px;
  background:var(--hub-panel-soft);
}
.dt-git-metric span,
.dt-next-card span {
  display:block;
  color:var(--hub-muted);
  font-size:11px;
  font-weight:750;
}
.dt-git-metric strong {
  display:block;
  margin-top:4px;
  color:var(--hub-ink);
  font-size:20px;
  line-height:1.05;
  font-weight:850;
  overflow:hidden;
  text-overflow:ellipsis;
  white-space:nowrap;
}
.dt-git-caption,
.dt-next-detail {
  margin-top:9px;
  color:var(--hub-muted-2);
  font-size:11px;
  line-height:1.45;
}
.dt-action-list {
  display:grid;
  gap:8px;
}
.dt-action-link {
  display:block;
  padding:10px 11px;
  border:1px solid var(--hub-border);
  border-radius:10px;
  background:var(--hub-panel-soft);
  color:var(--hub-ink) !important;
  font-size:12px;
  font-weight:850;
  text-decoration:none !important;
}
.dt-action-link:hover {
  border-color:var(--hub-accent);
  background:rgba(47, 128, 196, 0.08);
}
.dt-pill {
  display:inline-flex;
  align-items:center;
  border-radius:999px;
  padding:3px 7px;
  font-size:10px;
  font-weight:850;
  white-space:nowrap;
}
.dt-pill-ok,
.dt-pill-success,
.dt-pill-verified {
  background:rgba(18, 183, 106, 0.10);
  color:var(--hub-success);
}
.dt-pill-failure {
  background:rgba(240, 68, 56, 0.10);
  color:var(--hub-danger);
}
.dt-pill-pending {
  background:rgba(47, 128, 196, 0.10);
  color:var(--hub-accent);
}
.dt-pill-blocked,
.dt-pill-neutral {
  background:var(--hub-panel-soft);
  color:var(--hub-muted);
  border:1px solid var(--hub-border-soft);
}
.dt-filter-shell {
  padding:10px 12px;
  border-bottom:1px solid var(--hub-border-soft);
  background:var(--hub-panel-soft);
}
.dt-phase-hdr {
  color:var(--hub-muted);
  font-size:11px;
  font-weight:850;
  letter-spacing:0.04em;
  text-transform:uppercase;
  padding:12px 12px 7px 12px;
}
.dt-item-row {
  display:grid;
  grid-template-columns:44px minmax(0, 1fr) 110px;
  gap:12px;
  align-items:flex-start;
  padding:11px 12px;
  border-top:1px solid var(--hub-border-soft);
}
.dt-item-id {
  color:var(--hub-ink);
  font-size:13px;
  font-weight:850;
}
.dt-item-title {
  color:var(--hub-ink);
  font-size:13px;
  font-weight:800;
}
.dt-gate,
.dt-detail {
  display:block;
  margin-top:4px;
  color:var(--hub-muted-2);
  font-size:11px;
  line-height:1.45;
}
.dt-evidence {
  margin-top:8px;
}
.dt-evidence summary {
  color:var(--hub-accent);
  cursor:pointer;
  font-size:11px;
  font-weight:800;
}
.dt-evidence-line {
  color:var(--hub-muted);
  font-size:11px;
  line-height:1.45;
  margin-top:4px;
}
.dt-next-card strong {
  display:block;
  margin-top:4px;
  color:var(--hub-ink);
  font-size:13px;
  line-height:1.35;
}
.dt-next-card + .dt-next-card {
  margin-top:8px;
}
.dt-empty-note,
.dt-warning-note {
  padding:10px 11px;
  border:1px solid var(--hub-border-soft);
  border-radius:10px;
  background:var(--hub-panel-soft);
  color:var(--hub-muted);
  font-size:12px;
  line-height:1.45;
}
.dt-warning-note {
  border-color:rgba(240, 68, 56, 0.25);
  background:rgba(240, 68, 56, 0.06);
  color:var(--hub-danger);
}
@media (max-width: 900px) {
  .dt-git-grid,
  .dt-next-grid,
  .dt-git-metrics {
    grid-template-columns:1fr;
  }
  .dt-item-row {
    grid-template-columns:36px minmax(0, 1fr);
  }
  .dt-item-row .dt-pill {
    grid-column:2;
    justify-self:start;
  }
}
.sot-badge {
  display:inline-flex;
  align-items:center;
  padding:2px 8px;
  border-radius:999px;
  font-size:0.68rem;
  font-weight:800;
  letter-spacing:0.02em;
  line-height:1.4;
  white-space:nowrap;
}
.sot-badge-ok { background:rgba(18,183,106,0.12); color:#027a48; }
.sot-badge-warn { background:rgba(247,144,9,0.14); color:#b54708; }
.sot-badge-info { background:rgba(47,128,196,0.12); color:#175cd3; }
.sot-badge-muted { background:rgba(102,112,133,0.12); color:#475467; }
.sot-badge-neutral { background:rgba(152,162,179,0.14); color:#344054; }
.sot-lineage-grid {
  display:grid;
  grid-template-columns:repeat(2, minmax(0, 1fr));
  gap:12px;
  margin:12px 0;
}
.sot-lineage-block {
  border:1px solid rgba(47,128,196,0.14);
  border-radius:12px;
  padding:12px 14px;
  background:linear-gradient(180deg, #ffffff 0%, #f8fbfe 100%);
}
.sot-lineage-block h5 {
  margin:0 0 8px 0;
  font-size:0.82rem;
  color:#175cd3;
  font-weight:800;
}
.sot-path-line {
  font-family:ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size:0.72rem;
  line-height:1.5;
  color:#344054;
  word-break:break-all;
}
.sot-note {
  margin:8px 0 0 0;
  padding:8px 10px;
  border-radius:8px;
  background:rgba(47,128,196,0.06);
  color:#475467;
  font-size:0.74rem;
  line-height:1.45;
}
.sot-issue-line {
  margin-top:6px;
  padding-top:6px;
  border-top:1px dashed rgba(152,162,179,0.35);
  font-size:0.72rem;
  color:#667085;
  line-height:1.45;
}
@media (max-width: 900px) {
  .sot-lineage-grid { grid-template-columns:1fr; }
}
</style>
"""


def _render_html(html: str) -> None:
    """Render static HTML without Markdown code-block interpretation."""
    if hasattr(st, "html"):
        st.html(html)
        return
    st.markdown(html, unsafe_allow_html=True)


def _flow_card(*, stage_id: str, title: str, big: str, unit: str = "", sub: str = "", active: bool = False, alert: bool = False, empty: bool = False) -> str:
    card_class = "flow-card"
    if alert:
        card_class += " alert"
    elif active:
        card_class += " active"
    elif empty:
        card_class += " empty"
    big_html = f"<div class='big'>{escape(big)}<span class='unit'>{escape(unit)}</span></div>" if unit else f"<div class='big'>{escape(big)}</div>"
    return (
        f"<div class='{card_class}'>"
        f"<div class='stage-id'>{escape(stage_id)}</div>"
        f"<h4>{escape(title)}</h4>"
        f"{big_html}"
        f"<div class='sub'>{escape(sub)}</div>"
        f"</div>"
    )


def _flow_arrow() -> str:
    return "<div class='flow-arrow'>→</div>"


def _sot_format_paths(paths: list[str], *, client_canonical: bool = False) -> str:
    if not paths:
        if client_canonical:
            return "<div class='sot-path-line'>— <em>(client-canonical, generated_path=null)</em></div>"
        return "<div class='sot-path-line'>—</div>"
    return "".join(f"<div class='sot-path-line'>{escape(p)}</div>" for p in paths)


def _sot_render_summary_badges(manifest: dict, lineage: dict) -> None:
    meta = manifest.get("meta") or {}
    rollup = (lineage.get("issue_rollup") or {})
    archive = meta.get("archive_candidate_packs") or []
    covered = meta.get("covered_runtime_paths", "—")
    total = meta.get("runtime_candidate_count", "—")
    hub_kpi_grid([
        ("팩", str(meta.get("pack_count", "—")), "MANIFEST packs"),
        ("live=loader", f"{covered}/{total}", "covered runtime paths"),
        ("고아-live", str(len(meta.get("orphan_live_packs") or [])), "orphan_live_packs"),
        ("archive 후보", str(len(archive)), ", ".join(archive) if archive else "—"),
        ("issue", str(rollup.get("total", "—")), "issue_rollup.total"),
    ])


def _sot_filter_packs(
    packs: list[dict],
    *,
    coverage: str,
    loader: str,
    chapter: str,
    archive_only: bool,
    search: str,
    archive_ids: set[str],
) -> list[dict]:
    out: list[dict] = []
    q = search.strip().lower()
    for pack in packs:
        if coverage != "전체" and pack.get("coverage_status") != coverage:
            continue
        if loader != "전체" and pack.get("loader_reference_status") != loader:
            continue
        if chapter != "전체":
            chapters = pack.get("consumer_chapters") or []
            if chapter not in chapters:
                continue
        if archive_only and pack.get("pack_id") not in archive_ids:
            continue
        if q:
            blob = " ".join([
                pack.get("pack_id") or "",
                " ".join(pack.get("member_paths") or []),
                " ".join(sot.normalize_path_list(pack.get("dx_artifacts"))),
            ]).lower()
            if q not in blob:
                continue
        out.append(pack)
    out.sort(key=sot.status_sort_key)
    return out


def _sot_render_lineage_panel(
    pack: dict,
    lineage_row: dict | None,
    lineage: dict,
) -> None:
    hub_section("lineage 상세", level="page")
    if lineage_row is None:
        st.warning(f"`{pack.get('pack_id')}` 에 대한 pack_level_lineage 행이 없습니다.")
        return

    edit_paths = sot.normalize_path_list(lineage_row.get("edit_where"))
    gen_paths = sot.normalize_path_list(lineage_row.get("generates"))
    if not gen_paths and pack.get("generated_path") is None and pack.get("coverage_status") == "dx_covered_byte0":
        client_canonical = bool(pack.get("notes") and "client" in str(pack.get("notes")).lower())
    else:
        client_canonical = False

    used_loaders = sot.normalize_path_list(lineage_row.get("used_by_loaders"))
    consumers = sot.normalize_path_list(lineage_row.get("consumer_chapters"))
    risk = str(lineage_row.get("risk") or pack.get("notes") or "—")
    issues = sot.related_issues(pack, lineage)

    blocks = [
        ("어디서 편집?", _sot_format_paths(edit_paths)),
        (
            "무엇이 생성?",
            _sot_format_paths(gen_paths, client_canonical=client_canonical and not gen_paths),
        ),
        (
            "어디서 사용?",
            _sot_format_paths(used_loaders)
            + f"<div class='sot-note'>consumer: {escape(', '.join(consumers) or '—')}</div>",
        ),
        (
            "무엇이 위험?",
            f"<div class='sot-path-line'>{escape(risk)}</div>"
            + f"<div class='sot-note'>loader: {sot_loader_badge(pack.get('loader_reference_status') or '')}</div>"
            + "".join(
                f"<div class='sot-issue-line'><strong>{escape(i.get('issue_id', '—'))}</strong> "
                f"({escape(i.get('status', '—'))}) — {escape(i.get('description', ''))}</div>"
                for i in issues[:8]
            ),
        ),
    ]
    html = "<div class='sot-lineage-grid'>" + "".join(
        f"<div class='sot-lineage-block'><h5>{escape(title)}</h5>{body}</div>"
        for title, body in blocks
    ) + "</div>"
    _render_html(html)

    # core row-level (dx-covered)
    if pack.get("coverage_status") in ("dx_covered_byte0", "dx_covered_partial"):
        core_rows = lineage.get("core_lineage_row_level") or []
        if core_rows:
            hub_section("core row-level (P1~P3)")
            lines = []
            for row in core_rows:
                if not isinstance(row, dict):
                    continue
                artifact = row.get("artifact") or row.get("artifacts")
                if isinstance(artifact, list):
                    art_text = ", ".join(str(a) for a in artifact)
                else:
                    art_text = str(artifact or "—")
                count = row.get("row_count") or row.get("system_count") or row.get("module_count") or row.get("sub_override_count") or "—"
                lines.append(f"- **{row.get('phase', '—')}** · {art_text} · rows={count}")
            st.markdown("\n".join(lines))

    hub_section("편집 위치 안내")
    st.caption("실편집은 diagnosis-tool authoring → byte-0 재조립 파이프라인을 거칩니다. 관리탭은 read-only 가시화만 제공합니다.")
    for path in edit_paths:
        st.code(path, language=None)


def _render_sot_management() -> None:
    manifest, m_err = sot.load_manifest()
    lineage, l_err = sot.load_lineage()

    if manifest is None or lineage is None:
        reason = m_err or l_err or "알 수 없는 오류"
        st.error(f"P4-core 데이터를 불러올 수 없습니다: {reason}")
        repo = resolve_diagnosis_repo()
        if repo:
            st.code(str(repo.root), language=None)
        else:
            st.code(f"git clone {DIAGNOSIS_TOOL_GITHUB}.git", language="bash")
        return

    meta = manifest.get("meta") or {}
    packs: list[dict] = list(manifest.get("packs") or [])
    archive_ids = set(meta.get("archive_candidate_packs") or [])
    lineage_idx = sot.pack_lineage_index(lineage)

    hub_section("요약")
    _sot_render_summary_badges(manifest, lineage)
    st.caption(
        f"generated {meta.get('generated', '—')} · "
        f"MANIFEST {meta.get('phase', '—')} · "
        f"LINEAGE {(lineage.get('meta') or {}).get('phase', '—')}"
    )

    hub_section("dx 그리드")
    c1, c2, c3, c4 = st.columns(4)
    coverage_opts = ["전체"] + sorted({p.get("coverage_status") for p in packs if p.get("coverage_status")})
    loader_opts = ["전체"] + sorted({p.get("loader_reference_status") for p in packs if p.get("loader_reference_status")})
    chapter_opts = ["전체"] + sorted({ch for p in packs for ch in (p.get("consumer_chapters") or [])})
    with c1:
        cov_filter = st.selectbox("coverage", coverage_opts, key="sot_cov")
    with c2:
        loader_filter = st.selectbox("loader", loader_opts, key="sot_loader")
    with c3:
        ch_filter = st.selectbox("chapter", chapter_opts, key="sot_ch")
    with c4:
        archive_only = st.checkbox("archive 후보만", key="sot_arch")
    search = st.text_input("검색 (pack_id·path)", key="sot_search")

    filtered = _sot_filter_packs(
        packs,
        coverage=cov_filter,
        loader=loader_filter,
        chapter=ch_filter,
        archive_only=archive_only,
        search=search,
        archive_ids=archive_ids,
    )

    rows = []
    for pack in filtered:
        member = pack.get("member_paths") or []
        canonical = member[0] if member else "—"
        if len(member) > 1:
            canonical += f" (+{len(member) - 1})"
        dx = ", ".join(sot.normalize_path_list(pack.get("dx_artifacts"))) or "—"
        issue_n = len(sot.related_issues(pack, lineage))
        rows.append({
            "pack_id": pack.get("pack_id"),
            "status": pack.get("coverage_status"),
            "loader": pack.get("loader_reference_status"),
            "canonical": canonical,
            "dx_artifact": dx,
            "consumer": ", ".join(pack.get("consumer_chapters") or []),
            "lineage": pack.get("lineage_status"),
            "issues": issue_n,
        })

    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.caption(f"{len(filtered)} / {len(packs)} packs")

    pack_ids = [p.get("pack_id") for p in filtered if p.get("pack_id")]
    if not pack_ids:
        st.info("필터 조건에 맞는 팩이 없습니다.")
        return

    selected = st.selectbox("lineage 상세 — pack 선택", pack_ids, key="sot_selected_pack")
    selected_pack = next(p for p in filtered if p.get("pack_id") == selected)
    _sot_render_lineage_panel(selected_pack, lineage_idx.get(selected), lineage)


def render() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    meta = dm.load_migration_meta()
    items = dm.load_migration_items()

    repo, evals = _cached_evaluate(tuple(it.key for it in items))
    snap = measure_diagnosis()
    github_url = meta.get("github") or DIAGNOSIS_TOOL_GITHUB

    hub_pagebar(
        "진단툴",
        "Migration Control",
        f"{meta.get('version', '')} · git HEAD 기준으로 데이터 마이그레이션 진도를 자동 평가합니다.",
        "Git Verified",
    )
    _render_html(
        f"<div class='dt-source-line'>정본: <a href='{escape(github_url)}' target='_blank' rel='noopener noreferrer'>{escape(github_url)}</a></div>"
    )

    view = st.radio(
        "뷰",
        ["마이그레이션 진도", "진실원(SoT) 관리"],
        horizontal=True,
        label_visibility="collapsed",
        key="diag_mgmt_view",
    )
    if view == "진실원(SoT) 관리":
        _render_sot_management()
        return

    if st.button("git 기준 재평가", type="primary"):
        st.cache_data.clear()
        st.rerun()

    status_counts = _migration_status_counts(items, evals)
    _render_migration_flow(repo or snap.repo, snap, status_counts)

    hub_section("Git 스냅샷")
    _render_git_header(repo or snap.repo, snap)
    hub_section("마이그레이션 현황")
    _render_summary(status_counts)
    _render_items(items, evals)
    hub_section("다음 작업")
    _render_next(items, evals)


def _migration_status_counts(items, evals) -> dict[str, int]:
    counts = {"pending": 0, "success": 0, "failure": 0, "verified": 0, "blocked": 0}
    for item in items:
        status_value = evals[item.key].status
        counts[status_value] = counts.get(status_value, 0) + 1
    return counts


def _render_migration_flow(repo, snap, counts: dict[str, int]) -> None:
    git_big = repo.branch if repo else "Missing"
    git_sub = f"HEAD {repo.head_short}" if repo else "로컬 clone 연결 필요"
    data_src = f"{snap.tracked_data_src:,}"
    done_count = counts.get("success", 0) + counts.get("verified", 0)
    blocked_count = counts.get("blocked", 0)
    failed_count = counts.get("failure", 0)
    cards = [
        _flow_card(stage_id="① git", title="정본 확인", big=git_big, sub=git_sub, active=bool(repo and repo.remote_ok), alert=not bool(repo and repo.remote_ok)),
        _flow_arrow(),
        _flow_card(stage_id="② data/src", title="데이터 추적", big=data_src, unit="files", sub="tracked migration source", empty=(snap.tracked_data_src == 0)),
        _flow_arrow(),
        _flow_card(stage_id="③ 완료", title="검증 통과", big=f"{done_count:,}", unit="items", sub="success + verified", active=(done_count > 0)),
        _flow_arrow(),
        _flow_card(stage_id="④ 보완", title="차단·실패", big=f"{blocked_count + failed_count:,}", unit="items", sub=f"blocked {blocked_count:,} · failure {failed_count:,}", alert=(blocked_count + failed_count > 0)),
    ]
    _render_html("<div class='flow-row migration'>" + "".join(cards) + "</div>")


@st.cache_data(ttl=60)
def _cached_evaluate(_keys: tuple[str, ...]):
    items = dm.load_migration_items()
    return evaluate_all(items)


def _render_git_header(repo, snap) -> None:
    github = DIAGNOSIS_TOOL_GITHUB

    if repo is None:
        _render_html(
            f"""
<div class="dt-git-panel">
  <div class="dt-panel-head">
    <div>
      <div class="dt-panel-title">Git 스냅샷</div>
      <div class="dt-panel-subtitle">로컬 clone 연결 필요</div>
    </div>
    <span class="dt-pill dt-pill-failure">Missing</span>
  </div>
  <div class="dt-panel-body">
    <div class="dt-warning-note">{escape(github)} 의 로컬 clone을 찾을 수 없습니다.</div>
    <div class="dt-git-caption">clone 후 iris-hub와 형제 경로에 두거나 DIAGNOSIS_TOOL_GIT 환경변수로 경로를 지정하세요.</div>
  </div>
</div>
"""
        )
        st.code(f"git clone {github}.git", language="bash")
        return

    remote_status = "Git Verified" if repo.remote_ok else "Remote Check"
    remote_status_class = "dt-pill-ok" if repo.remote_ok else "dt-pill-failure"
    working_tree_status = "dirty" if repo.dirty else "clean"
    push_label = format_git_date(repo.last_push_iso)
    if repo.unpushed_commits > 0:
        push_label = f"{push_label} (+{repo.unpushed_commits})"

    remote_warning = ""
    if not repo.remote_ok:
        remote_warning = f"""
<div class="dt-warning-note">origin이 정본과 다릅니다. 기대: {escape(github)} · 실제: {escape(repo.remote_url or '—')}</div>
"""

    _render_html(
        f"""
<div class="dt-git-grid">
  <div class="dt-git-panel">
    <div class="dt-panel-head">
      <div>
        <div class="dt-panel-title">Git 스냅샷</div>
        <div class="dt-panel-subtitle">branch, HEAD, push, working tree를 한 번에 확인합니다.</div>
      </div>
      <span class="dt-pill {remote_status_class}">{remote_status}</span>
    </div>
    <div class="dt-panel-body">
      {remote_warning}
      <div class="dt-git-metrics">
        <div class="dt-git-metric"><span>branch</span><strong>{escape(repo.branch)}</strong></div>
        <div class="dt-git-metric"><span>HEAD</span><strong>{escape(repo.head_short)}</strong></div>
        <div class="dt-git-metric"><span>최근 푸시</span><strong>{escape(push_label)}</strong></div>
        <div class="dt-git-metric"><span>최근 커밋</span><strong>{escape(format_git_date(repo.last_commit_iso))}</strong></div>
        <div class="dt-git-metric"><span>data/src</span><strong>{snap.tracked_data_src:,}</strong></div>
        <div class="dt-git-metric"><span>working tree</span><strong>{escape(working_tree_status)}</strong></div>
      </div>
      <div class="dt-git-caption">clone: {escape(str(repo.root))} · origin: {escape(repo.remote_url or '—')} · 로컬 커밋: {escape(format_git_date(repo.last_commit_iso))}</div>
    </div>
  </div>
  <div class="dt-git-panel">
    <div class="dt-panel-head">
      <div>
        <div class="dt-panel-title">진입점</div>
        <div class="dt-panel-subtitle">정본 확인과 재평가 액션을 분리합니다.</div>
      </div>
      <span class="dt-pill dt-pill-neutral">Actions</span>
    </div>
    <div class="dt-panel-body">
      <div class="dt-action-list">
        <a class="dt-action-link" href="{escape(github)}" target="_blank" rel="noopener noreferrer">GitHub 정본 열기</a>
      </div>
      <div class="dt-git-caption">완성(푸시)일: {escape(format_git_date(repo.last_push_iso))}{' · 미푸시 ' + str(repo.unpushed_commits) + '건' if repo.unpushed_commits else ''}</div>
    </div>
  </div>
</div>
"""
    )


def _render_summary(counts: dict[str, int]) -> None:
    cards = [
        _flow_card(stage_id="pending", title="진입 대기", big=str(counts.get("pending", 0)), unit="items", sub="ready to enter", active=(counts.get("pending", 0) > 0)),
        _flow_arrow(),
        _flow_card(stage_id="success", title="완료", big=str(counts.get("success", 0)), unit="items", sub="completed", empty=(counts.get("success", 0) == 0)),
        _flow_arrow(),
        _flow_card(stage_id="failure", title="실패", big=str(counts.get("failure", 0)), unit="items", sub="needs work", alert=(counts.get("failure", 0) > 0)),
        _flow_arrow(),
        _flow_card(stage_id="blocked", title="차단", big=str(counts.get("blocked", 0)), unit="items", sub=f"verified {counts.get('verified', 0)}", alert=(counts.get("blocked", 0) > 0)),
    ]
    _render_html("<div class='flow-row migration'>" + "".join(cards) + "</div>")


def _render_items(items, evals) -> None:
    phase_filter = st.selectbox(
        "Phase 필터",
        ["전체"] + sorted({it.phase for it in items}, key=_phase_sort_key),
        label_visibility="collapsed",
    )

    by_phase: dict[str, list] = defaultdict(list)
    for it in items:
        if phase_filter != "전체" and it.phase != phase_filter:
            continue
        by_phase[it.phase].append(it)

    phase_sections = []
    for phase in sorted(by_phase.keys(), key=_phase_sort_key):
        rows = "".join(_render_row_html(it, evals[it.key]) for it in by_phase[phase])
        phase_sections.append(f'<div class="dt-phase-hdr">Phase {escape(phase)}</div>{rows}')

    st.markdown(
        f"""
<div class="dt-items-panel">
  <div class="dt-panel-head">
    <div>
      <div class="dt-panel-title">마이그레이션 항목</div>
      <div class="dt-panel-subtitle">게이트, 상태, 근거를 phase 단위로 확인합니다.</div>
    </div>
    <span class="dt-pill dt-pill-neutral">{len(by_phase)} phases</span>
  </div>
  <div class="dt-filter-shell">현재 필터: <strong>{escape(phase_filter)}</strong></div>
  {''.join(phase_sections)}
</div>
""",
        unsafe_allow_html=True,
    )


def _render_row_html(it, ev) -> str:
    status_label = dm.STATUS_LABEL.get(ev.status, ev.status)
    status_class = f"dt-pill-{escape(ev.status)}"
    gate_html = f'<span class="dt-gate">게이트: {escape(it.gate)}</span>' if it.gate else ""
    evidence_html = ""
    if ev.evidence:
        evidence_lines = "".join(
            f'<div class="dt-evidence-line">{escape(line)}</div>'
            for line in ev.evidence
        )
        evidence_html = f"""
<details class="dt-evidence">
  <summary>근거 {len(ev.evidence)}건</summary>
  {evidence_lines}
</details>
"""

    return f"""
<div class="dt-item-row">
  <div class="dt-item-id">{escape(str(it.id))}</div>
  <div>
    <div class="dt-item-title">{escape(it.title)}</div>
    {gate_html}
    <span class="dt-detail">{escape(ev.detail)}</span>
    {evidence_html}
  </div>
  <span class="dt-pill {status_class}">{escape(status_label)}</span>
</div>
"""


def _render_next(items, evals) -> None:
    ready = [it for it in items if evals[it.key].status == "pending"]
    failed = [it for it in items if evals[it.key].status == "failure"]
    blocked = [it for it in items if evals[it.key].status == "blocked"]

    ready_body = _render_next_cards(ready[:8], evals, "진입 가능") or "<div class='dt-empty-note'>진입 가능한 대기 항목 없음.</div>"
    failed_body = _render_next_cards(failed, evals, "재작업 필요") or "<div class='dt-empty-note'>실패 항목 없음.</div>"
    blocked_body = _render_blocked_cards(blocked, evals) or "<div class='dt-empty-note'>선행 미충족 항목 없음.</div>"

    st.markdown(
        f"""
<div class="dt-next-grid">
  <div class="dt-next-panel">
    <div class="dt-panel-head">
      <div>
        <div class="dt-panel-title">다음 작업</div>
        <div class="dt-panel-subtitle">즉시 진입 가능 항목과 실패 항목을 먼저 봅니다.</div>
      </div>
      <span class="dt-pill dt-pill-pending">{len(ready)} ready</span>
    </div>
    <div class="dt-panel-body">
      {failed_body if failed else ready_body}
    </div>
  </div>
  <div class="dt-next-panel">
    <div class="dt-panel-head">
      <div>
        <div class="dt-panel-title">차단 항목</div>
        <div class="dt-panel-subtitle">선행 조건 미충족으로 대기 중인 항목입니다.</div>
      </div>
      <span class="dt-pill dt-pill-blocked">{len(blocked)} blocked</span>
    </div>
    <div class="dt-panel-body">{blocked_body}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def _render_next_cards(items, evals, label: str) -> str:
    return "".join(
        f"""
<div class="dt-next-card">
  <span>{escape(label)} · Phase {escape(it.phase)} · {escape(str(it.id))}</span>
  <strong>{escape(it.title)}</strong>
  <div class="dt-next-detail">{escape(evals[it.key].detail)}</div>
</div>
"""
        for it in items
    )


def _render_blocked_cards(items, evals) -> str:
    cards = []
    for it in items[:8]:
        unmet = [
            dependency_key for dependency_key in it.depends
            if evals.get(dependency_key) and evals[dependency_key].status not in ("success", "verified")
        ]
        cards.append(
            f"""
<div class="dt-next-card">
  <span>blocked · Phase {escape(it.phase)} · {escape(str(it.id))}</span>
  <strong>{escape(it.title)}</strong>
  <div class="dt-next-detail">선행 미충족: {escape(', '.join(unmet) or '—')}</div>
</div>
"""
        )
    return "".join(cards)


def _phase_sort_key(phase: str) -> tuple:
    try:
        return (0, float(phase))
    except ValueError:
        return (1, phase)
