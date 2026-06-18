-- Migration 005 DOWN: 처리 락 컬럼 제거
-- SQLite는 DROP COLUMN을 3.35+에서만 지원. 안전하게 INDEX만 제거.
-- 컬럼은 그대로 두되 UPDATE로 비움.

BEGIN;

UPDATE document_meta SET processing_started_at = NULL;
DROP INDEX IF EXISTS idx_doc_meta_processing;

UPDATE meta_kv SET value='004' WHERE key='schema_version';

COMMIT;
