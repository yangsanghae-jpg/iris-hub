"""탭: 🔧 진단툴 — DIAG-SOT 진실원 관리 (P5 v2 · Q2/Q3/Q4/Q5 편집).

상단: 상태 스트립 + 가로 팩 선택기 · 본문: 전폭 3컬럼 그리드 + 반영 배너.
쓰기는 dx JSON만. runtime은 재생성 결과물.
"""
from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Any

import pandas as pd
import streamlit as st

from src.config import DIAGNOSIS_TOOL_GITHUB
from src.diagnosis_git import resolve_diagnosis_repo
from src.store import diag_sot as sot
from src.store import dx_editor, dx_index
from src.ui_kit import hub_pagebar

# 좌측 컨트롤(세부산업·전체 팩 상태) 공통 열 비율
_SOT_SIDE_COLS = [1, 2.8]

_Q1_SECTION_BLOCK_KEYS = {
    "Step1 — 산업군": "step1",
    "Step1.5 — 제품 선택": "step1_5",
    "UI 원칙": "ui_principle",
}


def _safe_block_key(text: str) -> str:
    out: list[str] = []
    for ch in str(text):
        if ch.isalnum():
            out.append(ch)
        elif ch in "._-":
            out.append(ch)
        elif not out or out[-1] != "_":
            out.append("_")
    return "".join(out).strip("_") or "block"

