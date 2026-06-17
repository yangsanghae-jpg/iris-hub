-- Migration 003 down: trigram → unicode61 (롤백)

BEGIN;

DROP TABLE IF EXISTS documents_fts;

CREATE VIRTUAL TABLE documents_fts USING fts5(
  title, body, tokenize='unicode61'
);

INSERT INTO documents_fts (rowid, title, body)
SELECT d.rowid, COALESCE(d.title, ''), COALESCE(GROUP_CONCAT(c.text, char(10)), '')
  FROM documents d
  LEFT JOIN chunks c ON c.doc_id = d.doc_id
  GROUP BY d.doc_id;

INSERT INTO meta_kv (key, value) VALUES ('schema_version', '002')
  ON CONFLICT(key) DO UPDATE SET value = '002';

COMMIT;
