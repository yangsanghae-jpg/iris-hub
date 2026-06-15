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

# 위키 3-파트 분류축 — 멀티라벨 JSON 배열로 저장 (V2.5.3 §3.10 v2)
MIGRATIONS = [
    "ALTER TABLE document_meta ADD COLUMN automation_levels_json TEXT DEFAULT '[]'",
    "ALTER TABLE document_meta ADD COLUMN system_domains_json    TEXT DEFAULT '[]'",
    "ALTER TABLE document_meta ADD COLUMN mgmt_categories_json   TEXT DEFAULT '[]'",
    "ALTER TABLE document_meta ADD COLUMN blurb_industry         TEXT",
    "ALTER TABLE document_meta ADD COLUMN blurb_system           TEXT",
    "ALTER TABLE document_meta ADD COLUMN blurb_mgmt             TEXT",
]


def ensure_schema(conn: sqlite3.Connection | None = None) -> None:
    """document_meta 테이블 + 인덱스 + 마이그레이션 컬럼. 매 호출 안전.

    conn을 주면 그 연결을 그대로 사용 (호출자 트랜잭션에 합류).
    안 주면 자체 connect/close (commit 포함).
    """
    own = False
    if conn is None:
        if not DB_PATH.exists():
            return
        conn = sqlite3.connect(DB_PATH)
        own = True
    try:
        conn.executescript(SCHEMA_SQL)
        # 추가 컬럼 — 이미 있으면 무시
        existing = {row[1] for row in conn.execute("PRAGMA table_info(document_meta)")}
        for stmt in MIGRATIONS:
            col = stmt.split("ADD COLUMN", 1)[1].strip().split()[0]
            if col not in existing:
                conn.execute(stmt)
        if own:
            conn.commit()
    finally:
        if own:
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
           fallback_used: bool = False,
           automation_levels: list[str] | None = None,
           system_domains: list[str] | None = None,
           mgmt_categories: list[str] | None = None,
           blurb_industry: str = "",
           blurb_system: str = "",
           blurb_mgmt: str = "",
           conn: sqlite3.Connection | None = None) -> None:
    """document_meta INSERT or REPLACE.

    conn 주면 그 연결로 INSERT 후 commit 안 함 (호출자가 commit 책임).
    안 주면 자체 connect → INSERT → commit → close.

    M5 운영에서 V2.6.2 K2 재처리 시 conn 미공유로 `database is locked`
    27/27 발생한 회귀 (2026-06-15) 수정.
    """
    own = False
    if conn is None:
        if not DB_PATH.exists():
            return
        conn = sqlite3.connect(DB_PATH)
        # 자체 연결일 때만 busy_timeout 박음 (호출자 conn은 호출자가 관리)
        conn.execute("PRAGMA busy_timeout=5000")
        own = True
    try:
        conn.execute(
            """INSERT OR REPLACE INTO document_meta
               (doc_id, summary, topics_json, entities_json, concepts_json,
                classifier_version, confidence, reason, k2_ms, fallback_used,
                automation_levels_json, system_domains_json, mgmt_categories_json,
                blurb_industry, blurb_system, blurb_mgmt)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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
                json.dumps(automation_levels or [], ensure_ascii=False),
                json.dumps(system_domains or [], ensure_ascii=False),
                json.dumps(mgmt_categories or [], ensure_ascii=False),
                blurb_industry,
                blurb_system,
                blurb_mgmt,
            ),
        )
        if own:
            conn.commit()
    finally:
        if own:
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
