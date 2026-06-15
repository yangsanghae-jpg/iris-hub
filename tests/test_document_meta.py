"""Tests for document_meta — conn 공유 + 락 회귀 (V2.6.2.1).

회귀 배경:
  M5에서 K2 재처리 27건 모두 `document_meta: database is locked` 실패.
  reprocess.py가 단일 conn으로 트랜잭션을 잡고 도는 동안
  document_meta.upsert가 별도 conn으로 INSERT 시도 → SQLITE_BUSY.

수정:
  upsert/ensure_schema에 `conn=` 파라미터 추가, 호출자가 자기 conn을
  넘기면 같은 트랜잭션에 합류. busy_timeout 안전망.
"""
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src import document_meta


@pytest.fixture
def temp_db(tmp_path):
    """document_meta 모듈의 DB_PATH를 임시 DB로 갈아끼움."""
    db = tmp_path / "test.db"
    # WAL + busy_timeout=0 — M5 운영 환경 재현
    conn = sqlite3.connect(db)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=0")
    # documents 테이블도 박아둠 (FK 없지만 reprocess 패턴 모방)
    conn.execute(
        "CREATE TABLE documents (doc_id TEXT PRIMARY KEY, industry TEXT, "
        "area TEXT, level TEXT)"
    )
    conn.commit()
    conn.close()

    with patch.object(document_meta, "DB_PATH", db):
        yield db


def test_upsert_with_external_conn(temp_db):
    """conn 인자로 외부 연결 받아 같은 트랜잭션에 합류."""
    conn = sqlite3.connect(temp_db)
    document_meta.ensure_schema(conn=conn)
    conn.commit()

    # documents에 1건 박고, 같은 트랜잭션 안에서 document_meta 박기
    conn.execute("BEGIN")
    conn.execute("INSERT INTO documents (doc_id, industry) VALUES (?, ?)",
                 ("doc_1", "B"))
    document_meta.upsert(
        "doc_1",
        summary="test summary",
        topics=["t1"],
        automation_levels=["auto2"],
        system_domains=["MES"],
        conn=conn,
    )
    conn.commit()
    conn.close()

    # 별도 reader로 검증
    r = sqlite3.connect(temp_db)
    r.row_factory = sqlite3.Row
    row = r.execute("SELECT * FROM document_meta WHERE doc_id=?", ("doc_1",)).fetchone()
    assert row is not None, "document_meta INSERT 실패"
    assert row["summary"] == "test summary"
    assert row["topics_json"] == '["t1"]'
    assert row["automation_levels_json"] == '["auto2"]'
    assert row["system_domains_json"] == '["MES"]'
    r.close()


def test_upsert_without_external_conn(temp_db):
    """conn 미전달 시 자체 connect/commit/close (기존 동작 유지)."""
    document_meta.ensure_schema()
    document_meta.upsert("doc_x", summary="standalone", topics=["a"])

    r = sqlite3.connect(temp_db)
    n = r.execute("SELECT COUNT(*) FROM document_meta WHERE doc_id=?",
                  ("doc_x",)).fetchone()[0]
    assert n == 1
    r.close()


def test_no_lock_when_caller_holds_transaction(temp_db):
    """회귀 테스트: 호출자가 트랜잭션을 잡고 있어도 락 충돌 없이 INSERT.

    수정 전이라면 `database is locked`로 실패했어야 함.
    """
    document_meta.ensure_schema()  # 자체 conn으로 schema 박음

    # M5 회귀 시나리오: reprocess가 conn을 잡고 루프 도는 패턴
    outer_conn = sqlite3.connect(temp_db)
    outer_conn.execute("PRAGMA busy_timeout=5000")
    outer_conn.execute("BEGIN")
    outer_conn.execute(
        "INSERT INTO documents (doc_id, industry) VALUES (?, ?)",
        ("doc_2", "C"),
    )

    # 같은 conn으로 document_meta INSERT — 충돌 안 나야 함
    document_meta.upsert(
        "doc_2",
        summary="locked-regression",
        classifier_version="k2-test-v2",
        conn=outer_conn,
    )

    outer_conn.commit()

    row = outer_conn.execute(
        "SELECT summary FROM document_meta WHERE doc_id=?", ("doc_2",)
    ).fetchone()
    assert row is not None
    assert row[0] == "locked-regression"
    outer_conn.close()


def test_ensure_schema_idempotent_with_conn(temp_db):
    """ensure_schema(conn=) 다중 호출에도 안전 (마이그레이션 컬럼 중복 ALTER 안 함)."""
    conn = sqlite3.connect(temp_db)
    document_meta.ensure_schema(conn=conn)
    document_meta.ensure_schema(conn=conn)
    document_meta.ensure_schema(conn=conn)
    conn.commit()

    cols = {r[1] for r in conn.execute("PRAGMA table_info(document_meta)")}
    assert "automation_levels_json" in cols
    assert "blurb_industry" in cols
    conn.close()
