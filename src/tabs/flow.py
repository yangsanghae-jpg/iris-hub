"""탭: 🔄 흐름 — V2.6.3.7 처리 콘솔.

V2.6.3.5: 5 단계 카드 가시화
V2.6.3.6: mirror 진입 자격 정책
V2.6.3.7: 데이터 탭의 재처리·sync 액션을 이쪽으로 이관 + 묶음/개별/선택 처리

구성:
  ① 처리 상태 4 카드 (대기/처리중/완료/영구보존)
  ② 처리 액션 — 묶음 / 개별 순서 / 선택 처리 + 야간 스케줄 체크박스 (UI만)
  ③ 진행률 (실행 직후)
  ④ Obsidian 동기화 (기존 정책 유지)
  ⑤ 단계별 흐름 가시화 (기존 5 카드)
  ⑥ 동기 점검
"""
from __future__ import annotations

import streamlit as st

from src.ui_kit import hub_pagebar, hub_section


_CSS = """
<style>
.flow-row {
  display:grid;
  gap:8px;
  align-items:stretch;
  margin:12px 0 10px 0;
}
.flow-row.queue {
  grid-template-columns: minmax(0, 1fr) 24px minmax(0, 1fr) 24px minmax(0, 1fr) 24px minmax(0, 1fr);
}
.flow-row.pipeline {
  grid-template-columns: minmax(0, 1fr) 22px minmax(0, 1fr) 22px minmax(0, 1fr) 22px minmax(0, 1fr) 22px minmax(0, 1fr);
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
.flow-card.alert {
  border-color:rgba(240,68,56,0.34);
  background:linear-gradient(180deg, #fffafa 0%, #fff5f5 100%);
}
.flow-card.alert::before { background:linear-gradient(90deg, #f04438, rgba(240,68,56,0.35)); }
.flow-card.empty {
  border-color:rgba(152,162,179,0.22);
  background:linear-gradient(180deg, #ffffff 0%, #fbfcfe 100%);
}
.flow-card.empty::before { background:linear-gradient(90deg, #98a2b3, rgba(152,162,179,0.18)); }
.flow-card.active {
  border-color:rgba(47,128,196,0.40);
  background:linear-gradient(180deg, #f7fbff 0%, #eef7ff 100%);
  box-shadow:0 10px 26px rgba(47,128,196,0.10);
}
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
.flow-card.alert .stage-id { background:rgba(240,68,56,0.10); color:#d92d20; }
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
.flow-card .sub b { color:#344054; font-weight:800; }
.flow-arrow {
  display:flex;
  align-items:center;
  justify-content:center;
  font-size:1.25rem;
  color:#98a2b3;
  min-width:0;
}
.flow-gap {
  margin-top:10px;
  padding:11px 13px;
  border:1px solid rgba(47,128,196,0.16);
  border-left:4px solid #2f80c4;
  background:linear-gradient(90deg, rgba(47,128,196,0.08), rgba(47,128,196,0.025));
  border-radius:10px;
  font-size:0.82rem;
  color:#344054;
}
.flow-gap.warn {
  border-color:rgba(247,144,9,0.24);
  border-left-color:#f79009;
  background:linear-gradient(90deg, rgba(247,144,9,0.10), rgba(247,144,9,0.025));
}
.flow-gap.alert {
  border-color:rgba(240,68,56,0.24);
  border-left-color:#f04438;
  background:linear-gradient(90deg, rgba(240,68,56,0.10), rgba(240,68,56,0.025));
}
.flow-gap code { font-size:0.86rem; }
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
}
.flow-console-note strong { color:#172033; font-weight:800; }
.flow-stage-title {
  margin:10px 0 6px 0;
  font-size:0.78rem;
  font-weight:850;
  color:#2f80c4;
  letter-spacing:0.02em;
}
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
  .flow-row.queue,
  .flow-row.pipeline {
    grid-template-columns:1fr;
  }
  .flow-arrow { display:none; }
}
</style>
"""


