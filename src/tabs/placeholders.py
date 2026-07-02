"""탭 4·5·6 placeholder — v1 활성 전까지 살아있는 백엔드 링크/상태 (V2.5.3 §3.1 + 본 사이클 연결)"""
from __future__ import annotations

import os
import socket
import sqlite3
from html import escape
from pathlib import Path

import streamlit as st

from src.config import IRIS_DB_PATH, IRIS_WIKI_PATH, IRIS_SYSTEM_LEGACY
from src.ui_kit import hub_equal_col, hub_kpi_grid, hub_pagebar, hub_panel, hub_two_col


# ─── 공통 헬퍼 ────────────────────────────────────────────────────────────


def _port_alive(host: str, port: int, timeout: float = 0.3) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _status_pill(label: str, host: str, port: int) -> tuple[str, bool]:
    alive = _port_alive(host, port)
    icon = "🟢" if alive else "🔴"
    return f"{icon} {label} :{port}", alive


def _link_button_row(items: list[tuple[str, str, str]]) -> None:
    """items = [(emoji_label, url, help_text)]"""
    cols = st.columns(len(items))
    for col, (label, url, helptxt) in zip(cols, items):
        with col:
            st.link_button(label, url, help=helptxt, use_container_width=True)


def _format_file_size(size_in_bytes: int) -> str:
    if size_in_bytes >= 1024 * 1024:
        return f"{size_in_bytes / (1024 * 1024):.1f} MB"
    if size_in_bytes >= 1024:
        return f"{size_in_bytes / 1024:.0f} KB"
    return f"{size_in_bytes:,} B"


def _count_lines(path: Path) -> int:
    with path.open(encoding="utf-8") as telemetry_file:
        return sum(1 for _ in telemetry_file)


def _service_status_rows() -> list[dict[str, str | int | bool]]:
    services = [
        {"name": "Grafana", "host": "127.0.0.1", "port": 3030, "role": "dashboard hub"},
        {"name": "Prometheus", "host": "127.0.0.1", "port": 9090, "role": "metrics source"},
        {"name": "Loki", "host": "127.0.0.1", "port": 3100, "role": "log backend"},
        {"name": "Promtail", "host": "127.0.0.1", "port": 9080, "role": "log shipper"},
    ]
    for service in services:
        service["alive"] = _port_alive(str(service["host"]), int(service["port"]))
    return services


def _render_service_status_grid(services: list[dict[str, str | int | bool]]) -> str:
    cards = []
    for service in services:
        is_alive = bool(service["alive"])
        status_class = "is-online" if is_alive else "is-offline"
        status_text = "Online" if is_alive else "Offline"
        cards.append(
            f"""
<div class="hub-observe-status-card">
  <div>
    <div class="hub-observe-name">{escape(str(service["name"]))}</div>
    <div class="hub-observe-meta">:{int(service["port"])} · {escape(str(service["role"]))}</div>
  </div>
  <span class="hub-observe-pill {status_class}">{status_text}</span>
</div>
"""
        )
    return f"<div class='hub-observe-status-grid'>{''.join(cards)}</div>"


def _render_observe_shortcuts() -> str:
    shortcuts = [
        ("Grafana 열기", "http://127.0.0.1:3030", "iris-v25-k5 패널과 관측 일반"),
        ("Prometheus 탐색", "http://127.0.0.1:9090", "메트릭 쿼리와 target 상태 확인"),
        ("Loki 로그", "http://127.0.0.1:3100", "Grafana 경유 권장, 로그 raw 탐색"),
    ]
    return "".join(
        f"""
<a class="hub-observe-link-card" href="{escape(url)}" target="_blank" rel="noopener noreferrer">
  <span class="hub-observe-link-title">{escape(title)}</span>
  <span class="hub-observe-link-detail">{escape(detail)}</span>
</a>
"""
        for title, url, detail in shortcuts
    )