_CSS = """
<style>
/* ── SOT 컨트롤 타이포 3종 (버튼·selectbox) ──
   chip   0.75rem  — 팩 pills (다수·2줄 라벨)
   ctrl   0.8125rem — 일반 버튼·selectbox·그리드 입력 (= hub 13px)
   banner 0.875rem  — 액션바 상태 배너 (버튼 아님)
*/
.sot-v2-strip {
  display:flex; flex-wrap:wrap; gap:10px 18px;
  padding:12px 14px; margin-bottom:12px;
  border:1px solid rgba(47,128,196,0.14); border-radius:12px;
  background:linear-gradient(180deg,#fff 0%,#f8fbfe 100%);
  font-size:0.82rem; color:#344054; line-height:1.5;
}
.sot-v2-strip strong { font-weight:800; color:#101828; }
/* pagebar 설명 = Q3 팩 desc(.sot-pack-desc) 톤 */
.hub-pagebar-desc {
  font-size:0.8rem !important; line-height:1.4 !important; color:#667085 !important;
}
/* ── SOT 제목 2종 ──
   section — 구역 소제목: 팩 선택 · 선택 팩명(Q3 규모 프로필 등)
   field   — 컨트롤 행 라벨: 전체 팩 상태 · 세부산업
*/
.sot-section-title,
.sot-section-title.sot-section-title--pack,
[data-testid="stHtml"] p.sot-section-title {
  font-size:0.9375rem !important; font-weight:700 !important; color:#101828 !important;
  line-height:1.3 !important; letter-spacing:-0.01em !important;
  margin:0 0 0.45rem !important;
}
.sot-section-title--pack { margin-top:0.6rem !important; }
.sot-field-label {
  font-size:0.8125rem !important; font-weight:600 !important; color:#344054 !important;
  line-height:1.25 !important; margin:0 0 0.35rem !important;
}
.sot-pack-strip { display:flex; flex-wrap:wrap; gap:6px; margin:0 0 10px; }
/* Q팩 pills — Streamlit 1.50+: stButtonGroup + st-key-sot_pack_pills */
.st-key-sot_pack_pills[data-testid="stElementContainer"] {
  width:100% !important; max-width:100% !important;
}
[data-testid="stVerticalBlock"]:has(.sot-pack-pills-marker) .st-key-sot_pack_pills,
.st-key-sot_pack_pills {
  min-height:unset !important; height:auto !important;
  margin-bottom:4px !important; padding-bottom:0 !important;
}
.st-key-sot_pack_pills [data-testid="stButtonGroup"] {
  width:100% !important; margin-bottom:0 !important; padding-bottom:0 !important;
}
.sot-pack-pills-marker { display:none !important; }
.st-key-sot_pack_pills [data-baseweb="button-group"] {
  display:flex !important; flex-wrap:wrap !important; gap:6px !important;
  width:100% !important; align-content:flex-start !important;
}
.st-key-sot_pack_pills [data-testid="stBaseButton-pills"],
.st-key-sot_pack_pills [data-testid="stBaseButton-pillsActive"] {
  flex:0 0 5.5rem !important; width:5.5rem !important;
  min-width:5.5rem !important; max-width:5.5rem !important;
  height:2.75rem !important; min-height:2.75rem !important; max-height:2.75rem !important;
  font-size:0.75rem !important; font-weight:700 !important;
  line-height:1.15 !important; letter-spacing:-0.02em !important;
  padding:3px 4px !important;
  white-space:normal !important; word-break:keep-all !important;
  text-align:center !important;
  display:inline-flex !important; align-items:center !important; justify-content:center !important;
  border-radius:0.5rem !important;
  border:1px solid rgba(49,51,63,0.2) !important;
  background:rgb(240,242,246) !important; color:#101828 !important;
  box-shadow:none !important; overflow:hidden !important;
}
.st-key-sot_pack_pills [data-testid="stBaseButton-pills"] [data-testid="stMarkdownContainer"],
.st-key-sot_pack_pills [data-testid="stBaseButton-pillsActive"] [data-testid="stMarkdownContainer"] {
  width:100% !important; overflow:hidden !important;
}
.st-key-sot_pack_pills [data-testid="stBaseButton-pills"] [data-testid="stMarkdownContainer"] p,
.st-key-sot_pack_pills [data-testid="stBaseButton-pillsActive"] [data-testid="stMarkdownContainer"] p {
  width:100% !important; margin:0 !important; text-align:center !important;
  font-size:0.75rem !important; line-height:1.15 !important;
  white-space:normal !important; word-break:keep-all !important;
  overflow-wrap:break-word !important;
}
.st-key-sot_pack_pills [data-testid="stBaseButton-pillsActive"] {
  background:rgba(47,128,196,0.14) !important;
  border-color:#2f80c4 !important; color:#175cd3 !important;
}
.st-key-sot_pack_pills [data-testid="stBaseButton-pills"]:hover {
  border-color:#2f80c4 !important;
}
/* ctrl — 좌측 selectbox·전체 버튼 (전체팩·세부산업) */
[data-testid="stColumn"]:has(.sot-side-ctrl-marker) [data-testid="stSelectbox"] > div > div,
[data-testid="stColumn"]:has(.sot-side-ctrl-marker) [data-testid="stSelectbox"] > div > div > div,
[data-testid="stColumn"]:has(.sot-side-ctrl-marker) [data-testid="stSelectbox"] [data-baseweb="select"],
[data-testid="stColumn"]:has(.sot-side-ctrl-marker) [data-testid="stButton"] > button {
  min-height:2.5rem !important; font-size:0.8125rem !important;
  border-radius:0.5rem !important;
}
[data-testid="stColumn"]:has(.sot-side-ctrl-marker) [data-testid="stButton"] > button {
  background:rgb(240,242,246) !important;
  border:1px solid rgba(49,51,63,0.2) !important;
  color:#31333f !important; font-weight:400 !important;
  justify-content:flex-start !important; text-align:left !important;
  padding:0.45rem 0.7rem !important;
}
[data-testid="stColumn"]:has(.sot-side-ctrl-marker) [data-testid="stButton"] > button p {
  font-size:0.8125rem !important; line-height:1.25 !important; margin:0 !important;
}
/* ctrl — 툴바·액션·팩빠른선택 버튼 */
.st-key-sot_refresh [data-testid="stButton"] > button,
.st-key-sot_undo [data-testid="stButton"] > button,
.st-key-sot_validate [data-testid="stButton"] > button,
.st-key-sot_save [data-testid="stButton"] > button,
.st-key-sot_all_packs_toggle [data-testid="stButton"] > button,
div[class*="st-key-sot_all_"] [data-testid="stButton"] > button {
  font-size:0.8125rem !important; font-weight:600 !important; line-height:1.25 !important;
}
.st-key-sot_refresh [data-testid="stButton"] > button p,
.st-key-sot_undo [data-testid="stButton"] > button p,
.st-key-sot_validate [data-testid="stButton"] > button p,
.st-key-sot_save [data-testid="stButton"] > button p,
.st-key-sot_all_packs_toggle [data-testid="stButton"] > button p,
div[class*="st-key-sot_all_"] [data-testid="stButton"] > button p {
  font-size:0.8125rem !important; line-height:1.25 !important; margin:0 !important;
}
/* 전체 팩 상태 펼침 — 우측 패널 */
.sot-all-packs-panel {
  border:1px solid rgba(49,51,63,0.12); border-radius:0.5rem;
  background:#fff; padding:8px 10px; margin-top:0;
}
/* 전체 팩 상태 — 구 expander 톤(다른 expander용) */
[data-testid="stExpander"] details {
  border: 1px solid rgba(49,51,63,0.2) !important;
  border-radius: 0.5rem !important;
  background: rgb(240,242,246) !important;
  overflow: hidden;
}
[data-testid="stExpander"] summary {
  background: rgb(240,242,246) !important;
  font-size: 0.875rem !important; font-weight: 400 !important;
  color: #31333f !important;
  padding: 0.45rem 0.7rem !important;
}
[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
  background: #fff !important;
  border-top: 1px solid rgba(49,51,63,0.12) !important;
}
.sot-v2-dot { display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:5px; vertical-align:middle; }
.sot-dot-synced { background:#12b76a; }
.sot-dot-pending { background:#f79009; }
.sot-dot-muted { background:#d0d5dd; }
.sot-sub-header {
  margin:14px 0 0; padding:8px 12px; border-radius:8px 8px 0 0;
  background:rgba(47,128,196,0.06); font-size:0.82rem; font-weight:700; color:#344054;
  border:1px solid rgba(49,51,63,0.12); border-bottom:none;
}
.sot-all-packs-table { font-size:0.75rem; color:#475467; width:100%; border-collapse:collapse; }
.sot-all-packs-table td { padding:4px 8px; border-bottom:1px solid rgba(47,128,196,0.08); }
.sot-v2-badge {
  display:inline-block; margin-left:6px; padding:1px 6px; border-radius:999px;
  font-size:0.62rem; font-weight:700; vertical-align:middle;
}
.sot-badge-deferred { background:rgba(152,162,179,0.18); color:#475467; }
.sot-badge-spine { background:rgba(47,128,196,0.12); color:#175cd3; }
.sot-badge-wait { background:rgba(247,144,9,0.14); color:#b54708; }
.sot-banner-wrap { display:flex; flex:1; width:100%; min-height:2.5rem; }
.sot-banner-wrap .sot-reflect-banner { flex:1; width:100%; }
.sot-reflect-banner {
  display:flex; align-items:center; min-height:2.5rem; height:100%;
  padding:0 12px !important; border-radius:0.5rem; margin:0;
  border:1px solid rgba(47,128,196,0.16);
  font-size:0.875rem !important; line-height:1.3 !important;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
}
.sot-reflect-banner strong { font-size:0.875rem !important; font-weight:700; }
div[data-testid="stHorizontalBlock"]:has(.sot-reflect-banner) {
  align-items:stretch !important;
}
div[data-testid="stHorizontalBlock"]:has(.sot-reflect-banner) [data-testid="column"] {
  display:flex !important; flex-direction:column !important; justify-content:stretch !important;
}
div[data-testid="stHorizontalBlock"]:has(.sot-reflect-banner) [data-testid="stVerticalBlock"] {
  flex:1 !important; display:flex !important; flex-direction:column !important;
}
div[data-testid="stHorizontalBlock"]:has(.sot-reflect-banner) [data-testid="stButton"] {
  flex:1 !important; display:flex !important;
}
div[data-testid="stHorizontalBlock"]:has(.sot-reflect-banner) [data-testid="stButton"] button {
  flex:1 !important; min-height:2.5rem !important; height:100% !important;
  font-size:0.8125rem !important; font-weight:600 !important;
  padding:0.4rem 0.5rem !important; border-radius:0.5rem !important;
  display:inline-flex !important; align-items:center !important; justify-content:center !important;
  text-align:center !important;
}
div[data-testid="stHorizontalBlock"]:has(.sot-reflect-banner) [data-testid="stButton"] button p {
  width:100% !important; margin:0 !important; text-align:center !important;
  font-size:0.8125rem !important; line-height:1.25 !important; white-space:normal !important;
}
.sot-sub-filter-row { align-items:flex-end !important; margin-bottom:8px; }
.sot-sub-hint {
  font-size:0.8rem; color:#667085; line-height:1.4;
  padding:0.55rem 0 0; margin:0;
}
[data-testid="stVerticalBlockBorderWrapper"]:has(.sot-edit-head-marker) {
  border-color: rgba(49,51,63,0.12) !important;
  border-radius: 0 0 8px 8px !important;
  border-top: none !important;
  margin: 8px 0 12px !important;
  overflow: hidden;
}
[data-testid="stVerticalBlockBorderWrapper"]:has(.sot-edit-head-marker) [data-testid="stHorizontalBlock"] {
  align-items: center !important;
  padding: 0 12px !important;
  margin: 0 !important;
  border-bottom: 1px solid rgba(49,51,63,0.08);
  min-height: 2.75rem;
}
[data-testid="stVerticalBlockBorderWrapper"]:has(.sot-edit-head-marker) [data-testid="stHorizontalBlock"]:first-of-type {
  background: rgb(240,242,246) !important;
  min-height: 2.25rem;
  border-bottom: 1px solid rgba(49,51,63,0.12);
}
[data-testid="stVerticalBlockBorderWrapper"]:has(.sot-edit-head-marker) [data-testid="stHorizontalBlock"]:last-of-type {
  border-bottom: none;
}
[data-testid="stVerticalBlockBorderWrapper"]:has(.sot-edit-head-marker) [data-testid="stHorizontalBlock"]:first-of-type p {
  font-size:0.8125rem !important; font-weight:600 !important; color:#31333f !important;
  margin:0 !important;
}
.sot-edit-item-name { font-size: 0.875rem; color: #31333f; line-height: 1.35; margin: 0; }
.sot-edit-item-hint { font-size: 0.75rem; color: #667085; line-height: 1.3; margin: 2px 0 0; }
.sot-edit-reflect { font-size: 0.8rem; color: #667085; line-height: 1.35; margin: 0; }
[data-testid="stVerticalBlockBorderWrapper"]:has(.sot-edit-head-marker) [data-testid="stNumberInput"] > div {
  background: transparent !important; gap: 4px !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:has(.sot-edit-head-marker) [data-testid="stNumberInput"] input {
  min-height:2rem !important; font-size:0.8125rem !important;
  border:1px solid rgba(49,51,63,0.18) !important; border-radius:6px !important;
  background:#fff !important; padding:0 8px !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:has(.sot-edit-head-marker) [data-testid="stTextInput"] input {
  min-height:2rem !important; font-size:0.8125rem !important;
  border:1px solid rgba(49,51,63,0.18) !important; border-radius:6px !important;
  background:#fff !important; padding:0 8px !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:has(.sot-edit-head-marker) [data-testid="stSelectbox"] > div > div,
[data-testid="stVerticalBlockBorderWrapper"]:has(.sot-edit-head-marker) [data-testid="stSelectbox"] > div > div > div,
[data-testid="stVerticalBlockBorderWrapper"]:has(.sot-edit-head-marker) [data-testid="stSelectbox"] [data-baseweb="select"] {
  min-height:2rem !important; font-size:0.8125rem !important;
  border-radius:6px !important; background:#fff !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:has(.sot-edit-head-marker) [data-testid="stNumberInput"] button {
  min-height:2rem !important; min-width:2rem !important;
  border:1px solid rgba(49,51,63,0.18) !important; border-radius:6px !important;
  background:#fff !important;
}
.sot-reflect-synced { background:rgba(18,183,106,0.08); border-color:rgba(18,183,106,0.25); color:#027a48; }
.sot-reflect-pending { background:rgba(247,144,9,0.1); border-color:rgba(247,144,9,0.28); color:#b54708; }
.sot-reflect-readonly { background:rgba(102,112,133,0.06); color:#475467; }
.sot-pack-desc { font-size:0.8rem; color:#667085; margin:0 0 8px; }
</style>
"""


