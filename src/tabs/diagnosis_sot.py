"""탭: 🔧 진단툴 — DIAG-SOT 진실원 관리 (P5 v2 · Q 파일럿).

좌: 팩 목록(챕터 그룹) · 우: 편집 그리드 + 반영 배너.
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
from src.ui_kit import hub_pagebar, hub_section

_CSS = """
<style>
.sot-v2-strip {
  display:flex; flex-wrap:wrap; gap:10px 18px;
  padding:12px 14px; margin-bottom:12px;
  border:1px solid rgba(47,128,196,0.14); border-radius:12px;
  background:linear-gradient(180deg,#fff 0%,#f8fbfe 100%);
  font-size:0.82rem; color:#344054; line-height:1.5;
}
.sot-v2-layout { display:grid; grid-template-columns:260px minmax(0,1fr); gap:14px; align-items:start; }
.sot-v2-list {
  border:1px solid rgba(47,128,196,0.14); border-radius:12px;
  background:#fff; max-height:72vh; overflow:auto; padding:8px 6px;
}
.sot-v2-group { margin:8px 0 4px; padding:4px 8px; font-size:0.7rem; font-weight:800; color:#667085; letter-spacing:0.04em; }
.sot-v2-pack-btn { width:100%; text-align:left !important; margin:2px 0 !important; }
.sot-v2-dot { display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:6px; vertical-align:middle; }
.sot-dot-synced { background:#12b76a; }
.sot-dot-pending { background:#f79009; }
.sot-v2-badge {
  display:inline-block; margin-left:6px; padding:1px 6px; border-radius:999px;
  font-size:0.62rem; font-weight:700; vertical-align:middle;
}
.sot-badge-deferred { background:rgba(152,162,179,0.18); color:#475467; }
.sot-badge-spine { background:rgba(47,128,196,0.12); color:#175cd3; }
.sot-badge-wait { background:rgba(247,144,9,0.14); color:#b54708; }
.sot-reflect-banner {
  padding:12px 14px; border-radius:10px; margin:10px 0 14px;
  border:1px solid rgba(47,128,196,0.16);
}
.sot-reflect-synced { background:rgba(18,183,106,0.08); border-color:rgba(18,183,106,0.25); color:#027a48; }
.sot-reflect-pending { background:rgba(247,144,9,0.1); border-color:rgba(247,144,9,0.28); color:#b54708; }
.sot-reflect-readonly { background:rgba(102,112,133,0.06); color:#475467; }
.sot-pack-title { font-size:1.05rem; font-weight:800; color:#101828; margin:0 0 4px; }
.sot-pack-desc { font-size:0.8rem; color:#667085; margin:0 0 8px; }
@media (max-width: 900px) { .sot-v2-layout { grid-template-columns: 1fr; } }
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
        runtime = (pack.get("member_paths") or [""])[0]
        dx_pid = dx_index.resolve_dx_pack_id(pack.get("pack_id", ""))
        status, _ = dx_index.runtime_sync_status(
            dx_idx.repo_root, runtime, dx_idx.q_matrix, dx_idx.q_framework, dx_pid
        )
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
    dx_pid = dx_index.resolve_dx_pack_id(pid)
    n = dx_idx.matrix_row_count(dx_pid)
    if n:
        return n
    return int(pack.get("member_count") or 0)


def _sync_dot(pack: dict, dx_idx: dx_index.DxIndex) -> str:
    mode = dx_index.pack_edit_mode(pack.get("pack_id", ""))
    if mode not in ("editable", "pilot_wait"):
        return ""
    runtime = (pack.get("member_paths") or [""])[0]
    if not runtime:
        return "sot-dot-pending"
    dx_pid = dx_index.resolve_dx_pack_id(pack.get("pack_id", ""))
    status, _ = dx_index.runtime_sync_status(
        dx_idx.repo_root, runtime, dx_idx.q_matrix, dx_idx.q_framework, dx_pid
    )
    return "sot-dot-synced" if status == "synced" else "sot-dot-pending"


def _pack_badge(mode: str) -> str:
    if mode == "deferred":
        return '<span class="sot-v2-badge sot-badge-deferred">편집 보류 (이견 조정 중)</span>'
    if mode == "spine":
        return '<span class="sot-v2-badge sot-badge-spine">참조 전용</span>'
    if mode == "pilot_wait":
        return '<span class="sot-v2-badge sot-badge-wait">파일럿 대기</span>'
    return ""


def _render_pack_list(packs: list[dict], dx_idx: dx_index.DxIndex, selected: str) -> str | None:
    groups: dict[str, list[dict]] = {}
    for pack in packs:
        g = dx_index.chapter_group(pack)
        groups.setdefault(g, []).append(pack)

    order = ["Q 수치팩", "A 콘텐츠팩", "기타"]
    clicked: str | None = None
    _render_html('<div class="sot-v2-list">')
    for gname in order:
        if gname not in groups:
            continue
        _render_html(f'<div class="sot-v2-group">{escape(gname)}</div>')
        for pack in sorted(groups[gname], key=lambda p: p.get("pack_id", "")):
            pid = pack.get("pack_id", "")
            title, _ = dx_index.pack_display(pid)
            mode = dx_index.pack_edit_mode(pid)
            dot = _sync_dot(pack, dx_idx)
            dot_cls = dot or "sot-dot-pending"
            count = _pack_row_count(pack, dx_idx)
            sel = " · 선택됨" if pid == selected else ""
            line = (
                f'<div style="padding:6px 8px;margin:2px 0;border-radius:8px;'
                f'{"background:rgba(47,128,196,0.08);" if pid == selected else ""}">'
                f'<span class="sot-v2-dot {dot_cls}"></span>'
                f'<strong style="font-size:0.78rem">{escape(title)}</strong>{sel}'
                f'<div style="font-size:0.68rem;color:#667085">{escape(pid)} · {count}행</div>'
                f"{_pack_badge(mode)}"
                f"</div>"
            )
            _render_html(line)
            if st.button("열기", key=f"sot_pick_{pid}", use_container_width=True):
                clicked = pid
    _render_html("</div>")
    return clicked


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
            "Q 수치팩 — q3 파일럿 PASS 후 편집을 엽니다."
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

    runtime = (pack.get("member_paths") or [""])[0]
    dx_pid = dx_index.resolve_dx_pack_id(pack.get("pack_id", ""))
    sync_st, detail = dx_index.runtime_sync_status(
        dx_idx.repo_root, runtime, dx_idx.q_matrix, dx_idx.q_framework, dx_pid
    )
    if session_dirty or sync_st != "synced":
        extra = f" · {detail}" if detail and not session_dirty else ""
        return (
            '<div class="sot-reflect-banner sot-reflect-pending">'
            "여기서 편집 → 실제 진단 리포트<br>"
            f"<strong>⚠ 수정됨 · 아직 반영 안 됨</strong>{escape(extra)}"
            "</div>",
            True,
        )
    return (
        '<div class="sot-reflect-banner sot-reflect-synced">'
        "여기서 편집 → 실제 진단 리포트<br>"
        "<strong>✓ 리포트와 일치</strong>"
        "</div>",
        True,
    )


def _render_q3_editor(pack: dict, dx_idx: dx_index.DxIndex) -> None:
    pid = pack.get("pack_id", "")
    dx_pid = dx_index.resolve_dx_pack_id(pid)
    matrix_rows = dx_idx.matrix_rows(dx_pid)
    subs = sorted({str(r.get("sub_code", "")) for r in matrix_rows if r.get("sub_code")})

    pending: dict[str, Any] = st.session_state.setdefault("sot_pending_edits", {})

    sub_filter = st.selectbox("세부산업", ["전체"] + subs, key="sot_sub_filter")
    sf = "" if sub_filter == "전체" else sub_filter
    grid_rows = dx_index.flatten_q3_grid_rows(matrix_rows, sub_filter=sf)

    for row in grid_rows:
        rk = row["_row_key"]
        if rk in pending:
            row["value"] = pending[rk]

    if not grid_rows:
        st.info("표시할 편집 항목이 없습니다.")
        return

    df = pd.DataFrame(
        [
            {
                "세부산업": r["sub_code"],
                "산업명": r["sub_label_ko"],
                "항목": r["meaning"],
                "부제": r["hint"],
                "값": r["value"],
                "어디에 반영": r["reflects"],
                "_key": r["_row_key"],
                "_editable": r["editable"],
            }
            for r in grid_rows
        ]
    )

    dev = st.session_state.get("sot_dev_mode", False)
    show_cols = ["세부산업", "산업명", "항목", "부제", "값", "어디에 반영"]
    if dev:
        show_cols.append("_key")

    edited = st.data_editor(
        df[show_cols],
        use_container_width=True,
        hide_index=True,
        disabled=["세부산업", "산업명", "항목", "부제", "어디에 반영"] + (["_key"] if dev else []),
        column_config={
            "값": st.column_config.TextColumn("값", width="medium"),
            "어디에 반영": st.column_config.TextColumn("어디에 반영", width="medium"),
        },
        key=f"sot_grid_{pid}_{sf}",
    )

    orig_map = {r["_row_key"]: r["value"] for r in grid_rows}
    key_by_label = {
        (r["sub_code"], r["meaning"]): r["_row_key"] for r in grid_rows
    }
    for _, erow in edited.iterrows():
        key = key_by_label.get((erow["세부산업"], erow["항목"]))
        if not key:
            continue
        new_val = erow["값"]
        old_val = orig_map.get(str(key))
        if str(new_val) != str(old_val):
            pending[str(key)] = _coerce_value(old_val, new_val)
        elif str(key) in pending:
            del pending[str(key)]

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
        if st.button("새로고침", type="secondary"):
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

    left, right = st.columns([1, 2.2])
    with left:
        hub_section("팩 목록", level="page")
        picked = _render_pack_list(packs, dx_idx, selected)
        if picked:
            st.session_state["sot_selected_pack"] = picked
            st.rerun()

    pack = next((p for p in packs if p.get("pack_id") == selected), packs[0])
    pending = st.session_state.get("sot_pending_edits") or {}
    session_dirty = bool(pending)

    with right:
        title, desc = dx_index.pack_display(pack.get("pack_id", ""))
        _render_html(f'<p class="sot-pack-title">{escape(title)}</p>')
        _render_html(f'<p class="sot-pack-desc">{escape(desc)}</p>')

        banner_html, can_edit = _reflect_banner(pack, dx_idx, session_dirty=session_dirty)
        _render_html(banner_html)

        mode = dx_index.pack_edit_mode(pack.get("pack_id", ""))
        if mode == "editable":
            _render_q3_editor(pack, dx_idx)

            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("되돌리기", type="secondary"):
                    st.session_state.pop("sot_pending_edits", None)
                    st.rerun()
            with c2:
                if st.button("검증", type="secondary"):
                    qm = dx_editor.load_q_matrix(repo.root)
                    qm = dx_index.apply_q3_grid_edits(
                        qm,
                        dx_index.resolve_dx_pack_id(pack.get("pack_id", "")),
                        pending,
                    )
                    issues = dx_editor.validate_q3_edits(
                        qm,
                        dx_index.resolve_dx_pack_id(pack.get("pack_id", "")),
                        dx_idx.sub_codes,
                    )
                    if not issues:
                        st.success("검증 통과")
                    else:
                        for iss in issues:
                            fn = st.warning if iss.level == "warn" else st.error
                            fn(iss.message)
            with c3:
                if st.button("저장하고 리포트에 반영", type="primary", disabled=not can_edit):
                    qm = dx_editor.load_q_matrix(repo.root)
                    dx_pid = dx_index.resolve_dx_pack_id(pack.get("pack_id", ""))
                    qm = dx_index.apply_q3_grid_edits(qm, dx_pid, pending)
                    runtime = (pack.get("member_paths") or [""])[0]
                    result = dx_editor.save_q3_and_rebuild(
                        repo, qm, runtime, dx_pack_id=dx_pid
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
        else:
            _render_readonly_pack(pack, dx_idx, lineage)

    dx_idx.close()
