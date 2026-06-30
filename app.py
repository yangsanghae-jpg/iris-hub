"""iris-hub v0 — 사이드바 내비게이션 (V2.8.2).

메뉴 (사이드바 세로 목록):
  IRIS 자체 (10): 🔧 진단툴 | 📥 입력 | 🌐 외부응답 | 🔄 흐름 | 📦 데이터 | ...
  외부 진입점 (4): 💬 WebUI | 🦅 OpenClaw | 🌐 Grafana | 📚 Obsidian
  설정 (1):       ⚙️ 설정

V2.6.2.9 — 📊 진척 (dashboard.render) 숨김.
  V2.6 phase 7건 종결로 추적 임무 완결.
  dashboard.py 모듈과 import는 보존 — 향후 운영 phase 진입 시 복원 가능.

V2.6.2.2 — 🧠 memory 진입점 제거 (페르소나 관리 의의 소멸).

UI 정책:
  - 헤더 간소화 (iris-hub 제목 작게)
  - 사이드바: 전체 메뉴 + 라이브 상태 (좁은 화면에서도 스크롤 없이 접근)
"""
from __future__ import annotations

import socket
from collections.abc import Callable

import streamlit as st

from src.tabs import diagnosis_mgmt, external, external_capture, flow, graph, intake, inventory, placeholders, pptx, presenton as presenton_tab, wiki_k2


def _port_alive(host: str, port: int, timeout: float = 0.3) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _render_wiki() -> None:
    wiki_k2.render()
    st.divider()
    placeholders.render_wiki()


NAV_ITEMS: list[tuple[str, str, Callable[[], None]]] = [
    ("diagnosis", "🔧 진단툴", diagnosis_mgmt.render),
    ("intake", "📥 입력", intake.render),
    ("external_capture", "🌐 외부응답", external_capture.render),
    ("flow", "🔄 흐름", flow.render),
    ("inventory", "📦 데이터", inventory.render),
    ("graph", "🕸️ 그래프", graph.render),
    ("insights", "📊 인사이트", placeholders.render_insights),
    ("wiki", "📚 위키", _render_wiki),
    ("pptx", "📊 PPT", pptx.render),
    ("presenton", "🦅 Presenton", presenton_tab.render),
    ("webui", "💬 WebUI", external.render_openwebui),
    ("openclaw", "🦅 OpenClaw", external.render_openclaw),
    ("grafana", "🌐 Grafana", external.render_grafana),
    ("obsidian", "📚 Obsidian", external.render_obsidian),
    ("settings", "⚙️ 설정", placeholders.render_settings),
]
NAV_LABELS = {key: label for key, label, _ in NAV_ITEMS}
NAV_RENDERERS = {key: render for key, _, render in NAV_ITEMS}


def _inject_css() -> None:
    """헤더 축소 + 사이드바 내비 여백."""
    st.markdown("""
<style>
/* 상단 여백 축소 */
.block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; }

/* iris-hub 제목 축소 */
h1 { font-size: 1.4rem !important; margin: 0 !important; padding: 0 !important; }
h1 + div[data-testid="stCaptionContainer"] { margin-bottom: 0.5rem !important; }

/* 사이드바 메뉴 — 세로 목록, 좁은 화면에서도 전체 항목 접근 */
section[data-testid="stSidebar"] div[data-testid="stRadio"] label {
    padding: 0.35rem 0.5rem !important;
    font-size: 0.92rem !important;
}
section[data-testid="stSidebar"] div[data-testid="stRadio"] > div {
    gap: 0.15rem !important;
}
</style>
    """, unsafe_allow_html=True)


def _sidebar_nav() -> str:
    with st.sidebar:
        st.markdown("### 📋 메뉴")
        page = st.radio(
            "메뉴",
            options=[key for key, _, _ in NAV_ITEMS],
            format_func=lambda key: NAV_LABELS[key],
            label_visibility="collapsed",
            key="iris_hub_nav",
        )

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

    return page


def main() -> None:
    st.set_page_config(
        page_title="iris-hub",
        page_icon="📊",
        layout="wide",
    )
    _inject_css()
    page = _sidebar_nav()

    # 간소 헤더 (1행)
    st.markdown("# 📊 iris-hub")
    st.caption("V2.8.2 · M2 :8765 · K2 v4 (9산업 · 시스템 20 · 관리 14)")

    NAV_RENDERERS[page]()


if __name__ == "__main__":
    main()