def _render_html(html: str) -> None:
    if hasattr(st, "html"):
        st.html(html)
        return
    st.markdown(html, unsafe_allow_html=True)


def _fmt_time(iso: str) -> str:
    if not iso or len(iso) < 16:
        return "—"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%m-%d %H:%M")
    except ValueError:
        return iso[:16]


def _status_strip(manifest: dict, dx_idx: dx_index.DxIndex, packs: list[dict]) -> None:
    meta = manifest.get("meta") or {}
    pack_n = meta.get("pack_count", len(packs))
    row_n = dx_idx.total_row_count()
    pending_n = 0
    for pack in packs:
        mode = dx_index.pack_edit_mode(pack.get("pack_id", ""))
        if mode != "editable":
            continue
        manifest_pid = pack.get("pack_id", "")
        status, _ = dx_index.pack_mirror_sync_status_from_index(dx_idx, manifest_pid)
        if status != "synced":
            pending_n += 1
    repo = resolve_diagnosis_repo()
    last = _fmt_time(repo.last_commit_iso if repo else "")
    text = (
        f"진실원 <strong>{pack_n}</strong>팩 · "
        f"<strong>{row_n:,}</strong>행 · "
        f"아직 리포트에 안 넣은 팩 <strong>{pending_n}</strong> · "
        f"마지막 반영 <strong>{last}</strong>"
    )
    _render_html(f'<div class="sot-v2-strip">{text}</div>')


