"""탭: 🦅 Presenton — V2.8.0.

Presenton (https://github.com/presenton/presenton, 8.4k★) Docker로 띄우고
HTTP API 호출해서 PPT 생성.

V2.7.5 Marp / V2.7.6 deck보다 *훨씬 정교한* 디자인 (이미지·차트·아이콘 자동 박힘).
대신 Docker 의존 + 외부 LLM 호출 + 인터넷 (이미지 API 사용 시).
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

import streamlit as st


_SAMPLE_PROMPT = """## NanoLN 종합 지표 관리 체계 — 진단 및 혁신

### 사업 특성
- 단결정 LN/LT 박막 소재 전문
- 고부가가치 · 고난도 공정 · 미세 품질 · 고객 인증 대응

### 현행 진단 (As-Is)
- 리포트 42개, 8개 부서 분산 → 체계 약함
- BSC 4관점 불균형 (내부 프로세스 90% 편중)
- 단결정·박막·CMP 공정 특화 지표 부족
- 후행 결과 위주, 선행 예방 부족

### 혁신 방향 (To-Be)
- KPI Tree로 묶인 종합 체계
- BSC 4관점 균형 (재무·고객·학습성장 보강)
- 공정 특화 지표 (회수율·Void·Ra·Qual)
- 3계층 KPI (전략/운영/관리)
- BI 자동화·SSoT

### 단계별 추진 (12개월)
1. Phase 1 (0~3M): 현행 정리·표준화
2. Phase 2 (3~6M): KPI Tree 설계
3. Phase 3 (6~9M): 공정 특화 보완
4. Phase 4 (9~12M): BI 자동화 구축
"""


_THEMES = ["royal_blue", "cream", "light_red", "faint_yellow", "dark"]


def render() -> None:
    # 입력 헬퍼 공유
    from src.tabs.pptx import _list_archive_content_md, _list_docs_md

    st.markdown("### 🦅 Presenton — V2.8.0")
    st.caption(
        "[Presenton](https://github.com/presenton/presenton) (8.4k★) — Docker로 띄운 외부 PPT 생성기. "
        "이미지·차트·아이콘 자동 박힘. Marp/deck 탭보다 *훨씬 정교*. "
        "별도 컨테이너 필요 (아래 안내)."
    )

    # 가동 상태
    from src import presenton
    alive = presenton.is_alive(timeout=1.5)
    col_status, col_url = st.columns([1, 4])
    with col_status:
        if alive:
            st.success(f"🟢 Presenton 가동")
        else:
            st.error(f"🔴 Presenton 미가동")
    with col_url:
        st.caption(f"URL: `{presenton.PRESENTON_URL}` (env `PRESENTON_URL`로 변경)")

    if not alive:
        with st.expander("📦 Docker로 Presenton 띄우기 (안내)", expanded=True):
            st.markdown(f"""
**M2 (qwen3:8b)** — 한 줄로 띄움:
```bash
docker run -d --name presenton -p 5000:80 \\
  -e LLM=ollama \\
  -e OLLAMA_MODEL=qwen3:8b \\
  -e OLLAMA_URL=http://host.docker.internal:11434 \\
  -e CAN_CHANGE_KEYS=false \\
  -v presenton-data:/app_data \\
  ghcr.io/presenton/presenton:latest
```

**M5 (qwen3:30b 또는 qwen3-next:80b)**:
```bash
docker run -d --name presenton -p 5000:80 \\
  -e LLM=ollama \\
  -e OLLAMA_MODEL=qwen3:30b \\
  -e OLLAMA_URL=http://host.docker.internal:11434 \\
  -v presenton-data:/app_data \\
  ghcr.io/presenton/presenton:latest
```

**이미지 제공자 (옵션, Pexels 무료)**:
- `-e IMAGE_PROVIDER=pexels -e PEXELS_API_KEY=...` 박음

