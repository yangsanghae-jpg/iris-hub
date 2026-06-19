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

from src.config import (
    IRIS_KNOWLEDGE_ARCHIVE,
    IRIS_KNOWLEDGE_DB_NEW,
    IRIS_KNOWLEDGE_EXTERNAL,
    IRIS_KNOWLEDGE_INBOX,
    IRIS_KNOWLEDGE_MIRROR,
    IRIS_KNOWLEDGE_RAW,
    IRIS_KNOWLEDGE_ROOT,
    IRIS_KNOWLEDGE_STAGING,
    IRIS_KNOWLEDGE_WIKI,
)
from src.flow import FlowSnapshot, measure_flow


_CSS = """
<style>
.flow-row { display:flex; gap:8px; align-items:stretch; margin:18px 0 8px 0; }
.flow-card {
  flex:1; border:1px solid rgba(120,120,120,0.25); border-radius:8px;
  padding:12px 14px; background:rgba(120,120,120,0.04);
  display:flex; flex-direction:column; gap:6px; min-width:0;
}
.flow-card.alert { border-color:#f08585; background:rgba(240,133,133,0.08); }
.flow-card.empty { opacity:0.55; }
.flow-card.active { border-color:#5fa8ff; background:rgba(95,168,255,0.10); }
.flow-card h4 { margin:0; font-size:0.95em; font-weight:600; }
.flow-card .stage-id { font-size:0.7em; color:#888; letter-spacing:0.5px; }
.flow-card .big { font-size:1.8em; font-weight:700; line-height:1.1; }
.flow-card .unit { font-size:0.8em; color:#888; margin-left:4px; }
.flow-card .sub { font-size:0.78em; color:#999; }
.flow-card .sub b { color:#bbb; }
.flow-arrow {
  display:flex; align-items:center; justify-content:center;
  font-size:1.5em; color:#aaa; min-width:24px;
}
.flow-gap {
  margin-top:14px; padding:10px 12px;
  border-left:3px solid #5fa8ff; background:rgba(95,168,255,0.06);
  border-radius:4px; font-size:0.85em;
}
.flow-gap.warn { border-left-color:#ffb86b; background:rgba(255,184,107,0.08); }
.flow-gap.alert { border-left-color:#f08585; background:rgba(240,133,133,0.08); }
.flow-gap code { font-size:0.92em; }
</style>
"""


def _fmt(n: int) -> str:
    return f"{n:,}"


def _card(*, stage_id: str, title: str, big, unit: str = "",
          sub: str = "", empty: bool = False, alert: bool = False,
          active: bool = False) -> str:
    cls = "flow-card"
    if alert:
        cls += " alert"
    elif active:
        cls += " active"
    elif empty:
        cls += " empty"
    big_html = (
        f"<div class='big'>{big}<span class='unit'>{unit}</span></div>"
        if unit else f"<div class='big'>{big}</div>"
    )
    sub_html = f"<div class='sub'>{sub}</div>" if sub else ""
    return (
        f"<div class='{cls}'>"
        f"<div class='stage-id'>{stage_id}</div>"
        f"<h4>{title}</h4>"
        f"{big_html}{sub_html}"
        f"</div>"
    )


def _arrow() -> str:
    return "<div class='flow-arrow'>→</div>"


# ─── ① 처리 상태 4 카드 ────────────────────────────────────────────────
def _render_queue_row() -> None:
    from src import queue as q
    snap = q.measure_queue(max_list=20)

    sub_waiting = "K2 미분석" if snap.waiting else "처리 대기 없음"
    sub_in = "락 박힘" if snap.in_progress else "—"
    sub_done = "K2 분석 통과"
    sub_arch = f"마지막 {_fmt(snap.archived)}건" if snap.archived else "—"

    cards = [
        _card(stage_id="① 대기열", title="📥 대기", big=_fmt(snap.waiting),
              unit="건", sub=sub_waiting, empty=(snap.waiting == 0)),
        _arrow(),
        _card(stage_id="② 처리중", title="⚙️ 처리중", big=_fmt(snap.in_progress),
              unit="건", sub=sub_in, active=(snap.in_progress > 0)),
        _arrow(),
        _card(stage_id="③ 완료", title="✅ 완료", big=_fmt(snap.done),
              unit="docs", sub=sub_done, empty=(snap.done == 0)),
        _arrow(),
        _card(stage_id="④ 영구보존", title="📦 archive", big=_fmt(snap.archived),
              unit="건", sub=sub_arch, empty=(snap.archived == 0)),
    ]
    st.markdown("<div class='flow-row'>" + "".join(cards) + "</div>",
                unsafe_allow_html=True)

    # 처리중 N건 있으면 좀비 정리 안내
    if snap.in_progress > 0:
        st.caption(
            f"⚙️ 처리중 {snap.in_progress}건 — 30분 이상 처리중인 좀비 락은 "
            "다음 묶음 처리 시 자동 해제됩니다."
        )

    # 안전망 점검 (V2.6.3.8)
    sn_col1, sn_col2 = st.columns([1, 3])
    with sn_col1:
        if st.button("🛡 안전망 점검", use_container_width=True, key="flow_audit",
                     help="좀비 락·고아 chunks/meta·FTS 불일치 자동 정정"):
            from src import health
            rep = health.audit(auto_fix=True)
            if rep.ok:
                st.success("✅ 무결성 OK — 좀비 없음")
            else:
                st.warning(
                    f"🛡 {rep.auto_fixed}건 정정 — "
                    + " · ".join(rep.notes[:5])
                )
    with sn_col2:
        st.caption(
            "🛡 안전망 — 좀비 락·고아 chunks/meta·FTS 불일치를 *자동 정정*. "
            "묶음 처리 시작 전에도 좀비 락만은 자동 해제."
        )


