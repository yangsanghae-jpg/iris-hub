"""document_meta 테이블 — K2 분석 결과 저장 자리.

iris-system 본체 (raw_intake)는 안 건드리고, hub 측에서 schema을 박는다.
별도 테이블이라 iris-system이 모르는 것은 의도된 것.
나중에 K2가 iris-system 본체에 박히면 이 모듈은 거기로 이주.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

DB_PATH = Path("/Users/iris/Documents/0Dev/iris-system/knowledge/_index.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS document_meta (
  doc_id              TEXT PRIMARY KEY,
  summary             TEXT,
  topics_json         TEXT,
  entities_json       TEXT,
  concepts_json       TEXT,
  classifier_version  TEXT,
  confidence          REAL,
  reason              TEXT,
  k2_at               TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  k2_ms               INTEGER,
  fallback_used       INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_doc_meta_classifier ON document_meta(classifier_version);
CREATE INDEX IF NOT EXISTS idx_doc_meta_k2_at ON document_meta(k2_at);
"""


def ensure_schema() -> None:
    """document_meta 테이블 + 인덱스가 없으면 만든다. 매 호출 안전."""
    if not DB_PATH.exists():
        return
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()


def upsert(doc_id: str, *,
           summary: str = "",
           topics: list[str] | None = None,
           entities: list[str] | None = None,
           concepts: list[str] | None = None,
           classifier_version: str = "",
           confidence: float = 0.0,
           reason: str = "",
           k2_ms: int = 0,
           fallback_used: bool = False) -> None:
    """document_meta INSERT or REPLACE. ensure_schema() 먼저 호출 권장."""
    if not DB_PATH.exists():
        return
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """INSERT OR REPLACE INTO document_meta
               (doc_id, summary, topics_json, entities_json, concepts_json,
                classifier_version, confidence, reason, k2_ms, fallback_used)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                doc_id,
                summary,
                json.dumps(topics or [], ensure_ascii=False),
                json.dumps(entities or [], ensure_ascii=False),
                json.dumps(concepts or [], ensure_ascii=False),
                classifier_version,
                confidence,
                reason,
                k2_ms,
                1 if fallback_used else 0,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get(doc_id: str) -> dict | None:
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM document_meta WHERE doc_id = ?", (doc_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def stats() -> dict:
    """document_meta 테이블 통계 — 데이터 탭에서 표시."""
    if not DB_PATH.exists():
        return {"total": 0, "fallback": 0, "by_classifier": {}}
    conn = sqlite3.connect(DB_PATH)
    try:
        # 테이블 존재 확인
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='document_meta'"
        ).fetchone()
        if not row:
            return {"total": 0, "fallback": 0, "by_classifier": {}}

        total = conn.execute("SELECT COUNT(*) FROM document_meta").fetchone()[0]
        fb = conn.execute("SELECT COUNT(*) FROM document_meta WHERE fallback_used=1").fetchone()[0]
        by = dict(conn.execute(
            "SELECT classifier_version, COUNT(*) FROM document_meta "
            "GROUP BY classifier_version"
        ).fetchall())
        return {"total": total, "fallback": fb, "by_classifier": by}
    finally:
        conn.close()


__all__ = ["ensure_schema", "upsert", "get", "stats", "SCHEMA_SQL"]
