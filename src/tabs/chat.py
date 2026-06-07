"""탭 7: 💬 챗 — L1 대화 채널 진입점 모음 (V2.5.3 §3.10 v1 정정 자리).

알다 v0.10.1 비주얼 대응:
  - 알다 Codexian 사이드패널 → OpenWebUI iframe
  - 알다 Obsidian 좌측 Vault → 별도 외부 시스템 (링크만)
  - 알다 Hermes/OpenClaw → iris-claw 진입점 (가동 시 링크)

본 탭의 자리:
  - L1-chat-webui (OpenWebUI :3000) — 정식 ①, iframe 임베드
  - L1-chat-claw (iris-claw :18789) — 정식 ②, 미가동 시 안내
  - Obsidian (외부 알다 시스템) — 참고용 링크
"""
from __future__ import annotations

import socket
from urllib.parse import quote

import streamlit as st
import streamlit.components.v1 as components


def _port_alive(host: str, port: int, timeout: float = 0.3) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def render() -> None:
    st.markdown("## 💬 챗")
    st.caption(
        "L1 대화 채널 — 알다 Codexian 사이드패널 패턴. "
        "iframe 임베드 (정식 ①·②) + 외부 시스템 링크 (참고)."
    )

    # ─── 진입점 선택 ───────────────────────────────────────────────────────
    webui_alive = _port_alive("127.0.0.1", 3000)
    claw_alive = _port_alive("127.0.0.1", 18789)

    options = []
    if webui_alive:
        options.append("L1-chat-webui (OpenWebUI)")
    if claw_alive:
        options.append("L1-chat-claw (OpenClaw)")
    options.append("Obsidian (외부 — 알다 시스템)")
    options.append("미선택 (안내만)")

    default_idx = 0 if (webui_alive or claw_alive) else len(options) - 1
    choice = st.radio(
        "진입점",
        options,
        index=default_idx,
        horizontal=True,
        label_visibility="collapsed",
    )

    st.divider()

    # ─── 상태 카드 3개 ─────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    with c1:
        if webui_alive:
            st.success("🟢 **L1-chat-webui**\n\n:3000 가동 중")
        else:
            st.error("🔴 **L1-chat-webui**\n\n:3000 미가동")
        st.link_button(
            "🔗 새 창",
            "http://127.0.0.1:3000",
            use_container_width=True,
        )

    with c2:
        if claw_alive:
            st.success("🟢 **L1-chat-claw**\n\n:18789 가동 중")
        else:
            st.warning(
                "🟡 **L1-chat-claw**\n\n워크스페이스만 존재\n(stack 미연결)"
            )
        st.link_button(
            "🔗 새 창",
            "http://127.0.0.1:18789",
            use_container_width=True,
        )

    with c3:
        st.info(
            "🔵 **Obsidian (알다)**\n\n"
            "외부 시스템, 참고용"
        )
        st.link_button(
            "📚 LearningMaster",
            "obsidian://open?vault=LearningMaster",
            use_container_width=True,
            help="Obsidian 데스크톱 앱 설치 + Vault 'LearningMaster' 존재 시",
        )

    st.divider()

    # ─── iframe 임베드 ───────────────────────────────────────────────────
    if choice.startswith("L1-chat-webui"):
        if webui_alive:
            components.iframe("http://127.0.0.1:3000", height=800, scrolling=True)
        else:
            st.error(
                "OpenWebUI :3000 미가동. iris-stack docker compose up 이후 새로고침.\n"
                "```bash\n"
                "cd ~/Documents/0Dev/iris-stack && docker compose up -d open-webui\n"
                "```"
            )
    elif choice.startswith("L1-chat-claw"):
        if claw_alive:
            components.iframe("http://127.0.0.1:18789", height=800, scrolling=True)
        else:
            st.warning(
                "iris-claw 미가동. V2.5.1 §11 우선순위 #10 — claw stack wire-up 별도 사이클.\n"
                "```bash\n"
                "cd ~/Documents/0Dev/iris-claw && docker compose up -d\n"
                "```"
            )
    elif choice.startswith("Obsidian"):
        st.info(
            "**Obsidian은 외부 시스템.** iframe 임베드 불가 (데스크톱 앱).\n\n"
            "- 정본 위치: `~/Documents/LearningMaster` (알다 V1.0 운영)\n"
            "- V2.5.2 §3.B에서 거부 결정 — Obsidian은 K6 편집 UI 후보일 뿐, IRIS truth는 SQLite\n"
            "- 본 카드는 *참고용*. 알다 시스템 자체 운영은 알다에서."
        )
    else:
        st.caption("위 진입점 중 하나를 선택하면 iframe 또는 안내가 표시됩니다.")

    st.divider()
    st.caption(
        "활성 시점: v0 사이드패널 1 (OpenWebUI iframe) — "
        "claw 통합은 V2.5.1 §11 #10 별도 사이클, "
        "추후 v2/v3에서 모델 토글 + 그래프 시각화 추가."
    )