def _render_stage_progress() -> None:
    """V2.7.0 — K2 3 단계 진척 가시화."""
    from src.flow import measure_flow
    s = measure_flow()
    total = s.db.source_docs
    if total == 0:
        return

    st.markdown("##### K2 단계별 진척")
    cols = st.columns(3)
    stages = [
        ("① extract", "🔑 키워드", s.db.extract_done, "topics·entities·concepts"),
        ("② classify", "🏷 분류", s.db.classify_done, "industry·area·5축"),
        ("③ summarize", "📝 요약", s.db.summarize_done, "summary·3 blurb"),
    ]
    for col, (label, emoji, done, sub) in zip(cols, stages):
        pct = (done / total) * 100 if total else 0
        with col:
            st.markdown(
                f"<div style='font-size:0.78em;color:#888'>{label}</div>"
                f"<div style='font-size:0.95em;font-weight:600'>{emoji}</div>"
                f"<div style='font-size:1.4em;font-weight:700'>{done:,} <span style='font-size:0.6em;color:#888'>/ {total:,}</span></div>"
                f"<div style='font-size:0.75em;color:#999'>{sub}</div>",
                unsafe_allow_html=True,
            )
            st.progress(min(pct / 100, 1.0))


# ─── ② 처리 액션 (묶음 / 개별 / 선택) ──────────────────────────────────
def _render_actions() -> None:
    from src import queue as q

    st.markdown("### 처리 액션")

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

    st.markdown("### Obsidian 동기화 (iris-mirror)")
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


# ─── ④ 단계별 흐름 가시화 (기존 5 카드) ────────────────────────────────
def _render_flow_row(s: FlowSnapshot) -> None:
    inbox_sub = (
        f"<b>intake</b> {s.inbox.intake} · <b>external</b> {s.inbox.external}"
        f"<br/><b>staging</b> {s.inbox.staging} · <b>_failed</b> {s.inbox.failed}"
    )
    archive_sub = (
        f"<b>{s.archive.days}</b>일치 · 마지막 <b>{s.archive.last_date}</b>"
        if s.archive.docs > 0 else "아직 카피 없음"
    )
    db_sub = (
        f"전체 <b>{_fmt(s.db.documents)}</b> · source <b>{_fmt(s.db.source_docs)}</b>"
        f"<br/>chunks <b>{_fmt(s.db.chunks)}</b> · FTS <b>{_fmt(s.db.fts)}</b>"
        f"<br/>📚 진입 자격 <b>{_fmt(s.db.eligible)}</b> (K2+매트릭스)"
    )
    mirror_sub = "Obsidian용 .md" if s.mirror.exists else "디렉터리 부재"
    wiki_sub = "K5 큐레이션" if s.wiki.exists else "디렉터리 부재"

    cards = [
        _card(stage_id="① 1-inbox", title="📥 입력 대기",
              big=_fmt(s.inbox.total), unit="건", sub=inbox_sub,
              empty=(s.inbox.total == 0)),
        _arrow(),
        _card(stage_id="② 3-archive", title="📦 원본 보존",
              big=_fmt(s.archive.docs), unit="건", sub=archive_sub,
              empty=(s.archive.docs == 0)),
        _arrow(),
        _card(stage_id="③ _index.db", title="💾 정본 DB",
              big=_fmt(s.db.documents), unit="docs", sub=db_sub,
              empty=(not s.db.exists), alert=(not s.db.exists)),
        _arrow(),
        _card(stage_id="④ mirror", title="📜 Obsidian 미러",
              big=_fmt(s.mirror.md_count), unit="md", sub=mirror_sub,
              empty=(s.mirror.md_count == 0)),
        _arrow(),
        _card(stage_id="⑤ wiki", title="📚 큐레이션",
              big=_fmt(s.wiki.md_count), unit="md", sub=wiki_sub,
              empty=(s.wiki.md_count == 0)),
    ]
    st.markdown("<div class='flow-row'>" + "".join(cards) + "</div>",
                unsafe_allow_html=True)


