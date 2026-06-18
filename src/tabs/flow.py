"""탭: 🔄 흐름 — V2.6.3.5 처리 흐름 시각화.

1-inbox → 3-archive (원본 보존) ↔ _index.db (정본 분석) ↔ mirror (Obsidian) → wiki (큐레이션)

각 단계의 현 잔량 + 동기 이상 가시화. *측정은 src.flow 위임, 본 모듈은 표시*.
"""
from __future__ import annotations

import streamlit as st

from src.config import (
    IRIS_KNOWLEDGE_ARCHIVE,
    IRIS_KNOWLEDGE_DB_NEW,
    IRIS_KNOWLEDGE_EXTERNAL,
    IRIS_KNOWLEDGE_MIRROR,
    IRIS_KNOWLEDGE_RAW,
    IRIS_KNOWLEDGE_ROOT,
    IRIS_KNOWLEDGE_STAGING,
    IRIS_KNOWLEDGE_WIKI,
    IRIS_KNOWLEDGE_INBOX,
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


def _card(
    *,
    stage_id: str,
    title: str,
    big: int | str,
    unit: str = "",
    sub: str = "",
    empty: bool = False,
    alert: bool = False,
) -> str:
    cls = "flow-card"
    if alert:
        cls += " alert"
    elif empty:
        cls += " empty"
    big_html = f"<div class='big'>{big}<span class='unit'>{unit}</span></div>" if unit else f"<div class='big'>{big}</div>"
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


def _render_flow_row(s: FlowSnapshot) -> None:
    inbox_sub = (
        f"<b>intake</b> {s.inbox.intake} · <b>external</b> {s.inbox.external}"
        f"<br/><b>staging</b> {s.inbox.staging} · <b>_failed</b> {s.inbox.failed}"
    )
    archive_sub = (
        f"<b>{s.archive.days}</b>일치 · 마지막 <b>{s.archive.last_date}</b>"
        if s.archive.docs > 0
        else "아직 카피 없음"
    )
    db_sub = (
        f"전체 <b>{_fmt(s.db.documents)}</b> · source <b>{_fmt(s.db.source_docs)}</b>"
        f"<br/>chunks <b>{_fmt(s.db.chunks)}</b> · FTS <b>{_fmt(s.db.fts)}</b>"
    )
    mirror_sub = "Obsidian용 .md" if s.mirror.exists else "디렉터리 부재"
    wiki_sub = "K5 큐레이션" if s.wiki.exists else "디렉터리 부재"

    cards = [
        _card(
            stage_id="① 1-inbox",
            title="📥 입력 대기",
            big=_fmt(s.inbox.total),
            unit="건",
            sub=inbox_sub,
            empty=(s.inbox.total == 0),
        ),
        _arrow(),
        _card(
            stage_id="② 3-archive",
            title="📦 원본 보존",
            big=_fmt(s.archive.docs),
            unit="건",
            sub=archive_sub,
            empty=(s.archive.docs == 0),
        ),
        _arrow(),
        _card(
            stage_id="③ _index.db",
            title="💾 정본 DB",
            big=_fmt(s.db.documents),
            unit="docs",
            sub=db_sub,
            empty=(not s.db.exists),
            alert=(not s.db.exists),
        ),
        _arrow(),
        _card(
            stage_id="④ mirror",
            title="📜 Obsidian 미러",
            big=_fmt(s.mirror.md_count),
            unit="md",
            sub=mirror_sub,
            empty=(s.mirror.md_count == 0),
        ),
        _arrow(),
        _card(
            stage_id="⑤ wiki",
            title="📚 큐레이션",
            big=_fmt(s.wiki.md_count),
            unit="md",
            sub=wiki_sub,
            empty=(s.wiki.md_count == 0),
        ),
    ]
    st.markdown("<div class='flow-row'>" + "".join(cards) + "</div>", unsafe_allow_html=True)


def _render_gaps(s: FlowSnapshot) -> None:
    st.markdown("### 동기 점검")

    # archive ↔ db
    a_gap = s.archive_db_gap
    if a_gap == 0:
        st.markdown(
            "<div class='flow-gap'>"
            "✅ <b>3-archive ↔ _index.db</b>: 일치 "
            f"(<code>{_fmt(s.archive.docs)} = {_fmt(s.db.source_docs)}</code>)"
            "</div>",
            unsafe_allow_html=True,
        )
    elif a_gap < 0:
        # archive 적음 → V2.6.3.2 이전부터 있던 doc + raw 카피 누락
        st.markdown(
            "<div class='flow-gap warn'>"
            f"⚠️ <b>3-archive ↔ _index.db</b>: archive에 <code>{abs(a_gap)}</code>건 부족 "
            f"(<code>archive {_fmt(s.archive.docs)} < db source {_fmt(s.db.source_docs)}</code>)"
            "<br/><span style='color:#999'>V2.6.3.2 카피 스크립트 이전부터 있던 doc일 가능성. "
            "<code>python scripts/archive_legacy_raw.py</code> 재실행으로 보충 가능.</span>"
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

    # db ↔ mirror
    m_gap = s.mirror_db_gap
    if m_gap == 0:
        st.markdown(
            "<div class='flow-gap'>"
            "✅ <b>_index.db source ↔ mirror</b>: 일치 "
            f"(<code>{_fmt(s.db.source_docs)} md</code>)"
            "</div>",
            unsafe_allow_html=True,
        )
    elif m_gap > 0:
        st.markdown(
            "<div class='flow-gap warn'>"
            f"⚠️ <b>_index.db source ↔ mirror</b>: mirror에 <code>{m_gap}</code>건 부족 "
            f"(<code>db source {_fmt(s.db.source_docs)} > mirror {_fmt(s.mirror.md_count)}</code>)"
            "<br/><span style='color:#999'>Obsidian sync로 미러 갱신 필요 — *📦 데이터* 탭의 Obsidian 동기화 UI 사용.</span>"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div class='flow-gap warn'>"
            f"⚠️ <b>_index.db source ↔ mirror</b>: mirror가 <code>{abs(m_gap)}</code>건 더 많음 "
            f"(<code>mirror {_fmt(s.mirror.md_count)} > db source {_fmt(s.db.source_docs)}</code>)"
            "<br/><span style='color:#999'>이전 LearningMaster/iris-mirror에서 단방향 카피된 잔재일 가능성. "
            "정상 신호 아님 — db 재인제스트 또는 mirror 정리 검토.</span>"
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
    st.markdown("### 🔄 처리 흐름 — 1-inbox → archive ↔ db ↔ mirror → wiki")
    st.caption("V2.6.3.5 · 각 단계의 잔량과 동기 이상을 한눈에 — 디스크 + DB 측정")

    s = measure_flow()
    _render_flow_row(s)
    _render_gaps(s)
    _render_paths(s)
