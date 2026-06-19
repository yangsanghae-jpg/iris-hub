-- Migration 006: K2 단계 분리 (V2.7.0)
-- document_meta에 단계별 timestamp 추가.
-- 각 단계 완료 시 박힘, 락 해제는 *모든 단계 완료* 또는 *실패 시*.

BEGIN;

ALTER TABLE document_meta ADD COLUMN extract_at TEXT;     -- ① 키워드 추출 완료 시각
ALTER TABLE document_meta ADD COLUMN classify_at TEXT;    -- ② 분류 완료 시각
ALTER TABLE document_meta ADD COLUMN summarize_at TEXT;   -- ③ 요약 완료 시각

CREATE INDEX IF NOT EXISTS idx_doc_meta_extract  ON document_meta(extract_at);
CREATE INDEX IF NOT EXISTS idx_doc_meta_classify ON document_meta(classify_at);
CREATE INDEX IF NOT EXISTS idx_doc_meta_summarize ON document_meta(summarize_at);

UPDATE meta_kv SET value='006' WHERE key='schema_version';

COMMIT;
