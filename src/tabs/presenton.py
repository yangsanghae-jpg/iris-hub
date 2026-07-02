"""탭: 🦅 Presenton — V2.8.0."""
from __future__ import annotations

import datetime as _dt

import streamlit as st

from src.config import hub_work_subdir
from src.ollama_models import chat_capable_models, list_installed_models, pick_default_chat_model
from src.runtime_llm import effective_presenton_ollama_model


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

_TEMPLATES = ["general", "royal_blue", "cream", "light_red", "faint_yellow", "dark"]


def _init_ollama_model_state() -> None:
    models = chat_capable_models()
    if "presenton_ollama_model" not in st.session_state:
        default = pick_default_chat_model(models) or (models[0] if models else "")
        st.session_state["presenton_ollama_model"] = default
    if "iris_llm_deep" not in st.session_state:
        st.session_state["iris_llm_deep"] = pick_default_chat_model(models) or ""


def render() -> None:
    # 입력 헬퍼 공유
    from src.tabs.pptx import _list_archive_content_md, _list_docs_md

    st.markdown("### 🦅 Presenton — V2.8.0")
    st.caption(
        "[Presenton](https://github.com/presenton/presenton) — Docker PPT 생성기. "
        f"산출물: `{hub_work_subdir('presenton')}` (Desktop 미사용)"
    )

    _init_ollama_model_state()
    from src.engine.output import presenton

    models = chat_capable_models()
    if not models:
        st.warning("Ollama 모델 없음 — `ollama list` 확인")
        models = list_installed_models()

    alive = presenton.is_alive(timeout=1.5)
    col_status, col_url = st.columns([1, 4])
    with col_status:
        st.success("🟢 Presenton 가동") if alive else st.error("🔴 Presenton 미가동")
    with col_url:
        st.caption(f"URL: `{presenton.PRESENTON_URL}` · 작업 폴더: `{presenton.PRESENTON_WORK_DIR}`")

    # Ollama 모델 선택 (컨테이너 OLLAMA_MODEL — 상황별 변경)
    st.markdown("**🤖 Ollama 모델 (Presenton 컨테이너용)**")
    if models:
        idx = 0
        cur = st.session_state.get("presenton_ollama_model", "")
        if cur in models:
            idx = models.index(cur)
        chosen = st.selectbox(
            "설치된 모델 중 선택",
            options=models,
            index=idx,
            key="presenton_ollama_model_select",
            help="Docker `OLLAMA_MODEL`에 박힘. 변경 후 컨테이너 재기동 필요.",
        )
        st.session_state["presenton_ollama_model"] = chosen
        st.session_state["iris_llm_deep"] = chosen
    else:
        chosen = effective_presenton_ollama_model()
        st.caption(f"현재 deep 슬롯: `{chosen}`")

    port = 5001 if ":5001" in presenton.PRESENTON_URL else 5000
    with st.expander("📦 Docker 명령 (선택 모델 반영)", expanded=not alive):
        st.code(presenton.docker_run_hint(ollama_model=chosen, port=port), language="bash")
        st.caption(
            "macOS는 AirPlay가 :5000 점유 → M5는 **:5001** 권장. "
            "`PRESENTON_URL=http://localhost:5001`"
        )

    if not alive:
        return

    st.divider()

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
        n_slides = st.slider("슬라이드 수", min_value=3, max_value=20, value=8, key="presenton_nslides")
        language = st.selectbox(
            "언어", options=["Korean", "English", "Chinese", "Japanese"],
            index=0, key="presenton_lang",
        )
        theme = st.selectbox(
            "템플릿", options=_TEMPLATES, index=0, key="presenton_theme",
        )
        export_as = st.radio(
            "형식", options=["pptx", "pdf"], horizontal=True, key="presenton_format",
        )
        save_to_disk = st.checkbox(
            "exports/ 에 추가 저장",
            value=False,
            key="presenton_save_disk",
            help="기본 저장은 작업 폴더. 체크 시 iris-knowledge/exports/에도 복사",
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
            with st.spinner(f"🦅 Presenton 생성 중… ({chosen}, {n_slides}장, 1~5분)"):
                r = presenton.generate(
                    prompt=prompt,
                    n_slides=n_slides,
                    language=language,
                    theme=theme,
                    export_as=export_as,
                )

            st.success(
                f"✅ 완료 — {r.size_bytes / 1024:.1f}KB · {r.elapsed_ms / 1000:.1f}초"
            )
            st.caption(f"📁 저장: `{r.out_path}`")

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
            st.download_button(
                f"💾 다운로드 ({r.out_path.name})",
                data=data,
                file_name=r.out_path.name,
                mime=(
                    "application/pdf" if export_as == "pdf"
                    else "application/vnd.openxmlformats-officedocument.presentationml.presentation"
                ),
                use_container_width=True,
            )

            if r.edit_path:
                st.markdown(f"🌐 [Presenton UI에서 편집]({r.edit_path})")

        except presenton.PresentonError as e:
            st.error(f"❌ 실패: {e}")
