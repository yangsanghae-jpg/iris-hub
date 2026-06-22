"""탭: 🎨 디자인 PPT — V2.7.6."""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

import streamlit as st


_SAMPLE_MD = """## NanoLN 종합 지표 관리 체계 — 진단 및 혁신

### 사업 특성
- 단결정 LN/LT 박막 소재 전문 (RF 필터·광통신·집적 광학)
- 고부가가치 / 고난도 공정 / 미세 품질 / 고객 인증 대응

### 현행 진단 (As-Is)
- 리포트는 42개 보유, 8개 부서 분산 → 체계 약함
- BSC 4관점 불균형: 내부 프로세스 90% 편중, 학습성장 0
- 단결정·박막·CMP 공정 특화 지표 부족
- 후행 결과 확인 위주, 선행 예방 부족
- 정의·자동화 미표준 → 부서별 해석 차이

### 혁신 방향 (To-Be)
- KPI Tree로 묶인 종합 지표 체계 (전사↔부서↔현장 인과)
- BSC 4관점 균형 (재무·고객·학습성장 보강)
- 공정 특화 지표 도입 (회수율·Void·Ra·Qual 통과율)
- 3계층 KPI 체계 (전략/운영/관리)
- KPI 정의서 11개 표준 항목
- BI 자동화·SSoT (MES/SPC/ERP 통합)

### 단계별 추진 로드맵 (12개월)
1. 0~3M Phase 1: 현행 정리·표준화 (42개 재분류, 통합, Owner 지정)
2. 3~6M Phase 2: KPI Tree 설계 (전사 목표, 3계층, 인과관계)
3. 6~9M Phase 3: 공정 특화 보완 (단결정·박막·CMP·고객)
4. 9~12M Phase 4: BI 자동화 구축 (데이터 매핑, 대시보드, 알람)

### 기대 효과 (5 관점)
- 경영: 전사 목표↔현장 연결, 통합 판단, 투자 우선순위
- 생산: 병목 조기 발견, Cycle Time/WIP 향상
- 품질: 수율 원인 추적, 사전 예방 전환
- 설비: 고장↔품질 영향, 예지보전
- 고객: 납기 리스크 사전 식별, Qual 강화, 신뢰도 향상
"""


def _save_to_exports(path: Path, ext: str) -> Path:
    from src.config import IRIS_KNOWLEDGE_PROCESSED
    exports_dir = IRIS_KNOWLEDGE_PROCESSED / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    target = exports_dir / f"deck_{stamp}.{ext}"
    import shutil
    shutil.copy2(path, target)
    return target


