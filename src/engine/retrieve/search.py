"""engine/retrieve/search — 볼트 전문 검색 + 개념 우선 (S5 §2).

1) 질의가 개념 별칭이면 그 개념 페이지를 최상단(resolve_concept).
2) FTS 문서 히트(store.vault.search_fts — unicode61 1차 → trigram 폴백 내장).
3) 시맨틱(FAISS)은 2차 — 가동 시 확장.
개념 히트를 앞에, 문서 히트를 뒤에. 위키·검색바 공용.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field

from src.store import knowledge, vault


@dataclass
class Hit:
    kind: str                    # 'concept' | 'doc'
    id: str                      # concept_id | doc_id
    title: str
    snippet: str = ""
    score: float = 0.0           # doc=bm25(작을수록 우수), concept=n/a
    extra: dict = field(default_factory=dict)


def search(
    query: str, limit: int = 20, conn: sqlite3.Connection | None = None
) -> list[Hit]:
    """개념 우선 + FTS 문서. 빈 질의면 []."""
    q = (query or "").strip()
    if not q:
        return []
    hits: list[Hit] = []
    concept_doc_ids: set[str] = set()

    # 1) 개념 우선
    cid = knowledge.resolve_concept(q, conn=conn)
    if cid:
        page = knowledge.concept_page(cid, conn=conn)
        if page:
            hits.append(Hit(
                kind="concept", id=cid, title=page.concept.canonical,
                snippet=(page.concept.definition or "")[:200],
                extra={"degree": page.concept.degree, "trust": page.concept.trust},
            ))
            concept_doc_ids = {d.doc_id for d in page.docs}

    # 2) FTS 문서 (trigram 폴백 내장). 개념 근거문서와 중복 제거.
    for h in vault.search_fts(q, limit=limit, conn=conn):
        if h.doc_id in concept_doc_ids:
            continue
        hits.append(Hit(
            kind="doc", id=h.doc_id, title=h.title or h.doc_id,
            snippet=h.snippet, score=h.score, extra={"channel": h.channel},
        ))
    return hits
