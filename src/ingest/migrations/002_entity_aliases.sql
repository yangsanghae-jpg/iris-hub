-- Migration 002: entity_aliases 테이블 신설
-- V2.5.1 §2.D (Entity 동의어/다국어 표기 분열 대응)
--
-- 한 entity가 ko/en/zh 등 여러 표기로 나타날 때 alias로 묶음.
-- 예: doc_id='ent_001' (Fenghua) ← aliases: ('Fenghua','en'), ('丰华','zh'), ('풍화','ko')

BEGIN;

CREATE TABLE IF NOT EXISTS entity_aliases (
  alias_id   INTEGER PRIMARY KEY AUTOINCREMENT,
  entity_id  TEXT    NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
  alias      TEXT    NOT NULL,
  lang       TEXT,
  created_at TEXT    NOT NULL DEFAULT (datetime('now')),
  UNIQUE (entity_id, alias, lang)
);

CREATE INDEX IF NOT EXISTS idx_alias_entity ON entity_aliases(entity_id);
CREATE INDEX IF NOT EXISTS idx_alias_text   ON entity_aliases(alias);

INSERT INTO meta_kv (key, value) VALUES ('schema_version', '002')
  ON CONFLICT(key) DO UPDATE SET value = '002';

COMMIT;
