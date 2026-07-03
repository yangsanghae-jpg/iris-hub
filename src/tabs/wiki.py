"""탭: 📚 위키 — 개념 중심 검색 위키 (S5, WIKI_REBUILD_DESIGN).

"이름으로 찾고 개념 페이지를 읽는다" (텍스트·리스트 중심).
관계 시각 탐색은 그래프 탭(S6). 같은 S4 개념 데이터를 다른 방식으로 소비.
좌: 개념 인덱스(degree 순) + 후보 · 메인: 검색 결과 or 개념 페이지.
"""
from __future__ import annotations

import html

import streamlit as st

from src.engine.retrieve import search as retrieve
from src.store import knowledge, vault
from src.ui_kit import hub_kpi_grid, hub_pagebar

_CHANNEL_BADGE = {"doc": "🔵 doc", "chat": "🟢 chat", "web": "🟡 web"}
_TRUST_BADGE = {"verified": "🟢 verified", "candidate": "⚪ candidate"}


def _select(cid: str) -> None:
    st.session_state["wiki_concept"] = cid


# ─── 좌 레일: 개념 인덱스 + 후보 ────────────────────────────────────────────
def _render_rail() -> None:
    concepts = knowledge.top_concepts(n=40)
    st.caption("개념 인덱스 · degree 순")
    if not concepts:
        st.info("개념 없음 — init_vault 시드/개념추출(S4) 후.")
    else:
        top = concepts[0].degree or 1
        for c in concepts:
            active = st.session_state.get("wiki_concept") == c.concept_id
            label = f"{'▸ ' if active else ''}{c.canonical}  ·  {c.degree}"
            st.button(label, key=f"wiki_idx_{c.concept_id}",
                      use_container_width=True,
                      on_click=_select, args=(c.concept_id,))
            bar = "█" * max(1, round((c.degree / top) * 10)) if c.degree else ""
            if bar:
                st.markdown(
                    f"<div style='margin:-6px 0 4px 4px;color:#2f80c4;font-size:0.7rem'>{bar}</div>",
                    unsafe_allow_html=True,
                )

    cands = knowledge.list_candidates(n=1000)
    st.divider()
    st.caption(f"🧩 개념 후보 {len(cands)}건 — 사전 미등록")
    st.markdown("<small>등록·기각은 데이터 탭 큐레이션에서.</small>", unsafe_allow_html=True)


# ─── 메인: 개념 페이지 ──────────────────────────────────────────────────────
def _render_concept_page(cid: str) -> None:
    page = knowledge.concept_page(cid)
    if page is None:
        st.warning(f"개념 없음: {cid}")
        return
    c = page.concept
    st.markdown(f"<small>위키 › concepts › {html.escape(cid)}</small>", unsafe_allow_html=True)
    st.markdown(f"### {html.escape(c.canonical)}  {_TRUST_BADGE.get(c.trust, c.trust)}")

    hub_kpi_grid([
        ("근거 문서", str(len(page.docs)), "concept_docs"),
        ("관련 개념", str(len(page.related)), "cooccur"),
        ("별칭", str(len(page.aliases)), "다국어"),
        ("degree", str(c.degree), "active 문서"),
    ])

    st.markdown("**정의**")
    st.markdown(c.definition or "_정의 미작성_")

    if page.aliases:
        chips = " ".join(
            f"<span style='background:#eef4fb;border-radius:10px;padding:2px 8px;"
            f"margin:2px;font-size:0.8rem'>{html.escape(a)}</span>"
            for a in page.aliases
        )
        st.markdown("**별칭**", unsafe_allow_html=True)
        st.markdown(chips, unsafe_allow_html=True)

    if page.related:
        st.markdown("**관련 개념** · 동시출현")
        cols = st.columns(min(len(page.related), 4))
        for i, r in enumerate(page.related):
            cols[i % len(cols)].button(
                f"{r.canonical} · {r.degree}", key=f"wiki_rel_{cid}_{r.concept_id}",
                use_container_width=True, on_click=_select, args=(r.concept_id,),
            )

    st.markdown(f"**근거 문서** · {len(page.docs)}건 (weight 순)")
    if not page.docs:
        st.caption("아직 이 개념에 연결된 문서 없음 — K2 개념추출(재수집) 후 채워집니다.")
    for d in page.docs[:30]:
        badge = _CHANNEL_BADGE.get(d.channel, d.channel)
        status = "" if d.status == "active" else f" · ⚠️{d.status}"
        meta = " · ".join(x for x in (d.industry, d.area, d.level) if x)
        st.markdown(
            f"- {badge}{status} **{html.escape(d.title or d.doc_id)}**"
            + (f"  <small>{html.escape(meta)}</small>" if meta else ""),
            unsafe_allow_html=True,
        )


# ─── 메인: 검색 결과 ────────────────────────────────────────────────────────
def _render_results(q: str) -> None:
    hits = retrieve.search(q, limit=30)
    concepts = [h for h in hits if h.kind == "concept"]
    docs = [h for h in hits if h.kind == "doc"]
    st.caption(f"'{q}' — 개념 {len(concepts)} · 문서 {len(docs)}")
    if not hits:
        st.info("검색 결과 없음. (빈 볼트거나 미색인 질의)")
        return
    for h in concepts:
        st.button(f"📘 {h.title}  · degree {h.extra.get('degree', 0)}",
                  key=f"wiki_hit_{h.id}", use_container_width=True,
                  on_click=_select, args=(h.id,))
        if h.snippet:
            st.caption(h.snippet)
    if docs:
        st.markdown("**문서 히트**")
    for h in docs:
        badge = _CHANNEL_BADGE.get(h.extra.get("channel"), "")
        st.markdown(f"- {badge} **{html.escape(h.title)}** — <small>{html.escape(h.snippet)}</small>",
                    unsafe_allow_html=True)


def render() -> None:
    n_concepts = len(knowledge.top_concepts(n=1))
    hub_pagebar(
        "위키", "Knowledge Wiki",
        "이름으로 찾고 개념 페이지를 읽습니다. 관계 시각 탐색은 그래프 탭.",
        "개념 있음" if n_concepts else "빈 볼트",
    )
    q = st.text_input(
        "검색", key="wiki_q", label_visibility="collapsed",
        placeholder="🔍 개념·문서 검색 — MES · 수율 · 키워드…",
    )

    left, main = st.columns([0.30, 0.70], gap="medium")
    with left:
        _render_rail()
    with main:
        if q.strip():
            _render_results(q.strip())
        elif st.session_state.get("wiki_concept"):
            _render_concept_page(st.session_state["wiki_concept"])
        else:
            st.info("← 좌측 개념을 선택하거나 상단에서 검색하세요.")
