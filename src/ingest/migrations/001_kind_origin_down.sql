-- Rollback 001: K3 kind/origin 제거
-- SQLite 3.35+ 필요 (ALTER TABLE DROP COLUMN). M5 = 3.51 ✅

BEGIN;

DROP INDEX IF EXISTS idx_doc_kind;
DROP INDEX IF EXISTS idx_doc_origin;

ALTER TABLE documents DROP COLUMN kind;
ALTER TABLE documents DROP COLUMN origin;

UPDATE meta_kv SET value = '000' WHERE key = 'schema_version';

COMMIT;
