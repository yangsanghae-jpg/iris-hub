"""외부 진입점 탭 — IRIS 자체 6탭과 같은 깊이로 평면화 (V2.5.3 §3.10 v1 정정).

알다 v0.10.1 Codexian 사이드패널 패턴 차용. 단 Streamlit은 사이드패널
제약 없어 *최상단 탭 11개로 평면화*.

각 진입점:
  - L1-chat-webui (OpenWebUI :3000)  — 정식 ①
  - L1-chat-claw (iris-claw :18789)  — 정식 ② (V2.5.1 §11 #10 미연결)
  - L5-observability (Grafana :3030) — V2.5.1 §11.6 관측 한 곳
  - L3-memory-admin (:18020)         — 메모리 운영
  - Obsidian (외부 알다 시스템)       — V2.5.2 §3.B 거부 정책, 참고용
"""
from __future__ import annotations

import socket

import streamlit as st
import streamlit.components.v1 as components


def _port_alive(host: str, port: int, timeout: float = 0.3) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _iframe_or_help(url: str, *, host: str, port: int, name: str, hint: str = "") -> None:
    alive = _port_alive(host, port)
    if alive:
        st.success(f"🟢 **{name}** — {host}:{port} 가동 중")
        st.link_button("🔗 새 창", url, use_container_width=False)
        components.iframe(url, height=900, scrolling=True)
    else:
        st.error(f"🔴 **{name}** — {host}:{port} 미가동")
        if hint:
            st.code(hint, language="bash")


# ─── L1 chat ────────────────────────────────────────────────────────────


def render_openwebui() -> None:
    _iframe_or_help(
        url="http://127.0.0.1:3000",
        host="127.0.0.1", port=3000, name="L1-chat-webui (OpenWebUI)",
        hint="cd ~/Documents/0Dev/iris-stack && docker compose up -d open-webui",
    )


def render_openclaw() -> None:
    alive = _port_alive("127.0.0.1", 18789)
    if alive:
        _iframe_or_help(
            url="http://127.0.0.1:18789",
            host="127.0.0.1", port=18789, name="L1-chat-claw (OpenClaw)",
        )
    else:
        st.warning("🟡 **L1-chat-claw (OpenClaw)** — 워크스페이스만 존재 (V2.5.1 §11 #10 stack 미연결)")
        st.markdown(
            "iris-claw는 docker-compose 정의는 있으나 *iris-stack wire-up 미완*. "
            "별도 사이클 후 가동 가능."
        )
        st.code(
            "cd ~/Documents/0Dev/iris-claw && docker compose up -d",
            language="bash",
        )
        st.link_button("🔗 새 창 (가동 시)", "http://127.0.0.1:18789")


# ─── L5 관측 ────────────────────────────────────────────────────────────


def render_grafana() -> None:
    _iframe_or_help(
        url="http://127.0.0.1:3030",
        host="127.0.0.1", port=3030, name="L5-observability (Grafana)",
        hint="cd ~/Documents/0Dev/iris-stack && \\\n"
             "docker compose -f docker-compose.observability.yml \\\n"
             "               -f docker-compose.observability.mac.yml up -d",
    )
    st.caption(
        "V2.5.1 §11.6: 관측은 Grafana 한 곳 정책. "
        "iris-v25-k5 패널은 K5 telemetry append 후 자동 점등."
    )


# ─── L3 메모리 운영 ────────────────────────────────────────────────────


def render_memory_admin() -> None:
    _iframe_or_help(
        url="http://127.0.0.1:18020",
        host="127.0.0.1", port=18020, name="L3-memory-admin",
        hint="cd ~/Documents/0Dev/iris-stack && docker compose up -d memory-admin",
    )
    st.caption("iris-memory (L3) 워킹메모리 운영. V2.5.1 §3 L3 단독 가동 + L2 통합은 토글.")


# ─── Obsidian (외부) ───────────────────────────────────────────────────


def render_obsidian() -> None:
    st.info(
        "🔵 **Obsidian (알다 외부 시스템)** — iframe 불가 (데스크톱 앱)"
    )
    st.markdown(
        "- 정본 위치: `~/Documents/LearningMaster` (알다 V1.0 운영)\n"
        "- **V2.5.2 §3.B 거부 결정**: Obsidian은 K6 편집 UI 후보일 뿐, IRIS truth는 SQLite\n"
        "- 본 탭은 *참고용 진입*. 알다 시스템 자체는 알다에서 운영."
    )
    st.link_button(
        "📚 LearningMaster Vault 열기",
        "obsidian://open?vault=LearningMaster",
        use_container_width=False,
        help="Obsidian 데스크톱 앱 설치 + 'LearningMaster' Vault 존재 시",
    )
