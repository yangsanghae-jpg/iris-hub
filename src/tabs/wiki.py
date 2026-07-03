"""탭: 📚 위키 — 개념 중심 검색 위키 (S5, WIKI_REBUILD_DESIGN).

"이름으로 찾고 개념 페이지를 읽는다" (텍스트·리스트 중심).
관계 시각 탐색은 그래프 탭(S6). 같은 S4 개념 데이터를 다른 방식으로 소비.
UI는 hub_ui.css 공용 컴포넌트만 사용(원시 헤더·인라인 스타일 금지, UI_UX_DESIGN).
"""
from __future__ import annotations

import html

import streamlit as st

from src.engine.retrieve import search as retrieve
from src.store import knowledge
from src.ui_kit import hub_kpi_grid, hub_pagebar, hub_section

_CHANNEL = {"doc": "doc", "chat": "chat", "web": "web"}


def _badge(cls: str, text: str) -> str:
    return f"<span class='hub-badge {cls}'>{html.escape(text)}</span>"


def _select(cid: str) -> None:
    st.session_state["wiki_concept"] = cid


# ─── 좌 레일: 개념 인덱스 + 후보 ────────────────────────────────────────────
def _render_rail() -> None:
    concepts = knowledge.top_concepts(n=40)
    hub_section("개념 인덱스 · degree 순")
    if not concepts:
        st.caption("개념 없음 — 개념추출(S4)/재수집 후 채워집니다.")
    else:
        top = concepts[0].degree or 1
        for c in concepts:
            active = st.session_state.get("wiki_concept") == c.concept_id
            st.button(
                f"{'● ' if active else ''}{c.canonical}   ·  {c.degree}",
                key=f"wiki_idx_{c.concept_id}", use_container_width=True,
                on_click=_select, args=(c.concept_id,),
            )
            pct = (c.degree / top * 100) if c.degree else 0
            st.markdown(
                f"<div class='hub-degbar'><span style='width:{pct:.0f}%'></span></div>",
                unsafe_allow_html=True,
            )

    n = len(knowledge.list_candidates(n=1000))
    hub_section("개념 후보")
    st.markdown(
        f"<div class='hub-candbox'>🧩 <b>{n}</b>건 · 사전 미등록 — 등록·기각은 데이터 탭 큐레이션에서.</div>",
        unsafe_allow_html=True,
    )


# ─── 메인: 개념 페이지 ──────────────────────────────────────────────────────
def _render_concept_page(cid: str) -> None:
    page = knowledge.concept_page(cid)
    if page is None:
        st.info(f"개념 없음: {cid}")
        return
    c = page.concept
    trust_cls = "verified" if c.trust == "verified" else "candidate"
    st.markdown(f"<div class='hub-breadcrumb'>위키 › concepts › {html.escape(cid)}</div>",
                unsafe_allow_html=True)
    st.markdown(
        f"<div class='hub-concept-head'>"
        f"<span class='hub-concept-title'>{html.escape(c.canonical)}</span>"
        f"{_badge(trust_cls, c.trust)}</div>",
        unsafe_allow_html=True,
    )
    hub_kpi_grid([
        ("근거 문서", str(len(page.docs)), "concept_docs"),
        ("관련 개념", str(len(page.related)), "cooccur"),
        ("별칭", str(len(page.aliases)), "다국어"),
        ("degree", str(c.degree), "active 문서"),
    ])

    hub_section("정의")
    st.markdown(
        f"<div class='hub-def'>{html.escape(c.definition) if c.definition else '<i>정의 미작성</i>'}</div>",
        unsafe_allow_html=True,
    )

    if page.aliases:
        hub_section("별칭 · 다국어")
        chips = "".join(f"<span class='hub-chip'>{html.escape(a)}</span>" for a in page.aliases)
        st.markdown(chips, unsafe_allow_html=True)

    if page.related:
        hub_section("관련 개념 · 동시출현")
        cols = st.columns(min(len(page.related), 4))
        for i, r in enumerate(page.related):
            cols[i % len(cols)].button(
                f"{r.canonical} · {r.degree}", key=f"wiki_rel_{cid}_{r.concept_id}",
                use_container_width=True, on_click=_select, args=(r.concept_id,),
            )

    hub_section(f"근거 문서 · {len(page.docs)}건")
    if not page.docs:
        st.caption("아직 연결된 문서 없음 — K2 개념추출(재수집) 후 채워집니다.")
    for d in page.docs[:30]:
        badge = _badge(_CHANNEL.get(d.channel, "doc"), d.channel)
        stt = "" if d.status == "active" else _badge("warn", d.status)
        meta = " · ".join(x for x in (d.industry, d.area, d.level) if x)
        st.markdown(
            f"<div class='hub-doc-row'>{badge}{stt}"
            f"<span class='t'>{html.escape(d.title or d.doc_id)}</span>"
            f"<span class='m'>{html.escape(meta)}</span></div>",
            unsafe_allow_html=True,
        )


# ─── 메인: 검색 결과 ────────────────────────────────────────────────────────
def _render_results(q: str) -> None:
    hits = retrieve.search(q, limit=30)
    concepts = [h for h in hits if h.kind == "concept"]
    docs = [h for h in hits if h.kind == "doc"]
    hub_section(f"검색 '{q}' · 개념 {len(concepts)} · 문서 {len(docs)}")
    if not hits:
        st.info("검색 결과 없음. (빈 볼트거나 미색인 질의)")
        return
    for h in concepts:
        st.button(f"📘 {h.title}   ·  degree {h.extra.get('degree', 0)}",
                  key=f"wiki_hit_{h.id}", use_container_width=True,
                  on_click=_select, args=(h.id,))
        if h.snippet:
            st.caption(h.snippet)
    if docs:
        hub_section("문서 히트")
    for h in docs:
        badge = _badge(_CHANNEL.get(h.extra.get("channel"), "doc"), h.extra.get("channel") or "doc")
        st.markdown(
            f"<div class='hub-doc-row'>{badge}"
            f"<span class='t'>{html.escape(h.title)}</span>"
            f"<span class='m'>{html.escape(h.snippet)}</span></div>",
            unsafe_allow_html=True,
        )


def render() -> None:
    n = len(knowledge.top_concepts(n=1))
    hub_pagebar(
        "위키", "Knowledge Wiki",
        "이름으로 찾고 개념 페이지를 읽습니다. 관계 시각 탐색은 그래프 탭.",
        "개념 있음" if n else "빈 볼트",
    )
    q = st.text_input(
        "검색", key="wiki_q", label_visibility="collapsed",
        placeholder="🔍 개념·문서 검색 — MES · 수율 · 키워드…",
    )

    left, main = st.columns([0.32, 0.68], gap="medium")
    with left:
        _render_rail()
    with main:
        if q.strip():
            _render_results(q.strip())
        else:
            cid = st.session_state.get("wiki_concept")
            if not cid:
                tops = knowledge.top_concepts(n=1)   # 첫 진입: 상위 개념 페이지 기본 표시
                cid = tops[0].concept_id if tops else None
            if cid:
                _render_concept_page(cid)
            else:
                st.info("개념이 아직 없습니다 — 개념추출(재수집) 후 채워집니다.")
