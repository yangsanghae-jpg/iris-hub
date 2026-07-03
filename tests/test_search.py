"""S5 — engine/retrieve/search: 개념 우선 · FTS 폴백 · 근거문서 중복제거."""
from src.engine.retrieve import search as retrieve
from src.store import knowledge, vault
from src.store.models import ChunkRow, ConceptRow, DocRow

TS = "2026-07-03T00:00:00+00:00"


def _concept():
    knowledge.upsert_concept(
        ConceptRow("mes", "MES(생산실행시스템)", definition="실행 계층 시스템", trust="verified")
    )
    knowledge.add_alias("mes", "MES", "en")
    knowledge.add_alias("mes", "생산실행시스템", "ko")


def test_search_empty(vault_root):
    assert retrieve.search("") == []
    assert retrieve.search("   ") == []


def test_search_concept_priority(vault_root):
    _concept()
    hits = retrieve.search("생산실행시스템")   # 별칭 → 개념
    assert hits and hits[0].kind == "concept" and hits[0].id == "mes"
    assert "실행 계층" in hits[0].snippet


def test_search_fts_doc_hit(vault_root):
    vault.upsert_document(DocRow("d1", "doc", TS, title="도입"))
    vault.insert_chunks("d1", [ChunkRow("c1", 0, "manufacturing execution deployment")])
    hits = retrieve.search("execution")
    assert any(h.kind == "doc" and h.id == "d1" for h in hits)


def test_search_dedup_concept_evidence(vault_root):
    _concept()
    vault.upsert_document(DocRow("d1", "doc", TS, title="MES 사례"))
    vault.insert_chunks("d1", [ChunkRow("c1", 0, "MES execution system")])
    knowledge.link_concept_doc("mes", "d1")
    hits = retrieve.search("MES")
    assert hits[0].kind == "concept" and hits[0].id == "mes"
    assert "d1" not in [h.id for h in hits if h.kind == "doc"]   # 근거문서 중복 제거


def test_search_miss(vault_root):
    assert retrieve.search("존재안하는질의xyz") == []
