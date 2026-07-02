"""탭: 📊 PPT — 마크다운 → PPTX 변환 (V2.7.5 → V2.7.6.3).

V2.7.6.3: deck 탭 흡수 + 엔진 선택 + 모델 선택
  - 엔진: 📄 Marp (단순·빠름) / 🎨 디자인 (컨설팅급 HTML)
  - 모델: Ollama 설치 모델 드롭다운 (고정 X)

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

from src.ui_kit import hub_pagebar, hub_section


_PPTX_CSS = """
<style>
.flow-row {
  display:grid;
  gap:8px;
  align-items:stretch;
  margin:12px 0 10px 0;
}
.flow-row.pipeline {
  grid-template-columns: minmax(0, 1fr) 22px minmax(0, 1fr) 22px minmax(0, 1fr) 22px minmax(0, 1fr);
}
.flow-row.engine {
  grid-template-columns: minmax(0, 1fr) 22px minmax(0, 1fr) 22px minmax(0, 1fr);
}
.flow-card {
  position:relative;
  min-height:118px;
  border:1px solid rgba(47,128,196,0.18);
  border-radius:14px;
  padding:14px 15px 13px 15px;
  background:linear-gradient(180deg, #ffffff 0%, #f8fbfe 100%);
  box-shadow:0 8px 22px rgba(16,24,40,0.045);
  display:flex;
  flex-direction:column;
  justify-content:space-between;
  gap:8px;
  min-width:0;
  overflow:hidden;
}
.flow-card::before {
  content:"";
  position:absolute;
  top:0;
  left:0;
  right:0;
  height:3px;
  background:linear-gradient(90deg, #2f80c4, rgba(47,128,196,0.35));
}
.flow-card.active {
  border-color:rgba(47,128,196,0.40);
  background:linear-gradient(180deg, #f7fbff 0%, #eef7ff 100%);
  box-shadow:0 10px 26px rgba(47,128,196,0.10);
}
.flow-card.empty {
  border-color:rgba(152,162,179,0.22);
  background:linear-gradient(180deg, #ffffff 0%, #fbfcfe 100%);
}
.flow-card.empty::before { background:linear-gradient(90deg, #98a2b3, rgba(152,162,179,0.18)); }
.flow-card h4 {
  margin:0;
  font-size:0.88rem;
  line-height:1.25;
  font-weight:780;
  color:#172033;
  letter-spacing:-0.01em;
}
.flow-card .stage-id {
  display:inline-flex;
  width:max-content;
  max-width:100%;
  padding:3px 7px;
  border-radius:999px;
  background:rgba(47,128,196,0.08);
  color:#2f80c4;
  font-size:0.66rem;
  line-height:1;
  font-weight:800;
  letter-spacing:0.04em;
  text-transform:uppercase;
}
.flow-card.empty .stage-id { background:rgba(152,162,179,0.10); color:#667085; }
.flow-card .big {
  font-size:1.95rem;
  font-weight:850;
  line-height:1;
  color:#101828;
  letter-spacing:-0.045em;
}
.flow-card .unit {
  font-size:0.78rem;
  color:#667085;
  margin-left:5px;
  font-weight:750;
  letter-spacing:-0.01em;
}
.flow-card .sub {
  font-size:0.74rem;
  line-height:1.45;
  color:#667085;
}
.flow-arrow {
  display:flex;
  align-items:center;
  justify-content:center;
  font-size:1.25rem;
  color:#98a2b3;
  min-width:0;
}
.flow-console-note {
  display:flex;
  align-items:center;
  gap:10px;
  margin:6px 0 12px 0;
  padding:9px 11px;
  border:1px solid rgba(47,128,196,0.14);
  border-radius:11px;
  background:rgba(47,128,196,0.045);
  color:#475467;
  font-size:0.78rem;
  line-height:1.45;
}
.flow-console-note strong { color:#172033; font-weight:800; }
.hub-pagebar {
  min-height:82px;
  overflow:visible !important;
  margin-top:10px !important;
  margin-bottom:14px !important;
  padding-top:16px !important;
  padding-bottom:16px !important;
  border-color:rgba(47,128,196,0.18) !important;
  background:linear-gradient(135deg, #ffffff 0%, #f7fbff 100%) !important;
  box-shadow:0 10px 28px rgba(16,24,40,0.055);
}
.hub-pagebar-title {
  font-size:1.32rem !important;
  line-height:1.28 !important;
  color:#101828 !important;
}
.hub-pagebar-desc {
  line-height:1.5 !important;
  overflow:visible !important;
  white-space:normal !important;
}
.hub-pagebar-title-row {
  align-items:center !important;
  min-height:28px;
}
.hub-pill {
  border:1px solid rgba(18,183,106,0.18);
  box-shadow:0 4px 10px rgba(18,183,106,0.08);
}
div[data-testid="stButton"] > button {
  min-height:36px;
  border-radius:10px;
  border-color:rgba(47,128,196,0.20);
  box-shadow:0 3px 10px rgba(16,24,40,0.035);
  font-weight:760;
}
div[data-testid="stButton"] > button:hover {
  border-color:rgba(47,128,196,0.48);
  background:rgba(47,128,196,0.045);
}
div[data-testid="stMetric"] {
  padding:8px 10px;
  border:1px solid rgba(47,128,196,0.12);
  border-radius:12px;
  background:#fff;
}
@media (max-width: 980px) {
  .flow-row,
  .flow-row.pipeline,
  .flow-row.engine {
    grid-template-columns:1fr;
  }
  .flow-arrow { display:none; }
}
</style>
"""


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


def _save_to_exports(pptx_path: Path, prefix: str = "slides") -> Path:
    """exports/ 디렉터리로 카피, 타임스탬프 박힘."""
    from src.config import IRIS_KNOWLEDGE_PROCESSED
    exports_dir = IRIS_KNOWLEDGE_PROCESSED / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    ext = pptx_path.suffix.lstrip(".")
    target = exports_dir / f"{prefix}_{stamp}.{ext}"
    import shutil
    shutil.copy2(pptx_path, target)
    return target


def _ollama_models() -> list[str]:
    """Ollama 설치 모델 목록 — embed 전용은 제외."""
    from src import llm
    names = llm.list_models()
    # 임베딩 전용 모델은 PPT용으로 못 씀
    return [n for n in names
            if not any(k in n.lower() for k in ("bge-m3", "nomic-embed", "embed"))]


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


_DEFAULT_DECK_COMPANY = "赛美特"


def _doc_title_from_upload(name: str) -> str:
    return Path(name).stem


def _init_deck_meta_defaults() -> None:
    if "pptx_deck_company" not in st.session_state:
        st.session_state["pptx_deck_company"] = _DEFAULT_DECK_COMPANY
    if "pptx_deck_title" not in st.session_state:
        st.session_state["pptx_deck_title"] = ""
    if "pptx_deck_subtitle" not in st.session_state:
        st.session_state["pptx_deck_subtitle"] = ""
    if "pptx_deck_date" not in st.session_state:
        st.session_state["pptx_deck_date"] = _dt.datetime.now().strftime("%Y.%m.%d | v1.0")


def _sync_deck_meta_from_source(*, source_key: str, doc_title: str | None) -> None:
    """새 문서 로딩 시 보고서 제목·부제를 문서명(확장자 제외)으로 채움."""
    if not doc_title:
        return
    if st.session_state.get("pptx_meta_source_key") != source_key:
        st.session_state["pptx_meta_source_key"] = source_key
        st.session_state["pptx_deck_title"] = doc_title
        st.session_state["pptx_deck_subtitle"] = doc_title


def _source_mode_summary(source_mode: str) -> tuple[str, str, str]:
    if source_mode.startswith("✍️"):
        return "직접", "textarea", "직접 작성"
    if source_mode.startswith("📂"):
        return "파일", "upload", ".md 업로드"
    if source_mode.startswith("📦"):
        return "Archive", "content", "content.md"
    if source_mode.startswith("📄"):
        return "Docs", "system", "docs/system"
    return "선택", "source", "소스 선택"


def _engine_summary(engine: str) -> tuple[str, str, str]:
    if engine.startswith("🎨"):
        return "Design", "HTML", "LLM 설계"
    return "Marp", "Fast", "단순·빠름"


def _current_markdown_length(source_mode: str) -> int:
    if source_mode.startswith("✍️"):
        return len(st.session_state.get("pptx_md", _SAMPLE_MD))
    return 0


def _card(*, stage_id: str, title: str, big: str, unit: str = "", sub: str = "", active: bool = False, empty: bool = False) -> str:
    card_class = "flow-card"
    if active:
        card_class += " active"
    elif empty:
        card_class += " empty"
    big_html = f"<div class='big'>{big}<span class='unit'>{unit}</span></div>" if unit else f"<div class='big'>{big}</div>"
    sub_html = f"<div class='sub'>{sub}</div>" if sub else ""
    return (
        f"<div class='{card_class}'>"
        f"<div class='stage-id'>{stage_id}</div>"
        f"<h4>{title}</h4>"
        f"{big_html}{sub_html}"
        f"</div>"
    )


def _arrow() -> str:
    return "<div class='flow-arrow'>→</div>"


def _render_deck_flow(source_mode: str, engine: str) -> None:
    source_big, source_unit, source_sub = _source_mode_summary(source_mode)
    engine_big, engine_unit, engine_sub = _engine_summary(engine)
    markdown_length = _current_markdown_length(source_mode)
    markdown_big = f"{markdown_length:,}" if markdown_length else "0"
    export_big = "PDF" if engine.startswith("🎨") else "PPTX"
    cards = [
        _card(stage_id="① 소스", title="입력 선택", big=source_big, unit=source_unit, sub=source_sub, active=True),
        _arrow(),
        _card(stage_id="② 원문", title="마크다운", big=markdown_big, unit="chars", sub="슬라이드 원본", empty=(markdown_length == 0)),
        _arrow(),
        _card(stage_id="③ 엔진", title="변환 방식", big=engine_big, unit=engine_unit, sub=engine_sub),
        _arrow(),
        _card(stage_id="④ 산출", title="다운로드", big=export_big, sub="exports 저장 선택"),
    ]
    st.markdown("<div class='flow-row pipeline'>" + "".join(cards) + "</div>", unsafe_allow_html=True)


def _render_source_caption(source_label: str, md_text: str) -> None:
    if source_label:
        source_text = f"소스: <strong>{source_label}</strong> · 본문 <strong>{len(md_text):,}</strong> chars"
    else:
        source_text = "소스 미선택 · 마크다운을 입력하거나 파일/archive/docs 자료를 선택하세요."
    st.markdown(f"<div class='flow-console-note'>{source_text}</div>", unsafe_allow_html=True)


def render() -> None:
    st.markdown(_PPTX_CSS, unsafe_allow_html=True)
    hub_pagebar(
        "PPT",
        "Deck Console",
        "마크다운 소스를 선택하고 변환 엔진을 정한 뒤 PPTX/PDF 산출물로 내보냅니다.",
        "Export Ready",
    )
    current_source_mode = st.session_state.get("pptx_source_mode", "✍️ 직접 입력 (textarea)")
    current_engine = st.session_state.get("pptx_engine", "📄 Marp (단순·빠름)")
    _render_deck_flow(current_source_mode, current_engine)

    hub_section("소스 선택")
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

    _init_deck_meta_defaults()

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
                doc_title = _doc_title_from_upload(uploaded.name)
                _sync_deck_meta_from_source(
                    source_key=f"upload:{uploaded.name}",
                    doc_title=doc_title,
                )
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
                    _sync_deck_meta_from_source(
                        source_key=f"archive:{path}",
                        doc_title=path.parent.name,
                    )
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
                    _sync_deck_meta_from_source(
                        source_key=f"docs:{path}",
                        doc_title=path.stem,
                    )
                    st.success(f"✅ 로딩 — {path.name} ({len(md_text):,} chars)")
                    with st.expander("📋 본문 미리보기 (앞 500자)", expanded=False):
                        st.code(md_text[:500] + ("..." if len(md_text) > 500 else ""),
                                language="markdown")
                except Exception as e:
                    st.error(f"❌ 파일 읽기 실패: {e}")

    hub_section("변환 설정")
    _render_source_caption(source_label, md_text)

    # ─── 엔진 선택 (V2.7.6.3) ───────────────────────────────────
    engine = st.radio(
        "🛠️ PPT 엔진",
        options=[
            "📄 Marp (단순·빠름)",
            "🎨 디자인 (컨설팅급, LLM 슬라이드 설계 → HTML 템플릿)",
        ],
        index=0,
        horizontal=False,
        key="pptx_engine",
        help="Marp = 마크다운을 슬라이드로 그대로 박음 (3~10초). "
             "디자인 = LLM이 패턴 결정 → HTML 렌더 (30~120초, playwright 필요).",
    )
    is_design = engine.startswith("🎨")

    # ─── 옵션 + 생성 버튼 ───────────────────────────────────────
    col_l, col_r = st.columns([3, 2])

    with col_l:
        if source_label:
            st.caption(f"📥 소스: **{source_label}** · 본문 **{len(md_text):,}** chars")
        else:
            st.caption("📥 소스 미선택")

        # 디자인 엔진은 메타 정보 필요
        if is_design:
            st.markdown("**📝 메타 정보 (디자인 엔진용)**")
            mc1, mc2 = st.columns(2)
            with mc1:
                deck_company = st.text_input("회사명", key="pptx_deck_company")
                deck_subtitle = st.text_input("부제", key="pptx_deck_subtitle")
            with mc2:
                deck_title = st.text_input("보고서 제목", key="pptx_deck_title")
                deck_date = st.text_input("날짜·버전", key="pptx_deck_date")

    with col_r:
        st.markdown("**🎨 옵션**")

        # ─── 모델 선택 (V2.7.6.3) — Ollama 설치 모델 ────────────
        from src.config import IRIS_LLM_DEEP
        installed = _ollama_models()
        if not installed:
            st.warning("⚠️ Ollama에 모델 0개 또는 Ollama 미가동")
            picked_model = None
        else:
            # 기본 선택: 현재 deep 슬롯 모델이 있으면 그것, 없으면 첫번째
            default_idx = 0
            for i, n in enumerate(installed):
                if n == IRIS_LLM_DEEP or n.startswith(IRIS_LLM_DEEP + ":"):
                    default_idx = i
                    break
            picked_model = st.selectbox(
                f"🧠 LLM 모델 ({len(installed)}개 설치)",
                options=installed,
                index=default_idx,
                key="pptx_model",
                help=f"Ollama 설치 모델. 기본 env IRIS_LLM_DEEP=`{IRIS_LLM_DEEP}`. "
                     "M2는 8b급, M5는 30b/80b 권장. Marp 엔진은 'LLM 재구조화' "
                     "체크시만 사용, 디자인 엔진은 항상 사용.",
            )

        st.divider()

        if not is_design:
            # ─── Marp 엔진 옵션 ─────────────────────────────────
            theme_name = st.selectbox(
                "테마",
                options=["iris (다크)", "default (기본)", "gaia (밝음)", "uncover (미니멀)"],
                index=0,
                help="iris는 IRIS 전용 다크 테마. 다른 테마는 Marp 내장.",
                key="pptx_theme",
            )
            paginate = st.checkbox("페이지 번호", value=True, key="pptx_paginate")
            use_llm_restructure = st.checkbox(
                "🤖 LLM 재구조화 (품질 ↑)",
                value=False,
                help="Marp 변환 *전*에 LLM이 마크다운을 프레젠테이션용으로 재구조화. "
                     "문서형 .md(예: 보고서)를 박으면 디자인·밀도 크게 향상. "
                     "본문 8000자 초과시 앞부분만 사용.",
                key="pptx_use_llm",
            )
        else:
            # ─── 디자인 엔진 옵션 ───────────────────────────────
            output_format = st.radio(
                "출력 형식",
                options=["PDF (벡터, 편집 불가)", "PPTX (이미지 임베드)"],
                index=0,
                key="pptx_deck_format",
            )
            # V2.8.2 — 2단 파이프라인 (극한 품질)
            use_2stage = st.checkbox(
                "🚀 2단 파이프라인 (품질 ↑↑)",
                value=True,
                help="① LLM이 입력을 풍부한 슬라이드용 마크다운으로 확장 (30~180초)\n"
                     "② 확장된 마크다운을 슬라이드 패턴에 매칭 (30~180초)\n"
                     "총 2~10분, 결과 25~30장 풍부함. OFF면 단일-패스 (V2.8.1).",
                key="pptx_use_2stage",
            )
            slide_target = st.selectbox(
                "🎯 목표 슬라이드 수",
                options=["auto (입력 크기에 따라)", "10장", "15장", "20장", "25장", "30장"],
                index=0,
                key="pptx_slide_target",
                help="auto: 입력 크기·2단 여부 자동 결정. "
                     "박은 수: LLM에게 정확히 그 장수 박으라 강제.",
            )
            paginate = True  # 디자인은 항상 페이지 번호
            theme_name = None
            use_llm_restructure = False

        save_to_disk = st.checkbox(
            "exports/ 에 영구 저장",
            value=is_design,  # 디자인은 기본 켜짐, Marp는 꺼짐
            help="iris-knowledge/2-processed/exports/ 에 카피",
            key="pptx_save_disk",
        )

        st.divider()

        if is_design:
            gen_btn = st.button(
                "🎨 디자인 PPT 생성",
                type="primary",
                use_container_width=True,
                disabled=not md_text.strip(),
                key="pptx_gen_design",
            )
            gen_pdf = False
        else:
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

    # ─── 생성 분기 ──────────────────────────────────────────────
    if is_design and gen_btn:
        # 슬라이드 수 파싱
        target_n: int | None = None
        if not slide_target.startswith("auto"):
            try:
                target_n = int(slide_target.replace("장", "").strip())
            except ValueError:
                target_n = None
        _generate_design(md_text, picked_model, output_format, save_to_disk,
                         deck_company, deck_title, deck_subtitle, deck_date,
                         use_2stage=use_2stage, target_slides=target_n)
        return

    if not is_design and (gen_btn or gen_pdf):
        _generate_marp(md_text, picked_model, theme_name, paginate,
                       use_llm_restructure, save_to_disk, gen_pdf)


def _generate_marp(md_text: str, picked_model: str | None,
                   theme_name: str, paginate: bool,
                   use_llm_restructure: bool, save_to_disk: bool,
                   gen_pdf: bool) -> None:
    from src import exporter

    # V2.7.5.2 — LLM 재구조화 (옵션)
    effective_md = md_text
    if use_llm_restructure:
        from src import exporter_llm
        try:
            with st.spinner("🤖 LLM 재구조화 중… (~30~120s, 모델 따라 다름)"):
                rr = exporter_llm.restructure_markdown(md_text, model=picked_model)
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
    theme_css = exporter.DEFAULT_THEME_PATH if theme_id == "iris" else None

    try:
        with st.spinner(f"{'PDF' if gen_pdf else 'PPT'} 생성 중… (3~10초)"):
            if gen_pdf:
                res = exporter.md_to_pdf(
                    effective_md, theme_css=theme_css,
                    theme_name=theme_id, paginate=paginate,
                )
            else:
                res = exporter.md_to_pptx(
                    effective_md, theme_css=theme_css,
                    theme_name=theme_id, paginate=paginate,
                )
    except exporter.ExportError as e:
        st.error(f"❌ 변환 실패: {e}")
        st.caption("Marp 미설치: `brew install marp-cli`")
        return

    st.success(
        f"✅ 생성 완료 — {res.size_bytes / 1024:.1f}KB · {res.elapsed_ms / 1000:.1f}초"
    )

    ext = "pdf" if gen_pdf else "pptx"
    with res.out_path.open("rb") as f:
        data = f.read()
    stamp = _dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    st.download_button(
        f"💾 다운로드 (slides_{stamp}.{ext})",
        data=data,
        file_name=f"slides_{stamp}.{ext}",
        mime=(
            "application/pdf" if gen_pdf
            else "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        ),
        use_container_width=True,
    )

    if save_to_disk:
        saved = _save_to_exports(res.out_path, prefix="slides")
        st.caption(f"📦 exports/ 저장: `{saved}`")


def _generate_design(md_text: str, picked_model: str | None,
                     output_format: str, save_to_disk: bool,
                     company: str, title: str, subtitle: str, date: str,
                     *,
                     use_2stage: bool = True,
                     target_slides: int | None = None) -> None:
    """V2.7.6 → V2.8.2 디자인 엔진.

    V2.8.2 변경:
    - use_2stage: True면 expander로 입력 확장 후 designer 호출
    - target_slides: 사용자가 직접 박은 슬라이드 수 (None=auto)
    """
    meta = {"company": company, "title": title, "subtitle": subtitle, "date": date}
    model_label = picked_model or "default"

    try:
        # ─── Stage 1: 입력 확장 (옵션) ──────────────────────────
        effective_md = md_text
        pre_expanded = False

        if use_2stage and len(md_text) >= 2000:
            from src.deck import expander
            try:
                with st.spinner(
                    "① LLM 입력 확장 중… (30~180초, 모델·입력 크기 따라)"
                ):
                    er = expander.expand_for_slides(
                        md_text, meta, model=picked_model, timeout=900,
                    )
                effective_md = er.md
                pre_expanded = True
                st.info(
                    f"🚀 확장 완료 — {er.model} · {er.elapsed_ms / 1000:.1f}s · "
                    f"{er.original_chars:,} → {er.output_chars:,}자"
                )
                with st.expander("📋 확장된 마크다운 미리보기 (앞 2000자)", expanded=False):
                    st.code(effective_md[:2000] +
                            ("..." if len(effective_md) > 2000 else ""),
                            language="markdown")
            except expander.ExpansionError as e:
                st.warning(f"⚠️ Stage 1 확장 실패: {e} — 원본 마크다운으로 계속")
        elif use_2stage:
            st.caption(f"📌 입력 {len(md_text):,}자 < 2000자 — Stage 1 자동 skip")

        # ─── Stage 2: 슬라이드 설계 ─────────────────────────────
        with st.spinner(
            f"② LLM 슬라이드 설계 중… (30~300초, model: {model_label})"
        ):
            from src.deck import designer
            deck = designer.design_deck(
                effective_md, meta,
                model=picked_model, timeout=600,
                pre_expanded=pre_expanded,
                target_slides=target_slides,
            )

        st.success(
            f"✅ 슬라이드 {len(deck.slides)}장 설계됨 "
            f"(model: {model_label}, "
            f"2단: {'ON' if use_2stage and pre_expanded else 'OFF'})"
        )

        with st.expander("📋 슬라이드 패턴 미리보기", expanded=False):
            for i, sl in enumerate(deck.slides, 1):
                label = str(sl.data.get("title", sl.data.get("company", "?")))[:80]
                # 항목 수 정보
                item_count = ""
                for key in ("phases", "dimensions", "cards", "metrics", "items",
                            "left_items", "right_items"):
                    if key in sl.data and isinstance(sl.data[key], list):
                        item_count = f" [{key}={len(sl.data[key])}]"
                        break
                st.write(f"{i}. **{sl.pattern}** — {label}{item_count}")

        # ─── Stage 3: 렌더 ──────────────────────────────────────
        fmt_label = "PDF" if "PDF" in output_format else "PPTX"
        with st.spinner(
            f"③ {fmt_label} 렌더 중… (슬라이드당 ~2초, 총 {len(deck.slides)*2}~{len(deck.slides)*4}초)"
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
            saved = _save_to_exports(out_path, prefix="deck")
            st.caption(f"📦 exports/ 저장: `{saved}`")

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
        st.caption("playwright 미설치라면: `pip install playwright && playwright install chromium`")