def _pack_row_count(pack: dict, dx_idx: dx_index.DxIndex) -> int:
    pid = pack.get("pack_id", "")
    q = dx_index.pack_q_code(pid)
    if q == "q1":
        n = dx_idx.q1_label_field_count()
        if n:
            return n
        return int(pack.get("member_count") or 0)
    if q == "q5":
        n = dx_idx.q5_row_count()
        if n:
            return n
        return int(pack.get("member_count") or 0)
    dx_pid = dx_index.resolve_dx_pack_id(pid)
    n = dx_idx.matrix_row_count(dx_pid)
    if n:
        return n
    return int(pack.get("member_count") or 0)


def _sync_dot(pack: dict, dx_idx: dx_index.DxIndex) -> str:
    mode = dx_index.pack_edit_mode(pack.get("pack_id", ""))
    if mode not in ("editable", "pilot_wait"):
        return ""
    manifest_pid = pack.get("pack_id", "")
    if not dx_index.pack_mirror_runtime_rels(manifest_pid):
        return "sot-dot-pending"
    status, _ = dx_index.pack_mirror_sync_status_from_index(dx_idx, manifest_pid)
    return "sot-dot-synced" if status == "synced" else "sot-dot-pending"


def _pack_badge(mode: str) -> str:
    if mode == "deferred":
        return '<span class="sot-v2-badge sot-badge-deferred">편집 보류 (이견 조정 중)</span>'
    if mode == "spine":
        return '<span class="sot-v2-badge sot-badge-spine">참조 전용</span>'
    if mode == "pilot_wait":
        return '<span class="sot-v2-badge sot-badge-wait">파일럿 대기</span>'
    return ""


def _q_pack_ids() -> list[str]:
    return list(dx_index.pack_scope().get("q_packs") or [])


def _pack_chip_label(manifest_pack_id: str) -> str:
    gloss = dx_index.pack_glossary().get(manifest_pack_id) or {}
    return gloss.get("chip_ko") or gloss.get("title_ko") or manifest_pack_id


def _all_packs_summary_line(packs: list[dict], dx_idx: dx_index.DxIndex) -> str:
    q_n = sum(1 for p in packs if dx_index.chapter_group(p) == "Q 수치팩")
    a_n = sum(1 for p in packs if dx_index.chapter_group(p) == "A 콘텐츠팩")
    pending = 0
    for pack in packs:
        if dx_index.pack_edit_mode(pack.get("pack_id", "")) != "editable":
            continue
        st_, _ = dx_index.pack_mirror_sync_status_from_index(dx_idx, pack.get("pack_id", ""))
        if st_ != "synced":
            pending += 1
    return f"Q {q_n} · A {a_n} · 전체 {len(packs)}팩 · 미반영 {pending}"


def _render_pack_chips(packs: list[dict], dx_idx: dx_index.DxIndex, selected: str) -> str | None:
    """상단 가로 Q팩 선택기 — pills, 선택 시 배경색 강조."""
    _render_html('<span class="sot-pack-pills-marker" aria-hidden="true"></span>')
    q_ids = set(_q_pack_ids())
    q_packs = [p for p in packs if p.get("pack_id") in q_ids]
    q_packs.sort(key=lambda p: _q_pack_ids().index(p.get("pack_id", "")) if p.get("pack_id") in q_ids else 99)

    if not q_packs:
        return None

    options = [p.get("pack_id", "") for p in q_packs]
    if "sot_pack_pills" not in st.session_state:
        st.session_state["sot_pack_pills"] = selected if selected in options else options[0]

    picked = st.pills(
        "팩",
        options=options,
        format_func=_pack_chip_label,
        selection_mode="single",
        key="sot_pack_pills",
        label_visibility="collapsed",
        width="stretch",
    )
    if picked and picked != selected:
        return str(picked)
    return None


