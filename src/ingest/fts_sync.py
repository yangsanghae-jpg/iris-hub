"""V2.5.3 §15 — FTS5 dual-tokenizer 인덱스 동기 헬퍼.

`documents_fts` (unicode61) + `documents_fts_trigram` (trigram) 둘 다 갱신.
raw_intake / reference_diagnosis / Makefile reindex-fts 한 곳에서 호출.
"""
from __future__ import annotations

import sqlite3


_REBUILD_TEMPLATE = """
DELETE FROM {table};
INSERT INTO {table} (rowid, title, body)
SELECT d.rowid, COALESCE(d.title, ''), COALESCE(GROUP_CONCAT(c.text, char(10)), '')
  FROM documents d
  LEFT JOIN chunks c ON c.doc_id = d.doc_id
  GROUP BY d.doc_id;
"""

_FTS_TABLES = ("documents_fts", "documents_fts_trigram")


def rebuild_all(conn: sqlite3.Connection) -> dict[str, int]:
    """두 FTS 인덱스 동시 재구축. Returns {table: row_count}."""
    out: dict[str, int] = {}
    for table in _FTS_TABLES:
        try:
            conn.executescript(_REBUILD_TEMPLATE.format(table=table))
            cnt = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            out[table] = cnt
        except sqlite3.OperationalError:
            # 마이그레이션 003 이전 DB 또는 트리그램 인덱스 부재
            out[table] = -1
    return out
