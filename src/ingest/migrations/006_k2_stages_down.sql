-- Migration 006 DOWN: 단계별 timestamp 제거
-- SQLite ALTER DROP COLUMN은 3.35+에서만 동작. 안전하게 INDEX만 제거 + UPDATE 비움.

BEGIN;

UPDATE document_meta SET extract_at=NULL, classify_at=NULL, summarize_at=NULL;
DROP INDEX IF EXISTS idx_doc_meta_extract;
DROP INDEX IF EXISTS idx_doc_meta_classify;
DROP INDEX IF EXISTS idx_doc_meta_summarize;

UPDATE meta_kv SET value='005' WHERE key='schema_version';

COMMIT;