def _render_all_packs_summary(packs: list[dict], dx_idx: dx_index.DxIndex, selected: str) -> str | None:
    """전체 팩 상태 — 세부산업과 동일 좌열 폭 + 우측 요약/펼침."""
    clicked: str | None = None
    groups: dict[str, list[dict]] = {}
    for pack in packs:
        g = dx_index.chapter_group(pack)
        groups.setdefault(g, []).append(pack)

    order = ["Q 수치팩", "A 콘텐츠팩", "기타"]
    open_ = st.session_state.get("sot_all_packs_open", False)
    summary = _all_packs_summary_line(packs, dx_idx)

    _render_html('<p class="sot-field-label">전체 팩 상태</p>')
    c_left, c_right = st.columns(_SOT_SIDE_COLS)
    with c_left:
        _render_html('<span class="sot-side-ctrl-marker" aria-hidden="true"></span>')
        if st.button("전체", key="sot_all_packs_toggle", use_container_width=True, type="secondary"):
            st.session_state["sot_all_packs_open"] = not open_
            st.rerun()
    with c_right:
        if not open_:
            _render_html(f'<p class="sot-sub-hint">{escape(summary)}</p>')
        else:
            rows_html: list[str] = []
            for gname in order:
                if gname not in groups:
                    continue
                for pack in sorted(groups[gname], key=lambda p: p.get("pack_id", "")):
                    pid = pack.get("pack_id", "")
                    title, _ = dx_index.pack_display(pid)
                    mode = dx_index.pack_edit_mode(pid)
                    dot = _sync_dot(pack, dx_idx) or "sot-dot-muted"
                    count = _pack_row_count(pack, dx_idx)
                    sel = " ✓" if pid == selected else ""
                    badge = _pack_badge(mode)
                    rows_html.append(
                        f"<tr><td><span class='sot-v2-dot {dot}'></span>{escape(title)}{sel}</td>"
                        f"<td>{escape(pid)}</td><td>{count}행</td><td>{badge}</td></tr>"
                    )
            table = (
                "<div class='sot-all-packs-panel'><table class='sot-all-packs-table'><tbody>"
                + "".join(rows_html)
                + "</tbody></table></div>"
            )
            _render_html(table)
            pick_cols = st.columns(4)
            for i, pack in enumerate(sorted(packs, key=lambda p: p.get("pack_id", ""))):
                pid = pack.get("pack_id", "")
                title, _ = dx_index.pack_display(pid)
                with pick_cols[i % 4]:
                    if st.button(title, key=f"sot_all_{pid}", use_container_width=True):
                        clicked = pid
    return clicked


def _apply_pending_edits(
    repo: Any,
    manifest_pid: str,
    pending: dict[str, Any],
) -> tuple[list[dict[str, Any]] | None, list[dict[str, Any]] | None, list[dict[str, Any]] | None]:
    """Q1 → q1_framework, Q2~Q4 → q_matrix, Q5 → q5_recommendation."""
    q = dx_index.pack_q_code(manifest_pid)
    if q == "q1":
        q1 = dx_editor.load_q1_framework(repo.root)
        return None, None, dx_index.apply_q1_label_edits(q1, pending)
    if q == "q5":
        q5 = dx_editor.load_q5_recommendation(repo.root)
        return None, dx_index.apply_q5_grid_edits(q5, pending), None
    qm = dx_editor.load_q_matrix(repo.root)
    return dx_index.apply_q3_grid_edits(qm, manifest_pid, pending), None, None


def _render_action_bar(
    pack: dict,
    dx_idx: dx_index.DxIndex,
    *,
    session_dirty: bool,
    repo: Any,
    manifest_pid: str,
    primary_dx: str,
    pending: dict[str, Any],
) -> None:
    """반영 배너(축소) + 되돌리기·검증·저장 버튼 동일 행."""
    banner_html, can_save = _reflect_banner(pack, dx_idx, session_dirty=session_dirty)
    c_banner, c_undo, c_val, c_save = st.columns([2.1, 0.72, 0.72, 0.72])
    with c_banner:
        _render_html(f'<div class="sot-banner-wrap">{banner_html}</div>')
    with c_undo:
        if st.button("되돌리기", type="secondary", use_container_width=True, key="sot_undo"):
            st.session_state.pop("sot_pending_edits", None)
            st.rerun()
    with c_val:
        if st.button("검증", type="secondary", use_container_width=True, key="sot_validate"):
            qm, q5, q1 = _apply_pending_edits(repo, manifest_pid, pending)
            issues = dx_editor.validate_q_pack_edits(
                qm or [],
                manifest_pid,
                dx_idx.sub_codes,
                q1_framework=q1,
                q5_recommendation=q5,
                pending_edits=pending if dx_index.pack_q_code(manifest_pid) == "q1" else None,
            )
            if not issues:
                st.success("검증 통과")
            else:
                for iss in issues:
                    fn = st.warning if iss.level == "warn" else st.error
                    fn(iss.message)
    with c_save:
        if st.button(
            "저장\n반영",
            type="primary",
            use_container_width=True,
            disabled=not can_save,
            key="sot_save",
        ):
            qm, q5, q1 = _apply_pending_edits(repo, manifest_pid, pending)
            result = dx_editor.save_q_pack_and_rebuild(
                repo,
                qm or [],
                manifest_pid,
                q1_framework=q1,
                q5_recommendation=q5,
                pending_edits=pending if dx_index.pack_q_code(manifest_pid) == "q1" else None,
            )
            if result.ok:
                st.session_state.pop("sot_pending_edits", None)
                st.cache_data.clear()
                st.success(result.message)
                st.rerun()
            else:
                st.error(result.message)
                for iss in result.issues:
                    st.warning(iss.message)