def _render_telemetry_log_rows(logs: list[Path]) -> str:
    if not logs:
        return """
<div class="hub-observe-empty-note">
  telemetry 로그가 아직 없습니다. 표준 K5 API 운영 시작 또는 L6-D1 호출 전환 후 자동 append됩니다.
</div>
"""

    rows = []
    for log_path in list(reversed(logs[-5:])):
        line_count = _count_lines(log_path)
        file_size = _format_file_size(log_path.stat().st_size)
        rows.append(
            f"""
<div class="hub-telemetry-row">
  <div class="hub-telemetry-file">
    <strong>{escape(log_path.name)}</strong>
    <span>latest telemetry append stream</span>
  </div>
  <div class="hub-telemetry-measure">
    <span>{line_count:,} lines</span>
    <span class="hub-observe-pill is-neutral">{escape(file_size)}</span>
  </div>
</div>
"""
        )
    return f"<div class='hub-telemetry-list'>{''.join(rows)}</div>"


def _render_observe_note(text: str) -> str:
    return f"<div class='hub-observe-note'>{escape(text)}</div>"


# ─── 탭 4: 인사이트 ──────────────────────────────────────────────────────


def render_insights() -> None:
    services = _service_status_rows()
    telemetry_root = Path(os.environ.get(
        "IRIS_TELEMETRY_ROOT",
        str(IRIS_SYSTEM_LEGACY / "storage" / "telemetry"),
    ))
    logs = sorted(telemetry_root.glob("iris_k5_telemetry.*.log")) if telemetry_root.exists() else []
    latest_log_line_count = _count_lines(logs[-1]) if logs else 0
    latest_log_caption = logs[-1].name if logs else "waiting for first append"

    service_status_by_name = {str(service["name"]): bool(service["alive"]) for service in services}
    hub_pagebar(
        "인사이트",
        "Insights Console",
        "Grafana 중심의 관측 백엔드 상태와 K5 telemetry 활성 흐름을 한 화면에서 확인합니다.",
        "Observe Ready",
    )
    hub_kpi_grid([
        ("Grafana", "Online" if service_status_by_name.get("Grafana") else "Offline", ":3030 · dashboard hub"),
        ("Prometheus", "Online" if service_status_by_name.get("Prometheus") else "Offline", ":9090 · metrics source"),
        ("Loki", "Online" if service_status_by_name.get("Loki") else "Offline", ":3100 · log backend"),
        ("Telemetry", f"{len(logs):,}", "log files"),
    ])

    observe_status_panel = hub_panel(
        "관측 백엔드 상태",
        _render_service_status_grid(services)
        + _render_observe_note("정책: 관측은 Grafana 한 곳에서 보는 구조를 유지합니다. 본 탭은 상태와 진입점 역할입니다."),
        subtitle="외부 관측 도구는 상태만 빠르게 확인하고, 상세 분석은 Grafana에서 수행합니다.",
    )
    observe_shortcut_panel = hub_panel(
        "바로가기",
        f"<div class='hub-observe-link-grid'>{_render_observe_shortcuts()}</div>",
        subtitle="자주 쓰는 관측 콘솔을 큰 액션 카드로 노출합니다.",
    )
    hub_two_col(observe_status_panel, observe_shortcut_panel)

    telemetry_status_panel = hub_panel(
        "K5 telemetry 상태",
        f"""
<div class="hub-observe-mini-kpi-grid">
  <div class="hub-observe-mini-kpi">
    <span>로그 파일</span>
    <strong>{len(logs):,}</strong>
    <small>telemetry root</small>
  </div>
  <div class="hub-observe-mini-kpi">
    <span>최신 로그</span>
    <strong>{latest_log_line_count:,}</strong>
    <small>{escape(latest_log_caption)}</small>
  </div>
</div>
{_render_observe_note("활성 트리거: 표준 K5 API 운영 시작 또는 L6-D1 호출 전환.")}
""",
        subtitle="retrieval 호출 흐름에서 append되는 telemetry 로그의 현황입니다.",
    )
    telemetry_log_panel = hub_panel(
        "최근 telemetry 로그",
        _render_telemetry_log_rows(logs),
        subtitle="최신 로그를 파일 단위로 보여주고, 이후 2차에서 상세 tail/검색을 붙입니다.",
    )
    hub_equal_col(telemetry_status_panel, telemetry_log_panel)

    st.markdown(
        _render_observe_note(
            "1차 적용 범위: placeholder 느낌을 제거하고 pagebar, KPI, 관측 상태, 바로가기, telemetry 로그 요약을 compact console로 운영화합니다. iframe 임베드나 상세 로그 tail/검색은 2차에서 처리합니다."
        ),
        unsafe_allow_html=True,
    )