def render() -> None:
    # 입력 헬퍼는 pptx 탭과 공유
    from src.tabs.pptx import _list_archive_content_md, _list_docs_md

    st.markdown("### 🎨 디자인 PPT — V2.7.6.1")
    st.caption(
        "마크다운 + 메타 정보를 박으면 LLM이 슬라이드 설계 → 컨설팅급 HTML 템플릿 렌더 → PDF/PPTX. "
        "**처리 시간 30~120초** (LLM + Chrome 렌더). 단순 마크다운은 📊 PPT 탭 사용."
    )

    # ─── 입력 방식 선택 (4 모드) ────────────────────────────────
    source_mode = st.radio(
        "마크다운 소스",
        options=[
            "✍️ 직접 입력 (textarea)",
            "📂 파일 업로드 (.md)",
            "📦 archive 자료 (content.md)",
            "📄 docs/system 보고서",
        ],
        horizontal=True,
        key="deck_source_mode",
    )

    md_text = ""
    source_label = ""

    if source_mode.startswith("✍️"):
        md_text = st.text_area(
            "마크다운 입력",
            value=st.session_state.get("deck_md", _SAMPLE_MD),
            key="deck_md_input",
            height=380,
        )
        st.session_state["deck_md"] = md_text
        source_label = "직접 입력"

    elif source_mode.startswith("📂"):
        uploaded = st.file_uploader(
            ".md 파일 선택", type=["md", "markdown", "txt"],
            key="deck_upload",
            help="마크다운 1개 파일. UTF-8 권장.",
        )
        if uploaded:
            try:
                md_text = uploaded.read().decode("utf-8")
                source_label = f"파일: {uploaded.name}"
                st.success(f"✅ 로딩 — {uploaded.name} ({len(md_text):,} chars)")
                with st.expander("📋 본문 미리보기 (앞 500자)", expanded=False):
                    st.code(md_text[:500] + ("..." if len(md_text) > 500 else ""),
                            language="markdown")
            except Exception as e:
                st.error(f"❌ 파일 읽기 실패: {e}")

    elif source_mode.startswith("📦"):
        archive_items = _list_archive_content_md()
        if not archive_items:
            st.info(
                "📦 3-archive에 인덱싱된 자료 없음. 📥 입력 탭 → 흐름 탭 처리 후 사용."
            )
        else:
            labels = ["(선택)"] + [lbl for lbl, _ in archive_items]
            picked = st.selectbox(
                f"archive 자료 ({len(archive_items)}건)",
                options=labels, key="deck_archive_pick",
            )
            if picked and picked != "(선택)":
                idx = labels.index(picked) - 1
                path = archive_items[idx][1]
                try:
                    md_text = path.read_text(encoding="utf-8")
                    source_label = f"archive: {path.parent.name}"
                    st.success(f"✅ 로딩 — {path.parent.name} ({len(md_text):,} chars)")
                    with st.expander("📋 본문 미리보기", expanded=False):
                        st.code(md_text[:500] + ("..." if len(md_text) > 500 else ""),
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
                options=labels, key="deck_docs_pick",
            )
            if picked and picked != "(선택)":
                idx = labels.index(picked) - 1
                path = docs_items[idx][1]
                try:
                    md_text = path.read_text(encoding="utf-8")
                    source_label = f"docs: {path.name}"
                    st.success(f"✅ 로딩 — {path.name} ({len(md_text):,} chars)")
                    with st.expander("📋 본문 미리보기", expanded=False):
                        st.code(md_text[:500] + ("..." if len(md_text) > 500 else ""),
                                language="markdown")
                except Exception as e:
                    st.error(f"❌ 읽기 실패: {e}")

    st.divider()

    col_l, col_r = st.columns([3, 2])
    with col_l:
        if source_label:
            st.caption(f"📥 소스: **{source_label}** · 본문 **{len(md_text):,}** chars")
        else:
            st.caption("📥 소스 미선택")

    with col_r:
        st.markdown("**📝 메타 정보**")
        company = st.text_input("회사명", value="NanoLN", key="deck_company")
        title = st.text_input("보고서 제목", value="종합 지표 관리 체계 진단 및 혁신 방안", key="deck_title")
        subtitle = st.text_input("부제", value="단결정 LN/LT 박막 공정 특성 기반", key="deck_subtitle")
        date = st.text_input("날짜·버전", value="2026.06.01 | v2.0", key="deck_date")

        st.divider()

        output_format = st.radio(
            "출력 형식",
            options=["PDF (벡터, 편집 불가)", "PPTX (이미지 임베드)"],
            index=0,
            key="deck_format",
        )
        save_to_disk = st.checkbox(
            "exports/ 에 영구 저장",
            value=True,
            key="deck_save_disk",
            help="iris-knowledge/2-processed/exports/ 에 저장",
        )

        gen_btn = st.button(
            "🎨 디자인 PPT 생성",
            type="primary",
            use_container_width=True,
            disabled=not md_text.strip(),
            key="deck_gen",
        )

    if gen_btn:
        meta = {
            "company": company,
            "title": title,
            "subtitle": subtitle,
            "date": date,
        }

        try:
            with st.spinner("① LLM 슬라이드 설계 중… (15~120초)"):
                from src.deck import designer
                deck = designer.design_deck(md_text, meta)

            st.success(f"✅ 슬라이드 {len(deck.slides)}장 설계됨")

            with st.expander("📋 슬라이드 패턴 미리보기", expanded=False):
                for i, sl in enumerate(deck.slides, 1):
                    label = sl.data.get("title", sl.data.get("company", "?"))[:60]
                    st.write(f"{i}. **{sl.pattern}** — {label}")

            fmt_label = "PDF" if "PDF" in output_format else "PPTX"
            with st.spinner(
                f"② {fmt_label} 렌더 중… (슬라이드당 ~2초, 총 {len(deck.slides)*2}~{len(deck.slides)*4}초)"
            ):
                if "PDF" in output_format:
                    from src.deck.renderer import render_deck_to_pdf
                    out_path = render_deck_to_pdf(deck)
                    ext, mime = "pdf", "application/pdf"
                else:
                    from src.deck.pptx_export import render_deck_to_pptx
                    out_path = render_deck_to_pptx(deck)
                    ext = "pptx"
                    mime = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

            size_kb = out_path.stat().st_size / 1024
            st.success(f"✅ 생성 완료 — {size_kb:.1f}KB")

            if save_to_disk:
                saved = _save_to_exports(out_path, ext)
                st.caption(f"저장: `{saved}`")

            with out_path.open("rb") as f:
                data = f.read()
            stamp = _dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
            st.download_button(
                f"💾 다운로드 (deck_{stamp}.{ext})",
                data=data,
                file_name=f"deck_{stamp}.{ext}",
                mime=mime,
                use_container_width=True,
            )

        except Exception as e:
            st.error(f"❌ 실패: {type(e).__name__}: {e}")
            st.caption("LLM 응답 형식이 깨졌거나 템플릿 데이터가 부족할 수 있음.")