# ─── ② 처리 액션 (묶음 / 개별 / 선택) ──────────────────────────────────
def _render_actions() -> None:
    from src.engine.curate import queue as q

    hub_section("처리 액션")

    # K2 토글 + 야간 스케줄 체크박스
    col1, col2, col3 = st.columns([1, 1, 2])
    use_k2 = col1.toggle("🤖 K2 LLM 분석", value=True, key="flow_use_k2",
                         help="자료당 5~30초. 끄면 규칙만으로 빠르게.")
    batch_n = col2.number_input("묶음 크기", min_value=1, max_value=50, value=5,
                                key="flow_batch_n",
                                help="묶음 처리 시 한번에 N건. M2 권장 5~10, M5 10~20.")
    schedule_night = col3.checkbox(
        "🌙 이후 자동으로 야간 처리 (스케줄러 박힘 후 활성)",
        value=False, key="flow_schedule_night", disabled=True,
        help="V2.6.3.7은 UI 자리만 둠. 야간 스케줄러는 별도 사이클에서 박음."
    )

    b1, b2, b3 = st.columns(3)
    do_batch = b1.button(
        f"📦 묶음 처리 ({batch_n}건)", use_container_width=True, key="flow_batch",
        help=f"대기열 위에서부터 {batch_n}건을 일괄 처리"
    )
    do_one = b2.button(
        "➡️ 개별 순서 처리 (1건)", use_container_width=True, key="flow_one",
        help="대기열 첫 자료 1건만 상세 처리"
    )

    # 선택 처리 — 대기열에서 직접 골라 처리 (V2.6.3.8 — doc_id 기반)
    snap = q.measure_queue(max_list=200)
    selected_doc_ids: list[str] = []
    if snap.waiting_docs:
        with b3:
            st.caption("✋ 선택 처리")
            # title (doc_id) 형태로 표시 — 사용자가 식별 가능
            options = {
                f"{d['title']} ({d['doc_id'][:24]})": d["doc_id"]
                for d in snap.waiting_docs[:50]
            }
            picked = st.multiselect(
                "대기에서 골라 우선 처리",
                options=list(options.keys()),
                key="flow_picked",
                label_visibility="collapsed",
            )
            selected_doc_ids = [options[name] for name in picked]
            do_picked = st.button(
                f"✋ 선택 {len(selected_doc_ids)}건 처리",
                use_container_width=True, key="flow_picked_run",
                disabled=(len(selected_doc_ids) == 0),
            )
    else:
        with b3:
            st.button("✋ 선택 처리 (대기 없음)",
                      use_container_width=True, disabled=True, key="flow_picked_run")
            do_picked = False

    # 실행 분기 (V2.6.3.8 — doc_id 리스트)
    doc_ids: list[str] = []
    if do_batch:
        doc_ids = q.fetch_waiting(int(batch_n))
    elif do_one:
        doc_ids = q.fetch_waiting(1)
    elif do_picked and selected_doc_ids:
        doc_ids = selected_doc_ids

    if doc_ids:
        prog = st.progress(0.0, text=f"처리 시작 — {len(doc_ids)}건…")
        with st.spinner(f"K2={'켬' if use_k2 else '끔'} · {len(doc_ids)}건 처리 중…"):
            r = q.process_batch(doc_ids, use_k2=use_k2)
        prog.progress(1.0, text=f"완료 — {r.succeeded}/{r.requested}건")

        rc1, rc2, rc3, rc4 = st.columns(4)
        rc1.metric("요청", r.requested)
        rc2.metric("성공", r.succeeded)
        rc3.metric("실패", r.failed)
        rc4.metric("건너뜀", r.skipped, help="이미 처리중이거나 빈 청크")

        if r.errors:
            with st.expander(f"⚠️ 오류 {len(r.errors)}건", expanded=True):
                for name, err in r.errors[:20]:
                    st.write(f"- `{name}` — {err}")
        elif r.succeeded > 0:
            st.success(f"✅ {r.succeeded:,}건 처리 완료 — 흐름 갱신을 보려면 새로고침")


