-- Migration 003: FTS5 토크나이저를 unicode61 → trigram 으로 전환
-- 발견: unicode61이 CJK 한자 연속(单晶薄膜, 良率 등)을 분절하지 못해
-- LN_LT 31KB 中文 본문이 영문 키워드 외 검색 불가 (V2.5.3 §13).
-- trigram은 모든 언어 N-gram 처리 — CJK·한국어·영문 일관 토큰화.

BEGIN;

DROP TABLE IF EXISTS documents_fts;

CREATE VIRTUAL TABLE documents_fts USING fts5(
  title, body, tokenize='trigram'
);

-- 기존 documents + chunks에서 재인덱싱
INSERT INTO documents_fts (rowid, title, body)
SELECT d.rowid, COALESCE(d.title, ''), COALESCE(GROUP_CONCAT(c.text, char(10)), '')
  FROM documents d
  LEFT JOIN chunks c ON c.doc_id = d.doc_id
  GROUP BY d.doc_id;

INSERT INTO meta_kv (key, value) VALUES ('schema_version', '003')
  ON CONFLICT(key) DO UPDATE SET value = '003';

COMMIT;
