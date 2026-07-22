"""탭: 📊 PPT — 마크다운 → PPTX 변환 (V2.9.0 — 4단계 위저드 재구현).

V2.9.0: docs/design/PPT_WIZARD_UX_DESIGN.md 확정 UX로 전면 재구현
  - 카드 2열 나열(진행상태/소스선택/변환설정) 폐기
  - 상단 스텝퍼(①소스 ②확장 ③설계 ④렌더) + 단일 포커스 패널 + 우측 사이드(단계별 전환)
    + 하단 진행 요약 스트립 구조로 교체
  - Marp 엔진 선택지 삭제 — 디자인 엔진(LLM 슬라이드 설계 → HTML/PPTX 렌더링) 단일화
  - ②확장을 명시적 처리 단계로 승격 (expander.expand_for_slides), ③설계에서
    designer.design_deck 실행, ④렌더에서 실제 PDF/PPTX 파일 생성
  - NOTE(구현 범위 한계 — 아래 "알려진 제약" 참고): 언어 선택 셀렉트박스는
    현재 백엔드(expander/designer/renderer/pptx_export)가 명시적 lang 파라미터를
    받지 않아(콘텐츠 자동 감지만 지원) 세션 상태 저장 UI로만 동작한다. 템플릿
    3종(iris다크/라이트/미니멀)·마스터 스타일도 렌더 엔진에 실제 배선된 개념이
    아직 없어 세션 상태 선택만 반영된다(진짜 렌더링 반영은 추후 백엔드 작업).
    이번 패스는 src/tabs/pptx.py 한 파일만 수정하는 범위였으므로 엔진 파일은
    건드리지 않았다.

V2.8.3: client/dev/diagnosistool_pptx_mock.html 목업을 실제 탭에 이식(폐기됨)
V2.7.6.3: deck 탭 흡수 + 엔진 선택 + 모델 선택
V2.7.5.1: 입력 방식 3종 — 직접 입력 / 파일 업로드 / 디스크 .md 선택
"""
from __future__ import annotations

import datetime as _dt
from html import escape as _esc
from pathlib import Path

import streamlit as st

from src.ui_kit import hub_pagebar