# ─── ③ Obsidian 동기화 ────────────────────────────────────────────────
def _render_sync() -> None:
    from src import obsidian_sync as osync

    hub_section("Obsidian 동기화")
    st.caption(
        "📚 정본 DB → 미러 단방향. **진입 자격**(K2 분석 + 매트릭스 키) 통과 자료만 박힘. "
        "자격 미달·DB 없는 좀비 .md는 자동 청소 (V2.6.3.6)."
    )

    sb1, sb2 = st.columns(2)
    sync_changed = sb1.button(
        "🔄 변경분만 동기화", use_container_width=True, key="flow_osync_changed",
        help="K2 재분석 또는 신규 자료만 다시 씀 (증분, 빠름)",
    )
    sync_force = sb2.button(
        "🔁 전체 다시 쓰기", use_container_width=True, key="flow_osync_force",
        help="변경 여부 무시하고 모든 자료 .md를 다시 씀 (느림)",
    )

    if sync_changed or sync_force:
        with st.spinner(f"mirror 동기화 중… {'전체 강제' if sync_force else '변경분'}"):
            sr = osync.sync_all(force=bool(sync_force))

        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("스캔", sr.scanned)
        sc2.metric("자격 통과", sr.eligible, help="K2 + 매트릭스")
        sc3.metric("작성", sr.written)
        sc4.metric("변경 없음", sr.skipped)

        sd1, sd2, sd3, sd4 = st.columns(4)
        sd1.metric("진입 거절", sr.rejected, help="자격 미달")
        sd2.metric("기존 .md 삭제", sr.purged)
        sd3.metric("좀비 삭제", sr.zombies, help="DB에 없는 잔재")
        sd4.metric("오류", len(sr.errors))

        if sr.errors:
            with st.expander(f"⚠️ 오류 {len(sr.errors)}건", expanded=True):
                for doc_id, err in sr.errors[:20]:
                    st.write(f"- `{doc_id}` — {err}")
        else:
            cleanup = sr.purged + sr.zombies
            msg_bits = []
            if sr.written > 0:
                msg_bits.append(f"✅ {sr.written:,}건 작성")
            if sr.skipped > 0:
                msg_bits.append(f"{sr.skipped:,}건 변경 없음")
            if cleanup > 0:
                msg_bits.append(f"🧹 {cleanup:,}건 정리")
            if msg_bits:
                st.success(" · ".join(msg_bits))
            else:
                st.info("🟢 mirror 동기 완료")


def _render_safety_audit() -> None:
    """안전망 점검 — 좀비 락·고아·FTS 불일치 자동 정정 (액션)."""
    sn_col1, sn_col2 = st.columns([1, 3])
    with sn_col1:
        if st.button("🛡 안전망 점검", use_container_width=True, key="flow_audit",
                     help="좀비 락·고아 chunks/meta·FTS 불일치 자동 정정"):
            from src import health
            rep = health.audit(auto_fix=True)
            if rep.ok:
                st.success("✅ 무결성 OK — 좀비 없음")
            else:
                st.warning(f"🛡 {rep.auto_fixed}건 정정 — " + " · ".join(rep.notes[:5]))
    with sn_col2:
        st.caption(
            "🛡 안전망 — 좀비 락·고아 chunks/meta·FTS 불일치를 *자동 정정*. "
            "묶음 처리 시작 전에도 좀비 락만은 자동 해제."
        )


def render() -> None:
    # S3-R3: 흐름 = 얇은 실행 콘솔(명령만). 현황·진척·파이프라인 관측은 데이터 탭으로 이관.
    #        관측 렌더러(_render_queue_row·_render_stage_progress·_render_flow_row·
    #        _render_gaps·_render_paths)는 더 이상 호출 안 함(후속 정리 대상).
    st.markdown(_CSS, unsafe_allow_html=True)
    hub_pagebar(
        "흐름",
        "Processing Console",
        "대기 자료를 묶음·개별·선택으로 처리하고 Obsidian 미러 동기화를 실행합니다. 현황·진척은 데이터 탭에서 봅니다.",
        "Queue Ready",
    )

    _render_actions()
    _render_safety_audit()
    st.divider()
    _render_sync()
