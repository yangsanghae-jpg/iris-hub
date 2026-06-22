"""탭 4·5·6 placeholder — v1 활성 전까지 살아있는 백엔드 링크/상태 (V2.5.3 §3.1 + 본 사이클 연결)"""
from __future__ import annotations

import os
import socket
import sqlite3
from pathlib import Path

import streamlit as st

from src.config import IRIS_DB_PATH, IRIS_WIKI_PATH, IRIS_SYSTEM_LEGACY


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


# ─── 탭 4: 인사이트 ──────────────────────────────────────────────────────


def render_insights() -> None:
    st.markdown("## 📊 인사이트")
    st.caption("관측은 Grafana 한 곳 정책 (V2.5.1 §11.6). 본 탭 v1 활성 시 iframe 임베드.")

    st.markdown("### 🔌 관측 백엔드 상태")
    rows = [
        _status_pill("Grafana", "127.0.0.1", 3030),
        _status_pill("Prometheus", "127.0.0.1", 9090),
        _status_pill("Loki", "127.0.0.1", 3100),
        _status_pill("Promtail", "127.0.0.1", 9080),
    ]
    cols = st.columns(len(rows))
    for col, (text, _) in zip(cols, rows):
        col.write(text)

    st.markdown("### 🔗 바로가기")
    _link_button_row([
        ("📊 Grafana 열기", "http://127.0.0.1:3030", "iris-v25-k5 패널 + 관측 일반"),
        ("📈 Prometheus", "http://127.0.0.1:9090", "메트릭 탐색"),
        ("📜 Loki", "http://127.0.0.1:3100", "로그 (Grafana 경유 권장)"),
    ])

    st.divider()
    st.markdown("### 📊 K5 telemetry 상태")
    telemetry_root = Path(os.environ.get(
        "IRIS_TELEMETRY_ROOT",
        str(IRIS_SYSTEM_LEGACY / "storage" / "telemetry"),
    ))
    logs = sorted(telemetry_root.glob("iris_k5_telemetry.*.log")) if telemetry_root.exists() else []
    c1, c2 = st.columns(2)
    c1.metric("telemetry 로그 파일", len(logs))
    if logs:
        latest = logs[-1]
        size = latest.stat().st_size
        line_count = sum(1 for _ in latest.open(encoding="utf-8"))
        c2.metric(f"최신 ({latest.name})", f"{line_count:,} 줄 / {size:,} B")
    else:
        c2.warning("telemetry 미발생 — /api/v1/retrieval 호출 시 자동 append")

    st.caption(
        "활성 트리거: L6-D1 호출 전환 (V2.5.1 §7 Phase 5.7) 또는 사용자가 K5 표준 API 운영 시작"
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
