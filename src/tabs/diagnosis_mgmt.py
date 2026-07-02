"""탭: 🔧 진단툴 — git 기준 마이그레이션 진도 자동 평가."""
from __future__ import annotations

from collections import defaultdict

import streamlit as st

from src import diagnosis_migration as dm
from src.config import DIAGNOSIS_TOOL_GITHUB
from src.diagnosis_git import format_git_date
from src.diagnosis_eval import evaluate_all
from src.diagnosis_measurements import measure_diagnosis
from src.ui_kit import hub_kpi_grid, hub_pagebar, hub_section

_CSS = """
<style>
.dt-phase-hdr {
  font-size:0.85em; font-weight:700; color:#555;
  margin:18px 0 8px 0; padding-bottom:4px;
  border-bottom:2px solid rgba(100,100,100,0.15);
}
.dt-gate { font-size:0.78em; color:#888; }
.dt-detail { font-size:0.75em; color:#666; }
</style>
"""


def render() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    meta = dm.load_migration_meta()
    items = dm.load_migration_items()

    if st.button("🔄 git 기준 재평가", type="primary"):
        st.cache_data.clear()

    repo, evals = _cached_evaluate(tuple(it.key for it in items))
    snap = measure_diagnosis()

    hub_pagebar(
        "진단툴",
        "Migration Control",
        f"{meta.get('version', '')} · git HEAD 기준으로 데이터 마이그레이션 진도를 자동 평가합니다.",
        "Git Verified",
    )
    st.caption(
        f"정본: [{meta.get('github') or DIAGNOSIS_TOOL_GITHUB}]({meta.get('github') or DIAGNOSIS_TOOL_GITHUB})"
    )

    _render_git_header(repo or snap.repo, snap)
    st.divider()
    _render_summary(items, evals)
    st.divider()
    _render_items(items, evals)
    st.divider()
    _render_next(items, evals)


@st.cache_data(ttl=60)
def _cached_evaluate(_keys: tuple[str, ...]):
    items = dm.load_migration_items()
    return evaluate_all(items)


def _render_git_header(repo, snap) -> None:
    hub_section("📍 Git 스냅샷")
    github = DIAGNOSIS_TOOL_GITHUB

    if repo is None:
        st.error(f"**{github}** 의 로컬 clone을 찾을 수 없습니다.")
        st.code(f"git clone {github}.git", language="bash")
        st.caption(
            "clone 후 iris-hub와 형제 경로(`…/0Dev/diagnosis-tool`)에 두거나 "
            "`DIAGNOSIS_TOOL_GIT=/path/to/clone` 으로 지정."
        )
        st.link_button("GitHub 열기", github, use_container_width=False)
        return

    if not repo.remote_ok:
        st.warning(
            f"origin이 정본과 다릅니다. 기대: `{github}` · 실제: `{repo.remote_url}`"
        )

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("branch", repo.branch)
    c2.metric("HEAD", repo.head_short)
    push_label = format_git_date(repo.last_push_iso)
    if repo.unpushed_commits > 0:
        push_label = f"{push_label} (+{repo.unpushed_commits})"
    c3.metric("최근 푸시", push_label)
    c4.metric("최근 커밋", format_git_date(repo.last_commit_iso))
    c5.metric("data/src", snap.tracked_data_src)
    c6.metric("working tree", "dirty" if repo.dirty else "clean")

    st.link_button("GitHub 정본", github, use_container_width=False)
    st.caption(
        f"clone: `{repo.root}` · origin: `{repo.remote_url or '—'}` · "
        f"완성(푸시)일: **{format_git_date(repo.last_push_iso)}** · "
        f"로컬 커밋: {format_git_date(repo.last_commit_iso)}"
        + (f" · 미푸시 {repo.unpushed_commits}건" if repo.unpushed_commits else "")
    )


def _render_summary(items, evals) -> None:
    counts = {"pending": 0, "success": 0, "failure": 0, "verified": 0, "blocked": 0}
    for it in items:
        st_val = evals[it.key].status
        counts[st_val] = counts.get(st_val, 0) + 1

    hub_kpi_grid([
        ("pending", str(counts["pending"]), "ready to enter"),
        ("success", str(counts["success"]), "completed"),
        ("failure", str(counts["failure"]), "needs work"),
        ("blocked", str(counts["blocked"]), f"verified {counts['verified']}"),
    ])


def _render_items(items, evals) -> None:
    hub_section("📋 마이그레이션 항목")

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

    for phase in sorted(by_phase.keys(), key=_phase_sort_key):
        st.markdown(f'<div class="dt-phase-hdr">Phase {phase}</div>', unsafe_allow_html=True)
        for it in by_phase[phase]:
            _render_row(it, evals[it.key])


def _render_row(it, ev) -> None:
    cols = st.columns([0.6, 4, 1.2, 3])
    cols[0].write(f"**{it.id}**")
    title_col = cols[1]
    title_col.write(it.title)
    if it.gate:
        title_col.markdown(f'<span class="dt-gate">게이트: {it.gate}</span>', unsafe_allow_html=True)
    title_col.markdown(f'<span class="dt-detail">{ev.detail}</span>', unsafe_allow_html=True)

    icon = dm.STATUS_ICON.get(ev.status, "⬜")
    label = dm.STATUS_LABEL.get(ev.status, ev.status)
    cols[2].write(f"{icon} {label}")

    if ev.evidence:
        with cols[3].expander("근거", expanded=False):
            for line in ev.evidence:
                st.caption(line)


def _render_next(items, evals) -> None:
    hub_section("🎯 다음 작업")
    ready = [it for it in items if evals[it.key].status == "pending"]
    failed = [it for it in items if evals[it.key].status == "failure"]
    blocked = [it for it in items if evals[it.key].status == "blocked"]

    if ready:
        st.markdown("**⬜ 진입 가능 (대기)**")
        for it in ready[:8]:
            ev = evals[it.key]
            st.write(f"- Phase **{it.phase}** · {it.id} — {it.title}")
            st.caption(ev.detail)
    else:
        st.info("진입 가능한 대기 항목 없음.")

    if failed:
        st.markdown("**❌ 실패 — git 기준 재작업 필요**")
        for it in failed:
            st.write(f"- Phase **{it.phase}** · {it.id} — {it.title}")
            st.caption(evals[it.key].detail)

    if blocked:
        with st.expander(f"🔒 선행 미충족 ({len(blocked)}건)", expanded=False):
            for it in blocked:
                unmet = [
                    d for d in it.depends
                    if evals.get(d) and evals[d].status not in ("success", "verified")
                ]
                st.write(f"- **{it.key}** {it.title} ← {', '.join(unmet)}")


def _phase_sort_key(phase: str) -> tuple:
    try:
        return (0, float(phase))
    except ValueError:
        return (1, phase)
