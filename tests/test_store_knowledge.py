"""S1 — 지식 DAL: 개념·별칭·정규화·링크·degree·페이지·그래프."""
from src.store import knowledge, vault
from src.store.models import ConceptRow, DocRow


def _concept(cid="mes", canonical="MES(생산실행시스템)", **kw):
    return ConceptRow(concept_id=cid, canonical=canonical, **kw)


def _doc(doc_id):
    return DocRow(doc_id=doc_id, channel="doc", ingested_at="2026-07-03T00:00:00+00:00")


def test_upsert_and_resolve_by_id(vault_root):
    knowledge.upsert_concept(_concept())
    assert knowledge.resolve_concept("mes") == "mes"


def test_resolve_by_alias_multilingual(vault_root):
    knowledge.upsert_concept(_concept())
    knowledge.add_alias("mes", "制造执行系统", "zh")
    knowledge.add_alias("mes", "생산실행시스템", "ko")
    assert knowledge.resolve_concept("制造执行系统") == "mes"
    assert knowledge.resolve_concept("생산실행시스템") == "mes"


def test_resolve_by_canonical_case_insensitive(vault_root):
    knowledge.upsert_concept(_concept(cid="oee", canonical="OEE"))
    assert knowledge.resolve_concept("oee") == "oee"       # id
    assert knowledge.resolve_concept("OEE") == "oee"       # canonical


def test_resolve_miss_returns_none(vault_root):
    assert knowledge.resolve_concept("존재안함") is None
    assert knowledge.resolve_concept("") is None


def test_link_and_recompute_degree(vault_root):
    knowledge.upsert_concept(_concept())
    for d in ("d1", "d2"):
        vault.upsert_document(_doc(d))
        knowledge.link_concept_doc("mes", d)
    knowledge.recompute_degree()
    top = knowledge.top_concepts()
    assert top[0].concept_id == "mes" and top[0].degree == 2


def test_concept_page(vault_root):
    knowledge.upsert_concept(_concept(definition="실행 계층 시스템"))
    knowledge.add_alias("mes", "MES", "en")
    vault.upsert_document(_doc("d1"))
    vault.upsert_document(_doc("d2"))
    vault.set_status("d2", "rejected")           # 비active 는 근거에서 제외
    knowledge.link_concept_doc("mes", "d1")
    knowledge.link_concept_doc("mes", "d2")
    page = knowledge.concept_page("mes")
    assert page.concept.definition == "실행 계층 시스템"
    assert "MES" in page.aliases
    assert [d.doc_id for d in page.docs] == ["d1"]   # active 만


def test_concept_graph_center_and_edges(vault_root):
    for cid in ("mes", "spc", "oee"):
        knowledge.upsert_concept(_concept(cid=cid, canonical=cid.upper()))
    knowledge.add_relation("mes", "spc", "cooccur", 3)
    knowledge.add_relation("mes", "oee", "cooccur", 1)
    g = knowledge.concept_graph(center="mes", hops=1)
    ids = {n.concept_id for n in g.nodes}
    assert {"mes", "spc", "oee"} <= ids
    assert any(e.src_id == "mes" and e.dst_id == "spc" and e.weight == 3 for e in g.edges)


def test_concept_graph_default_topN(vault_root):
    knowledge.upsert_concept(_concept())
    g = knowledge.concept_graph()
    assert any(n.concept_id == "mes" for n in g.nodes)