def _reflect_banner(
    pack: dict,
    dx_idx: dx_index.DxIndex,
    *,
    session_dirty: bool,
) -> tuple[str, bool]:
    """Returns (html, can_save)."""
    mode = dx_index.pack_edit_mode(pack.get("pack_id", ""))
    if mode == "deferred":
        return (
            '<div class="sot-reflect-banner sot-reflect-readonly">'
            "챕터 콘텐츠팩 — 편집 보류 (이견 조정 중). 상태만 표시합니다."
            "</div>",
            False,
        )
    if mode == "spine":
        return (
            '<div class="sot-reflect-banner sot-reflect-readonly">'
            "척추 코드 — 고영향 참조 전용. 편집은 별도 판단 후 진행합니다."
            "</div>",
            False,
        )
    if mode == "pilot_wait":
        return (
            '<div class="sot-reflect-banner sot-reflect-readonly">'
            "Q 수치팩 — 아직 편집 개방 전인 팩입니다."
            "</div>",
            False,
        )
    if mode != "editable":
        return (
            '<div class="sot-reflect-banner sot-reflect-readonly">'
            "이 팩은 현재 읽기 전용입니다."
            "</div>",
            False,
        )

    manifest_pid = pack.get("pack_id", "")
    sync_st, detail = dx_index.pack_mirror_sync_status_from_index(dx_idx, manifest_pid)
    if session_dirty or sync_st != "synced":
        extra = f" · {detail}" if detail and not session_dirty else ""
        return (
            '<div class="sot-reflect-banner sot-reflect-pending">'
            f"여기서 편집 → 리포트 · <strong>⚠ 아직 반영 안 됨</strong>{escape(extra)}"
            "</div>",
            True,
        )
    return (
        '<div class="sot-reflect-banner sot-reflect-synced">'
        "여기서 편집 → 리포트 · <strong>✓ 리포트와 일치</strong>"
        "</div>",
        True,
    )


def _format_item_label(meaning: str, hint: str) -> str:
    if hint:
        return f"{meaning} — {hint}"
    return meaning


def _cell_display_value(val: Any, *, locked: bool = False) -> str:
    if locked:
        return f"🔒 {val}"
    if val is None:
        return ""
    return str(val)


def _grid_df(grid_rows: list[dict[str, Any]], *, dev: bool) -> pd.DataFrame:
    records = []
    for r in grid_rows:
        locked = not r.get("editable", True)
        records.append(
            {
                "항목": _format_item_label(r["meaning"], r["hint"]),
                "값": _cell_display_value(r["value"], locked=locked),
                "어디에 반영": r["reflects"],
            }
        )
    df = pd.DataFrame(records)
    # TextColumn 편집 — int64 자동 추론 방지
    df["값"] = df["값"].astype(str)
    if dev:
        df["_key"] = [r["_row_key"] for r in grid_rows]
        df["_field_path"] = [r.get("field_path", "") for r in grid_rows]
    return df


def _render_q3_field_rows(
    grid_rows: list[dict[str, Any]],
    *,
    block_key: str,
    pending: dict[str, Any],
    q: str,
) -> dict[str, Any]:
    """편집 그리드 — dataframe 톤의 bordered 테이블 + 행별 위젯."""
    editable_rows = [r for r in grid_rows if r.get("editable", True)]
    if not editable_rows:
        return pending

    with st.container(border=True):
        _render_html('<span class="sot-edit-head-marker" aria-hidden="true"></span>')
        hdr = st.columns([2.3, 1, 1.3])
        with hdr[0]:
            st.markdown("**항목**")
        with hdr[1]:
            st.markdown("**값**")
        with hdr[2]:
            st.markdown("**어디에 반영**")

        for row in editable_rows:
            rk = str(row["_row_key"])
            fp = str(row.get("field_path") or "")
            spec = dx_index.q_field_editor_spec(q, fp)
            orig = row["value"]
            current = pending.get(rk, orig)
            meaning = escape(str(row["meaning"]))
            hint = escape(str(row.get("hint") or ""))
            reflect = escape(str(row.get("reflects") or "—"))

            col_label, col_val, col_ref = st.columns([2.3, 1, 1.3])
            with col_label:
                hint_html = (
                    f'<p class="sot-edit-item-hint">{hint}</p>' if hint else ""
                )
                _render_html(
                    f'<p class="sot-edit-item-name">{meaning}</p>{hint_html}'
                )
            with col_val:
                widget_key = f"sot_f_{block_key}_{rk}"
                if spec.get("type") == "select":
                    options = dx_index.q_field_select_options(q, str(spec.get("options_ref") or ""))
                    if not options:
                        options = [str(current)]
                    cur_s = str(current)
                    idx = options.index(cur_s) if cur_s in options else 0
                    new_val = st.selectbox(
                        "값",
                        options,
                        index=idx,
                        key=widget_key,
                        label_visibility="collapsed",
                    )
                elif spec.get("type") == "number":
                    try:
                        num = int(current)
                    except (TypeError, ValueError):
                        num = 0
                    lo = int(spec.get("min", 0))
                    hi = int(spec.get("max", 100))
                    new_val = st.number_input(
                        "값",
                        min_value=lo,
                        max_value=hi,
                        step=int(spec.get("step", 1)),
                        value=num,
                        key=widget_key,
                        label_visibility="collapsed",
                    )
                elif spec.get("type") == "textarea":
                    new_val = st.text_area(
                        "값",
                        value=str(current),
                        key=widget_key,
                        label_visibility="collapsed",
                        height=80,
                    )
                else:
                    new_val = st.text_input(
                        "값",
                        value=str(current),
                        key=widget_key,
                        label_visibility="collapsed",
                    )

                coerced = _coerce_value(orig, new_val)
                if coerced != orig:
                    pending[rk] = coerced
                elif rk in pending:
                    del pending[rk]
            with col_ref:
                _render_html(f'<p class="sot-edit-reflect">{reflect}</p>')

    return pending


