"""탭: 📊 PPT — 마크다운 → PPTX 변환 (V2.7.5 → V2.7.5.1).

V2.7.5.1: 입력 방식 3종 — 직접 입력 / 파일 업로드 / 디스크 .md 선택
  - 3-archive/<doc>/content.md (인덱싱된 자료)
  - /0Dev/docs/system/*.md (보고서·지시서)
  - 사용자 textarea 직접 입력

특징:
  - frontmatter 자동 박힘 (사용자가 안 박아도 됨)
  - iris.css 다크 테마 기본 적용
  - 슬라이드 구분: `---` (가장 친숙)
  - 결과는 streamlit st.download_button + 영구 저장 옵션
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

import streamlit as st


_SAMPLE_MD = """# IRIS 주간 보고
## 2026-06-20

---

## 📊 처리 현황

- documents **1,304** 행
- chunks **5,331** 청크
- archive **33** 자료

> 진실원: archive의 마크다운 파일, DB는 인덱스

---

## 산업 분포

| 산업 | 자료수 | 비율 |
|---|---:|---:|
| B 반도체 | 458 | 35% |
| C 전자조립 | 335 | 26% |
| D 디스플레이 | 95 | 7% |
| H 자동차 | 110 | 8% |

---

## 다음 사이클

- V2.7.5 PPT Export *(현 슬라이드)*
- V2.7.6 OpenClaw 통합
- V2.7.1 야간 스케줄러

---

<!-- _class: lead -->