띄운 후 위 상태가 🟢로 바뀌면 사용 가능.
""")
        return

    st.divider()

    # ─── 입력 방식 선택 (4 모드) ────────────────────────────────
    source_mode = st.radio(
        "마크다운/프롬프트 소스",
        options=[
            "✍️ 직접 입력 (textarea)",
            "📂 파일 업로드 (.md)",
            "📦 archive 자료 (content.md)",
            "📄 docs/system 보고서",
        ],
        horizontal=True,
        key="presenton_source_mode",
    )

    prompt = ""
    source_label = ""

    if source_mode.startswith("✍️"):
        prompt = st.text_area(
            "프롬프트 (마크다운 또는 자연어)",
            value=st.session_state.get("presenton_prompt", _SAMPLE_PROMPT),
            key="presenton_prompt_input",
            height=380,
            help="Presenton LLM이 내용을 보고 슬라이드 구조·디자인 결정. "
                 "구조화된 마크다운일수록 결과 안정.",
        )
        st.session_state["presenton_prompt"] = prompt
        source_label = "직접 입력"

    elif source_mode.startswith("📂"):
        uploaded = st.file_uploader(
            ".md 파일 선택", type=["md", "markdown", "txt"],
            key="presenton_upload",
        )
        if uploaded:
            try:
                prompt = uploaded.read().decode("utf-8")
                source_label = f"파일: {uploaded.name}"
                st.success(f"✅ 로딩 — {uploaded.name} ({len(prompt):,} chars)")
                with st.expander("📋 본문 미리보기", expanded=False):
                    st.code(prompt[:500] + ("..." if len(prompt) > 500 else ""),
                            language="markdown")
            except Exception as e:
                st.error(f"❌ 파일 읽기 실패: {e}")

    elif source_mode.startswith("📦"):
        archive_items = _list_archive_content_md()
        if not archive_items:
            st.info("📦 3-archive에 인덱싱된 자료 없음.")
        else:
            labels = ["(선택)"] + [lbl for lbl, _ in archive_items]
            picked = st.selectbox(
                f"archive 자료 ({len(archive_items)}건)",
                options=labels, key="presenton_archive_pick",
            )
            if picked and picked != "(선택)":
                idx = labels.index(picked) - 1
                path = archive_items[idx][1]
                try:
                    prompt = path.read_text(encoding="utf-8")
                    source_label = f"archive: {path.parent.name}"
                    st.success(f"✅ 로딩 — {path.parent.name} ({len(prompt):,} chars)")
                    with st.expander("📋 본문 미리보기", expanded=False):
                        st.code(prompt[:500] + ("..." if len(prompt) > 500 else ""),
                                language="markdown")
                except Exception as e:
                    st.error(f"❌ 읽기 실패: {e}")

    elif source_mode.startswith("📄"):
        docs_items = _list_docs_md()
        if not docs_items:
            st.info("📄 /0Dev/docs/system/ 에 .md 없음.")
        else:
            labels = ["(선택)"] + [lbl for lbl, _ in docs_items]
            picked = st.selectbox(
                f"docs/system 보고서 ({len(docs_items)}건)",
                options=labels, key="presenton_docs_pick",
            )
            if picked and picked != "(선택)":
                idx = labels.index(picked) - 1
                path = docs_items[idx][1]
                try:
                    prompt = path.read_text(encoding="utf-8")
                    source_label = f"docs: {path.name}"
                    st.success(f"✅ 로딩 — {path.name} ({len(prompt):,} chars)")
                    with st.expander("📋 본문 미리보기", expanded=False):
                        st.code(prompt[:500] + ("..." if len(prompt) > 500 else ""),
                                language="markdown")
                except Exception as e:
                    st.error(f"❌ 읽기 실패: {e}")

    st.divider()

    # 옵션
    col_l, col_r = st.columns([3, 2])
    with col_l:
        if source_label:
            st.caption(f"📥 소스: **{source_label}** · 본문 **{len(prompt):,}** chars")
        else:
            st.caption("📥 소스 미선택")

    with col_r:
        st.markdown("**🎨 옵션**")
        n_slides = st.slider("슬라이드 수", min_value=3, max_value=20, value=8,
                              key="presenton_nslides")
        language = st.selectbox(
            "언어", options=["Korean", "English", "Chinese", "Japanese"],
            index=0, key="presenton_lang",
        )
        theme = st.selectbox(
            "테마 (Presenton 내장)", options=_THEMES,
            index=0, key="presenton_theme",
        )
        export_as = st.radio(
            "형식", options=["pptx", "pdf"], horizontal=True, key="presenton_format",
        )
        save_to_disk = st.checkbox(
            "exports/ 에 영구 저장",
            value=True,
            key="presenton_save_disk",
            help="iris-knowledge/2-processed/exports/ 에 저장",
        )

        st.divider()

        gen_btn = st.button(
            "🦅 Presenton으로 생성",
            type="primary",
            use_container_width=True,
            disabled=not prompt.strip(),
            key="presenton_gen",
        )

    if gen_btn:
        try:
            with st.spinner(
                f"🦅 Presenton 생성 중… ({n_slides}장, 모델·이미지 따라 1~5분)"
            ):
                r = presenton.generate(
                    prompt=prompt,
                    n_slides=n_slides,
                    language=language,
                    theme=theme,
                    export_as=export_as,
                )

            st.success(
                f"✅ 생성 완료 — {r.size_bytes / 1024:.1f}KB · {r.elapsed_ms / 1000:.1f}초"
            )

            # 영구 저장
            if save_to_disk:
                from src.config import IRIS_KNOWLEDGE_PROCESSED
                exports_dir = IRIS_KNOWLEDGE_PROCESSED / "exports"
                exports_dir.mkdir(parents=True, exist_ok=True)
                stamp = _dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
                target = exports_dir / f"presenton_{stamp}.{export_as}"
                import shutil
                shutil.copy2(r.out_path, target)
                st.caption(f"📦 저장: `{target}`")

            with r.out_path.open("rb") as f:
                data = f.read()
            stamp = _dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
            st.download_button(
                f"💾 다운로드 (presenton_{stamp}.{export_as})",
                data=data,
                file_name=f"presenton_{stamp}.{export_as}",
                mime=(
                    "application/pdf" if export_as == "pdf"
                    else "application/vnd.openxmlformats-officedocument.presentationml.presentation"
                ),
                use_container_width=True,
            )

            if r.edit_path:
                st.markdown(
                    f"🌐 [Presenton UI에서 편집·재생성·이미지 교체]({r.edit_path})"
                )

        except presenton.PresentonError as e:
            st.error(f"❌ 실패: {e}")
