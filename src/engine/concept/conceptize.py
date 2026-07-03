"""engine/concept/conceptize — K2 ④단계: 원시 개념 → 정규화·연결 or 후보 (S4 §3).

문서의 concepts_json 각 항목을 resolve →
  매칭: store.knowledge.link_concept_doc (weight=문서 내 빈도)
  미매칭(거부 아님): store.knowledge.add_candidate (후보 큐)
LLM 불필요 — 사전 매칭 + 규칙. K2 배치가 문서 처리 끝에 호출.
"""
from __future__ import annotations

import json
import sqlite3
from collections import Counter

from src.store import knowledge

from . import resolve as resolver


def _as_list(concepts_raw) -> list[str]:
    """concepts_json(str|list) → 문자열 리스트."""
    if concepts_raw is None:
        return []
    if isinstance(concepts_raw, str):
        try:
            concepts_raw = json.loads(concepts_raw)
        except (ValueError, TypeError):
            return [concepts_raw] if concepts_raw.strip() else []
    if isinstance(concepts_raw, list):
        return [str(x) for x in concepts_raw if str(x).strip()]
    return []


def conceptize_doc(
    doc_id: str, concepts_raw, conn: sqlite3.Connection | None = None
) -> dict:
    """문서의 원시 개념을 정규화·연결. Returns {'linked':[cid], 'candidates':[key]}."""
    counts = Counter(_as_list(concepts_raw))
    linked: list[str] = []
    candidates: list[str] = []
    for raw, freq in counts.items():
        if resolver.is_rejected(raw):
            continue
        cid = resolver.resolve(raw, conn=conn)
        if cid:
            knowledge.link_concept_doc(cid, doc_id, weight=float(freq), conn=conn)
            linked.append(cid)
        else:
            key = resolver.normalize_key(raw)
            if key:
                knowledge.add_candidate(key, sample=raw, doc_id=doc_id, conn=conn)
                candidates.append(key)
    return {"linked": linked, "candidates": candidates}
