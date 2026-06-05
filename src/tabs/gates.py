"""탭 3: 게이트 — 다음 진입 가능한 Phase 안내 (V2.5.3 §3.4)"""
from __future__ import annotations

import streamlit as st

from src import phases as ph
from src import state as st_mod


def render() -> None:
    st.markdown("## 🎯 다음 게이트")
    phs = ph.load_phases()
    sk = st_mod.status_by_key_for_phases(phs)

    # 분류
    next_phases: list[ph.Phase] = []
    blocked: list[ph.Phase] = []
    in_progress: list[ph.Phase] = []

    for p in phs:
        block = st_mod.get_phase_block(p)
        display = ph.derive_display_status(p, block.get("status"), sk)
        if display == "pending":
            next_phases.append(p)
        elif display == "blocked":
            blocked.append(p)
        elif display == "in_progress":
            in_progress.append(p)

    if in_progress:
        st.markdown("### ⏳ 진행 중")
        for p in in_progress:
            _phase_card(p, "in_progress")
        st.divider()

    if next_phases:
        st.markdown("### 🔓 진입 가능 (의존성 충족)")
        for p in next_phases:
            _phase_card(p, "pending")
    else:
        st.info("진입 가능한 Phase 없음. 진행 중 작업 완료 또는 우회 마킹 필요.")

    if blocked:
        st.divider()
        st.markdown("### 🔒 의존성 미충족 (대기)")
        for p in blocked:
            unmet = [d for d in p.depends if sk.get(d) not in ("done", "skipped")]
            st.write(f"- **{p.version} Phase {p.id}** — {p.title} (의존: {', '.join(unmet)})")


def _phase_card(p, status: str) -> None:
    with st.container(border=True):
        st.markdown(f"### {p.version} Phase {p.id} — {p.title}")
        c1, c2, c3 = st.columns(3)
        c1.write(f"⏱ 추정: **{p.est_days}일**")
        c2.write(f"🔗 의존: {', '.join(p.depends) if p.depends else '없음'}")
        c3.write(f"📍 상태: **{status}**")
