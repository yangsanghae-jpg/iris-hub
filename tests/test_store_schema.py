"""S1 — 스키마 적용·버전·멱등."""
from src.store import db


EXPECTED_TABLES = {
    "documents", "chunks", "documents_fts", "documents_fts_trigram",
    "document_meta", "embeddings",
    "concepts", "concept_aliases", "concept_docs", "concept_relations",
    "meta_kv",
    "dx_industry", "dx_sub_industry", "dx_import",
}


def test_ensure_schema_creates_all_tables(vault_root):
    conn = db.get_conn()
    try:
        names = {
            r["name"] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table','view')"
            ).fetchall()
        }
    finally:
        conn.close()
    assert EXPECTED_TABLES <= names


def test_schema_version_recorded(vault_root):
    conn = db.get_conn()
    try:
        v = conn.execute(
            "SELECT value FROM meta_kv WHERE key='schema_version'"
        ).fetchone()["value"]
    finally:
        conn.close()
    assert int(v) == db.SCHEMA_VERSION


def test_ensure_schema_idempotent(vault_root):
    # 재실행 안전 — 예외 없이 같은 버전 반환.
    assert db.ensure_schema() == db.SCHEMA_VERSION
    assert db.ensure_schema() == db.SCHEMA_VERSION


def test_foreign_keys_enforced(vault_root):
    import sqlite3
    conn = db.get_conn()
    try:
        # 존재하지 않는 doc_id 로 청크 삽입 → FK 위반.
        try:
            conn.execute(
                "INSERT INTO chunks(chunk_id, doc_id, ord, text) VALUES ('c1','missing',0,'x')"
            )
            conn.commit()
            violated = False
        except sqlite3.IntegrityError:
            violated = True
    finally:
        conn.close()
    assert violated
