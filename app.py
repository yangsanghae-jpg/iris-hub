"""iris-hub v0 진입점 — V2.5.3 §3.1 6탭 구조 (3 active + 3 placeholder)"""
import streamlit as st

from src.tabs import dashboard, gates, inventory, placeholders


def main() -> None:
    st.set_page_config(
        page_title="iris-hub",
        page_icon="📊",
        layout="wide",
    )

    st.markdown("# 📊 iris-hub")
    st.caption("진도 점검 콘솔 · V2.5.3 동결 · M2 :8765")

    tabs = st.tabs([
        "📊 진척",
        "📦 데이터",
        "🎯 게이트",
        "📊 인사이트",
        "📚 위키",
        "⚙️ 설정",
    ])

    with tabs[0]:
        dashboard.render()
    with tabs[1]:
        inventory.render()
    with tabs[2]:
        gates.render()
    with tabs[3]:
        placeholders.render_insights()
    with tabs[4]:
        placeholders.render_wiki()
    with tabs[5]:
        placeholders.render_settings()


if __name__ == "__main__":
    main()
