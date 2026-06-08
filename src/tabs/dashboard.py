"""탭 1: 진척 + 다음 작업 — V2.5.3 §3.2 + 게이트 흡수 (2026-06-08)"""
from __future__ import annotations

import streamlit as st

from src import phases as ph
from src import state as st_mod

ICON = {
    "done": "✅",
    "in_progress": "⏳",
    "skipped": "🔵",
    "pending": "⬜",
    "blocked": "🔒",
}


def render() -> None:
    phs = ph.load_phases()
    sk = st_mod.status_by_key_for_phases(phs)

    counts = {"done": 0, "in_progress": 0, "skipped": 0, "pending": 0, "blocked": 0}
    rows = []
    for p in phs:
        block = st_mod.get_phase_block(p)
        display = ph.derive_display_status(p, block.get("status"), sk)
        counts[display] += 1
        rows.append((p, display, block))

    # ─── 상단 요약 ───────────────────────────────────────────────────────
    st.markdown("## 📊 마일스톤 진척도")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("✅ 완료", counts["done"])
    c2.metric("⏳ 진행", counts["in_progress"])
    c3.metric("🔵 우회", counts["skipped"])
    c4.metric("⬜ 대기", counts["pending"])
    c5.metric("🔒 막힘", counts["blocked"])

    st.divider()

    # ─── Phase 행 ──────────────────────────────────────────────────────
    for p, display, block in rows:
        cols = st.columns([1.5, 1, 5, 2, 2.5])
        cols[0].write(f"**{p.version}**")
        cols[1].write(f"Phase {p.id}")
        cols[2].write(p.title)
        cols[3].write(f"{ICON[display]} {display}")

        date_text = ""
        if display == "done" and block.get("done"):
            date_text = block["done"][:10]
        elif display == "in_progress" and block.get("started"):
            date_text = f"start {block['started'][:10]}"
        elif display == "skipped" and block.get("skipped"):
            date_text = f"skip: {block['skipped']}"
        cols[4].write(date_text)

        with st.expander("⋮ 액션", expanded=False):
            ac1, ac2, ac3, ac4, ac5 = st.columns(5)
            if ac1.button("✅ 완료", key=f"done-{p.key}"):
                st_mod.mark_done(p)
                st.rerun()
            if ac2.button("⏳ 시작", key=f"start-{p.key}"):
                st_mod.mark_start(p)
                st.rerun()
            reason = ac3.text_input("우회 사유", key=f"skipreason-{p.key}", label_visibility="collapsed", placeholder="우회 사유")
            if ac4.button("🔵 우회", key=f"skip-{p.key}"):
                st_mod.mark_skip(p, reason or "(no reason)")
                st.rerun()
            if ac5.button("↩️ 취소", key=f"unset-{p.key}"):
                st_mod.mark_unset(p)
                st.rerun()
            note = block.get("note", "")
            new_note = st.text_input("📝 메모", value=note, key=f"note-{p.key}")
            if new_note != note:
                st_mod.set_note(p, new_note)
                st.rerun()

    # ─── 다음 작업 (이전 게이트 탭 흡수) ─────────────────────────────────
    st.divider()
    _render_next_actions(phs, sk)


def _render_next_actions(phs, sk: dict[str, str]) -> None:
    """이전 gates.py 흡수. 진입 가능 / 진행 중 / 막힘 분류."""
    st.markdown("## 🎯 다음 작업")

    in_progress: list = []
    next_phases: list = []
    blocked: list = []
    for p in phs:
        block = st_mod.get_phase_block(p)
        display = ph.derive_display_status(p, block.get("status"), sk)
        if display == "in_progress":
            in_progress.append((p, block))
        elif display == "pending":
            next_phases.append(p)
        elif display == "blocked":
            blocked.append(p)

    if in_progress:
        st.markdown("### ⏳ 진행 중")
        for p, _ in in_progress:
            _phase_card(p, "in_progress")
        st.markdown("")

    if next_phases:
        st.markdown("### 🔓 진입 가능 (의존성 충족)")
        for p in next_phases:
            _phase_card(p, "pending")
    else:
        st.success(
            "🎉 V2.5.1 §7 7 Phase 모두 종결 — 진입 가능 Phase 없음. "
            "다음 사이클은 V2.5.3 §18.7/§19.3 *Phase 외 정정 후보* 중 결정."
        )
        with st.expander("📋 Phase 외 후보 (§18.7 + §19.3)", expanded=False):
            st.markdown("""
- **raw_intake orphan chunks 자동 정리** (§18.6)
- **reference 630건 K3 매트릭스 키 재검증** (§17.6)
- **flatten_json chunk 길이 정책** (§17.6)
- **reference_diagnosis content hash 적용** (§18.7)
- **migrate.py schema bootstrap** (M5 §6.2)
- **5.7 L6-D1 호출 전환** — V2.5 §10 (a)(c)(d) 측정 가능
- **semantic (B)/(C) 본질 해결** (§19.3) — 9000+ ingest 시점 보류
            """)

    if blocked:
        st.markdown("### 🔒 의존성 미충족")
        for p in blocked:
            unmet = [d for d in p.depends if sk.get(d) not in ("done", "skipped")]
            st.write(f"- **{p.version} Phase {p.id}** — {p.title} (의존: {', '.join(unmet)})")


def _phase_card(p, status: str) -> None:
    with st.container(border=True):
        st.markdown(f"#### {p.version} Phase {p.id} — {p.title}")
        c1, c2, c3 = st.columns(3)
        c1.write(f"⏱ 추정: **{p.est_days}일**")
        c2.write(f"🔗 의존: {', '.join(p.depends) if p.depends else '없음'}")
        c3.write(f"📍 상태: **{status}**")