def _render_q3_grid_block(
    grid_rows: list[dict[str, Any]],
    *,
    block_key: str,
    dev: bool,
    pending: dict[str, Any],
    q: str,
    readonly: bool = False,
) -> dict[str, Any]:
    if readonly:
        df = _grid_df(grid_rows, dev=dev)
        show_cols = ["항목", "값", "어디에 반영"]
        st.dataframe(df[show_cols], use_container_width=True, hide_index=True)
        return pending

    return _render_q3_field_rows(grid_rows, block_key=block_key, pending=pending, q=q)


def _render_q1_label_editor(pack: dict, dx_idx: dx_index.DxIndex) -> None:
    """Q1 metadata UI 라벨 pointer 에디터 (industries 트리 잠금)."""
    pid = pack.get("pack_id", "")
    q = "q1"
    pending: dict[str, Any] = st.session_state.setdefault("sot_pending_edits", {})
    dev = st.session_state.get("sot_dev_mode", False)

    grid_rows = dx_index.flatten_q1_label_rows(dx_idx.q1_framework)
    if not grid_rows:
        st.info("표시할 편집 항목이 없습니다.")
        return

    _render_html(
        '<p class="sot-sub-hint">'
        "UI 표시 문자열만 편집합니다. 산업·제품 분류 트리(industries)와 버전 배지는 잠겨 있습니다."
        "</p>"
    )

    sections: list[str] = []
    for row in grid_rows:
        sec = str(row.get("section") or "기타")
        if sec not in sections:
            sections.append(sec)

    for sec in sections:
        block = [r for r in grid_rows if r.get("section") == sec]
        if not block:
            continue
        _render_html(f'<div class="sot-sub-header">{escape(sec)}</div>')
        pending = _render_q3_grid_block(
            block,
            block_key=_q1_section_block_key(pid, sec),
            dev=dev,
            pending=pending,
            q=q,
            readonly=False,
        )

    st.session_state["sot_pending_edits"] = pending


def _q1_section_block_key(pid: str, section: str) -> str:
    slug = _Q1_SECTION_BLOCK_KEYS.get(section) or _safe_block_key(section)
    return f"{pid}_{slug}"


def _sub_filter_key(manifest_pid: str) -> str:
    return f"sot_sub_filter_{manifest_pid}"


def _ensure_sub_filter_default(manifest_pid: str, subs: list[str]) -> None:
    """팩별 세부산업 필터 — 기본값은 첫 세부산업(편집 폼 즉시 표시)."""
    key = _sub_filter_key(manifest_pid)
    options = ["전체"] + subs
    cur = st.session_state.get(key)
    if cur not in options:
        st.session_state[key] = subs[0] if subs else "전체"


def _render_q3_editor(pack: dict, dx_idx: dx_index.DxIndex) -> None:
    pid = pack.get("pack_id", "")
    q = dx_index.pack_q_code(pid)
    if q == "q1":
        _render_q1_label_editor(pack, dx_idx)
        return

    pending: dict[str, Any] = st.session_state.setdefault("sot_pending_edits", {})
    dev = st.session_state.get("sot_dev_mode", False)

    if q == "q5":
        rec_rows = dx_idx.q5_recommendation_rows()
        subs = sorted({str(r.get("sub_code", "")) for r in rec_rows if r.get("sub_code")})
    else:
        dx_pid = dx_index.resolve_dx_pack_id(pid)
        matrix_rows = dx_idx.matrix_rows(dx_pid)
        subs = sorted({str(r.get("sub_code", "")) for r in matrix_rows if r.get("sub_code")})

    _ensure_sub_filter_default(pid, subs)
    sub_key = _sub_filter_key(pid)

    _render_html('<p class="sot-field-label">세부산업</p>')
    c_sel, c_hint = st.columns(_SOT_SIDE_COLS)
    with c_sel:
        _render_html('<span class="sot-side-ctrl-marker" aria-hidden="true"></span>')
        sub_filter = st.selectbox(
            "세부산업",
            ["전체"] + subs,
            key=sub_key,
            label_visibility="collapsed",
        )
    sf = "" if sub_filter == "전체" else sub_filter
    with c_hint:
        if not sf:
            _render_html(
                '<p class="sot-sub-hint">'
                "전체 보기는 읽기 전용입니다. 값을 고치려면 세부산업을 하나 고르세요."
                "</p>"
            )
    grid_rows = (
        dx_index.flatten_q5_grid_rows(rec_rows, sub_filter=sf)
        if q == "q5"
        else dx_index.flatten_q_grid_rows(dx_idx.matrix_rows(dx_index.resolve_dx_pack_id(pid)), pid, sub_filter=sf)
    )

    if not grid_rows:
        st.info("표시할 편집 항목이 없습니다.")
        return

    if sf:
        sub_label = next((r["sub_label_ko"] for r in grid_rows if r["sub_label_ko"]), "")
        header = f"{sf} {sub_label}".strip()
        _render_html(f'<div class="sot-sub-header">{escape(header)}</div>')
        pending = _render_q3_grid_block(
            grid_rows, block_key=f"{pid}_{sf}", dev=dev, pending=pending, q=q, readonly=False
        )
    else:
        by_sub: dict[str, list[dict[str, Any]]] = {}
        for row in grid_rows:
            by_sub.setdefault(row["sub_code"], []).append(row)
        _render_html(
            '<p class="sot-sub-hint">'
            f"전체 {len(subs)}개 세부산업 요약 — 편집은 위에서 세부산업을 하나 고르세요."
            "</p>"
        )
        for sub in subs[:12]:
            block = by_sub.get(sub)
            if not block:
                continue
            sub_label = block[0].get("sub_label_ko") or ""
            header = f"{sub} {sub_label}".strip()
            with st.expander(header, expanded=False):
                pending = _render_q3_grid_block(
                    block,
                    block_key=f"{pid}_{sub}_ro",
                    dev=dev,
                    pending=pending,
                    q=q,
                    readonly=True,
                )
        if len(subs) > 12:
            st.caption(f"… 외 {len(subs) - 12}개 세부산업 (전체 펼침은 성능상 생략)")

    st.session_state["sot_pending_edits"] = pending


