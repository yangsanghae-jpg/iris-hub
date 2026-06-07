"""iris-hub v0 진입점 — V2.5.3 §3.1 7탭 구조 (3 active + 챗 + 3 placeholder)"""
import socket

import streamlit as st

from src.tabs import chat, dashboard, gates, inventory, placeholders


def _port_alive(host: str, port: int, timeout: float = 0.3) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _sidebar() -> None:
    with st.sidebar:
        st.markdown("### 🔗 운영 콘솔")
        st.caption("외부 백엔드 직접 접근")
        st.link_button("📊 Grafana", "http://127.0.0.1:3030", use_container_width=True)
        st.link_button("💬 OpenWebUI 챗", "http://127.0.0.1:3000", use_container_width=True)
        st.link_button("🦅 OpenClaw", "http://127.0.0.1:18789", use_container_width=True,
                       help="iris-claw — 가동 시 (V2.5.1 §11 #10)")
        st.link_button("🧠 memory-admin", "http://127.0.0.1:18020", use_container_width=True)
        st.link_button("📚 Obsidian (알다)", "obsidian://open?vault=LearningMaster",
                       use_container_width=True,
                       help="외부 시스템 — 데스크톱 앱 설치 시")

        st.divider()
        st.markdown("### 🟢 라이브 상태")
        for label, port in [
            ("Grafana", 3030),
            ("OpenWebUI", 3000),
            ("OpenClaw", 18789),
            ("L2-gateway", 8011),
            ("L3-memory", 8001),
            ("L4-RS-search", 8020),
            ("K5 wiki :8081", 8081),
            ("nomic-embed", 11434),
        ]:
            alive = _port_alive("127.0.0.1", port)
            icon = "🟢" if alive else "🔴"
            st.caption(f"{icon} {label}")


def main() -> None:
    st.set_page_config(
        page_title="iris-hub",
        page_icon="📊",
        layout="wide",
    )

    _sidebar()

    st.markdown("# 📊 iris-hub")
    st.caption("진도 점검 콘솔 · V2.5.3 동결 · M2 :8765")

    tabs = st.tabs([
        "📊 진척",
        "📦 데이터",
        "🎯 게이트",
        "📊 인사이트",
        "📚 위키",
        "⚙️ 설정",
        "💬 챗",
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
    with tabs[6]:
        chat.render()


if __name__ == "__main__":
    main()