# ─── ⑤ 동기 점검 ──────────────────────────────────────────────────────
def _render_gaps(s: FlowSnapshot) -> None:
    st.markdown("### 동기 점검")

    # archive ↔ db.source — raw 인제스트만 비교 (ref_catalog 등은 archive 대상 아님)
    a_gap = s.archive_db_gap
    if a_gap == 0:
        st.markdown(
            "<div class='flow-gap'>"
            f"✅ <b>3-archive ↔ _index.db</b>: 일치 "
            f"(<code>{_fmt(s.archive.docs)} = {_fmt(s.db.source_docs)}</code>)"
            "</div>",
            unsafe_allow_html=True,
        )
    elif a_gap < 0:
        st.markdown(
            "<div class='flow-gap'>"
            f"ℹ️ <b>3-archive ↔ _index.db</b>: archive <code>{_fmt(s.archive.docs)}</code> · "
            f"DB source <code>{_fmt(s.db.source_docs)}</code> "
            f"(차이 <code>{abs(a_gap)}</code>건)"
            "<br/><span style='color:#999'>"
            "ref_catalog·진단툴 자료는 별도 경로 인제스트되어 archive 대상이 아님 — 정상."
            "</span>"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div class='flow-gap'>"
            f"ℹ️ <b>3-archive ↔ _index.db</b>: archive가 <code>{a_gap}</code>건 더 많음 "
            "(정상 — archive는 누적 보존)."
            "</div>",
            unsafe_allow_html=True,
        )

    # db.eligible ↔ mirror
    m_gap = s.mirror_db_gap
    if m_gap == 0:
        st.markdown(
            "<div class='flow-gap'>"
            "✅ <b>진입 자격 ↔ mirror</b>: 일치 "
            f"(<code>{_fmt(s.db.eligible)} md</code>) — *지식화된 자료*만 mirror에 박힘."
            "</div>",
            unsafe_allow_html=True,
        )
    elif m_gap > 0:
        st.markdown(
            "<div class='flow-gap warn'>"
            f"⚠️ <b>진입 자격 ↔ mirror</b>: mirror에 <code>{m_gap}</code>건 부족"
            "<br/><span style='color:#999'>위 Obsidian 동기화 버튼으로 보충.</span>"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div class='flow-gap alert'>"
            f"❌ <b>진입 자격 ↔ mirror</b>: mirror에 <code>{abs(m_gap)}</code>건 잉여"
            "<br/><span style='color:#999'>Obsidian 동기화 시 자동 정리됨.</span>"
            "</div>",
            unsafe_allow_html=True,
        )


def _render_paths(s: FlowSnapshot) -> None:
    with st.expander("📍 실제 경로", expanded=False):
        st.code(
            f"ROOT     {IRIS_KNOWLEDGE_ROOT}\n"
            f"1-inbox/\n"
            f"  intake   {IRIS_KNOWLEDGE_RAW}  ({s.inbox.intake})\n"
            f"  external {IRIS_KNOWLEDGE_EXTERNAL}  ({s.inbox.external})\n"
            f"  staging  {IRIS_KNOWLEDGE_STAGING}  ({s.inbox.staging})\n"
            f"  _failed  {IRIS_KNOWLEDGE_INBOX / '_failed'}  ({s.inbox.failed})\n"
            f"3-archive  {IRIS_KNOWLEDGE_ARCHIVE}  ({s.archive.docs} docs · {s.archive.days}일)\n"
            f"_index.db  {IRIS_KNOWLEDGE_DB_NEW}  ({'존재' if s.db.exists else '부재'} · {s.db.db_size_mb}MB)\n"
            f"mirror     {IRIS_KNOWLEDGE_MIRROR}  ({s.mirror.md_count} md)\n"
            f"wiki       {IRIS_KNOWLEDGE_WIKI}  ({s.wiki.md_count} md)",
            language="text",
        )


def render() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown("### 🔄 처리 콘솔 — 대기 → 처리중 → 완료")
    st.caption(
        "V2.6.3.7 · 대기 자료를 묶음·개별·선택으로 처리. "
        "Obsidian 동기화도 여기서. 데이터 탭은 *상태 보고*만 표시."
    )

    _render_queue_row()
    _render_stage_progress()
    _render_actions()
    st.divider()
    _render_sync()
    st.divider()

    s = measure_flow()
    st.markdown("### 단계별 흐름")
    _render_flow_row(s)
    _render_gaps(s)
    _render_paths(s)