def _coerce_value(old: Any, new: Any) -> Any:
    if isinstance(old, bool):
        return str(new).lower() in ("true", "1", "yes")
    if isinstance(old, int):
        try:
            return int(new)
        except (TypeError, ValueError):
            return old
    if isinstance(old, float):
        try:
            return float(new)
        except (TypeError, ValueError):
            return old
    return new


def _render_readonly_pack(pack: dict, dx_idx: dx_index.DxIndex, lineage: dict) -> None:
    lineage_idx = sot.pack_lineage_index(lineage)
    row = lineage_idx.get(pack.get("pack_id"))
    if row:
        gen = sot.normalize_path_list(row.get("generates"))
        used = sot.normalize_path_list(row.get("used_by_loaders"))
        st.markdown("**반영 경로**")
        for p in gen:
            st.caption(f"생성 → `{p}`")
        if used:
            st.caption(f"사용 → {', '.join(used[:3])}{'…' if len(used) > 3 else ''}")
    dx_art = sot.normalize_path_list(pack.get("dx_artifacts"))
    if dx_art:
        st.markdown("**진실원 위치**")
        for p in dx_art:
            st.code(p, language=None)
    st.caption(f"상태 · {pack.get('coverage_status', '—')}")


def render() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)

    hub_pagebar(
        "진단툴",
        "진실원 관리",
        "팩 목록에서 고르고 값을 고친 뒤 리포트에 반영합니다",
        "DIAG-SOT",
    )

    col_refresh, col_dev = st.columns([1, 3])
    with col_refresh:
        if st.button("새로고침", type="secondary", key="sot_refresh"):
            st.cache_data.clear()
            st.session_state.pop("sot_pending_edits", None)
            st.rerun()
    with col_dev:
        st.session_state["sot_dev_mode"] = st.checkbox("개발자 보기", key="sot_dev_cb")

    manifest, m_err = sot.load_manifest()
    lineage, l_err = sot.load_lineage()
    repo = resolve_diagnosis_repo()

    if manifest is None or lineage is None or repo is None:
        reason = m_err or l_err or "diagnosis-tool clone 없음"
        st.error(f"데이터를 불러올 수 없습니다 — {reason}")
        st.code(f"git clone {DIAGNOSIS_TOOL_GITHUB}.git", language="bash")
        return

    dx_idx, dx_err = dx_index.load_dx_index(repo)
    if dx_idx is None:
        st.error(f"dx JSON 로드 실패 — {dx_err}")
        return

    packs: list[dict] = list(manifest.get("packs") or [])
    _status_strip(manifest, dx_idx, packs)

    selected = st.session_state.get("sot_selected_pack") or "q3_scale_profile"
    if selected not in {p.get("pack_id") for p in packs}:
        selected = "q3_scale_profile"

    _render_html('<p class="sot-section-title">팩 선택</p>')
    chip_pick = _render_pack_chips(packs, dx_idx, selected)
    all_pick = _render_all_packs_summary(packs, dx_idx, selected)
    if chip_pick or all_pick:
        new_sel = chip_pick or all_pick
        if new_sel != selected:
            st.session_state.pop("sot_pending_edits", None)
            st.session_state.pop(_sub_filter_key(new_sel), None)
        st.session_state["sot_selected_pack"] = new_sel
        if new_sel in set(_q_pack_ids()):
            st.session_state["sot_pack_pills"] = new_sel
        st.rerun()

    pill_sel = st.session_state.get("sot_pack_pills")
    valid_ids = {p.get("pack_id") for p in packs}
    if pill_sel and pill_sel in valid_ids:
        selected = pill_sel
        st.session_state["sot_selected_pack"] = selected

    pack = next((p for p in packs if p.get("pack_id") == selected), packs[0])
    manifest_pid = pack.get("pack_id", "")
    primary_dx = dx_index.resolve_dx_pack_id(manifest_pid)
    pending = st.session_state.get("sot_pending_edits") or {}
    session_dirty = bool(pending)

    title, desc = dx_index.pack_display(pack.get("pack_id", ""))
    _render_html(f'<p class="sot-section-title sot-section-title--pack">{escape(title)}</p>')
    _render_html(f'<p class="sot-pack-desc">{escape(desc)}</p>')

    mode = dx_index.pack_edit_mode(pack.get("pack_id", ""))
    if mode == "editable":
        _render_action_bar(
            pack,
            dx_idx,
            session_dirty=session_dirty,
            repo=repo,
            manifest_pid=manifest_pid,
            primary_dx=primary_dx,
            pending=pending,
        )
        _render_q3_editor(pack, dx_idx)
    else:
        banner_html, _ = _reflect_banner(pack, dx_idx, session_dirty=session_dirty)
        _render_html(banner_html)
        _render_readonly_pack(pack, dx_idx, lineage)

    dx_idx.close()
