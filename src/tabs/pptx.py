"""탭: 📊 PPT — 마크다운 → PPTX 변환 (V2.8.3 — 진단툴 스타일+컬러 목업 이식).

V2.8.3: client/dev/diagnosistool_pptx_mock.html 목업을 실제 탭에 이식
  - 라이브 파이프라인 스트립(①소스→②확장→③설계→④렌더, 호버 상세)
  - 소스 선택: 왼쪽 세로 레일(4모드, 실시간 카운트) + 오른쪽 정보 영역(ㅏ자)
  - archive/docs: 드롭다운 대신 리스트+프리뷰 2단
  - 변환 설정: 공통(버튼식) + 디자인 상세(샘플/언어/컬러 NEW) 박스

V2.7.6.3: deck 탭 흡수 + 엔진 선택 + 모델 선택
V2.7.5.1: 입력 방식 3종 — 직접 입력 / 파일 업로드 / 디스크 .md 선택
"""
from __future__ import annotations

import datetime as _dt
from html import escape as _esc
from pathlib import Path

import streamlit as st

from src.ui_kit import hub_pagebar, hub_section


# ─── 디자인 토큰 (client/dev/diagnosistool_pptx_mock.html 이식, --pptx- 네임스페이스) ──
_PPTX_CSS = """
<style>
:root {
  --pptx-bg:#f4f7fb; --pptx-card:#ffffff; --pptx-text:#1f2a37; --pptx-muted:#6b7280;
  --pptx-line:#e5e7eb; --pptx-shadow:0 10px 30px rgba(15,23,42,0.08); --pptx-radius:16px;
  --pptx-s1-border:#eeeeee; --pptx-s1-text-main:#111827; --pptx-s1-text-sub:#6b7280;
  --pptx-ch-1:#3b82f6; --pptx-ch-2:#22c55e; --pptx-ch-3:#6366f1; --pptx-ch-4:#f59e0b;
  --pptx-ch-5:#ef4444; --pptx-ch-6:#06b6d4; --pptx-ch-7:#a855f7;
}

/* ── hub_ui.css가 전탭 공통으로 .block-container를 1180px로 캡핑 — 진단툴(별도
   standalone 앱)엔 이 캡이 없어 PC 화면에서 상대적으로 좁아 보임. 이 CSS는
   pptx.render() 안에서만 주입되므로 PPT 탭에 있을 때만 넓어지고, 다른 탭으로
   가면 이 <style>이 DOM에서 빠져 원래 1180px로 돌아감(다른 탭 무영향). ── */
.block-container {
  max-width: 1800px !important;
}
/* 소스 레일은 목업처럼 고정 폭 유지 — 페이지가 넓어져도 st.columns 비율대로
   같이 늘어나면 아이콘 행이 불필요하게 뚱뚱해짐. */
[data-testid="stColumn"]:has(> div .pptx-rail-anchor) {
  flex: 0 0 220px !important; max-width: 220px !important; min-width: 220px !important;
}

/* ── hub_pagebar을 진단툴 topbar 톤으로 (PPT 탭 전용, 다른 탭 무영향) ── */
.hub-pagebar {
  border-color: var(--pptx-line) !important;
  background: var(--pptx-card) !important;
  box-shadow: var(--pptx-shadow) !important;
}
.hub-pagebar-title { color: var(--pptx-text) !important; }

/* ── 라이브 파이프라인 스트립 ── */
.flow-strip {
  display:flex; align-items:stretch; gap:0;
  background:var(--pptx-card); border:1px solid var(--pptx-line); border-radius:12px;
  box-shadow:0 1px 2px rgba(15,23,42,0.04); overflow:visible; margin-bottom:6px;
}
.flow-seg { display:flex; align-items:center; gap:9px; padding:11px 14px; flex:1 1 0; min-width:0; position:relative; cursor:default; }
.flow-seg:first-child { border-radius:12px 0 0 12px; }
.flow-seg.active:last-child { border-radius:0 12px 12px 0; }
.flow-seg .ic { width:18px; height:18px; border-radius:50%; flex:0 0 auto; display:flex; align-items:center; justify-content:center; font-size:10px; font-weight:900; border:1.5px solid var(--hue); }
.flow-seg.done .ic { background:var(--hue); color:#fff; border-color:var(--hue); }
.flow-seg.done .ic::before { content:"✓"; }
.flow-seg.pending .ic { border-color:var(--pptx-s1-border); color:transparent; }
.flow-seg.active .ic { border-color:var(--hue); color:var(--hue); animation:pptx-spin .9s linear infinite; border-right-color:transparent; border-top-color:transparent; }
@keyframes pptx-spin { to { transform:rotate(360deg); } }
.flow-seg .lab { font-size:10.5px; font-weight:800; color:var(--hue); letter-spacing:.02em; flex:0 0 auto; }
.flow-seg.pending .lab { color:var(--pptx-muted); }
.flow-seg .val { font-size:12.5px; font-weight:650; color:var(--pptx-s1-text-main); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.flow-seg.pending .val { color:#b8c0cc; font-weight:500; }
.flow-seg .val .u { font-size:10.5px; color:var(--pptx-muted); font-weight:600; margin-left:3px; }
.flow-seg.active { background:var(--tint); }
.flow-seg .caret { margin-left:4px; color:#cbd5e1; font-size:9px; flex:0 0 auto; }
.flow-arrow { display:flex; align-items:center; color:#cbd5e1; font-size:12px; padding:0 2px; flex:0 0 auto; }
.flow-seg .detail {
  position:absolute; top:calc(100% + 8px); left:0; z-index:20; width:280px;
  background:#fff; border:1px solid var(--pptx-line); border-radius:12px;
  box-shadow:0 12px 32px rgba(15,23,42,0.14); padding:12px 13px;
  opacity:0; visibility:hidden; transform:translateY(-4px);
  transition:opacity .15s ease, transform .15s ease; pointer-events:none;
}
.flow-seg:hover .detail { opacity:1; visibility:visible; transform:translateY(0); }
.flow-seg .detail::before { content:""; position:absolute; top:-5px; left:20px; width:9px; height:9px; background:#fff; border-left:1px solid var(--pptx-line); border-top:1px solid var(--pptx-line); transform:rotate(45deg); }
.detail .d-head { display:flex; align-items:center; gap:7px; margin-bottom:8px; }
.detail .d-lab { font-size:10.5px; font-weight:800; color:var(--hue); }
.detail .d-meta { font-size:10.5px; color:var(--pptx-muted); margin-left:auto; }
.detail .d-stat { font-size:15px; font-weight:800; color:var(--pptx-s1-text-main); margin-bottom:8px; }
.detail .d-stat .u { font-size:11px; color:var(--pptx-muted); font-weight:600; margin-left:3px; }
.detail .d-list { display:flex; flex-direction:column; gap:4px; }
.detail .d-item { display:flex; align-items:center; gap:7px; font-size:11.5px; color:var(--pptx-s1-text-main); }
.detail .d-item .n { color:#b8c0cc; font-variant-numeric:tabular-nums; width:15px; flex:0 0 auto; }
.detail .d-item .pat { font-weight:700; color:var(--hue); flex:0 0 auto; }
.detail .d-item .tt { color:var(--pptx-s1-text-sub); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.detail .d-more { font-size:10.5px; color:var(--pptx-muted); margin-top:6px; }
.detail .d-code { margin-top:8px; padding:8px 9px; background:#f8fafc; border:1px solid var(--pptx-s1-border); border-radius:7px; font-family:ui-monospace,"SF Mono",monospace; font-size:10.5px; color:var(--pptx-s1-text-sub); line-height:1.5; white-space:pre-wrap; max-height:88px; overflow:hidden; }
.flow-progress { height:4px; border-radius:999px; background:#eef2f7; overflow:hidden; margin:8px 2px 4px; }
.flow-progress > span { display:block; height:100%; background:var(--pptx-ch-2); transition:width .4s ease; }
.flow-caption { font-size:11px; color:var(--pptx-muted); margin:0 2px 16px; display:flex; align-items:center; gap:6px; }
.flow-caption .live-dot { width:6px; height:6px; border-radius:50%; background:var(--pptx-ch-2); animation:pptx-blink 1s ease-in-out infinite; }
@keyframes pptx-blink { 50% { opacity:.3; } }

/* ── 섹션 타이틀 ── */
.pptx-section-title { font-size:13px; font-weight:800; color:var(--pptx-text); margin:20px 0 10px; display:flex; align-items:center; gap:8px; }
.pptx-section-title .dot { width:8px; height:8px; border-radius:50%; background:var(--pptx-ch-1); }

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

/* ── 엔진 선택 라디오도 같은 카드 톤 ── */
.st-key-pptx_engine div[data-testid="stRadio"] > div[role="radiogroup"] {
  display:flex !important; gap:10px !important;
}
.st-key-pptx_engine div[data-testid="stRadio"] label {
  border:1px solid var(--pptx-s1-border) !important; border-radius:10px !important;
  padding:11px 13px !important; background:#fff !important; flex:1 1 0 !important;
}
.st-key-pptx_engine div[data-testid="stRadio"] label:nth-of-type(1) { border-left:3px solid var(--pptx-ch-4) !important; }
.st-key-pptx_engine div[data-testid="stRadio"] label:nth-of-type(2) { border-left:3px solid var(--pptx-ch-5) !important; }
.st-key-pptx_engine div[data-testid="stRadio"] label:nth-of-type(1):has(input:checked) { background:#fffbeb !important; border-color:var(--pptx-ch-4) !important; }
.st-key-pptx_engine div[data-testid="stRadio"] label:nth-of-type(2):has(input:checked) { background:#fef2f2 !important; border-color:var(--pptx-ch-5) !important; }

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
.pptx-caption { font-size:12px; color:var(--pptx-muted); margin-bottom:10px; }
.pptx-caption strong { color:var(--pptx-s1-text-main); }

/* ── 변환 설정: 공통/디자인 상세 박스 — 이 Streamlit 버전은 st.container(border=True)의
   테두리를 별도 wrapper가 아니라 .st-key-<KEY>가 붙은 stVerticalBlock 자신에 그림
   (실측 확인: stVerticalBlockBorderWrapper testid 없음). ── */
.st-key-pptx_common_box {
  border-color: rgba(245,158,11,0.32) !important; border-radius:12px !important;
}
.st-key-pptx_design_box {
  border-color: rgba(239,68,68,0.32) !important; border-radius:12px !important; background:#fffafa !important;
}
.set-glabel { font-size:11px; font-weight:800; letter-spacing:.04em; text-transform:uppercase; color:var(--pptx-muted); margin-bottom:6px; display:flex; align-items:center; gap:7px; }
.set-glabel .g-dot { width:7px; height:7px; border-radius:50%; }
.new-tag { font-size:8.5px; font-weight:800; color:#b25e09; background:#fef3e2; border-radius:4px; padding:1px 5px; margin-left:6px; letter-spacing:.02em; }
.wire-note { font-size:11px; color:var(--pptx-muted); margin-top:6px; padding:8px 10px; border:1px dashed var(--pptx-s1-border); border-radius:10px; background:#fbfcfe; line-height:1.5; }

/* 디자인 샘플 썸네일 (st.pills로 실제 선택 가능, 카드는 프리뷰용 시각 장식) */
.sample-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin-bottom:6px; }
.sample-card { border:1px solid var(--pptx-s1-border); border-radius:10px; overflow:hidden; background:#fff; }
.sample-card.sel { border-color:var(--pptx-ch-5); box-shadow:0 0 0 1px rgba(239,68,68,0.35); }
.sample-thumb { height:44px; display:flex; flex-direction:column; padding:7px 8px; gap:4px; }
.sample-thumb .bar { height:5px; border-radius:2px; width:62%; }
.sample-thumb .row { display:flex; gap:4px; margin-top:auto; }
.sample-thumb .row i { flex:1; height:11px; border-radius:3px; display:block; }
.sample-name { padding:5px 8px; font-size:11px; font-weight:700; color:var(--pptx-s1-text-main); border-top:1px solid var(--pptx-s1-border); text-align:center; }

/* ── 공용 버튼식 세그먼트(st.pills) 스킨 ── */
.st-key-pptx_output_format_pills [data-baseweb="button-group"],
.st-key-pptx_paginate_pills [data-baseweb="button-group"],
.st-key-pptx_save_disk_pills [data-baseweb="button-group"],
.st-key-pptx_slide_target_pills [data-baseweb="button-group"],
.st-key-pptx_sample_pills [data-baseweb="button-group"],
.st-key-pptx_lang_pills [data-baseweb="button-group"],
.st-key-pptx_color_pills [data-baseweb="button-group"] {
  display:flex !important; gap:0 !important; width:100% !important; overflow:hidden !important;
  border-radius:10px !important; border:1px solid rgba(47,128,196,0.20) !important; background:#fff !important;
}
.st-key-pptx_output_format_pills [data-testid="stBaseButton-pills"],
.st-key-pptx_output_format_pills [data-testid="stBaseButton-pillsActive"],
.st-key-pptx_paginate_pills [data-testid="stBaseButton-pills"],
.st-key-pptx_paginate_pills [data-testid="stBaseButton-pillsActive"],
.st-key-pptx_save_disk_pills [data-testid="stBaseButton-pills"],
.st-key-pptx_save_disk_pills [data-testid="stBaseButton-pillsActive"],
.st-key-pptx_slide_target_pills [data-testid="stBaseButton-pills"],
.st-key-pptx_slide_target_pills [data-testid="stBaseButton-pillsActive"],
.st-key-pptx_sample_pills [data-testid="stBaseButton-pills"],
.st-key-pptx_sample_pills [data-testid="stBaseButton-pillsActive"],
.st-key-pptx_lang_pills [data-testid="stBaseButton-pills"],
.st-key-pptx_lang_pills [data-testid="stBaseButton-pillsActive"],
.st-key-pptx_color_pills [data-testid="stBaseButton-pills"],
.st-key-pptx_color_pills [data-testid="stBaseButton-pillsActive"] {
  flex:1 1 0 !important; border-radius:0 !important; border:0 !important; box-shadow:none !important;
  background:transparent !important; color:#6b7280 !important; font-weight:800 !important;
  padding:8px 10px !important; min-height:34px !important; height:100% !important;
}
.st-key-pptx_output_format_pills [data-testid="stBaseButton-pillsActive"] { background:rgba(37,99,235,0.14) !important; color:#2563eb !important; }
.st-key-pptx_paginate_pills [data-testid="stBaseButton-pillsActive"],
.st-key-pptx_save_disk_pills [data-testid="stBaseButton-pillsActive"] { background:rgba(34,197,94,0.14) !important; color:#15803d !important; }
.st-key-pptx_slide_target_pills [data-testid="stBaseButton-pillsActive"] { background:rgba(99,102,241,0.14) !important; color:#4f46e5 !important; }
.st-key-pptx_sample_pills [data-testid="stBaseButton-pillsActive"],
.st-key-pptx_lang_pills [data-testid="stBaseButton-pillsActive"],
.st-key-pptx_color_pills [data-testid="stBaseButton-pillsActive"] { background:rgba(239,68,68,0.14) !important; color:#dc2626 !important; }

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


def _current_markdown_length(source_mode: str, md_text: str) -> int:
    return len(md_text)


# ─── 라이브 파이프라인 스트립 ────────────────────────────────────────────
def _seg(lab: str, hue: str, tint: str, state: str, val: str, unit: str = "",
        detail: str | None = None) -> str:
    cls = f"flow-seg {state}"
    style = f"--hue:{hue}; --tint:{tint};"
    caret = "<span class='caret'>▼</span>" if detail else ""
    detail_html = f"<div class='detail'>{detail}</div>" if detail else ""
    unit_html = f"<span class='u'>{_esc(unit)}</span>" if unit else ""
    return (
        f"<div class='{cls}' style='{style}'>"
        f"<span class='ic'></span><span class='lab'>{_esc(lab)}</span>"
        f"<span class='val'>{_esc(val)}{unit_html}</span>{caret}{detail_html}"
        f"</div>"
    )


def _source_detail(source_label: str, md_text: str) -> str:
    snippet = _esc(md_text[:110]) + ("…" if len(md_text) > 110 else "")
    return (
        f"<div class='d-head'><span class='d-lab'>① 소스</span><span class='d-meta'>{_esc(source_label or '미선택')}</span></div>"
        f"<div class='d-stat'>{len(md_text):,}<span class='u'>chars</span></div>"
        f"<div class='d-code'>{snippet}</div>"
    )


def _render_strip(placeholder, *, engine_is_design: bool, source_label: str, md_text: str,
                  stage_expand: dict | None, stage_design: dict | None,
                  stage_render: dict | None, engine_label: str, export_fmt: str) -> None:
    """스트립을 placeholder에 그림. 여러 번 호출해 실시간 갱신 (같은 run 안에서도, rerun 이후에도)."""
    s1 = _seg("① 소스", "var(--pptx-ch-1)", "#eff6ff", "done" if md_text else "pending",
              source_label or "미선택", f"{len(md_text):,}자" if md_text else "",
              _source_detail(source_label, md_text) if md_text else None)

    if engine_is_design:
        if stage_expand:
            d2 = (f"<div class='d-head'><span class='d-lab'>② 입력 확장 · Stage 1</span>"
                  f"<span class='d-meta'>{stage_expand['elapsed']:.1f}s</span></div>"
                  f"<div class='d-stat'>{stage_expand['in']:,} → {stage_expand['out']:,}<span class='u'>자 · {stage_expand['out']/max(stage_expand['in'],1):.1f}×</span></div>"
                  f"<div class='d-code'>{_esc(stage_expand['preview'])}</div>"
                  f"<div class='d-more'>모델 {_esc(stage_expand['model'])}</div>")
            s2 = _seg("② 확장", "var(--pptx-ch-6)", "#ecfeff", "done",
                      f"{stage_expand['in']:,} → {stage_expand['out']:,}", "자", d2)
        else:
            s2 = _seg("② 확장", "var(--pptx-ch-6)", "#ecfeff", "pending", "대기")

        if stage_design:
            items_html = "".join(
                f"<div class='d-item'><span class='n'>{i}</span><span class='pat'>{_esc(p)}</span><span class='tt'>{_esc(t)}</span></div>"
                for i, p, t in stage_design["items"][:5]
            )
            more = len(stage_design["items"]) - 5
            more_html = f"<div class='d-more'>+{more}장 더 · model {_esc(stage_design['model'])}</div>" if more > 0 else f"<div class='d-more'>model {_esc(stage_design['model'])}</div>"
            d3 = (f"<div class='d-head'><span class='d-lab'>③ 슬라이드 설계 · Stage 2</span>"
                  f"<span class='d-meta'>{stage_design['elapsed']:.1f}s</span></div>"
                  f"<div class='d-stat'>{stage_design['n']}<span class='u'>장 · {stage_design['patterns']}개 패턴</span></div>"
                  f"<div class='d-list'>{items_html}</div>{more_html}")
            s3 = _seg("③ 설계", "var(--pptx-ch-4)", "#fffbeb", "done",
                      f"{stage_design['n']}", "장 설계됨", d3)
        else:
            s3 = _seg("③ 설계", "var(--pptx-ch-4)", "#fffbeb", "pending", "대기")

        if stage_render:
            if stage_render.get("done"):
                d4 = (f"<div class='d-head'><span class='d-lab'>④ {_esc(stage_render['fmt'])} 렌더 · Stage 3</span>"
                      f"<span class='d-meta'>{stage_render['elapsed']:.1f}s</span></div>"
                      f"<div class='d-stat'>{stage_render['total']}<span class='u'>장 · {stage_render['size_kb']:.1f}KB</span></div>")
                s4 = _seg("④ 렌더", "var(--pptx-ch-2)", "#f0fdf4", "done",
                          stage_render["fmt"], f"{stage_render['total']}장 완료", d4)
            else:
                cur, total = stage_render["current"], stage_render["total"]
                pct = int(cur / max(total, 1) * 100)
                d4 = (f"<div class='d-head'><span class='d-lab'>④ {_esc(stage_render['fmt'])} 렌더 · Stage 3</span>"
                      f"<span class='d-meta'>{stage_render['elapsed']:.0f}s 경과</span></div>"
                      f"<div class='d-stat'>{cur} / {total}<span class='u'>장 · {pct}%</span></div>"
                      f"<div class='d-list'><div class='d-item'><span class='n'>{cur}</span><span class='pat' style='color:var(--pptx-ch-2)'>▸</span>"
                      f"<span class='tt'>{_esc(stage_render.get('label',''))} 렌더 중…</span></div></div>")
                s4 = _seg("④ 렌더", "var(--pptx-ch-2)", "#f0fdf4", "active",
                          f"{stage_render['fmt']} {cur} / {total}", "장", d4)
        else:
            s4 = _seg("④ 렌더", "var(--pptx-ch-2)", "#f0fdf4", "pending", "대기")
    else:
        # Marp 엔진 — 실제로는 단일 변환 호출이라 ②/③은 즉시 done, ④만 생성 전후로 갈림
        s2 = _seg("② 원문", "var(--pptx-ch-6)", "#ecfeff",
                  "done" if md_text else "pending", f"{len(md_text):,}", "chars")
        s3 = _seg("③ 엔진", "var(--pptx-ch-4)", "#fffbeb", "done", engine_label, "Fast")
        if stage_render:
            if stage_render.get("done"):
                s4 = _seg("④ 산출", "var(--pptx-ch-2)", "#f0fdf4", "done",
                          export_fmt, f"{stage_render['size_kb']:.1f}KB")
            else:
                s4 = _seg("④ 산출", "var(--pptx-ch-2)", "#f0fdf4", "active", export_fmt, "생성 중…")
        else:
            s4 = _seg("④ 산출", "var(--pptx-ch-2)", "#f0fdf4", "pending", export_fmt)

    html = (
        "<div class='flow-strip'>" + s1 + "<div class='flow-arrow'>→</div>" + s2 +
        "<div class='flow-arrow'>→</div>" + s3 + "<div class='flow-arrow'>→</div>" + s4 +
        "</div>"
    )
    placeholder.markdown(html, unsafe_allow_html=True)


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
              <div class="dp-foot">→ <b>② 원문으로 {len(md_text):,}자 전달</b></div>
            </div>""",
            unsafe_allow_html=True,
        )
    return md_text, source_label


