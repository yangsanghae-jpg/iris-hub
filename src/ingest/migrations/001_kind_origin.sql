-- Migration 001: K3 `kind` + `origin` 컬럼 추가
-- V2.5.1 §2.A (Source/Entity/Concept 3층) + §2.D (Echo Chamber 차단)
--
-- documents.kind   ∈ {source, entity, concept}  — NULL 허용 (기존 행은 미분류 상태로 유지)
-- documents.origin ∈ {human, ai, hybrid}        — NOT NULL DEFAULT 'human' (기존 행 = human 추정)
--
-- 적용 후 V2.6 K6 Curate가 Trigger A/B 입력에서 origin='ai' 제외 가능.

BEGIN;

ALTER TABLE documents ADD COLUMN kind   TEXT;
ALTER TABLE documents ADD COLUMN origin TEXT NOT NULL DEFAULT 'human';

CREATE INDEX IF NOT EXISTS idx_doc_kind   ON documents(kind);
CREATE INDEX IF NOT EXISTS idx_doc_origin ON documents(origin);

-- schema_version 갱신
INSERT INTO meta_kv (key, value) VALUES ('schema_version', '001')
  ON CONFLICT(key) DO UPDATE SET value = '001';

COMMIT;
