"""외부 진입점 탭 — IRIS 자체 7탭과 같은 깊이로 평면화 (V2.5.3 §3.10 v1 정정).

알다 v0.10.1 Codexian 사이드패널 패턴 차용. 단 Streamlit은 사이드패널
제약 없어 *최상단 탭으로 평면화*.

각 진입점:
  - L1-chat-webui (OpenWebUI :3000)  — 정식 ①
  - L1-chat-claw (iris-claw :18789)  — 정식 ② (V2.5.1 §11 #10 미연결)
  - L5-observability (Grafana :3030) — V2.5.1 §11.6 관측 한 곳
  - Obsidian (외부 알다 시스템)       — V2.5.2 §3.B 거부 정책, 참고용

V2.6.2.2 (2026-06-16): 🧠 memory 진입점 제거.
  원안은 OpenClaw 페르소나 관리용이었으나 페르소나 운영 자체가 의미 없어져 폐기.
  L3-memory-admin 컨테이너는 iris-stack에 남아있을 수 있으나 hub UI에서 노출 안 함.
"""
from __future__ import annotations

import json
import socket
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

import streamlit as st
import streamlit.components.v1 as components

_OPENCLAW_CONFIG = Path.home() / ".openclaw" / "openclaw.json"


def _openclaw_token() -> str | None:
    """gateway.auth.token 읽기 (~/.openclaw/openclaw.json). 실패 시 None.

    V2.9 OpenClaw 연동 개선 — 토큰은 URL 프래그먼트(#token=)로만 전달한다.
    (OpenClaw 공식 방식: 쿼리 파라미터가 아니라 프래그먼트 — 프래그먼트는
    HTTP 요청에 실려 나가지 않아 서버 로그·Referer에 노출되지 않는다.
    Control UI는 로드 후 sessionStorage로 옮기고 URL에서 즉시 제거한다.)
    """
    try:
        cfg = json.loads(_OPENCLAW_CONFIG.read_text(encoding="utf-8"))
        token = cfg.get("gateway", {}).get("auth", {}).get("token")
        return token or None
    except Exception:
        return None


def _port_alive(host: str, port: int, timeout: float = 0.3) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _iframe_blocked(url: str) -> bool:
    """X-Frame-Options 또는 CSP frame-ancestors로 iframe 차단 여부."""
    try:
        req = Request(url, method="HEAD")
        with urlopen(req, timeout=1.0) as resp:
            headers = {k.lower(): v.lower() for k, v in resp.getheaders()}
        xfo = headers.get("x-frame-options", "")
        if xfo in ("deny", "sameorigin"):
            return True
        csp = headers.get("content-security-policy", "")
        if "frame-ancestors" in csp and ("'none'" in csp or "'self'" in csp):
            return True
        return False
    except Exception:
        # HEAD 실패 시 GET으로 한 번 더
        try:
            with urlopen(url, timeout=1.0) as resp:
                headers = {k.lower(): v.lower() for k, v in resp.getheaders()}
            xfo = headers.get("x-frame-options", "")
            if xfo in ("deny", "sameorigin"):
                return True
            csp = headers.get("content-security-policy", "")
            if "frame-ancestors" in csp and ("'none'" in csp or "'self'" in csp):
                return True
        except Exception:
            pass
        return False


def _iframe_or_help(url: str, *, host: str, port: int, name: str, hint: str = "") -> None:
    alive = _port_alive(host, port)
    if not alive:
        st.error(f"🔴 **{name}** — {host}:{port} 미가동")
        if hint:
            st.code(hint, language="bash")
        return

    blocked = _iframe_blocked(url)
    if blocked:
        st.success(f"🟢 **{name}** — {host}:{port} 가동 중 · iframe 차단됨")
        # 같은 탭 이동 (큰 버튼) + 새 창 (옵션)
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(
                f"""
<a href="{url}" target="_top" style="
    display: block;
    width: 100%;
    padding: 1rem;
    background: #FF4B4B;
    color: white;
    text-align: center;
    text-decoration: none;
    border-radius: 8px;
    font-weight: 600;
    font-size: 1.1rem;
">➡️ {name} 같은 탭에서 열기 (뒤로가기로 hub 복귀)</a>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.link_button("🔗 새 창", url, use_container_width=True)
        st.caption(
            "🔒 본 서비스는 보안 정책상 iframe 차단 "
            "(`X-Frame-Options: DENY` 또는 CSP `frame-ancestors`)."
        )
        return

    st.success(f"🟢 **{name}** — {host}:{port} 가동 중")
    st.link_button("🔗 새 창", url, use_container_width=False)
    components.iframe(url, height=900, scrolling=True)


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
        token = _openclaw_token()
        base = "http://127.0.0.1:18789/chat?session=main"
        # 127.0.0.1 한정 — 로컬 전용 서비스만 토큰을 URL에 싣는다.
        url = f"{base}#token={quote(token)}" if token else base
        _iframe_or_help(
            url=url,
            host="127.0.0.1", port=18789, name="L1-chat-claw (OpenClaw)",
        )
        if token:
            st.caption(
                "🔑 gateway 토큰 자동 포함 링크 — 붙여넣기 불필요 "
                "(URL 프래그먼트 `#token=`로 전달, 서버 로그에 남지 않음). "
                "`session=main` 고정으로 항상 같은 대화로 이어짐."
            )
        else:
            st.caption(
                "⚠️ `~/.openclaw/openclaw.json`에서 gateway 토큰을 읽지 못함 — "
                "Control UI에서 수동 입력 필요."
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


# ─── L3 메모리 운영 (V2.6.2.2 폐기) ────────────────────────────────────
# render_memory_admin 제거 — OpenClaw 페르소나 관리 의의 소멸로 운영 진입점 폐기.
# iris-stack의 memory-admin 컨테이너 자체는 별도 사이클에서 정리.


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