# ─── 탭 5: 위키 ──────────────────────────────────────────────────────────


def render_wiki() -> None:
    st.markdown("## 📚 위키")
    st.caption("K6 Curate 가동 후 lint·broken·orphan·duplicate·승격 흐름 본격 표시.")

    st.markdown("### 🔌 K5 wiki server 상태")
    wiki_alive = _port_alive("127.0.0.1", 8081)
    if wiki_alive:
        st.success("🟢 wiki server :8081 가동 중")
        st.markdown("**바로가기**")
        _link_button_row([
            ("📚 /wiki/lint", "http://127.0.0.1:8081/wiki/lint", "broken/orphan/duplicate"),
            ("📖 /wiki/history", "http://127.0.0.1:8081/wiki/history", "ingest 이력"),
            ("📘 OpenAPI docs", "http://127.0.0.1:8081/docs", "FastAPI Swagger"),
        ])
    else:
        st.warning("🔴 wiki server :8081 미가동")
        with st.expander("가동 방법"):
            st.code(
                "cd ~/iris-system && \\\n"
                "WIKI_MODEL=qwen3.5:4b \\\n"
                "  ~/iris-local/venv/iris-system/bin/uvicorn apps.wiki.server:app \\\n"
                "  --host 127.0.0.1 --port 8081",
                language="bash",
            )

    st.divider()
    st.markdown("### 📦 wiki/ 디렉터리 측정")

    wiki_dir = IRIS_WIKI_PATH
    if not wiki_dir.exists():
        st.error(f"wiki/ 디렉터리 부재: {wiki_dir}")
        return

    md_files = list(wiki_dir.rglob("*.md"))
    c1, c2, c3 = st.columns(3)
    c1.metric("wiki/ .md 총수", len(md_files))
    c2.metric("areas/concepts/industries", len(list(wiki_dir.glob("*/*.md"))))
    c3.metric("디렉터리", len([p for p in wiki_dir.iterdir() if p.is_dir()]))

    with st.expander("📁 디렉터리별 .md 개수"):
        for sub in sorted([p for p in wiki_dir.iterdir() if p.is_dir()]):
            n = len(list(sub.rglob("*.md")))
            st.write(f"- `{sub.name}/` — **{n}** files")

    st.caption(
        "활성 트리거: K6 Curate가 raw → wiki/*.md 자동 생성 시작 (qwen3.5:4b 또는 그 이상)"
    )


# ─── 탭 6: 설정 ──────────────────────────────────────────────────────────


