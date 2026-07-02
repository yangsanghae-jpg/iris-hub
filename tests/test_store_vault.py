"""S1 — 볼트 DAL: 문서·청크·검색(dual tokenizer)·큐레이션·통계."""
from src.store import vault
from src.store.models import ChunkRow, DocRow


def _doc(doc_id="doc_20260703_001", channel="doc", **kw):
    return DocRow(doc_id=doc_id, channel=channel, ingested_at="2026-07-03T00:00:00+00:00", **kw)


def test_upsert_and_get_document(vault_root):
    vault.upsert_document(_doc(title="MES 도입", industry="A"))
    got = vault.get_document("doc_20260703_001")
    assert got is not None and got.title == "MES 도입" and got.industry == "A"


def test_upsert_document_is_update(vault_root):
    vault.upsert_document(_doc(title="v1"))
    vault.upsert_document(_doc(title="v2", status="quarantine"))
    got = vault.get_document("doc_20260703_001")
    assert got.title == "v2" and got.status == "quarantine"


def test_search_unicode61_hit(vault_root):
    vault.upsert_document(_doc(title="영문"))
    vault.insert_chunks("doc_20260703_001", [
        ChunkRow("c1", 0, "manufacturing execution system deployment"),
    ])
    hits = vault.search_fts("execution")
    assert [h.doc_id for h in hits] == ["doc_20260703_001"]


def test_search_trigram_fallback_cjk_substring(vault_root):
    """한글 부분 매치는 unicode61(토큰 전체) 실패 → trigram 폴백으로 회수."""
    vault.upsert_document(_doc(title="한글"))
    vault.insert_chunks("doc_20260703_001", [
        ChunkRow("c1", 0, "생산실행시스템 도입 사례"),
    ])
    # 'ecution' 아닌 한글 내부 부분 문자열
    hits = vault.search_fts("실행시스")
    assert [h.doc_id for h in hits] == ["doc_20260703_001"]


def test_search_excludes_non_active(vault_root):
    vault.upsert_document(_doc(status="rejected"))
    vault.insert_chunks("doc_20260703_001", [ChunkRow("c1", 0, "execution system")])
    assert vault.search_fts("execution") == []


def test_set_status_gate(vault_root):
    vault.upsert_document(_doc())
    vault.set_status("doc_20260703_001", "quarantine", reason="저신뢰")
    assert vault.get_document("doc_20260703_001").status == "quarantine"


def test_queue_snapshot(vault_root):
    vault.upsert_document(_doc("d1"))
    vault.upsert_document(_doc("d2"))
    vault.upsert_document(_doc("d3"))
    vault.upsert_meta("d1", k2_done_at="2026-07-03T01:00:00+00:00")
    vault.upsert_meta("d2", processing_started_at="2026-07-03T01:00:00+00:00")
    vault.upsert_meta("d3", fail_count=2, last_error="boom")
    q = vault.queue_snapshot()
    assert q.total == 3 and q.done == 1 and q.processing == 1 and q.failed == 1
    assert q.pending == 1  # d3: 미완주·미처리중


def test_doc_distribution(vault_root):
    vault.upsert_document(_doc("d1", channel="doc", industry="A"))
    vault.upsert_document(_doc("d2", channel="web", industry="A"))
    vault.upsert_document(_doc("d3", channel="web", industry="B", status="rejected"))
    dist = vault.doc_distribution()
    assert dist.by_channel == {"doc": 1, "web": 2}
    assert dist.by_industry == {"A": 2, "B": 1}
    assert dist.by_status["active"] == 2 and dist.by_status["rejected"] == 1


def test_cascade_delete_chunks(vault_root):
    vault.upsert_document(_doc())
    vault.insert_chunks("doc_20260703_001", [ChunkRow("c1", 0, "x")])
    conn = vault.get_conn()
    try:
        conn.execute("DELETE FROM documents WHERE doc_id='doc_20260703_001'")
        conn.commit()
        n = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    finally:
        conn.close()
    assert n == 0
