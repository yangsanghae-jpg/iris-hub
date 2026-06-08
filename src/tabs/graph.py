"""탭: 🕸️ 그래프 — 알다 Graph view 대응 (V2.5.2 §3.C 활성 트리거).

지금 상태 (2026-06-08):
  - documents 6건 — 노드로는 적음
  - [[wikilinks]] 정책 박혀 있으나 wiki/*.md 본문 거의 없어 엣지 0
  - K3 관계 4종 (`references / belongs_to / impacts / derived_from`) 미적용

활성 트리거 (V2.5.2 §3.C):
  - K6 Curate 가동 → wiki/*.md 누적 → [[wikilinks]] 엣지 형성
  - K3 관계 4종 흡수 결정 (보류→격상) → entity_aliases·관계 테이블
  - 알다 9089 entity 도달 시 본격 시각화 가치

본 탭은 placeholder + 현재 그래프 가능 상태 측정.
"""
from __future__ import annotations

import re
import sqlite3
from collections import defaultdict
from pathlib import Path

import streamlit as st

from src.config import IRIS_SYSTEM_DB

WIKI_DIR = Path("/Users/iris/Documents/0Dev/iris-system/knowledge/wiki")
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]")


def _scan_wikilinks() -> tuple[int, int, dict[str, int]]:
    """wiki/*.md 본문에서 [[wikilinks]] 추출. (files, edges, by_target)."""
    if not WIKI_DIR.exists():
        return 0, 0, {}
    md_files = list(WIKI_DIR.rglob("*.md"))
    by_target: dict[str, int] = defaultdict(int)
    edges = 0
    for f in md_files:
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        for m in WIKILINK_RE.finditer(text):
            tgt = m.group(1).strip()
            by_target[tgt] += 1
            edges += 1
    return len(md_files), edges, dict(by_target)


def render() -> None:
    st.markdown("## 🕸️ 그래프")
    st.caption(
        "알다 Graph view 대응 자리. K6 Curate + V2.5.2 §3.C 관계 4종 흡수 후 본격 활성."
    )

    # ─── 현재 그래프 가능 상태 ─────────────────────────────────────────
    st.markdown("### 📊 현재 그래프 시드")

    files, edges, by_target = _scan_wikilinks()

    docs_count = 0
    if IRIS_SYSTEM_DB.exists():
        conn = sqlite3.connect(IRIS_SYSTEM_DB)
        try:
            docs_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        finally:
            conn.close()

    c1, c2, c3 = st.columns(3)
    c1.metric("노드 후보 (documents)", docs_count, help="alda 9,719 노트 vs 본 IRIS")
    c2.metric("엣지 후보 ([[wikilinks]])", edges, help="wiki/*.md 본문 스캔")
    c3.metric("wiki/*.md 파일", files)

    st.divider()

    # ─── placeholder 안내 ──────────────────────────────────────────────
    st.markdown("### 📍 활성 트리거 — V2.5.2 §3.C")

    st.info(
        "**활성 조건 (셋 중 하나라도 충족 시 점진 활성):**\n\n"
        "1. **K6 Curate 가동** → `knowledge/wiki/*.md` 자동 생성 → `[[wikilinks]]` 엣지 형성\n"
        "2. **K3 관계 4종 흡수** (V2.5.2 §3.C: `references / belongs_to / impacts / derived_from`)\n"
        "3. **documents 100건+** — 시각적 가치 임계치"
    )

    st.markdown("**현재 미달:** "
                f"엣지 {edges}개 / 알다 격차 {-(9089 - docs_count):,} entity")

    st.divider()

    # ─── 엣지 분포 (있을 때만) ────────────────────────────────────────
    if by_target:
        st.markdown("### 🔗 wikilink 타겟 빈도")
        rows = sorted(by_target.items(), key=lambda x: -x[1])
        st.dataframe(
            {"target": [r[0] for r in rows[:30]],
             "incoming": [r[1] for r in rows[:30]]},
            use_container_width=True,
            hide_index=True,
        )
        if len(rows) > 30:
            st.caption(f"... (+ {len(rows) - 30}개)")
    else:
        st.warning("`[[wikilinks]]` 엣지 0건 — wiki 본문이 비어있거나 링크 미작성.")
        st.markdown(
            "**해결 시점:**\n"
            "- K6 Curate가 `raw → wiki/*.md` 자동 생성 (사양 박힘, 구현 자리)\n"
            "- 또는 사람이 직접 [[link]] 추가\n"
        )

    st.divider()

    # ─── 미래 시각화 기술 후보 ────────────────────────────────────────
    st.markdown("### 🔮 활성 시 시각화 기술 후보")
    st.markdown(
        "| 라이브러리 | 패턴 | 비고 |\n"
        "|---|---|---|\n"
        "| `pyvis` | interactive HTML | 알다와 가장 비슷, 노드 드래그 |\n"
        "| `streamlit-agraph` | Streamlit 네이티브 | 의존 적음, 100~500노드 |\n"
        "| `networkx + plotly` | 정적·빠름 | 1000+ 노드, 비줌·인터랙션 제약 |\n"
        "| `D3.js` (custom iframe) | full custom | V2.6 후반, 알다 비주얼 재현 |"
    )
    st.caption(
        "결정 시점: 엣지 100건+ 또는 V2.5.2 §3.C 관계 4종 흡수 확정 시."
    )
