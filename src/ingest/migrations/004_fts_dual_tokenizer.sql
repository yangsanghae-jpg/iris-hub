-- Migration 004: documents_fts_trigram 보조 인덱스 신설 (CJK 보조)
-- V2.5.3 §13.2 발견: unicode61이 CJK 미분절, trigram이 한국어 2자 미분절.
-- 두 인덱스 병행 + retrieval에서 OR 결합으로 양쪽 강점 살림.
-- 003에서 documents_fts를 trigram으로 바꾼 결정을 정정:
--   - documents_fts (메인) → unicode61 복원 (한국어·영문 강점)
--   - documents_fts_trigram (보조) → trigram (CJK 처리)

BEGIN;

-- 메인 인덱스 unicode61 복원
DROP TABLE IF EXISTS documents_fts;

CREATE VIRTUAL TABLE documents_fts USING fts5(
  title, body, tokenize='unicode61'
);

INSERT INTO documents_fts (rowid, title, body)
SELECT d.rowid, COALESCE(d.title, ''), COALESCE(GROUP_CONCAT(c.text, char(10)), '')
  FROM documents d
  LEFT JOIN chunks c ON c.doc_id = d.doc_id
  GROUP BY d.doc_id;

-- 보조 trigram 인덱스 신설 (CJK + 부분 매치)
CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts_trigram USING fts5(
  title, body, tokenize='trigram'
);

INSERT INTO documents_fts_trigram (rowid, title, body)
SELECT d.rowid, COALESCE(d.title, ''), COALESCE(GROUP_CONCAT(c.text, char(10)), '')
  FROM documents d
  LEFT JOIN chunks c ON c.doc_id = d.doc_id
  GROUP BY d.doc_id;

INSERT INTO meta_kv (key, value) VALUES ('schema_version', '004')
  ON CONFLICT(key) DO UPDATE SET value = '004';

COMMIT;
