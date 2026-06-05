"""탭 1: 진척 — V2.5.3 §3.2"""
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
    st.markdown("## 📊 마일스톤 진척도")
    phs = ph.load_phases()
    sk = st_mod.status_by_key_for_phases(phs)

    counts = {"done": 0, "in_progress": 0, "skipped": 0, "pending": 0, "blocked": 0}
    rows = []
    for p in phs:
        block = st_mod.get_phase_block(p)
        display = ph.derive_display_status(p, block.get("status"), sk)
        counts[display] += 1
        rows.append((p, display, block))

    # summary
    total = len(phs)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("✅ 완료", counts["done"])
    c2.metric("⏳ 진행", counts["in_progress"])
    c3.metric("🔵 우회", counts["skipped"])
    c4.metric("⬜ 대기", counts["pending"])
    c5.metric("🔒 막힘", counts["blocked"])

    st.divider()

    # phase rows
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

        # 마킹 액션 (H.15)
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
