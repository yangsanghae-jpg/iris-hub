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
from pathlib import Path

import streamlit as st

from src.tabs import diagnosis_mgmt, external, flow, graph, intake, inventory, pptx, wiki


def _port_alive(host: str, port: int, timeout: float = 0.3) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


NAV_ITEMS: list[tuple[str, str, Callable[[], None]]] = [
    ("diagnosis", "🔧 진단툴", diagnosis_mgmt.render),
    ("intake", "📥 입력", intake.render),
    ("flow", "🔄 흐름", flow.render),
    ("inventory", "📦 데이터", inventory.render),
    ("graph", "🕸️ 그래프", graph.render),
    ("wiki", "📚 위키", wiki.render),
    ("pptx", "📊 PPT", pptx.render),
    ("webui", "💬 WebUI", external.render_openwebui),
    ("openclaw", "🦅 OpenClaw", external.render_openclaw),
]
NAV_GROUPS: list[tuple[str, list[str]]] = [
    ("Core", ["diagnosis", "intake", "flow"]),
    ("Knowledge", ["inventory", "graph", "wiki"]),
    ("Create", ["pptx"]),
    ("External", ["webui", "openclaw"]),
]
NAV_LABELS = {key: label for key, label, _ in NAV_ITEMS}
NAV_RENDERERS = {key: render for key, _, render in NAV_ITEMS}


def _inject_css() -> None:
    """Load app-wide shared UI CSS once at startup."""
    css_path = Path(__file__).parent / "data" / "themes" / "hub_ui.css"
    css = css_path.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def _sidebar_nav() -> str:
    if "iris_hub_nav" not in st.session_state:
        st.session_state.iris_hub_nav = "diagnosis"

    with st.sidebar:
        st.markdown(
            """
<div class="hub-sidebar-brand">
  <div class="hub-sidebar-title">IRIS HUB</div>
  <div class="hub-sidebar-subtitle">Knowledge Ops</div>
</div>
""",
            unsafe_allow_html=True,
        )

        for group_name, page_keys in NAV_GROUPS:
            st.markdown(
                f'<div class="hub-sidebar-group">{group_name}</div>',
                unsafe_allow_html=True,
            )
            for page_key in page_keys:
                is_active = st.session_state.iris_hub_nav == page_key
                if is_active:
                    st.markdown('<div class="hub-nav-active">', unsafe_allow_html=True)
                if st.button(
                    NAV_LABELS[page_key],
                    key=f"nav_{page_key}",
                    type="primary" if is_active else "secondary",
                    use_container_width=True,
                ):
                    st.session_state.iris_hub_nav = page_key
                    st.rerun()
                if is_active:
                    st.markdown("</div>", unsafe_allow_html=True)

        status_rows = []
        online_count = 0
        for label, port in [
            ("Grafana", 3030),
            ("WebUI", 3000),
            ("OpenClaw", 18789),
            ("Gateway", 8011),
        ]:
            alive = _port_alive("127.0.0.1", port)
            if alive:
                online_count += 1
            status = "Online" if alive else "Offline"
            status_rows.append(
                f'<div class="hub-status-row"><span>{label}</span><strong class="hub-status-ok">{status}</strong></div>'
            )

        st.markdown(
            f"""
<div class="hub-sidebar-status">
  <div class="hub-status-head">
    <span class="hub-status-title">Status</span>
    <span class="hub-status-ok">{online_count}/4</span>
  </div>
  {''.join(status_rows)}
</div>
""",
            unsafe_allow_html=True,
        )

    return st.session_state.iris_hub_nav


def main() -> None:
    st.set_page_config(
        page_title="iris-hub",
        page_icon="📊",
        layout="wide",
    )
    _inject_css()
    page = _sidebar_nav()

    NAV_RENDERERS[page]()


if __name__ == "__main__":
    main()
