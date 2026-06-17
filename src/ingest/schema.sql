PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS documents (
  doc_id      TEXT PRIMARY KEY,
  path        TEXT NOT NULL,
  lane        TEXT NOT NULL,
  trust       TEXT NOT NULL DEFAULT 'verified',
  industry    TEXT,
  area        TEXT,
  level       TEXT,
  title       TEXT,
  source_url  TEXT,
  fetched_at  TEXT,
  promoted_to TEXT
);
CREATE INDEX IF NOT EXISTS idx_doc_matrix ON documents(industry, area, level);
CREATE INDEX IF NOT EXISTS idx_doc_lane   ON documents(lane);

CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
  title, body, tokenize='unicode61'
);

-- V2.5.3 §14: 보조 trigram 인덱스 (CJK + 부분 매치). 한국어·영문은 unicode61 우선.
CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts_trigram USING fts5(
  title, body, tokenize='trigram'
);

CREATE TABLE IF NOT EXISTS chunks (
  chunk_id TEXT PRIMARY KEY,
  doc_id   TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
  ord      INTEGER NOT NULL,
  text     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id);

-- chunk_vec (sqlite-vec) deferred: macOS system Python lacks enable_load_extension.
-- Will be created when K5-③ semantic search lands (V2.3 K4-EMB).
-- CREATE VIRTUAL TABLE chunk_vec USING vec0(embedding FLOAT[768]);

CREATE TABLE IF NOT EXISTS meta_kv (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