def render() -> None:
    st.markdown(_PPTX_CSS, unsafe_allow_html=True)
    hub_pagebar(
        "PPT",
        "Deck Console",
        "마크다운 소스를 선택하고 변환 엔진을 정한 뒤 PPTX/PDF 산출물로 내보냅니다.",
        "Export Ready",
    )

    strip_ph = st.empty()
    caption_ph = st.empty()

    st.markdown("<div class='pptx-section-title'><span class='dot'></span>소스 선택</div>", unsafe_allow_html=True)
    with st.container(border=True):
        rail_col, body_col = st.columns([176, 600])

        _init_deck_meta_defaults()
        archive_items = _list_archive_content_md()
        docs_items = _list_docs_md()

        with rail_col:
            st.markdown("<div class='pptx-rail-anchor'></div>", unsafe_allow_html=True)
            upload_name = st.session_state.get("pptx_upload_name")
            # 옵션 정체성(_SOURCE_MODES)과 표시 라벨(실시간 카운트)을 분리 —
            # 라벨에 매 rerun마다 바뀌는 글자수를 그대로 넣으면 위젯 상태 매칭이 깨짐.
            def _fmt(m: str) -> str:
                return _rail_label(m, md_chars=len(st.session_state.get("pptx_md", _SAMPLE_MD)),
                                   upload_name=upload_name, archive_n=len(archive_items), docs_n=len(docs_items))

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
                    key="pptx_md_input", height=204,
                    help="`---`로 슬라이드 구분. 표·인용·코드 모두 박힘.",
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

            elif source_mode.startswith("📄"):
                md_text, source_label = _render_doc_picker(
                    docs_items, kind="docs/system", hue="var(--pptx-ch-3)", tint="#eef2ff",
                    key_prefix="pptx_docs",
                )

    st.markdown("<div class='pptx-section-title'><span class='dot' style='background:var(--pptx-ch-4)'></span>변환 설정</div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(f"<div class='pptx-caption'>소스: <strong>{_esc(source_label or '미선택')}</strong> · 본문 <strong>{len(md_text):,}</strong> chars</div>", unsafe_allow_html=True)

        engine = st.radio(
            "🛠️ PPT 엔진",
            options=["📄 Marp (단순·빠름)", "🎨 디자인 (컨설팅급, LLM 슬라이드 설계 → HTML 템플릿)"],
            index=0, key="pptx_engine",
            help="Marp = 마크다운을 슬라이드로 그대로 박음 (3~10초). "
                 "디자인 = LLM이 패턴 결정 → HTML 렌더 (30~120초, playwright 필요).",
        )
        is_design = engine.startswith("🎨")

        with st.container(border=True, key="pptx_common_box"):
            st.markdown("<div class='set-glabel'><span class='g-dot' style='background:var(--pptx-ch-4)'></span>공통 설정 · Marp · 디자인</div>", unsafe_allow_html=True)

            r1c1, r1c2, r1c3 = st.columns(3)
            with r1c1:
                if "pptx_output_format_pills" not in st.session_state:
                    st.session_state["pptx_output_format_pills"] = "📄 PDF"
                out_choice = st.pills("출력 형식", options=["📄 PDF", "📊 PPTX"], selection_mode="single",
                                      key="pptx_output_format_pills", width="stretch")
            with r1c2:
                if "pptx_paginate_pills" not in st.session_state:
                    st.session_state["pptx_paginate_pills"] = "ON"
                pag_choice = st.pills("페이지 번호", options=["ON", "OFF"], selection_mode="single",
                                     key="pptx_paginate_pills", width="stretch")
            with r1c3:
                if "pptx_save_disk_pills" not in st.session_state:
                    st.session_state["pptx_save_disk_pills"] = "ON" if is_design else "OFF"
                save_choice = st.pills("exports 저장", options=["ON", "OFF"], selection_mode="single",
                                      key="pptx_save_disk_pills", width="stretch")

            output_format = "PDF (벡터, 편집 불가)" if "PDF" in str(out_choice) else "PPTX (이미지 임베드)"
            paginate = str(pag_choice) == "ON"
            save_to_disk = str(save_choice) == "ON"

            from src.config import IRIS_LLM_DEEP
            installed = _ollama_models()
            if not installed:
                st.warning("⚠️ Ollama에 모델 0개 또는 Ollama 미가동")
                picked_model = None
            else:
                default_idx = 0
                for i, n in enumerate(installed):
                    if n == IRIS_LLM_DEEP or n.startswith(IRIS_LLM_DEEP + ":"):
                        default_idx = i
                        break
                picked_model = st.selectbox(
                    f"🧠 LLM 모델 ({len(installed)}개 설치)", options=installed, index=default_idx,
                    key="pptx_model",
                    help=f"Ollama 설치 모델. 기본 env IRIS_LLM_DEEP=`{IRIS_LLM_DEEP}`.",
                )

        theme_name = None
        use_llm_restructure = False
        use_2stage = False
        slide_target = "auto (입력 크기에 따라)"
        deck_company = st.session_state.get("pptx_deck_company", _DEFAULT_DECK_COMPANY)
        deck_title = st.session_state.get("pptx_deck_title", "")
        deck_subtitle = st.session_state.get("pptx_deck_subtitle", "")
        deck_date = st.session_state.get("pptx_deck_date", "")

        if not is_design:
            c1, c2 = st.columns(2)
            with c1:
                theme_name = st.selectbox(
                    "테마", options=["iris (다크)", "default (기본)", "gaia (밝음)", "uncover (미니멀)"],
                    index=0, key="pptx_theme", help="iris는 IRIS 전용 다크 테마. 다른 테마는 Marp 내장.",
                )
            with c2:
                use_llm_restructure = st.checkbox(
                    "🤖 LLM 재구조화 (품질 ↑)", value=False, key="pptx_use_llm",
                    help="Marp 변환 *전*에 LLM이 마크다운을 프레젠테이션용으로 재구조화.",
                )
        else:
            with st.container(border=True, key="pptx_design_box"):
                st.markdown("<div class='set-glabel'><span class='g-dot' style='background:var(--pptx-ch-5)'></span>디자인 엔진 상세</div>", unsafe_allow_html=True)

                st.markdown(
                    """<div class="sample-grid">
                      <div class="sample-card sel">
                        <div class="sample-thumb" style="background:linear-gradient(180deg,#fff,#f4f8ff)">
                          <div class="bar" style="background:#1a3a6b"></div>
                          <div class="row"><i style="background:#2563eb"></i><i style="background:#1a3a6b"></i><i style="background:#3b82f6"></i></div>
                        </div><div class="sample-name">블루 (기본)</div>
                      </div>
                      <div class="sample-card">
                        <div class="sample-thumb" style="background:linear-gradient(180deg,#fff,#f6f6f6)">
                          <div class="bar" style="background:#1a1a1a"></div>
                          <div class="row"><i style="background:#404040"></i><i style="background:#737373"></i><i style="background:#a3a3a3"></i></div>
                        </div><div class="sample-name">흑백</div>
                      </div>
                      <div class="sample-card">
                        <div class="sample-thumb" style="background:linear-gradient(180deg,#fff,#fef6ff)">
                          <div class="bar" style="background:#7c3aed"></div>
                          <div class="row"><i style="background:#e89324"></i><i style="background:#15803d"></i><i style="background:#dc2626"></i></div>
                        </div><div class="sample-name">컬러풀</div>
                      </div>
                    </div>""",
                    unsafe_allow_html=True,
                )
                st.markdown("<span style='font-size:11.5px;font-weight:700;color:#6b7280'>📐 디자인 샘플</span><span class='new-tag'>NEW</span>", unsafe_allow_html=True)
                if "pptx_sample_pills" not in st.session_state:
                    st.session_state["pptx_sample_pills"] = "블루 (기본)"
                st.pills("디자인 샘플 선택", options=["블루 (기본)", "흑백", "컬러풀"], selection_mode="single",
                        key="pptx_sample_pills", label_visibility="collapsed", width="stretch")
                st.markdown("<div class='wire-note'>현재 <code>_base.html.j2</code>가 테마 1개뿐이라서, 흑백/컬러풀용 base 변형 CSS 2개 추가 배선이 필요합니다.</div>", unsafe_allow_html=True)

                st.markdown("<div style='margin-top:14px'><span style='font-size:11.5px;font-weight:700;color:#6b7280'>🌐 언어</span><span class='new-tag'>NEW</span></div>", unsafe_allow_html=True)
                if "pptx_lang_pills" not in st.session_state:
                    st.session_state["pptx_lang_pills"] = "한국어"
                st.pills("언어 선택", options=["한국어", "中文", "자동 (소스)"], selection_mode="single",
                        key="pptx_lang_pills", label_visibility="collapsed", width="stretch")
                st.markdown("<div class='wire-note'>지금은 소스 언어를 따라가서, designer 프롬프트에 한국어/중국어 강제 지시 배선이 필요합니다.</div>", unsafe_allow_html=True)

                st.markdown("<div style='margin-top:14px'><span style='font-size:11.5px;font-weight:700;color:#6b7280'>🎨 컬러 (액센트)</span><span class='new-tag'>NEW</span></div>", unsafe_allow_html=True)
                if "pptx_color_pills" not in st.session_state:
                    st.session_state["pptx_color_pills"] = "⬛ 네이비"
                st.pills("컬러 선택", options=["⬛ 네이비", "🔵 블루", "🟧 오렌지", "🟩 그린", "🟪 퍼플", "🟥 레드"],
                        selection_mode="single", key="pptx_color_pills", label_visibility="collapsed", width="stretch")
                st.markdown("<div class='wire-note'><code>_base.html.j2</code>의 팔레트는 고정이라서, 선택 색을 <code>--accent</code>에 주입하는 배선이 필요합니다.</div>", unsafe_allow_html=True)

                st.markdown("<hr style='margin:14px 0;border:none;border-top:1px solid #eee'>", unsafe_allow_html=True)

                sc1, sc2 = st.columns([2, 1])
                with sc1:
                    if "pptx_slide_target_pills" not in st.session_state:
                        st.session_state["pptx_slide_target_pills"] = "auto (입력 크기에 따라)"
                    slide_target = st.pills(
                        "🎯 목표 슬라이드 수",
                        options=["auto (입력 크기에 따라)", "10장", "15장", "20장", "25장", "30장"],
                        selection_mode="single", key="pptx_slide_target_pills", width="stretch",
                    )
                with sc2:
                    use_2stage = st.checkbox("🚀 2단 파이프라인 (품질 ↑↑)", value=True, key="pptx_use_2stage",
                                            help="① LLM 입력 확장 → ② 슬라이드 패턴 매칭. OFF면 단일-패스.")

                st.markdown("<div style='margin-top:10px'><span style='font-size:11.5px;font-weight:700;color:#6b7280'>📝 메타 정보</span></div>", unsafe_allow_html=True)
                mc0, mc1, mc2, mc3 = st.columns(4)
                with mc0:
                    deck_company = st.text_input("회사명", key="pptx_deck_company")
                with mc1:
                    deck_title = st.text_input("보고서 제목", key="pptx_deck_title")
                with mc2:
                    deck_subtitle = st.text_input("부제", key="pptx_deck_subtitle")
                with mc3:
                    deck_date = st.text_input("날짜·버전", key="pptx_deck_date")

        if is_design:
            gen_btn = st.button("🎨 디자인 PPT 생성", type="primary", use_container_width=True,
                               disabled=not md_text.strip(), key="pptx_gen_design")
        else:
            gen_pdf = "PDF" in str(output_format)
            gen_btn = st.button("📄 PDF 생성" if gen_pdf else "📊 PPT 생성", type="primary",
                               use_container_width=True, disabled=not md_text.strip(), key="pptx_gen_marp")

    # ─── 스트립 그리기 (생성 전: 현재 선택 상태 그대로) ──────────────────
    engine_label = "Design" if is_design else "Marp"
    export_fmt = "PDF" if "PDF" in str(output_format) else ("PPTX" if is_design else "PPTX")
    _render_strip(strip_ph, engine_is_design=is_design, source_label=source_label, md_text=md_text,
                 stage_expand=st.session_state.get("pptx_last_stage_expand"),
                 stage_design=st.session_state.get("pptx_last_stage_design"),
                 stage_render=st.session_state.get("pptx_last_stage_render"),
                 engine_label=engine_label, export_fmt=export_fmt)

    # ─── 생성 분기 ──────────────────────────────────────────────
    if gen_btn:
        # 새 생성 시작 — 이전 실행의 스테이지 결과 초기화
        st.session_state["pptx_last_stage_expand"] = None
        st.session_state["pptx_last_stage_design"] = None
        st.session_state["pptx_last_stage_render"] = None

        if is_design:
            target_n: int | None = None
            if not str(slide_target).startswith("auto"):
                try:
                    target_n = int(str(slide_target).replace("장", "").strip())
                except ValueError:
                    target_n = None
            _generate_design(
                md_text, picked_model, output_format, save_to_disk,
                deck_company, deck_title, deck_subtitle, deck_date,
                use_2stage=use_2stage, target_slides=target_n,
                strip_ph=strip_ph, source_label=source_label,
            )
            return

        gen_pdf = "PDF" in str(output_format)
        _generate_marp(
            md_text, picked_model, theme_name, paginate,
            use_llm_restructure, save_to_disk, gen_pdf,
            strip_ph=strip_ph, source_label=source_label, engine_label=engine_label,
        )


def _generate_marp(md_text: str, picked_model: str | None,
                   theme_name: str, paginate: bool,
                   use_llm_restructure: bool, save_to_disk: bool,
                   gen_pdf: bool, *, strip_ph, source_label: str, engine_label: str) -> None:
    from src.engine.output import exporter

    def _repaint(stage_render: dict | None) -> None:
        _render_strip(strip_ph, engine_is_design=False, source_label=source_label, md_text=md_text,
                     stage_expand=None, stage_design=None, stage_render=stage_render,
                     engine_label=engine_label, export_fmt="PDF" if gen_pdf else "PPTX")

    _repaint({"done": False})

    effective_md = md_text
    if use_llm_restructure:
        from src.engine.output import exporter_llm
        try:
            with st.spinner("🤖 LLM 재구조화 중… (~30~120s, 모델 따라 다름)"):
                rr = exporter_llm.restructure_markdown(md_text, model=picked_model)
            effective_md = rr.md
            st.info(
                f"🤖 재구조화 완료 — {rr.model} · {rr.elapsed_ms / 1000:.1f}s · "
                f"{rr.original_chars:,} → {rr.output_chars:,}자 · 슬라이드 ~{rr.slides_count}장"
            )
            with st.expander("📋 재구조화된 마크다운 미리보기", expanded=False):
                st.code(effective_md[:1500] + ("..." if len(effective_md) > 1500 else ""), language="markdown")
        except exporter_llm.RestructureError as e:
            st.warning(f"⚠️ LLM 재구조화 실패: {e} — 원본 마크다운 사용")

    theme_map = {"iris (다크)": "iris", "default (기본)": "default", "gaia (밝음)": "gaia", "uncover (미니멀)": "uncover"}
    theme_id = theme_map.get(theme_name, "iris")
    theme_css = exporter.DEFAULT_THEME_PATH if theme_id == "iris" else None

    try:
        with st.spinner(f"{'PDF' if gen_pdf else 'PPT'} 생성 중… (3~10초)"):
            t0 = _dt.datetime.now()
            if gen_pdf:
                res = exporter.md_to_pdf(effective_md, theme_css=theme_css, theme_name=theme_id, paginate=paginate)
            else:
                res = exporter.md_to_pptx(effective_md, theme_css=theme_css, theme_name=theme_id, paginate=paginate)
    except exporter.ExportError as e:
        st.error(f"❌ 변환 실패: {e}")
        st.caption("Marp 미설치: `brew install marp-cli`")
        _repaint(None)
        return

    result = {"done": True, "size_kb": res.size_bytes / 1024, "elapsed": res.elapsed_ms / 1000}
    st.session_state["pptx_last_stage_render"] = result
    _repaint(result)

    st.success(f"✅ 생성 완료 — {res.size_bytes / 1024:.1f}KB · {res.elapsed_ms / 1000:.1f}초")

    ext = "pdf" if gen_pdf else "pptx"
    with res.out_path.open("rb") as f:
        data = f.read()
    stamp = _dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    st.download_button(
        f"💾 다운로드 (slides_{stamp}.{ext})", data=data, file_name=f"slides_{stamp}.{ext}",
        mime="application/pdf" if gen_pdf else "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        use_container_width=True,
    )
    if save_to_disk:
        saved = _save_to_exports(res.out_path, prefix="slides")
        st.caption(f"📦 exports/ 저장: `{saved}`")


def _generate_design(md_text: str, picked_model: str | None,
                     output_format: str, save_to_disk: bool,
                     company: str, title: str, subtitle: str, date: str,
                     *, use_2stage: bool = True, target_slides: int | None = None,
                     strip_ph, source_label: str) -> None:
    """V2.7.6 → V2.8.3 디자인 엔진. 스테이지마다 strip_ph를 실시간 갱신."""
    meta = {"company": company, "title": title, "subtitle": subtitle, "date": date}
    model_label = picked_model or "default"

    def _repaint(stage_expand=None, stage_design=None, stage_render=None) -> None:
        _render_strip(strip_ph, engine_is_design=True, source_label=source_label, md_text=md_text,
                     stage_expand=stage_expand, stage_design=stage_design, stage_render=stage_render,
                     engine_label="Design", export_fmt="PDF" if "PDF" in output_format else "PPTX")

    _repaint()

    try:
        effective_md = md_text
        pre_expanded = False
        stage_expand_result = None

        if use_2stage and len(md_text) >= 2000:
            from src.engine.output.deck import expander
            try:
                with st.spinner("① LLM 입력 확장 중… (30~180초, 모델·입력 크기 따라)"):
                    er = expander.expand_for_slides(md_text, meta, model=picked_model, timeout=900)
                effective_md = er.md
                pre_expanded = True
                stage_expand_result = {
                    "in": er.original_chars, "out": er.output_chars,
                    "elapsed": er.elapsed_ms / 1000, "model": er.model,
                    "preview": effective_md[:200],
                }
                st.session_state["pptx_last_stage_expand"] = stage_expand_result
                _repaint(stage_expand=stage_expand_result)
                st.info(f"🚀 확장 완료 — {er.model} · {er.elapsed_ms / 1000:.1f}s · {er.original_chars:,} → {er.output_chars:,}자")
                with st.expander("📋 확장된 마크다운 미리보기 (앞 2000자)", expanded=False):
                    st.code(effective_md[:2000] + ("..." if len(effective_md) > 2000 else ""), language="markdown")
            except expander.ExpansionError as e:
                st.warning(f"⚠️ Stage 1 확장 실패: {e} — 원본 마크다운으로 계속")
        elif use_2stage:
            st.caption(f"📌 입력 {len(md_text):,}자 < 2000자 — Stage 1 자동 skip")

        with st.spinner(f"② LLM 슬라이드 설계 중… (30~300초, model: {model_label})"):
            t0 = _dt.datetime.now()
            from src.engine.output.deck import designer
            deck = designer.design_deck(effective_md, meta, model=picked_model, timeout=600,
                                        pre_expanded=pre_expanded, target_slides=target_slides)
            elapsed2 = (_dt.datetime.now() - t0).total_seconds()

        items = []
        for i, sl in enumerate(deck.slides, 1):
            label = str(sl.data.get("title", sl.data.get("company", "?")))[:40]
            items.append((i, sl.pattern, label))
        stage_design_result = {
            "n": len(deck.slides), "patterns": len(set(sl.pattern for sl in deck.slides)),
            "elapsed": elapsed2, "model": model_label, "items": items,
        }
        st.session_state["pptx_last_stage_design"] = stage_design_result
        _repaint(stage_expand=stage_expand_result, stage_design=stage_design_result)

        st.success(f"✅ 슬라이드 {len(deck.slides)}장 설계됨 (model: {model_label}, 2단: {'ON' if use_2stage and pre_expanded else 'OFF'})")
        with st.expander("📋 슬라이드 패턴 미리보기", expanded=False):
            for i, pat, label in items:
                st.write(f"{i}. **{pat}** — {label}")

        fmt_label = "PDF" if "PDF" in output_format else "PPTX"
        render_t0 = _dt.datetime.now()

        def _on_progress(cur: int, total: int, label: str) -> None:
            elapsed = (_dt.datetime.now() - render_t0).total_seconds()
            live = {"current": cur, "total": total, "label": label, "elapsed": elapsed, "fmt": fmt_label, "done": False}
            _repaint(stage_expand=stage_expand_result, stage_design=stage_design_result, stage_render=live)

        with st.spinner(f"③ {fmt_label} 렌더 중… (슬라이드당 ~2초, 총 {len(deck.slides)*2}~{len(deck.slides)*4}초)"):
            if "PDF" in output_format:
                from src.engine.output.deck.renderer import render_deck_to_pdf
                out_path = render_deck_to_pdf(deck, on_progress=_on_progress)
                ext, mime = "pdf", "application/pdf"
            else:
                from src.engine.output.deck.pptx_export import render_deck_to_pptx
                out_path = render_deck_to_pptx(deck, on_progress=_on_progress)
                ext = "pptx"
                mime = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

        size_kb = out_path.stat().st_size / 1024
        elapsed3 = (_dt.datetime.now() - render_t0).total_seconds()
        stage_render_result = {"done": True, "total": len(deck.slides), "size_kb": size_kb, "elapsed": elapsed3, "fmt": fmt_label}
        st.session_state["pptx_last_stage_render"] = stage_render_result
        _repaint(stage_expand=stage_expand_result, stage_design=stage_design_result, stage_render=stage_render_result)

        st.success(f"✅ 생성 완료 — {size_kb:.1f}KB")
        if save_to_disk:
            saved = _save_to_exports(out_path, prefix="deck")
            st.caption(f"📦 exports/ 저장: `{saved}`")

        with out_path.open("rb") as f:
            data = f.read()
        stamp = _dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        st.download_button(
            f"💾 다운로드 (deck_{stamp}.{ext})", data=data, file_name=f"deck_{stamp}.{ext}",
            mime=mime, use_container_width=True,
        )

    except Exception as e:
        st.error(f"❌ 실패: {type(e).__name__}: {e}")
        st.caption("playwright 미설치라면: `pip install playwright && playwright install chromium`")