def render_settings() -> None:
    st.markdown("## ⚙️ 설정")
    st.caption("v1에서 GUI 토글. 현재는 운영 환경변수 + 현 상태 *조회*.")

    from src.config import IRIS_HUB_WORK_DIR, IRIS_LLM_DEEP, IRIS_LLM_EMBED, IRIS_LLM_FAST
    from src.ollama_models import chat_capable_models, list_installed_models, pick_default_chat_model

    st.markdown("### 🤖 LLM 모델 (Ollama 설치 목록)")
    chats = chat_capable_models()
    all_m = list_installed_models()
    embeds = [m for m in all_m if m not in chats]

    if chats:
        deep_default = pick_default_chat_model(chats) or chats[0]
        if "iris_llm_deep" not in st.session_state:
            st.session_state["iris_llm_deep"] = deep_default
        d_idx = chats.index(st.session_state["iris_llm_deep"]) if st.session_state["iris_llm_deep"] in chats else 0
        st.selectbox(
            "deep (K2·PPT 재구조화·deck)",
            options=chats,
            index=d_idx,
            key="iris_llm_deep",
        )
    else:
        st.warning("Ollama chat 모델 없음")

    if chats:
        fast_default = IRIS_LLM_FAST if IRIS_LLM_FAST in chats else chats[0]
        if "iris_llm_fast" not in st.session_state:
            st.session_state["iris_llm_fast"] = fast_default
        f_idx = chats.index(st.session_state["iris_llm_fast"]) if st.session_state["iris_llm_fast"] in chats else 0
        st.selectbox("fast (UI 즉응)", options=chats, index=f_idx, key="iris_llm_fast")

    if embeds:
        e_default = IRIS_LLM_EMBED if IRIS_LLM_EMBED in embeds else embeds[0]
        if "iris_llm_embed" not in st.session_state:
            st.session_state["iris_llm_embed"] = e_default
        e_idx = embeds.index(st.session_state["iris_llm_embed"]) if st.session_state["iris_llm_embed"] in embeds else 0
        st.selectbox("embed", options=embeds, index=e_idx, key="iris_llm_embed")

    st.caption(f"작업 산출물 폴더: `{IRIS_HUB_WORK_DIR}`")

    st.divider()
    st.markdown("### 🌐 환경 변수 (운영 토글)")
    env_table = [
        ("IRIS_SECURE_GATE", "on", "secure lane 차단 게이트 (V2.6 Phase 2)"),
        ("IRIS_SEMANTIC", "on", "FAISS 시맨틱 활성 (V2.6 Phase 5.4)"),
        ("IRIS_EVAL_LANE", "bronze", "eval 기본 lane 필터 (V2.5.3 §17)"),
        ("IRIS_EMBED_MAX_CHARS", "2500", "embed truncation (V2.5.3 §17)"),
        ("IRIS_SEMANTIC_FILTERED_K", "50", "필터 시 over-fetch 배율 (V2.5.3 §19)"),
        ("IRIS_SEMANTIC_K", "4", "필터 없을 때 over-fetch (V2.5.3 §19)"),
        ("WIKI_MODEL", "qwen3.5:4b", "K6 Curate LLM 모델"),
        ("IRIS_TELEMETRY_ROOT", "iris-system/storage/telemetry", "telemetry JSONL 경로"),
    ]
    st.dataframe(
        {"env": [r[0] for r in env_table],
         "default": [r[1] for r in env_table],
         "용도": [r[2] for r in env_table]},
        use_container_width=True,
        hide_index=True,
    )

    st.divider()
    st.markdown("### 🗄 DB 메타 상태")
    if IRIS_DB_PATH.exists():
        conn = sqlite3.connect(IRIS_DB_PATH)
        try:
            rows = conn.execute(
                "SELECT key, value FROM meta_kv WHERE key NOT LIKE 'phase_%' ORDER BY key"
            ).fetchall()
            if rows:
                st.dataframe(
                    {"key": [r[0] for r in rows], "value": [r[1] for r in rows]},
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("meta_kv 비어 있음")
        finally:
            conn.close()
    else:
        st.error(f"_index.db 부재: {IRIS_DB_PATH}")

    st.divider()
    st.markdown("### 🔗 운영 콘솔 바로가기")
    _link_button_row([
        ("💬 OpenWebUI", "http://127.0.0.1:3000", "L1-chat-webui"),
        ("🤖 L2 모델", "http://127.0.0.1:8011/v1/models", "iris-l2-gateway"),
    ])

    st.caption(
        "활성 트리거: secure 운영 진입 + lane 다양화 (V2.6 후반)"
    )
