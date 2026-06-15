"""탭: 🕸️ 그래프 — 알다 Graph view 대응 (V2.5.2 §3.C 활성 트리거).

구성:
  - 상단 컨트롤 (상위 N, Concept 포함, 인물관계만, 검색)
  - Type 필터 (kind: source/entity/concept)
  - force-directed graph (streamlit-agraph)
  - 노드: documents, 엣지: lane/industry 같은 그룹 + chunks 연결

알다 v0.10.1 비주얼 차용. 6 docs 시드에서는 *볼륨 부족*하나 K3/K6 가동 시
자동으로 풍성해지는 자리.
"""
from __future__ import annotations

import re
import sqlite3
from collections import defaultdict
from pathlib import Path

import streamlit as st
from streamlit_agraph import Config, Edge, Node, agraph

from src.config import IRIS_SYSTEM_DB

WIKI_DIR = Path("/Users/iris/Documents/0Dev/iris-system/knowledge/wiki")
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]")

# 노드 색상 (알다 비주얼 차용)
COLOR_BY_KIND = {
    "source": "#9370DB",     # 보라 (알다 entity 색)
    "entity": "#FF8C00",     # 주황 (알다 hub 색)
    "concept": "#90EE90",    # 연두 (알다 concept 색)
    "(null)": "#888888",     # 회색 (미분류)
}
COLOR_BY_LANE = {
    "bronze": "#CD7F32",
    "silver": "#C0C0C0",
    "gold":   "#FFD700",
    "reference": "#4682B4",
    "secure":    "#DC143C",
}


