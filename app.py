"""iris-hub v0 — 평면 탭 구조 (V2.5.3 §3.10 + 본 사이클 수정).

탭 구조:
  IRIS 자체 (7):  📊 진척 | 📥 입력 | 🌐 외부응답 | 📦 데이터 | 🕸️ 그래프 | 📊 인사이트 | 📚 위키
  외부 진입점 (4): 💬 WebUI | 🦅 OpenClaw | 🌐 Grafana | 📚 Obsidian
  설정 (1):       ⚙️ 설정

UI 정책:
  - 헤더 간소화 (iris-hub 제목 작게)
  - 상단 탭 sticky (스크롤 무관 항상 표시)
  - 사이드바: 운영 콘솔 + 라이브 상태 (장기 통합 후보)
"""
import socket

import streamlit as st

from src.tabs import dashboard, external, external_capture, graph, intake, inventory, placeholders, wiki_k2


def _port_alive(host: str, port: int, timeout: float = 0.3) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _inject_css() -> None:
    """헤더 축소 + 탭 sticky."""
    st.markdown("""
<style>
/* 상단 여백 축소 */
.block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; }

/* iris-hub 제목 축소 */
h1 { font-size: 1.4rem !important; margin: 0 !important; padding: 0 !important; }
h1 + div[data-testid="stCaptionContainer"] { margin-bottom: 0.5rem !important; }

/* 상단 탭 sticky */
div[data-testid="stTabs"] > div:first-child {
    position: sticky;
    top: 0;
    background: white;
    z-index: 999;
    padding: 0.25rem 0;
    border-bottom: 1px solid #eee;
}
/* dark mode 호환 */
@media (prefers-color-scheme: dark) {
    div[data-testid="stTabs"] > div:first-child { background: #0e1117; }
}

/* 탭 폰트·여백 압축 */
button[data-baseweb="tab"] { padding: 0.4rem 0.8rem !important; font-size: 0.9rem !important; }
</style>
    """, unsafe_allow_html=True)


def _sidebar() -> None:
    with st.sidebar:
        st.markdown("### 🔗 운영 콘솔")
        st.caption("외부 백엔드 (장기: 상단 탭과 통합 후보)")
        st.link_button("📊 Grafana", "http://127.0.0.1:3030", use_container_width=True)
        st.link_button("💬 OpenWebUI", "http://127.0.0.1:3000", use_container_width=True)
        st.link_button("🦅 OpenClaw", "http://127.0.0.1:18789", use_container_width=True)
        st.link_button("📚 Obsidian", "obsidian://open?vault=LearningMaster",
                       use_container_width=True)

        st.divider()
        st.markdown("### 🟢 라이브 상태")
        for label, port in [
            ("Grafana", 3030),
            ("OpenWebUI", 3000),
            ("OpenClaw", 18789),
            ("L2-gateway", 8011),
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
    _inject_css()
    _sidebar()

    # 간소 헤더 (1행)
    st.markdown("# 📊 iris-hub")
    st.caption("V2.6.2.2 · M2 :8765 · K2 v2 멀티라벨")

    tabs = st.tabs([
        # IRIS 자체 (7)
        "📊 진척",
        "📥 입력",
        "🌐 외부응답",
        "📦 데이터",
        "🕸️ 그래프",
        "📊 인사이트",
        "📚 위키",
        # 외부 진입점 (4) — V2.6.2.2: 🧠 memory 제거 (페르소나 관리 의의 소멸)
        "💬 WebUI",
        "🦅 OpenClaw",
        "🌐 Grafana",
        "📚 Obsidian",
        # 설정 — 맨 뒤
        "⚙️ 설정",
    ])

    # IRIS 자체
    with tabs[0]:  dashboard.render()
    with tabs[1]:  intake.render()              # 기존 — 손대지 않음
    with tabs[2]:  external_capture.render()    # 신규 — 외부 LLM 응답 보존
    with tabs[3]:  inventory.render()
    with tabs[4]:  graph.render()
    with tabs[5]:  placeholders.render_insights()
    with tabs[6]:
        wiki_k2.render()
        st.divider()
        placeholders.render_wiki()
    # 외부
    with tabs[7]:  external.render_openwebui()
    with tabs[8]:  external.render_openclaw()
    with tabs[9]:  external.render_grafana()
    with tabs[10]: external.render_obsidian()
    # 설정 (맨 뒤)
    with tabs[11]: placeholders.render_settings()


if __name__ == "__main__":
    main()
