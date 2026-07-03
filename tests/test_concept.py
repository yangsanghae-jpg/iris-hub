"""S4 — 개념층: 정규화(resolve)·연결(conceptize)·degree·동시출현."""
from src.engine.concept import conceptize, resolve
from src.store import knowledge, vault
from src.store.models import ConceptRow, DocRow

TS = "2026-07-03T00:00:00+00:00"


def _seed(cid="mes", canonical="MES(생산실행시스템)",
          aliases=(("MES", "en"), ("생산실행시스템", "ko"), ("制造执行系统", "zh"))):
    knowledge.upsert_concept(ConceptRow(concept_id=cid, canonical=canonical, trust="verified"))
    for a, lang in aliases:
        knowledge.add_alias(cid, a, lang)


def _doc(doc_id):
    vault.upsert_document(DocRow(doc_id=doc_id, channel="doc", ingested_at=TS))


# ─── resolve ──────────────────────────────────────────────────────────────
def test_resolve_dict_alias_multilingual(vault_root):
    _seed()
    assert resolve.resolve("생산실행시스템") == "mes"
    assert resolve.resolve("制造执行系统") == "mes"
    assert resolve.resolve("MES") == "mes"


def test_resolve_fallback_normalize(vault_root):
    _seed()
    assert resolve.resolve("M.E.S") == "mes"   # 기호 제거 → 'mes' == concept_id


def test_resolve_stopword_rejected(vault_root):
    assert resolve.resolve("시스템") is None
    assert resolve.is_rejected("데이터")
    assert resolve.is_rejected("system")


def test_resolve_reject_short_and_digit(vault_root):
    assert resolve.resolve("A") is None
    assert resolve.resolve("123") is None


def test_resolve_miss_returns_none(vault_root):
    _seed()
    assert resolve.resolve("존재안하는개념xyz") is None


# ─── conceptize ─────────────────────────────────────────────────────────────
def test_conceptize_links_matched(vault_root):
    _seed()
    _doc("d1")
    r = conceptize.conceptize_doc("d1", ["MES", "MES", "생산실행시스템"])
    assert "mes" in r["linked"]
    page = knowledge.concept_page("mes")
    assert [d.doc_id for d in page.docs] == ["d1"]


def test_conceptize_unmatched_to_candidates(vault_root):
    _doc("d1")
    r = conceptize.conceptize_doc("d1", ["큐 타임", "큐 타임", "리드타임"])
    assert r["linked"] == []
    assert set(r["candidates"])                       # 미매칭 → 후보
    cands = {c["raw_norm"]: c for c in knowledge.list_candidates()}
    assert "큐타임" in cands and cands["큐타임"]["doc_count"] >= 1


def test_conceptize_skips_stopwords(vault_root):
    _doc("d1")
    r = conceptize.conceptize_doc("d1", ["시스템", "데이터", "123"])
    assert r["linked"] == [] and r["candidates"] == []
    assert knowledge.list_candidates() == []          # stopword는 후보도 아님


def test_conceptize_accepts_json_string(vault_root):
    _seed()
    _doc("d1")
    r = conceptize.conceptize_doc("d1", '["MES", "存在しない"]')
    assert "mes" in r["linked"]


# ─── degree · cooccurrence ──────────────────────────────────────────────────
def test_recompute_degree_active_only(vault_root):
    _seed()
    for d in ("d1", "d2", "d3"):
        _doc(d)
        knowledge.link_concept_doc("mes", d)
    vault.set_status("d3", "rejected")
    knowledge.recompute_degree()
    assert knowledge.concept_page("mes").concept.degree == 2   # active만


def test_recompute_cooccurrence(vault_root):
    _seed()
    knowledge.upsert_concept(ConceptRow("spc", "SPC", trust="verified"))
    for d in ("d1", "d2", "d3"):
        _doc(d)
        knowledge.link_concept_doc("mes", d)
        knowledge.link_concept_doc("spc", d)
    n = knowledge.recompute_cooccurrence(min_docs=3)
    assert n == 1
    edges = knowledge.concept_graph().edges
    assert any({e.src_id, e.dst_id} == {"mes", "spc"} and e.kind == "cooccur" for e in edges)


def test_cooccurrence_below_threshold(vault_root):
    _seed()
    knowledge.upsert_concept(ConceptRow("spc", "SPC", trust="verified"))
    for d in ("d1", "d2"):        # 2건 < min_docs=3
        _doc(d)
        knowledge.link_concept_doc("mes", d)
        knowledge.link_concept_doc("spc", d)
    assert knowledge.recompute_cooccurrence(min_docs=3) == 0