# ─── 디자인 토큰 (client/dev/pptx_wizard_mock.html 이식, --pptx- 네임스페이스) ──
_PPTX_CSS = """
<style>
:root {
  --pptx-bg:#f4f7fb; --pptx-card:#ffffff; --pptx-text:#1f2a37; --pptx-muted:#6b7280;
  --pptx-line:#e5e7eb; --pptx-shadow:0 10px 30px rgba(15,23,42,0.08); --pptx-radius:16px;
  --pptx-s1-border:#eeeeee; --pptx-s1-text-main:#111827; --pptx-s1-text-sub:#6b7280;
  --pptx-ch-1:#3b82f6; --pptx-ch-2:#22c55e; --pptx-ch-3:#6366f1; --pptx-ch-4:#f59e0b;
  --pptx-ch-5:#ef4444; --pptx-ch-6:#06b6d4; --pptx-ch-7:#a855f7;
}

/* ── 배경 대비: --pptx-bg 토큰이 정의만 되고 미적용이던 문제 수정. PPT 탭에
   있을 때만 <style>이 DOM에 존재하므로 다른 탭 배경엔 영향 없음. ── */
.stApp, [data-testid="stAppViewContainer"] {
  background: var(--pptx-bg) !important;
}

/* ── hub_ui.css가 전탭 공통으로 .block-container를 1180px로 캡핑 — 진단툴(별도
   standalone 앱)엔 이 캡이 없어 PC 화면에서 상대적으로 좁아 보임. 이 CSS는
   pptx.render() 안에서만 주입되므로 PPT 탭에 있을 때만 넓어지고, 다른 탭으로
   가면 이 <style>이 DOM에서 빠져 원래 1180px로 돌아감(다른 탭 무영향). ── */
.block-container {
  max-width: 1800px !important;
}
/* 소스 레일 폭 고정 — 이전에는 `:has(.pptx-rail-anchor)`로 찾아서 강제로
   220px를 줬는데, :has()가 조상 방향으로 과매칭되어 레일의 진짜 부모 열뿐
   아니라 그 바깥 패널 컨테이너 자체까지 220px로 짓눌러버리는 회귀가 있었다
   (패널 전체가 찌그러지고 우측 사이드바가 비정상적으로 넓어짐). 이제 anchor가
   아니라 rail_col 자신에게 준 고유 key(.st-key-pptx_rail_col)를 직접 타겟팅. */
[data-testid="stColumn"]:has(> div > .st-key-pptx_rail_col) {
  flex: 0 0 220px !important; max-width: 220px !important; min-width: 220px !important;
}

/* ── hub_pagebar을 진단툴 topbar 톤으로 (PPT 탭 전용, 다른 탭 무영향) ── */
.hub-pagebar {
  border-color: var(--pptx-line) !important;
  background: var(--pptx-card) !important;
  box-shadow: var(--pptx-shadow) !important;
}
.hub-pagebar-title { color: var(--pptx-text) !important; }

/* ── 스텝퍼 ── */
.st-key-pptx_stepper_box {
  padding:0 !important; overflow:hidden !important; margin-bottom:6px !important;
  border-radius: 12px !important; background: var(--pptx-card) !important;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04) !important; border-color: var(--pptx-line) !important;
}
.st-key-pptx_stepper_box [data-testid="stVerticalBlock"] { gap:0 !important; }
.st-key-pptx_stepper_box [data-testid="stButton"] button {
  border:none !important; border-radius:0 !important; background:#fff !important;
  padding:12px 14px !important; font-size:13px !important; font-weight:800 !important;
  color:var(--pptx-s1-text-sub) !important; text-align:left !important; min-height:44px !important;
  border-right:1px solid var(--pptx-s1-border) !important; border-bottom:3px solid transparent !important;
  white-space:normal !important; width:100% !important;
}
.st-key-pptx_stepper_box [data-testid="stCaptionContainer"] { padding:0 14px 8px !important; margin-top:-6px !important; }

/* ── panel / side / progress ── */
.st-key-pptx_panel_box, .st-key-pptx_side_box, .st-key-pptx_progress_box {
  border-color: var(--pptx-line) !important; box-shadow: var(--pptx-shadow) !important;
  border-radius: var(--pptx-radius) !important; background: var(--pptx-card) !important;
}
.st-key-pptx_panel_box { padding:20px 22px !important; min-height:420px !important; }

/* ── 네이티브 위젯 폰트: Streamlit 기본(16px 안팎)이 목업(11.5~13px) 대비 커서
   전체가 확대된 것처럼 보이던 핵심 원인. PPT 탭 콘텐츠 영역에서만 축소. ── */
.st-key-pptx_panel_box [data-testid="stWidgetLabel"] p,
.st-key-pptx_side_box [data-testid="stWidgetLabel"] p {
  font-size: 12px !important; font-weight: 700 !important; color: var(--pptx-muted) !important;
}
.st-key-pptx_panel_box textarea,
.st-key-pptx_panel_box [data-baseweb="select"] *,
.st-key-pptx_side_box [data-baseweb="select"] *,
.st-key-pptx_panel_box [data-testid="stMarkdownContainer"] p,
.st-key-pptx_side_box [data-testid="stMarkdownContainer"] p {
  font-size: 13px !important;
}
.st-key-pptx_panel_box [data-testid="stRadio"] label p,
.st-key-pptx_side_box [data-testid="stRadio"] label p {
  font-size: 12.5px !important;
}
.st-key-pptx_panel_box [data-testid="stBaseButton-secondary"] p,
.st-key-pptx_side_box [data-testid="stBaseButton-secondary"] p {
  font-size: 12.5px !important;
}
/* ── Streamlit 기본 포커스 링 무력화: 셀렉트박스·버튼·텍스트에어리어를 클릭할
   때마다 파란 아웃라인/보더가 뜨는 건 Streamlit(BaseWeb) 기본 동작이지 목업
   디자인이 아니다. 이걸 한 번도 꺼준 적이 없어서 상호작용할 때마다 "커스텀
   안 된 기본 UI"처럼 보였다. 실제 선택/활성 상태(스텝퍼 활성, 라디오 선택,
   템플릿 선택 카드 등)만 목업이 정한 파란색을 쓰고, 나머지 포커스는 중립. ── */
.st-key-pptx_panel_box button:focus,
.st-key-pptx_panel_box button:focus-visible,
.st-key-pptx_side_box button:focus,
.st-key-pptx_side_box button:focus-visible,
.st-key-pptx_progress_box button:focus,
.st-key-pptx_progress_box button:focus-visible,
.st-key-pptx_stepper_box button:focus,
.st-key-pptx_stepper_box button:focus-visible {
  outline: none !important; box-shadow: none !important; border-color: var(--pptx-s1-border) !important;
}
.st-key-pptx_panel_box [data-baseweb="select"] > div,
.st-key-pptx_side_box [data-baseweb="select"] > div,
.st-key-pptx_panel_box [data-baseweb="base-input"],
.st-key-pptx_side_box [data-baseweb="base-input"] {
  border-color: var(--pptx-s1-border) !important; box-shadow: none !important;
}
.st-key-pptx_panel_box [data-baseweb="select"]:focus-within > div,
.st-key-pptx_side_box [data-baseweb="select"]:focus-within > div {
  border-color: var(--pptx-s1-border) !important; box-shadow: none !important;
}
.st-key-pptx_panel_box textarea:focus,
.st-key-pptx_panel_box textarea:focus-visible {
  border-color: var(--pptx-s1-border) !important; box-shadow: none !important; outline: none !important;
}
.st-key-pptx_panel_box [data-testid="stRadio"] label:has(input:checked) div:first-child {
  border-color: #3b82f6 !important;
}

.st-key-pptx_progress_box { border-radius: 12px !important; box-shadow:none !important; margin-top:8px !important; }
/* ── 진행 요약 스트립 "편집" 버튼 — 캡션처럼 작아 클릭 어포던스가 없던 문제
   수정: 실제 버튼처럼 보이는 배경·라운드·패딩 부여 (목업 링크색 #3b82f6 톤). ── */
.st-key-pptx_progress_box [data-testid="stButton"] button {
  border:none !important; background:#eff6ff !important; color:#3b82f6 !important;
  font-size:11px !important; font-weight:800 !important; padding:3px 8px !important;
  min-height:24px !important; border-radius:6px !important;
}

/* ── 하단 다음/이전 액션 버튼 시인성 ── */
.st-key-pptx_next_btn button {
  background:#111 !important; color:#fff !important; border:none !important; font-weight:800 !important;
}
.st-key-pptx_prev_btn button {
  background:#fff !important; border:1px solid var(--pptx-line) !important;
  color:var(--pptx-muted) !important; font-weight:700 !important;
}

.expand-note { font-size:12px; color:var(--pptx-muted); margin-bottom:14px; line-height:1.6; }
.expand-box {
  background:#f9fafb; border:1px solid var(--pptx-s1-border); border-radius:10px; padding:14px;
  font-family:ui-monospace, monospace; font-size:12px; line-height:1.7; white-space:pre-wrap;
  max-height:340px; overflow:auto; color:var(--pptx-s1-text-main);
}
.expand-box.accent { background:#eff6ff; border-color:#bfdbfe; }
.expand-sub { font-size:11px; font-weight:800; color:var(--pptx-muted); margin-bottom:6px; }
.llm-status { display:flex; align-items:center; gap:7px; font-size:11.5px; color:var(--pptx-muted); font-weight:700; }
.llm-status .dot { width:7px; height:7px; border-radius:50%; }
.llm-status .dot.done { background:#16a34a; }

.tpl-section > label { display:block; font-size:11.5px; font-weight:700; color:var(--pptx-muted); margin-bottom:8px; }
.tpl-thumb { width:100%; aspect-ratio:16/10; border-radius:6px; }
.tpl-name { font-size:10.5px; font-weight:700; color:var(--pptx-s1-text-main); margin-top:4px; text-align:center; }
.tpl-badge { display:block; font-size:9px; font-weight:800; color:#16a34a; }

.master-section-label { font-size:11.5px; font-weight:700; color:var(--pptx-muted); margin:14px 0 8px; }
.master-section-label .hint { font-weight:500; color:var(--pptx-muted); font-size:10.5px; }

.render-status { display:flex; align-items:center; gap:7px; font-size:11.5px; color:var(--pptx-muted); font-weight:700; margin-bottom:14px; }
.render-status .dot { width:7px; height:7px; border-radius:50%; background:#16a34a; }
.render-thumb {
  aspect-ratio:16/10; border-radius:6px; padding:14px; display:flex; flex-direction:column; gap:6px;
  color:#fff; overflow:hidden; margin-top:6px;
}
.render-thumb-title { font-size:12.5px; font-weight:800; }
.render-thumb-body { font-size:10px; line-height:1.55; opacity:.85; white-space:pre-line; overflow:hidden; }
.render-meta { font-size:10.5px; color:var(--pptx-muted); font-weight:700; margin-top:6px; }

.issue-legend { display:flex; flex-direction:column; gap:2px; }
.src-settings-note {
  font-size:11px; color:var(--pptx-muted); line-height:1.5;
  border-top:1px dashed var(--pptx-s1-border); padding-top:10px; margin-top:6px;
}

.p-k { font-size:10.5px; color:var(--pptx-muted); font-weight:700; }
.p-v { font-size:12px; font-weight:700; color:var(--pptx-s1-text-main); margin-top:2px; margin-bottom:4px; }

/* ── 소스 선택: 왼쪽 레일(4모드). Streamlit이 key= 위젯에 자동으로 붙이는
   .st-key-<KEY> 클래스로 스코프 (marker+:has() 조상매칭은 여러 중첩 레벨이
   동시에 만족돼 다른 라디오 그룹과 색이 섞이는 버그가 있어 폐기). ── */
.st-key-pptx_source_mode_v2 div[data-testid="stRadio"] > div[role="radiogroup"] {
  display:flex !important; flex-direction:column !important; gap:8px !important;
}
.st-key-pptx_source_mode_v2 div[data-testid="stRadio"] label {
  border:1px solid var(--pptx-s1-border) !important; border-radius:10px !important;
  padding:9px 11px !important; background:#fff !important; width:100% !important;
  transition:background .15s ease, border-color .15s ease;
}
.st-key-pptx_source_mode_v2 div[data-testid="stRadio"] label p {
  font-size:13.5px !important; font-weight:650 !important; color:var(--pptx-s1-text-main) !important;
}
.st-key-pptx_source_mode_v2 div[data-testid="stRadio"] label:nth-of-type(1) { border-left:3px solid var(--pptx-ch-1) !important; }
.st-key-pptx_source_mode_v2 div[data-testid="stRadio"] label:nth-of-type(2) { border-left:3px solid var(--pptx-ch-6) !important; }
.st-key-pptx_source_mode_v2 div[data-testid="stRadio"] label:nth-of-type(3) { border-left:3px solid var(--pptx-ch-4) !important; }
.st-key-pptx_source_mode_v2 div[data-testid="stRadio"] label:nth-of-type(4) { border-left:3px solid var(--pptx-ch-3) !important; }
.st-key-pptx_source_mode_v2 div[data-testid="stRadio"] label:nth-of-type(1):has(input:checked) { background:#eff6ff !important; border-color:var(--pptx-ch-1) !important; }
.st-key-pptx_source_mode_v2 div[data-testid="stRadio"] label:nth-of-type(2):has(input:checked) { background:#ecfeff !important; border-color:var(--pptx-ch-6) !important; }
.st-key-pptx_source_mode_v2 div[data-testid="stRadio"] label:nth-of-type(3):has(input:checked) { background:#fffbeb !important; border-color:var(--pptx-ch-4) !important; }
.st-key-pptx_source_mode_v2 div[data-testid="stRadio"] label:nth-of-type(4):has(input:checked) { background:#eef2ff !important; border-color:var(--pptx-ch-3) !important; }

/* ── doc-pick 2단 (archive/docs) ── */
.doc-list-wrap [data-testid="stVerticalBlockBorderWrapper"] { border:none !important; }
.doc-item-btn button {
  width:100% !important; text-align:left !important; justify-content:flex-start !important;
  border:1px solid var(--pptx-s1-border) !important; border-radius:9px !important; background:#fff !important;
  padding:8px 11px !important; font-size:12.5px !important; font-weight:600 !important; margin-bottom:6px !important;
}
.doc-item-btn.sel button { border-color:var(--hue) !important; background:var(--tint) !important; }
.doc-preview {
  border:1px solid var(--pptx-s1-border); border-radius:10px; background:#fbfcfe; padding:11px 13px;
  display:flex; flex-direction:column; min-width:0; height:230px; overflow:hidden;
}
.doc-preview .dp-head { display:flex; align-items:center; gap:8px; margin-bottom:8px; }
.doc-preview .dp-name { font-size:12.5px; font-weight:750; color:var(--pptx-s1-text-main); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.doc-preview .dp-badge { margin-left:auto; font-size:10.5px; font-weight:800; color:var(--hue); background:var(--tint); border-radius:999px; padding:2px 9px; flex:0 0 auto; }
.doc-preview .dp-body { font-family:ui-monospace,"SF Mono",monospace; font-size:11px; color:var(--pptx-s1-text-sub); line-height:1.55; white-space:pre-wrap; flex:1 1 auto; overflow:hidden; }
.doc-preview .dp-foot { margin-top:9px; padding-top:8px; border-top:1px solid var(--pptx-s1-border); font-size:11px; color:var(--pptx-muted); display:flex; align-items:center; gap:6px; }
.doc-preview .dp-foot b { color:var(--pptx-ch-6); font-weight:800; }

div[data-testid="stButton"] > button { min-height:36px; border-radius:10px; }
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
    return [n for n in names
            if not any(k in n.lower() for k in ("bge-m3", "nomic-embed", "embed"))]


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
                title = doc_dir.name
                manifest = doc_dir / "manifest.json"
                if manifest.exists():
                    try:
                        import json
                        m = json.loads(manifest.read_text(encoding="utf-8"))
                        title = m.get("title") or doc_dir.name
                    except Exception:
                        pass
                items.append((title, content))
    return items


def _list_docs_md() -> list[tuple[str, Path]]:
    """/0Dev/docs/system/*.md 목록."""
    docs_dir = Path("/Users/iris/Documents/0Dev/docs/system")
    if not docs_dir.exists():
        return []
    items: list[tuple[str, Path]] = []
    for p in sorted(docs_dir.glob("*.md"), reverse=True):
        items.append((p.stem, p))
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


# ─── 소스 모드 메타 (레일 아이콘·색·실시간 카운트 라벨) ─────────────────────
_SOURCE_MODES = ["✍️ 직접 입력", "📂 파일 업로드", "📦 archive 자료", "📄 docs/system"]


def _rail_label(mode: str, *, md_chars: int, upload_name: str | None,
               archive_n: int, docs_n: int) -> str:
    if mode.startswith("✍️"):
        return f"✍️ 직접 입력 · {md_chars:,}자" if md_chars else "✍️ 직접 입력 · 0자"
    if mode.startswith("📂"):
        return f"📂 파일 업로드 · {upload_name}" if upload_name else "📂 파일 업로드 · 미선택"
    if mode.startswith("📦"):
        return f"📦 archive 자료 · {archive_n}건"
    return f"📄 docs/system · {docs_n}건"


# ─── 소스 선택: 왼쪽 레일 + 오른쪽 정보 영역(ㅏ자) ───────────────────────
def _render_doc_picker(items: list[tuple[str, Path]], *, kind: str, hue: str, tint: str,
                       key_prefix: str) -> tuple[str, str]:
    """archive/docs 공통: 왼쪽 검색+스크롤 리스트, 오른쪽 프리뷰. (md_text, source_label) 반환."""
    md_text = ""
    source_label = ""
    if not items:
        st.info(f"{kind}에 자료 없음.")
        return md_text, source_label

    # 식별자는 경로 문자열(고유) 사용 — title은 표시 전용. 같은 title이 서로
    # 다른 날짜 폴더에 중복 존재할 수 있어(예: README가 여러 archive에 존재)
    # title을 키/식별자로 쓰면 StreamlitDuplicateElementKey 충돌·오선택이 남.
    by_path = {str(p): (t, p) for t, p in items}
    pick_key = f"{key_prefix}_picked"
    query_key = f"{key_prefix}_query"
    if pick_key not in st.session_state or st.session_state[pick_key] not in by_path:
        st.session_state[pick_key] = str(items[0][1])

    col_list, col_prev = st.columns([1.05, 1], gap="small")
    with col_list:
        query = st.text_input(
            f"🔍 {kind} 검색 ({len(items)}건)", key=query_key,
            label_visibility="collapsed", placeholder=f"🔍 {kind} 검색 ({len(items)}건)",
        )
        filtered = [it for it in items if query.lower() in it[0].lower()] if query else items
        st.markdown("<div class='doc-list-wrap'>", unsafe_allow_html=True)
        with st.container(height=165):
            for i, (title, path) in enumerate(filtered[:60]):
                path_key = str(path)
                sel = st.session_state[pick_key] == path_key
                st.markdown(f"<div class='doc-item-btn{' sel' if sel else ''}' style='--hue:{hue}; --tint:{tint}'>",
                            unsafe_allow_html=True)
                if st.button(("✓ " if sel else "") + title, key=f"{key_prefix}_btn_{i}_{path_key}",
                             use_container_width=True):
                    st.session_state[pick_key] = path_key
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    picked_title, picked_path = by_path.get(st.session_state[pick_key], items[0])
    try:
        md_text = picked_path.read_text(encoding="utf-8")
        source_label = f"{kind}: {picked_title}"
        _sync_deck_meta_from_source(source_key=f"{key_prefix}:{picked_path}", doc_title=picked_title)
    except Exception as e:
        st.error(f"❌ 파일 읽기 실패: {e}")

    with col_prev:
        preview = _esc(md_text[:400]) + ("…" if len(md_text) > 400 else "")
        st.markdown(
            f"""<div class="doc-preview" style="--hue:{hue}; --tint:{tint}">
              <div class="dp-head"><span class="dp-name">{_esc(picked_title)}</span>
              <span class="dp-badge">{len(md_text):,}자</span></div>
              <div class="dp-body">{preview}</div>
              <div class="dp-foot">→ <b>② 확장으로 {len(md_text):,}자 전달</b></div>
            </div>""",
            unsafe_allow_html=True,
        )
    return md_text, source_label


# ─── 세션 상태 초기화 ────────────────────────────────────────────────────
def _init_wizard_state() -> None:
    st.session_state.setdefault("pptx_wizard_step", 0)
    st.session_state.setdefault("pptx_lang", "한국어")
    st.session_state.setdefault("pptx_page_count", "자동 (LLM 판단)")
    st.session_state.setdefault("pptx_template", "iris (다크)")
    st.session_state.setdefault("pptx_master_style", {
        "title_font": "Pretendard", "title_size": "32pt", "title_color": "#f8fafc",
        "pageno_pos": "우측 하단", "logo_fixed": False,
    })
    st.session_state.setdefault("pptx_issue_types", {"글자 겹침 오류"})
    st.session_state.setdefault("pptx_selected_pages", set())
    st.session_state.setdefault("pptx_output_format", "PDF")
    st.session_state.setdefault("pptx_density", "보통")
    st.session_state.setdefault("pptx_pageno_on", True)
    st.session_state.setdefault("pptx_save_disk", False)
    st.session_state.setdefault("pptx_use_other_llm_design", False)
    st.session_state.setdefault("pptx_design_model_override", None)


def _current_meta() -> dict:
    return {
        "company": st.session_state.get("pptx_deck_company", _DEFAULT_DECK_COMPANY),
        "title": st.session_state.get("pptx_deck_title", ""),
        "subtitle": st.session_state.get("pptx_deck_subtitle", ""),
        "date": st.session_state.get("pptx_deck_date", ""),
        "lang": st.session_state.get("pptx_lang", "한국어"),
    }


def _target_slides_from_page_count() -> int | None:
    pc = st.session_state.get("pptx_page_count", "자동 (LLM 판단)")
    if pc.startswith("자동"):
        return None
    try:
        return int(pc.replace("장", "").strip())
    except ValueError:
        return None


# ─── 스텝퍼 ──────────────────────────────────────────────────────────────
_STEP_LABELS = ["① 소스", "② 확장", "③ 설계", "④ 렌더"]
_STEP_HUES = ["var(--pptx-ch-1)", "var(--pptx-ch-3)", "var(--pptx-ch-4)", "var(--pptx-ch-6)"]


def _step_sub_labels() -> list[str]:
    md_text = st.session_state.get("pptx_md", _SAMPLE_MD)
    src_len = len(md_text)
    expand_result = st.session_state.get("pptx_expand_result")
    deck = st.session_state.get("pptx_deck")
    render_result = st.session_state.get("pptx_render_result")
    return [
        f"직접 입력 · {src_len:,}자" if src_len else "미선택",
        f"{expand_result['model']} · 완료" if expand_result else "대기 중",
        (f"{st.session_state.get('pptx_template', 'iris (다크)')} · "
         f"{st.session_state.get('pptx_output_format', 'PDF')}") if deck else "대기 중",
        f"{render_result['fmt']} 완료" if render_result else "대기 중",
    ]


def _render_stepper(step: int) -> None:
    subs = _step_sub_labels()
    css_parts = []
    for i in range(4):
        hue = _STEP_HUES[i]
        # 선택자 특이도(specificity) 주의: 위 static 규칙
        # `.st-key-pptx_stepper_box [data-testid="stButton"] button`은
        # 클래스/속성 2개 + 태그 1개(0,2,1) — 여기서 `.st-key-pptx_step_btn_N button`만
        # 쓰면(0,1,1) 특이도가 낮아 static 규칙에 밀려 활성 단계 강조색이 통째로
        # 무효화된다(실사용 스크린샷에서 스텝퍼가 항상 "무채색"으로 보이던 원인).
        # `[data-testid="stButton"]`까지 포함해 static 규칙과 같은 형태로 맞춰
        # 특이도를 동일 이상으로 올린다.
        sel = f".st-key-pptx_stepper_box .st-key-pptx_step_btn_{i} [data-testid=\"stButton\"] button"
        if i == step:
            css_parts.append(
                f"{sel} {{ background:#fafbfd !important; "
                f"border-bottom:3px solid {hue} !important; color:{hue} !important; }}"
            )
        elif i < step:
            css_parts.append(
                f"{sel} {{ color:var(--pptx-s1-text-main) !important; }}"
            )
        else:
            css_parts.append(
                f"{sel} {{ color:var(--pptx-muted) !important; }}"
            )
    st.markdown("<style>" + "\n".join(css_parts) + "</style>", unsafe_allow_html=True)

    with st.container(border=True, key="pptx_stepper_box"):
        cols = st.columns(4)
        for i, (lab, sub) in enumerate(zip(_STEP_LABELS, subs)):
            with cols[i]:
                mark = "✓ " if i < step else ""
                if st.button(f"{mark}{lab}", key=f"pptx_step_btn_{i}", use_container_width=True):
                    st.session_state["pptx_wizard_step"] = i
                    st.rerun()
                st.caption(sub)


def _render_progress_strip(step: int) -> None:
    subs = _step_sub_labels()
    with st.container(border=True, key="pptx_progress_box"):
        cols = st.columns(4)
        for i in range(4):
            with cols[i]:
                muted = "color:#b8c0cc;font-weight:500;" if i > step else ""
                st.markdown(
                    f"<div class='p-k'>{_STEP_LABELS[i]}</div>"
                    f"<div class='p-v' style='{muted}'>{_esc(subs[i])}</div>",
                    unsafe_allow_html=True,
                )
                if i < 3:
                    if st.button("편집", key=f"pptx_progress_edit_{i}"):
                        st.session_state["pptx_wizard_step"] = i
                        st.rerun()


# ─── 우측 사이드 (①②③=생성 설정, ④=문제 유형) ──────────────────────────
def _render_side(step: int) -> None:
    if step == 3:
        st.markdown("<h4 style='font-size:12px;font-weight:800;color:var(--pptx-muted);"
                    "text-transform:uppercase;letter-spacing:.03em;margin:0 0 10px'>문제 유형</h4>",
                    unsafe_allow_html=True)
        issues: set[str] = st.session_state.setdefault("pptx_issue_types", {"글자 겹침 오류"})
        options = ["언어 선택 오류", "내용 밀도 오류", "글자 겹침 오류", "페이지 형식 오류"]
        for opt in options:
            checked = st.checkbox(opt, value=opt in issues, key=f"pptx_issue_{opt}")
            if checked:
                issues.add(opt)
            else:
                issues.discard(opt)
        st.session_state["pptx_issue_types"] = issues
        st.markdown(
            "<div class='src-settings-note'>왼쪽에서 선택한 페이지에 표시된 문제만 골라 "
            "그 부분에 집중해서 다시 생성합니다.</div>", unsafe_allow_html=True,
        )
        return

    st.markdown("<h4 style='font-size:12px;font-weight:800;color:var(--pptx-muted);"
                "text-transform:uppercase;letter-spacing:.03em;margin:0 0 10px'>생성 설정</h4>",
                unsafe_allow_html=True)
    lang_opts = ["한국어", "English", "중국어"]
    cur_lang = st.session_state.get("pptx_lang", "한국어")
    st.session_state["pptx_lang"] = st.selectbox(
        "언어", lang_opts, index=lang_opts.index(cur_lang) if cur_lang in lang_opts else 0,
        key="pptx_lang_sel",
    )
    pc_opts = ["자동 (LLM 판단)", "5장", "10장", "15장"]
    cur_pc = st.session_state.get("pptx_page_count", "자동 (LLM 판단)")
    st.session_state["pptx_page_count"] = st.selectbox(
        "페이지 수", pc_opts, index=pc_opts.index(cur_pc) if cur_pc in pc_opts else 0,
        key="pptx_page_count_sel",
    )

    from src.config import IRIS_LLM_DEEP
    installed = _ollama_models()
    if not installed:
        st.warning("⚠️ Ollama에 모델 0개 또는 미가동")
    else:
        default_idx = 0
        for i, n in enumerate(installed):
            if n == IRIS_LLM_DEEP or n.startswith(IRIS_LLM_DEEP + ":"):
                default_idx = i
                break
        cur_model = st.session_state.get("pptx_model")
        idx = installed.index(cur_model) if cur_model in installed else default_idx
        st.session_state["pptx_model"] = st.selectbox(
            f"LLM 모델 ({len(installed)}개 설치)", installed, index=idx, key="pptx_model_sel",
        )
    st.markdown(
        "<div class='src-settings-note'>여기서 정한 값이 ②확장의 LLM 변환에 그대로 적용됩니다.</div>",
        unsafe_allow_html=True,
    )


# ─── ① 소스 ──────────────────────────────────────────────────────────────
def _step_source(archive_items: list[tuple[str, Path]], docs_items: list[tuple[str, Path]]) -> tuple[str, str]:
    st.markdown("<h3 style='font-size:14px;font-weight:800;margin:0 0 14px;"
                "color:var(--pptx-s1-text-main)'>① 소스 선택</h3>", unsafe_allow_html=True)
    st.markdown(
        "<div class='expand-note'>PPT로 만들 원본을 고릅니다. 직접 입력하거나, 파일을 올리거나, "
        "archive · docs/system에 이미 있는 자료를 골라도 됩니다. 오른쪽에서 정한 언어 · 페이지 수 · "
        "모델이 다음 단계 LLM 변환에 그대로 쓰입니다.</div>", unsafe_allow_html=True,
    )

    rail_col, body_col = st.columns([176, 600])
    upload_name = st.session_state.get("pptx_upload_name")

    def _fmt(m: str) -> str:
        return _rail_label(m, md_chars=len(st.session_state.get("pptx_md", _SAMPLE_MD)),
                           upload_name=upload_name, archive_n=len(archive_items), docs_n=len(docs_items))

    with rail_col, st.container(key="pptx_rail_col"):
        source_mode = st.radio(
            "마크다운 소스", options=_SOURCE_MODES, format_func=_fmt,
            key="pptx_source_mode_v2", label_visibility="collapsed",
        )

    md_text = ""
    source_label = ""

    with body_col:
        if source_mode.startswith("✍️"):
            md_text = st.text_area(
                "마크다운 입력",
                value=st.session_state.get("pptx_md", _SAMPLE_MD),
                key="pptx_md_input", height=280,
                help="원본 텍스트를 그대로 붙여넣으세요. 표·인용·리스트 모두 다음 단계에서 활용됩니다.",
                label_visibility="collapsed",
            )
            st.session_state["pptx_md"] = md_text
            source_label = "직접 입력"

        elif source_mode.startswith("📂"):
            uploaded = st.file_uploader(
                ".md 파일 선택", type=["md", "markdown", "txt"], key="pptx_upload",
                help="마크다운 1개 파일. UTF-8 인코딩 권장.",
            )
            if uploaded:
                try:
                    md_text = uploaded.read().decode("utf-8")
                    source_label = f"파일: {uploaded.name}"
                    st.session_state["pptx_upload_name"] = uploaded.name
                    st.session_state["pptx_md"] = md_text
                    _sync_deck_meta_from_source(
                        source_key=f"upload:{uploaded.name}",
                        doc_title=_doc_title_from_upload(uploaded.name),
                    )
                    st.caption(f"✅ {uploaded.name} · {len(md_text):,} chars")
                except Exception as e:
                    st.error(f"❌ 파일 읽기 실패: {e}")

        elif source_mode.startswith("📦"):
            md_text, source_label = _render_doc_picker(
                archive_items, kind="archive 자료", hue="var(--pptx-ch-4)", tint="#fffbeb",
                key_prefix="pptx_archive",
            )
            if md_text:
                st.session_state["pptx_md"] = md_text

        elif source_mode.startswith("📄"):
            md_text, source_label = _render_doc_picker(
                docs_items, kind="docs/system", hue="var(--pptx-ch-3)", tint="#eef2ff",
                key_prefix="pptx_docs",
            )
            if md_text:
                st.session_state["pptx_md"] = md_text

    st.session_state["pptx_source_label"] = source_label
    return md_text, source_label


# ─── ② 확장 · LLM 변환 ──────────────────────────────────────────────────
def _run_expand(md_text: str, meta: dict, model: str | None) -> None:
    from src.engine.output.deck import expander
    try:
        with st.spinner("① LLM 입력 확장 중… (30~180초, 모델·입력 크기 따라)"):
            er = expander.expand_for_slides(
                md_text, meta, model=model, timeout=900,
                lang=st.session_state.get("pptx_lang", "한국어"),
            )
        st.session_state["pptx_expand_result"] = {
            "md": er.md, "elapsed": er.elapsed_ms / 1000, "model": er.model,
            "in": er.original_chars, "out": er.output_chars,
        }
        # 소스가 바뀐 뒤 재확장이면 하위 단계 캐시 무효화
        st.session_state["pptx_deck"] = None
        st.session_state["pptx_design_meta"] = None
        st.session_state["pptx_render_result"] = None
    except expander.ExpansionError as e:
        st.error(f"❌ 확장 실패: {e}")


def _step_expand(md_text: str) -> None:
    st.markdown("<h3 style='font-size:14px;font-weight:800;margin:0 0 14px;"
                "color:var(--pptx-s1-text-main)'>② 확장 · LLM 변환</h3>", unsafe_allow_html=True)
    st.markdown(
        "<div class='expand-note'>①에서 정한 언어 · 페이지 수 · 모델로 LLM이 소스를 읽고, "
        "슬라이드용으로 더 풍부하게 재구조화한 마크다운을 생성합니다. 이 결과가 ③설계 단계의 입력이 됩니다.</div>",
        unsafe_allow_html=True,
    )

    if not md_text.strip():
        st.info("①소스에서 원본을 먼저 고르세요.")
        return

    result = st.session_state.get("pptx_expand_result")
    meta = _current_meta()
    model = st.session_state.get("pptx_model")

    row1, row2 = st.columns([4, 1])
    with row1:
        if result:
            st.markdown(
                f"<div class='llm-status'><span class='dot done'></span>"
                f"{_esc(result['model'])} · 변환 완료 · {result['elapsed']:.1f}초 · "
                f"소스 {result['in']:,}자 → {result['out']:,}자</div>", unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div class='llm-status'><span class='dot' style='background:#f59e0b'></span>"
                "아직 확장되지 않음</div>", unsafe_allow_html=True,
            )
    with row2:
        btn_label = "🔁 재생성" if result else "▶ 확장 시작"
        if st.button(btn_label, key="pptx_expand_run_btn", use_container_width=True):
            _run_expand(md_text, meta, model)
            st.rerun()

    if result:
        st.markdown("<div class='expand-sub'>출력 · LLM이 생성한 슬라이드용 마크다운 (③설계 입력)</div>",
                    unsafe_allow_html=True)
        preview = result["md"][:4000] + ("…" if len(result["md"]) > 4000 else "")
        st.markdown(f"<div class='expand-box accent'>{_esc(preview)}</div>", unsafe_allow_html=True)


# ─── ③ 설계 ──────────────────────────────────────────────────────────────
_TEMPLATES = [("iris (다크)", "#111827"), ("iris (라이트)", "#f3f4f6"), ("미니멀", "#e5e7eb")]


def _run_design(effective_md: str, meta: dict, model: str | None, *,
                pre_expanded: bool, target_slides: int | None) -> None:
    from src.engine.output.deck import designer
    try:
        with st.spinner(f"② LLM 슬라이드 설계 중… (30~300초, model: {model or 'default'})"):
            t0 = _dt.datetime.now()
            deck = designer.design_deck(
                effective_md, meta, model=model, timeout=600,
                pre_expanded=pre_expanded, target_slides=target_slides,
            )
            elapsed = (_dt.datetime.now() - t0).total_seconds()
        st.session_state["pptx_deck"] = deck
        st.session_state["pptx_design_meta"] = {
            "elapsed": elapsed, "model": model or "default", "n": len(deck.slides),
        }
        st.session_state["pptx_render_result"] = None
        st.session_state["pptx_selected_pages"] = set(range(1, len(deck.slides) + 1))
    except designer.DesignError as e:
        st.error(f"❌ 설계 실패: {e}")


def _step_design() -> None:
    st.markdown("<h3 style='font-size:14px;font-weight:800;margin:0 0 14px;"
                "color:var(--pptx-s1-text-main)'>③ 변환 설정</h3>", unsafe_allow_html=True)
    st.markdown(
        "<div class='expand-note'>②에서 나온 마크다운을 슬라이드로 렌더링합니다. 페이지별 내용에 맞는 "
        "레이아웃을 LLM이 골라 템플릿에 맞춰 그려냅니다.</div>", unsafe_allow_html=True,
    )

    # ── 템플릿 갤러리 ──
    st.markdown("<div class='tpl-section'><label>템플릿</label></div>", unsafe_allow_html=True)
    imp_col1, imp_col2 = st.columns([5, 1])
    with imp_col1:
        st.text_input(
            "템플릿 가져오기", key="pptx_tpl_import_query",
            placeholder="URL 또는 검색어로 템플릿 가져오기 (예: notion, 컨설팅 제안서 다크)",
            label_visibility="collapsed",
        )
    with imp_col2:
        if st.button("가져오기", key="pptx_tpl_import_btn", use_container_width=True):
            st.toast("준비 중입니다")

    tpl_cols = st.columns(len(_TEMPLATES))
    for i, (name, color) in enumerate(_TEMPLATES):
        with tpl_cols[i]:
            st.markdown(f"<div class='tpl-thumb' style='background:{color}'></div>", unsafe_allow_html=True)
            sel = st.session_state.get("pptx_template") == name
            if st.button(("✓ " if sel else "") + name, key=f"pptx_tpl_btn_{i}", use_container_width=True):
                st.session_state["pptx_template"] = name
                st.rerun()
            st.markdown(f"<div class='tpl-name'>{_esc(name)}</div>", unsafe_allow_html=True)

    # ── 마스터 스타일 ──
    st.markdown(
        "<div class='master-section-label'>마스터 스타일 <span class='hint'>— 모든 페이지에 고정 적용, "
        "템플릿을 바꿔도 여기서 손댄 값은 유지됩니다</span></div>", unsafe_allow_html=True,
    )
    ms = st.session_state["pptx_master_style"]
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        fonts = ["Pretendard", "SUIT", "Noto Sans KR"]
        ms["title_font"] = st.selectbox(
            "제목 폰트", fonts, index=fonts.index(ms.get("title_font", "Pretendard")),
            key="pptx_master_font",
        )
    with fc2:
        sizes = ["32pt", "28pt", "24pt"]
        ms["title_size"] = st.selectbox(
            "제목 크기", sizes, index=sizes.index(ms.get("title_size", "32pt")),
            key="pptx_master_size",
        )
    with fc3:
        color_opts = [("#f8fafc", "화이트"), ("#3b82f6", "블루"), ("#f59e0b", "오렌지")]
        labels = [lab for _, lab in color_opts]
        cur_label = next((lab for c, lab in color_opts if c == ms.get("title_color")), labels[0])
        picked = st.selectbox("제목 색상", labels, index=labels.index(cur_label), key="pptx_master_color")
        ms["title_color"] = dict((lab, c) for c, lab in color_opts)[picked]

    mc1, mc2 = st.columns(2)
    with mc1:
        positions = ["우측 하단", "좌측 하단", "중앙 하단"]
        ms["pageno_pos"] = st.selectbox(
            "페이지 번호 위치", positions, index=positions.index(ms.get("pageno_pos", "우측 하단")),
            key="pptx_master_pageno_pos",
        )
    with mc2:
        ms["logo_fixed"] = st.checkbox("로고 고정 표시", value=ms.get("logo_fixed", False), key="pptx_master_logo")
    st.session_state["pptx_master_style"] = ms

    # ── 컴팩트 설정 행 ──
    cr1, cr2, cr3, cr4, cr5 = st.columns(5)
    with cr1:
        fmt_opts = ["PDF", "PPTX"]
        cur_fmt = st.session_state.get("pptx_output_format", "PDF")
        st.session_state["pptx_output_format"] = st.selectbox(
            "출력 형식", fmt_opts, index=fmt_opts.index(cur_fmt) if cur_fmt in fmt_opts else 0,
            key="pptx_output_format_sel",
        )
    with cr2:
        density_opts = ["보통", "여유 (텍스트 적게)", "빽빽 (텍스트 많이)"]
        cur_density = st.session_state.get("pptx_density", "보통")
        st.session_state["pptx_density"] = st.selectbox(
            "레이아웃 밀도", density_opts,
            index=density_opts.index(cur_density) if cur_density in density_opts else 0,
            key="pptx_density_sel",
        )
    with cr3:
        st.session_state["pptx_pageno_on"] = st.checkbox(
            "페이지 번호", value=st.session_state.get("pptx_pageno_on", True), key="pptx_pageno_chk",
        )
    with cr4:
        st.session_state["pptx_save_disk"] = st.checkbox(
            "exports 저장", value=st.session_state.get("pptx_save_disk", False), key="pptx_save_disk_chk",
        )
    with cr5:
        st.session_state["pptx_use_other_llm_design"] = st.checkbox(
            "설계에서 다른 LLM", value=st.session_state.get("pptx_use_other_llm_design", False),
            key="pptx_other_llm_chk",
        )
        if st.session_state["pptx_use_other_llm_design"]:
            installed = _ollama_models()
            if installed:
                st.session_state["pptx_design_model_override"] = st.selectbox(
                    "설계용 모델", installed, key="pptx_design_model_sel",
                )

    # ── 설계 실행 ──
    st.markdown("<hr style='margin:14px 0;border:none;border-top:1px dashed var(--pptx-s1-border)'>",
               unsafe_allow_html=True)
    expand_result = st.session_state.get("pptx_expand_result")
    md_text = st.session_state.get("pptx_md", "")
    effective_md = expand_result["md"] if expand_result else md_text
    pre_expanded = bool(expand_result)
    deck = st.session_state.get("pptx_deck")
    design_meta = st.session_state.get("pptx_design_meta")

    dcol1, dcol2 = st.columns([4, 1])
    with dcol1:
        if design_meta:
            st.markdown(
                f"<div class='llm-status'><span class='dot done'></span>"
                f"{_esc(design_meta['model'])} · 설계 완료 · {design_meta['elapsed']:.1f}초 · "
                f"{design_meta['n']}장</div>", unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div class='llm-status'><span class='dot' style='background:#f59e0b'></span>"
                "아직 설계되지 않음</div>", unsafe_allow_html=True,
            )
    with dcol2:
        btn_label = "🔁 재설계" if deck else "🎨 설계 실행"
        if st.button(btn_label, key="pptx_design_run_btn", disabled=not effective_md.strip(),
                     use_container_width=True):
            model = (st.session_state.get("pptx_design_model_override")
                    if st.session_state.get("pptx_use_other_llm_design")
                    else st.session_state.get("pptx_model"))
            _run_design(effective_md, _current_meta(), model,
                       pre_expanded=pre_expanded, target_slides=_target_slides_from_page_count())
            st.rerun()


# ─── ④ 렌더 · 결과 리뷰 ──────────────────────────────────────────────────
def _run_render(deck, output_format: str, save_disk: bool) -> None:
    fmt_label = "PDF" if output_format == "PDF" else "PPTX"
    try:
        with st.spinner(f"③ {fmt_label} 렌더 중… (슬라이드당 ~2초)"):
            t0 = _dt.datetime.now()
            if fmt_label == "PDF":
                from src.engine.output.deck.renderer import render_deck_to_pdf
                out_path = render_deck_to_pdf(deck)
                ext, mime = "pdf", "application/pdf"
            else:
                from src.engine.output.deck.pptx_export import render_deck_to_pptx
                out_path = render_deck_to_pptx(deck)
                ext = "pptx"
                mime = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            elapsed = (_dt.datetime.now() - t0).total_seconds()
        size_kb = out_path.stat().st_size / 1024
        result = {
            "out_path": str(out_path), "ext": ext, "mime": mime,
            "size_kb": size_kb, "elapsed": elapsed, "fmt": fmt_label,
        }
        if save_disk:
            saved = _save_to_exports(out_path, prefix="deck")
            result["saved_to"] = str(saved)
        st.session_state["pptx_render_result"] = result
    except Exception as e:
        st.error(f"❌ 렌더 실패: {type(e).__name__}: {e}")
        st.caption("playwright 미설치라면: `pip install playwright && playwright install chromium`")


def _step_render() -> None:
    deck = st.session_state.get("pptx_deck")
    render_result = st.session_state.get("pptx_render_result")

    st.markdown("<h3 style='font-size:14px;font-weight:800;margin:0 0 14px;"
                "color:var(--pptx-s1-text-main)'>④ 렌더 · 결과 리뷰</h3>", unsafe_allow_html=True)
    st.markdown(
        "<div class='expand-note'>생성된 페이지를 확인하고, 마음에 안 드는 페이지만 선택해서 "
        "다시 생성할 수 있습니다.</div>", unsafe_allow_html=True,
    )

    if not deck:
        st.info("아직 설계된 슬라이드가 없습니다. ③설계 단계에서 '설계 실행'을 먼저 눌러주세요.")
        return

    tpl = st.session_state.get("pptx_template", "iris (다크)")
    if render_result:
        st.markdown(
            f"<div class='render-status'><span class='dot'></span>"
            f"{render_result['fmt']} 생성 완료 · {len(deck.slides)}페이지 · {_esc(tpl)} 템플릿 · "
            f"{render_result['size_kb']:.1f}KB</div>", unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div class='render-status'><span class='dot' style='background:#f59e0b'></span>"
            "아직 렌더되지 않음 — 아래 '전체 재생성'을 눌러주세요.</div>", unsafe_allow_html=True,
        )

    selected: set[int] = st.session_state.setdefault(
        "pptx_selected_pages", set(range(1, len(deck.slides) + 1)),
    )
    cols = st.columns(3)
    for i, slide in enumerate(deck.slides, 1):
        title = str(slide.data.get("title", slide.data.get("company", slide.pattern)))[:40]
        body_bits = [str(v) for k, v in slide.data.items()
                    if isinstance(v, str) and k not in ("title", "subtitle") and v]
        body_preview = " · ".join(body_bits)[:90]
        col = cols[(i - 1) % 3]
        with col:
            checked = st.checkbox(f"{i}. {title}", value=i in selected, key=f"pptx_page_chk_{i}")
            if checked:
                selected.add(i)
            else:
                selected.discard(i)
            st.markdown(
                f"<div class='render-thumb' style='background:#111827'>"
                f"<div class='render-thumb-title'>{_esc(title)}</div>"
                f"<div class='render-thumb-body'>{_esc(body_preview)}</div></div>"
                f"<div class='render-meta'>page {i} · {_esc(slide.pattern)}</div>",
                unsafe_allow_html=True,
            )
    st.session_state["pptx_selected_pages"] = selected

    n_sel = len(selected)
    st.markdown(
        f"<div style='font-size:11.5px;color:var(--pptx-muted);font-weight:700;margin:14px 0 8px'>"
        f"{n_sel}개 페이지 선택됨</div>", unsafe_allow_html=True,
    )

    ac1, ac2, ac3 = st.columns(3)
    output_format = st.session_state.get("pptx_output_format", "PDF")
    save_disk = st.session_state.get("pptx_save_disk", False)
    with ac1:
        if st.button("🎯 표시한 문제로 재생성", key="pptx_regen_issues", use_container_width=True):
            # 이번 패스에서는 부분 재생성 대신 전체 재생성으로 동작 (계획서 확정 기본값).
            _run_render(deck, output_format, save_disk)
            st.rerun()
    with ac2:
        if st.button("🔁 전체 재생성", key="pptx_regen_all", use_container_width=True):
            _run_render(deck, output_format, save_disk)
            st.rerun()
    with ac3:
        if render_result:
            out_path = Path(render_result["out_path"])
            if out_path.exists():
                with out_path.open("rb") as f:
                    data = f.read()
                stamp = _dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
                st.download_button(
                    f"💾 {render_result['fmt']} 다운로드", data=data,
                    file_name=f"deck_{stamp}.{render_result['ext']}",
                    mime=render_result["mime"], use_container_width=True, key="pptx_download_btn",
                )
            else:
                st.caption("⚠️ 파일이 사라졌습니다 — 다시 생성해주세요.")
    if render_result and render_result.get("saved_to"):
        st.caption(f"📦 exports/ 저장: `{render_result['saved_to']}`")


# ─── 단계 전환 로직 (하단 이전/다음) ──────────────────────────────────────
def _advance_from(step: int) -> None:
    md_text = st.session_state.get("pptx_md", "")
    meta = _current_meta()
    model = st.session_state.get("pptx_model")

    if step == 0:
        st.session_state["pptx_wizard_step"] = 1

    elif step == 1:
        if not st.session_state.get("pptx_expand_result") and md_text.strip():
            _run_expand(md_text, meta, model)
        st.session_state["pptx_wizard_step"] = 2

    elif step == 2:
        expand_result = st.session_state.get("pptx_expand_result")
        effective_md = expand_result["md"] if expand_result else md_text
        pre_expanded = bool(expand_result)
        if not st.session_state.get("pptx_deck") and effective_md.strip():
            design_model = (st.session_state.get("pptx_design_model_override")
                            if st.session_state.get("pptx_use_other_llm_design")
                            else model)
            _run_design(effective_md, meta, design_model,
                       pre_expanded=pre_expanded, target_slides=_target_slides_from_page_count())
        deck = st.session_state.get("pptx_deck")
        if deck and not st.session_state.get("pptx_render_result"):
            _run_render(deck, st.session_state.get("pptx_output_format", "PDF"),
                       st.session_state.get("pptx_save_disk", False))
        st.session_state["pptx_wizard_step"] = 3

    else:
        deck = st.session_state.get("pptx_deck")
        if deck:
            _run_render(deck, st.session_state.get("pptx_output_format", "PDF"),
                       st.session_state.get("pptx_save_disk", False))

    st.rerun()


# ─── 메인 render() ───────────────────────────────────────────────────────
def render() -> None:
    st.markdown(_PPTX_CSS, unsafe_allow_html=True)
    hub_pagebar(
        "PPT",
        "Deck Console",
        "마크다운 소스를 선택하고 언어 · 페이지 수 · 템플릿을 정한 뒤 PPTX/PDF 산출물로 내보냅니다.",
        "Export Ready",
    )

    _init_wizard_state()
    _init_deck_meta_defaults()
    archive_items = _list_archive_content_md()
    docs_items = _list_docs_md()

    step = st.session_state["pptx_wizard_step"]
    _render_stepper(step)

    panel_col, side_col = st.columns([3, 1], gap="medium")

    with panel_col:
        with st.container(border=True, key="pptx_panel_box"):
            if step == 0:
                _step_source(archive_items, docs_items)
            elif step == 1:
                _step_expand(st.session_state.get("pptx_md", ""))
            elif step == 2:
                _step_design()
            else:
                _step_render()

    with side_col:
        with st.container(border=True, key="pptx_side_box"):
            _render_side(step)

    _render_progress_strip(step)

    next_labels = ["다음: 확장", "다음: 설계", "다음: 렌더", "PDF 생성"]
    _, act_col = st.columns([3, 1])
    with act_col:
        pc, nc = st.columns(2)
        with pc:
            if st.button("이전", key="pptx_prev_btn", disabled=(step == 0), use_container_width=True):
                st.session_state["pptx_wizard_step"] = max(0, step - 1)
                st.rerun()
        with nc:
            if st.button(next_labels[step], key="pptx_next_btn", type="primary", use_container_width=True):
                _advance_from(step)