def _load_docs() -> list[dict]:
    if not IRIS_SYSTEM_DB.exists():
        return []
    conn = sqlite3.connect(IRIS_SYSTEM_DB)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("""
            SELECT d.doc_id, d.title, d.lane, d.kind, d.industry, d.area, d.level,
                   COUNT(c.chunk_id) AS chunk_count
              FROM documents d
              LEFT JOIN chunks c ON c.doc_id = d.doc_id
             GROUP BY d.doc_id
             ORDER BY d.lane, d.industry, d.doc_id
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _scan_wikilinks() -> dict[str, int]:
    if not WIKI_DIR.exists():
        return {}
    by_target: dict[str, int] = defaultdict(int)
    for f in WIKI_DIR.rglob("*.md"):
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        for m in WIKILINK_RE.finditer(text):
            tgt = m.group(1).strip()
            by_target[tgt] += 1
    return dict(by_target)


def render() -> None:
    docs = _load_docs()
    if not docs:
        st.error("documents 없음. raw_intake.py 실행 후 새로고침.")
        return

    # ─── 컨트롤을 expander 안으로 (기본 접힘) ────────────────────────
    with st.expander("🕸️ 그래프 컨트롤 (V2.5.2 §3.C · V2.5.3 §3.10 v1)", expanded=False):
        c1, c2, c3, c4 = st.columns([2, 1.5, 1.5, 2])
        with c1:
            top_n = st.slider("상위 N개 노드", 5, 200, min(50, len(docs)), step=5)
        with c2:
            show_isolated = st.checkbox("고립 노드 숨기기", value=False)
        with c3:
            include_concept = st.checkbox("Concept 포함", value=True)
        with c4:
            search = st.text_input("🔍 노드 검색", placeholder="title 부분 일치", label_visibility="collapsed")

        # Type 필터
        kinds_present = sorted({(d["kind"] or "(null)") for d in docs})
        type_cols = st.columns(max(len(kinds_present) + 1, 2))
        type_cols[0].markdown("**Type 필터**")
        type_filter = {}
        for col, k in zip(type_cols[1:], kinds_present):
            type_filter[k] = col.checkbox(k or "(null)", value=True, key=f"type-{k}")

    # ─── 노드/엣지 구성 ────────────────────────────────────────────────
    # 필터 적용
    filtered = []
    for d in docs:
        k = d["kind"] or "(null)"
        if not type_filter.get(k, True):
            continue
        if not include_concept and k == "concept":
            continue
        if search and search.lower() not in (d["title"] or "").lower():
            continue
        filtered.append(d)

    filtered = filtered[:top_n]

    # 노드 빌드
    nodes: list[Node] = []
    edges: list[Edge] = []
    by_lane: dict[str, list[str]] = defaultdict(list)
    by_industry_area: dict[str, list[str]] = defaultdict(list)

    for d in filtered:
        k = d["kind"] or "(null)"
        color = COLOR_BY_KIND.get(k, "#888")
        # 크기 = chunks 수 (chunks 많을수록 큰 노드)
        size = 15 + min(d["chunk_count"], 30) * 2
        label = (d["title"] or d["doc_id"])[:30]
        title_full = (
            f"doc_id: {d['doc_id']}\n"
            f"lane: {d['lane']} · kind: {k}\n"
            f"industry: {d['industry']} / area: {d['area']} / level: {d['level']}\n"
            f"chunks: {d['chunk_count']}"
        )
        nodes.append(Node(
            id=d["doc_id"],
            label=label,
            size=size,
            color=color,
            title=title_full,   # hover tooltip
        ))
        by_lane[d["lane"] or "(null)"].append(d["doc_id"])
        key = f"{d['industry'] or '?'}/{d['area'] or '?'}"
        by_industry_area[key].append(d["doc_id"])

    # 엣지 빌드 — 같은 (industry, area) 매트릭스 키 → 클러스터
    for key, dids in by_industry_area.items():
        if key == "?/?" or len(dids) < 2:
            continue
        for i in range(len(dids)):
            for j in range(i + 1, len(dids)):
                edges.append(Edge(
                    source=dids[i],
                    target=dids[j],
                    label="same matrix",
                    color="#3399ff",
                ))

    # 같은 lane도 약한 엣지로 (단 secure는 격리)
    for lane, dids in by_lane.items():
        if lane in ("secure", "(null)") or len(dids) < 2:
            continue
        for i in range(len(dids)):
            for j in range(i + 1, len(dids)):
                # 이미 matrix 엣지 있으면 추가 안 함
                already = any(
                    (e.source == dids[i] and e.to == dids[j]) or
                    (e.source == dids[j] and e.to == dids[i])
                    for e in edges
                )
                if already:
                    continue
                edges.append(Edge(
                    source=dids[i],
                    target=dids[j],
                    color="#cccccc",
                    width=1,
                ))

    # 고립 노드 숨기기
    if show_isolated:
        connected = set()
        for e in edges:
            connected.add(e.source)
            connected.add(e.to)
        nodes = [n for n in nodes if n.id in connected]

    # ─── 한 줄 요약 (4개 metric 대신) ───────────────────────────────
    matrix_clusters = len(by_industry_area) - (1 if "?/?" in by_industry_area else 0)
    st.caption(
        f"🕸️ **노드 {len(nodes)}** / 전체 {len(docs)} · "
        f"엣지 {len(edges)} · "
        f"matrix 클러스터 {matrix_clusters} · "
        f"lane {len(by_lane)}종"
    )

    # ─── force-directed graph ────────────────────────────────────────
    if not nodes:
        st.warning("필터 조건에 맞는 노드 없음. 필터를 풀어보세요.")
        return

    config = Config(
        width="100%",
        height=600,
        directed=False,
        physics=True,
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#F7A7A6",
        collapsible=False,
        node={"labelProperty": "label", "renderLabel": True},
        link={"labelProperty": "label", "renderLabel": False},
    )
    agraph(nodes=nodes, edges=edges, config=config)

    st.caption(
        "💡 노드 드래그 가능, hover로 상세 정보. "
        "엣지: 🔵 같은 matrix (industry/area) · ⚪ 같은 lane."
    )

    # ─── 시드 상태 + 활성 트리거 ────────────────────────────────────
    st.divider()
    with st.expander("📍 활성 트리거 (V2.5.2 §3.C) — 그래프가 풍성해지는 조건"):
        st.markdown("""
**현재 6 documents는 force-directed 시각화엔 *볼륨 부족*.** 다음 셋 중 하나 충족 시 자동 풍성화:

1. **K6 Curate 가동** → `knowledge/wiki/*.md` 자동 생성 → `[[wikilinks]]` 엣지 형성
2. **K3 관계 4종 흡수** (`references / belongs_to / impacts / derived_from`)
3. **documents 100건+** — 시각적 가치 임계치

알다 운영 입증값 9,089 entity / 4,229 concept 도달 시 본 뷰가 *알다 Graph view* 수준.
        """)

    # wikilink 시드 (참고)
    by_target = _scan_wikilinks()
    if by_target:
        with st.expander(f"🔗 wiki/*.md [[wikilinks]] 시드 ({sum(by_target.values())}개)"):
            rows = sorted(by_target.items(), key=lambda x: -x[1])
            st.dataframe(
                {"target": [r[0] for r in rows[:30]],
                 "incoming": [r[1] for r in rows[:30]]},
                use_container_width=True,
                hide_index=True,
            )
