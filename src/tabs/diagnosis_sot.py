"""탭: 🔧 진단툴 — DIAG-SOT 진실원(MANIFEST+LINEAGE) read-only 가시화."""
from __future__ import annotations

from html import escape

import streamlit as st

from src.config import DIAGNOSIS_TOOL_GITHUB
from src.diagnosis_git import resolve_diagnosis_repo
from src.store import diag_sot as sot
from src.ui_kit import hub_kpi_grid, hub_pagebar, hub_section, sot_loader_badge

_CSS = """
<style>
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
    if hasattr(st, "html"):
        st.html(html)
        return
    st.markdown(html, unsafe_allow_html=True)


def _format_paths(paths: list[str], *, client_canonical: bool = False) -> str:
    if not paths:
        if client_canonical:
            return "<div class='sot-path-line'>— <em>(client-canonical, generated_path=null)</em></div>"
        return "<div class='sot-path-line'>—</div>"
    return "".join(f"<div class='sot-path-line'>{escape(p)}</div>" for p in paths)


def _render_summary_badges(manifest: dict, lineage: dict) -> None:
    meta = manifest.get("meta") or {}
    rollup = lineage.get("issue_rollup") or {}
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


def _filter_packs(
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


def _render_lineage_panel(
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
        ("어디서 편집?", _format_paths(edit_paths)),
        (
            "무엇이 생성?",
            _format_paths(gen_paths, client_canonical=client_canonical and not gen_paths),
        ),
        (
            "어디서 사용?",
            _format_paths(used_loaders)
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
                count = (
                    row.get("row_count")
                    or row.get("system_count")
                    or row.get("module_count")
                    or row.get("sub_override_count")
                    or "—"
                )
                lines.append(f"- **{row.get('phase', '—')}** · {art_text} · rows={count}")
            st.markdown("\n".join(lines))

    hub_section("편집 위치 안내")
    st.caption(
        "실편집은 diagnosis-tool authoring → byte-0 재조립 파이프라인을 거칩니다. "
        "이 탭은 read-only 가시화만 제공합니다."
    )
    for path in edit_paths:
        st.code(path, language=None)


def render() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)

    hub_pagebar(
        "진단툴",
        "SoT Control",
        "MANIFEST+LINEAGE 기반 진실원 그리드 · lineage 4블록(edit→generate→use→risk). read-only.",
        "DIAG-SOT",
    )

    if st.button("데이터 새로고침", type="secondary"):
        st.cache_data.clear()
        st.rerun()

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
    _render_summary_badges(manifest, lineage)
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

    filtered = _filter_packs(
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
    _render_lineage_panel(selected_pack, lineage_idx.get(selected), lineage)
