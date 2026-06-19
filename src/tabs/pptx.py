"""탭: 📊 PPT — 마크다운 → PPTX 변환 (V2.7.5).

사용자가 textarea에 마크다운을 박으면 Marp로 .pptx 생성 → 다운로드.

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


def render() -> None:
    st.markdown("### 📊 마크다운 → PPT — V2.7.5")
    st.caption(
        "마크다운을 박으면 Marp로 .pptx 생성. 슬라이드 구분은 `---` (3 하이픈). "
        "frontmatter는 자동으로 박힘 (안 박아도 됨)."
    )

    # 사용자 입력
    col_l, col_r = st.columns([3, 2])
    with col_l:
        md_text = st.text_area(
            "마크다운 입력",
            value=st.session_state.get("pptx_md", _SAMPLE_MD),
            key="pptx_md_input",
            height=420,
            help="`---`로 슬라이드 구분. 표·인용·코드 모두 박힘.",
        )
        st.session_state["pptx_md"] = md_text

    with col_r:
        st.markdown("**🎨 옵션**")
        theme_name = st.selectbox(
            "테마",
            options=["iris (다크)", "default (기본)", "gaia (밝음)", "uncover (미니멀)"],
            index=0,
            help="iris는 IRIS 전용 다크 테마. 다른 테마는 Marp 내장.",
        )
        paginate = st.checkbox("페이지 번호", value=True)
        save_to_disk = st.checkbox(
            "exports/ 에 영구 저장",
            value=False,
            help="iris-knowledge/2-processed/exports/ 에도 카피",
        )

        st.divider()

        gen_btn = st.button(
            "📊 PPT 생성",
            type="primary",
            use_container_width=True,
            disabled=not md_text.strip(),
        )

        gen_pdf = st.button(
            "📄 PDF 생성 (보너스)",
            use_container_width=True,
            disabled=not md_text.strip(),
        )

    if gen_btn or gen_pdf:
        from src import exporter

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
                        md_text,
                        theme_css=theme_css,
                        theme_name=theme_id,
                        paginate=paginate,
                    )
                else:
                    res = exporter.md_to_pptx(
                        md_text,
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