# 끝
"""


def _save_to_exports(pptx_path: Path) -> Path:
    """exports/ 디렉터리로 카피, 타임스탬프 박힘."""
    from src.config import IRIS_KNOWLEDGE_PROCESSED
    exports_dir = IRIS_KNOWLEDGE_PROCESSED / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    target = exports_dir / f"slides_{stamp}.pptx"
    import shutil
    shutil.copy2(pptx_path, target)
    return target


# ─── V2.7.5.1 — 디스크 마크다운 소스 ──────────────────────────────────
def _list_archive_content_md() -> list[tuple[str, Path]]:
    """3-archive/<date>/<doc_id>/content.md 목록 — (라벨, 경로)."""
    from src.config import IRIS_KNOWLEDGE_ARCHIVE
    if not IRIS_KNOWLEDGE_ARCHIVE.exists():
        return []
    items: list[tuple[str, Path]] = []
    for date_dir in sorted(IRIS_KNOWLEDGE_ARCHIVE.iterdir(), reverse=True):
        if not date_dir.is_dir():
            continue
        for doc_dir in sorted(date_dir.iterdir()):
            content = doc_dir / "content.md"
            if content.exists():
                # title 추출: manifest.json에서 가져옴, 없으면 doc_id
                title = doc_dir.name
                manifest = doc_dir / "manifest.json"
                if manifest.exists():
                    try:
                        import json
                        m = json.loads(manifest.read_text(encoding="utf-8"))
                        title = m.get("title") or doc_dir.name
                    except Exception:
                        pass
                size_kb = content.stat().st_size / 1024
                label = f"📦 [{date_dir.name}] {title[:50]} ({size_kb:.1f}KB)"
                items.append((label, content))
    return items


def _list_docs_md() -> list[tuple[str, Path]]:
    """/0Dev/docs/system/*.md 목록."""
    docs_dir = Path("/Users/iris/Documents/0Dev/docs/system")
    if not docs_dir.exists():
        return []
    items: list[tuple[str, Path]] = []
    for p in sorted(docs_dir.glob("*.md"), reverse=True):
        size_kb = p.stat().st_size / 1024
        label = f"📄 {p.name[:60]} ({size_kb:.1f}KB)"
        items.append((label, p))
    return items


def render() -> None:
    st.markdown("### 📊 마크다운 → PPT — V2.7.5.1")
    st.caption(
        "마크다운을 박으면 Marp로 .pptx 생성. 입력 3 방식 — *직접 입력 / 파일 업로드 / 디스크 .md 선택*. "
        "슬라이드 구분 `---`. frontmatter 자동 박힘."
    )

    # ─── 입력 방식 선택 ──────────────────────────────────────────
    source_mode = st.radio(
        "마크다운 소스",
        options=[
            "✍️ 직접 입력 (textarea)",
            "📂 파일 업로드 (.md)",
            "📦 archive 자료 (content.md)",
            "📄 docs/system 보고서",
        ],
        horizontal=True,
        key="pptx_source_mode",
    )

    # ─── 소스에 따른 본문 결정 ──────────────────────────────────
    md_text = ""
    source_label = ""

    if source_mode.startswith("✍️"):
        md_text = st.text_area(
            "마크다운 입력",
            value=st.session_state.get("pptx_md", _SAMPLE_MD),
            key="pptx_md_input",
            height=380,
            help="`---`로 슬라이드 구분. 표·인용·코드 모두 박힘.",
        )
        st.session_state["pptx_md"] = md_text
        source_label = "직접 입력"

    elif source_mode.startswith("📂"):
        uploaded = st.file_uploader(
            ".md 파일 선택", type=["md", "markdown", "txt"],
            key="pptx_upload",
            help="마크다운 1개 파일. UTF-8 인코딩 권장.",
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
                md_text = ""

    elif source_mode.startswith("📦"):
        archive_items = _list_archive_content_md()
        if not archive_items:
            st.info(
                "📦 3-archive에 인덱싱된 자료 없음. "
                "📥 입력 탭에서 폴더 박은 후 흐름 탭에서 처리하면 archive에 박힘."
            )
        else:
            labels = ["(선택)"] + [lbl for lbl, _ in archive_items]
            picked = st.selectbox(
                f"archive 자료 ({len(archive_items)}건)",
                options=labels, key="pptx_archive_pick",
            )
            if picked and picked != "(선택)":
                idx = labels.index(picked) - 1
                path = archive_items[idx][1]
                try:
                    md_text = path.read_text(encoding="utf-8")
                    source_label = f"archive: {path.parent.name}"
                    st.success(f"✅ 로딩 — {path.parent.name} ({len(md_text):,} chars)")
                    with st.expander("📋 본문 미리보기 (앞 500자)", expanded=False):
                        st.code(md_text[:500] + ("..." if len(md_text) > 500 else ""),
                                language="markdown")
                except Exception as e:
                    st.error(f"❌ 파일 읽기 실패: {e}")

    elif source_mode.startswith("📄"):
        docs_items = _list_docs_md()
        if not docs_items:
            st.info("📄 /0Dev/docs/system/ 에 .md 없음.")
        else:
            labels = ["(선택)"] + [lbl for lbl, _ in docs_items]
            picked = st.selectbox(
                f"docs/system 보고서 ({len(docs_items)}건)",
                options=labels, key="pptx_docs_pick",
            )
            if picked and picked != "(선택)":
                idx = labels.index(picked) - 1
                path = docs_items[idx][1]
                try:
                    md_text = path.read_text(encoding="utf-8")
                    source_label = f"docs: {path.name}"
                    st.success(f"✅ 로딩 — {path.name} ({len(md_text):,} chars)")
                    with st.expander("📋 본문 미리보기 (앞 500자)", expanded=False):
                        st.code(md_text[:500] + ("..." if len(md_text) > 500 else ""),
                                language="markdown")
                except Exception as e:
                    st.error(f"❌ 파일 읽기 실패: {e}")

    st.divider()

    # ─── 옵션 + 생성 버튼 ───────────────────────────────────────
    col_l, col_r = st.columns([3, 2])

    with col_l:
        if source_label:
            st.caption(f"📥 소스: **{source_label}** · 본문 **{len(md_text):,}** chars")
        else:
            st.caption("📥 소스 미선택")

    with col_r:
        st.markdown("**🎨 옵션**")
        theme_name = st.selectbox(
            "테마",
            options=["iris (다크)", "default (기본)", "gaia (밝음)", "uncover (미니멀)"],
            index=0,
            help="iris는 IRIS 전용 다크 테마. 다른 테마는 Marp 내장.",
            key="pptx_theme",
        )
        paginate = st.checkbox("페이지 번호", value=True, key="pptx_paginate")
        save_to_disk = st.checkbox(
            "exports/ 에 영구 저장",
            value=False,
            help="iris-knowledge/2-processed/exports/ 에도 카피",
            key="pptx_save_disk",
        )
        use_llm_restructure = st.checkbox(
            "🤖 LLM 재구조화 (품질 ↑)",
            value=False,
            help="Marp 변환 *전*에 LLM(qwen3:8b deep)이 마크다운을 프레젠테이션용으로 재구조화. "
                 "문서형 .md(예: 보고서)를 박으면 디자인·밀도 크게 향상. "
                 "M2 ~30~60s, M5 ~60~120s (모델 차이). "
                 "본문 8000자 초과시 앞부분만 사용.",
            key="pptx_use_llm",
        )

        st.divider()

        gen_btn = st.button(
            "📊 PPT 생성",
            type="primary",
            use_container_width=True,
            disabled=not md_text.strip(),
            key="pptx_gen_pptx",
        )

        gen_pdf = st.button(
            "📄 PDF 생성 (보너스)",
            use_container_width=True,
            disabled=not md_text.strip(),
            key="pptx_gen_pdf",
        )

    if gen_btn or gen_pdf:
        from src import exporter

        # V2.7.5.2 — LLM 재구조화 (옵션)
        effective_md = md_text
        if use_llm_restructure:
            from src import exporter_llm
            try:
                with st.spinner(
                    "🤖 LLM 재구조화 중… (~30~120s, 모델 따라 다름)"
                ):
                    rr = exporter_llm.restructure_markdown(md_text)
                effective_md = rr.md
                st.info(
                    f"🤖 재구조화 완료 — {rr.model} · {rr.elapsed_ms / 1000:.1f}s · "
                    f"{rr.original_chars:,} → {rr.output_chars:,}자 · "
                    f"슬라이드 ~{rr.slides_count}장"
                )
                with st.expander("📋 재구조화된 마크다운 미리보기", expanded=False):
                    st.code(effective_md[:1500] +
                            ("..." if len(effective_md) > 1500 else ""),
                            language="markdown")
            except exporter_llm.RestructureError as e:
                st.warning(f"⚠️ LLM 재구조화 실패: {e} — 원본 마크다운 사용")

        # 테마 이름 매핑
        theme_map = {
            "iris (다크)": "iris",
            "default (기본)": "default",
            "gaia (밝음)": "gaia",
            "uncover (미니멀)": "uncover",
        }
        theme_id = theme_map.get(theme_name, "iris")
        # iris는 커스텀 CSS, 나머지는 Marp 내장이라 theme_css 안 박음
        theme_css = exporter.DEFAULT_THEME_PATH if theme_id == "iris" else None

        try:
            with st.spinner(f"{'PDF' if gen_pdf else 'PPT'} 생성 중… (3~10초)"):
                if gen_pdf:
                    res = exporter.md_to_pdf(
                        effective_md,
                        theme_css=theme_css,
                        theme_name=theme_id,
                        paginate=paginate,
                    )
                else:
                    res = exporter.md_to_pptx(
                        effective_md,
                        theme_css=theme_css,
                        theme_name=theme_id,
                        paginate=paginate,
                    )
        except exporter.ExportError as e:
            st.error(f"❌ 변환 실패: {e}")
            st.caption(
                "Marp 미설치라면 macOS에서: `brew install marp-cli`. "
                "Chrome 미설치라면: macOS는 보통 기본 박혀 있음 — 경로 확인 필요."
            )
            return

        st.success(
            f"✅ 생성 완료 — {res.size_bytes / 1024:.1f}KB · {res.elapsed_ms / 1000:.1f}초"
        )

        # 다운로드 버튼
        ext = "pdf" if gen_pdf else "pptx"
        with res.out_path.open("rb") as f:
            data = f.read()
        stamp = _dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        st.download_button(
            f"💾 다운로드 (slides_{stamp}.{ext})",
            data=data,
            file_name=f"slides_{stamp}.{ext}",
            mime=(
                "application/pdf"
                if gen_pdf
                else "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            ),
            use_container_width=True,
        )

        # 영구 저장
        if save_to_disk and not gen_pdf:
            saved = _save_to_exports(res.out_path)
            st.caption(f"📦 exports/ 저장: `{saved}`")
