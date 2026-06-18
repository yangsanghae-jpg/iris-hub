-- Migration 005: 처리 락 컬럼 (V2.6.3.7)
-- document_meta에 처리중 표식 박기 — 흐름 탭 큐/액션 동시 클릭 방지용.
-- processing_started_at NOT NULL이면 "처리중" 상태.
-- 처리 끝나면 NULL로 되돌리거나, 성공 시 k2_at 갱신과 함께 NULL.

BEGIN;

ALTER TABLE document_meta ADD COLUMN processing_started_at TEXT;
CREATE INDEX IF NOT EXISTS idx_doc_meta_processing ON document_meta(processing_started_at);

UPDATE meta_kv SET value='005' WHERE key='schema_version';

COMMIT;
