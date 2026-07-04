-- iris-hub 저장소 스키마 (S1) — STORE_SCHEMA_DESIGN §2
-- 단일 SQLite. ④데이터볼트 그룹 + ③지식저장소 그룹. 마이그레이션 누적 아님 — 새 출발.
-- SCHEMA_VERSION 은 src/store/db.py 가 관리(meta_kv.schema_version).

PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA foreign_keys=ON;

-- ─────────────────────────────────────────────────────────────────────────
-- ④ 데이터볼트 그룹 (문서층)
-- ─────────────────────────────────────────────────────────────────────────

-- 문서 (원본 1건 = 1행)
CREATE TABLE IF NOT EXISTS documents (
  doc_id        TEXT PRIMARY KEY,               -- {channel}_{yyyymmdd}_{seq} 또는 raw:{hash}
  channel       TEXT NOT NULL,                  -- doc | chat | web
  source        TEXT,                           -- 원본 경로 | 세션id | URL
  original_path TEXT,                           -- vault/originals/ 내 보존 경로 (copy-on-ingest)
  title         TEXT,
  trust         TEXT NOT NULL DEFAULT 'auto',    -- auto | clipped | verified
  status        TEXT NOT NULL DEFAULT 'active',  -- active | quarantine | rejected
  industry      TEXT, area TEXT, level TEXT,     -- K2 분류
  ingested_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_doc_status  ON documents(status);
CREATE INDEX IF NOT EXISTS idx_doc_channel ON documents(channel);

-- 청크 (검색·RAG 단위)
CREATE TABLE IF NOT EXISTS chunks (
  chunk_id TEXT PRIMARY KEY,
  doc_id   TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
  ord      INTEGER NOT NULL,
  text     TEXT NOT NULL,
  page_ref TEXT                                  -- 원문 위치 앵커 (p.12 등) — 환각 억제
);
CREATE INDEX IF NOT EXISTS idx_chunk_doc ON chunks(doc_id);

-- 전문검색 (dual tokenizer — unicode61 + CJK trigram, 검증된 패턴)
-- unicode61 은 chunks 외부콘텐츠 연결(rowid=chunks.rowid), trigram 은 독립(수동 동기).
CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts
  USING fts5(text, content='chunks', content_rowid='rowid');
CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts_trigram
  USING fts5(text, tokenize='trigram');

-- K2 처리 산출 (문서별 1행)
CREATE TABLE IF NOT EXISTS document_meta (
  doc_id                TEXT PRIMARY KEY REFERENCES documents(doc_id) ON DELETE CASCADE,
  summary               TEXT,
  topics_json           TEXT, entities_json TEXT, concepts_json TEXT,  -- 원시 추출(정규화 전)
  extract_at            TEXT, classify_at TEXT, summarize_at TEXT,      -- 단계별 timestamp (재개)
  k2_done_at            TEXT,                    -- 3단계 완주 (done 판정)
  classifier_version    TEXT, confidence REAL, fallback_used INTEGER DEFAULT 0,
  processing_started_at TEXT,                    -- 락 (좀비 안전망)
  fail_count            INTEGER DEFAULT 0, last_error TEXT
);

-- 임베딩 (시맨틱 검색 — FAISS 사이드카가 정본, 여기는 참조 매핑)
CREATE TABLE IF NOT EXISTS embeddings (
  chunk_id TEXT PRIMARY KEY REFERENCES chunks(chunk_id) ON DELETE CASCADE,
  faiss_id INTEGER, model TEXT, dim INTEGER
);

-- ─────────────────────────────────────────────────────────────────────────
-- ③ 지식저장소 그룹 (개념층)
-- ─────────────────────────────────────────────────────────────────────────

-- 개념 (1급 객체 — "Knowledge Unit")
CREATE TABLE IF NOT EXISTS concepts (
  concept_id  TEXT PRIMARY KEY,                 -- canonical snake_case (mes, yield_rate, rtd)
  canonical   TEXT NOT NULL,                    -- 표시명
  definition  TEXT,                             -- 개념 정의 (위키 개념 페이지 본문)
  trust       TEXT DEFAULT 'candidate',         -- candidate | verified (사람 승인 게이트)
  degree      INTEGER DEFAULT 0,                -- 연결 문서 수 (자산 크기 — 캐시)
  created_at  TEXT, updated_at TEXT
);

-- 개념 별칭 (정규화의 핵심 — MES=생산실행시스템=制造执行系统)
CREATE TABLE IF NOT EXISTS concept_aliases (
  concept_id TEXT NOT NULL REFERENCES concepts(concept_id) ON DELETE CASCADE,
  alias      TEXT NOT NULL,
  lang       TEXT,                              -- ko | en | zh
  PRIMARY KEY (concept_id, alias)
);
CREATE INDEX IF NOT EXISTS idx_alias ON concept_aliases(alias);

-- 개념 ↔ 문서 링크 (degree 원천)
CREATE TABLE IF NOT EXISTS concept_docs (
  concept_id TEXT NOT NULL REFERENCES concepts(concept_id) ON DELETE CASCADE,
  doc_id     TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
  weight     REAL DEFAULT 1.0,                  -- 관련도 (빈도·위치 기반)
  PRIMARY KEY (concept_id, doc_id)
);

-- 개념 ↔ 개념 관계 (동시출현 1차 → 명시적 Fact 2차)
CREATE TABLE IF NOT EXISTS concept_relations (
  src_id TEXT NOT NULL REFERENCES concepts(concept_id) ON DELETE CASCADE,
  dst_id TEXT NOT NULL REFERENCES concepts(concept_id) ON DELETE CASCADE,
  kind   TEXT NOT NULL DEFAULT 'cooccur',       -- cooccur | uses | integrates | ...
  weight INTEGER DEFAULT 1,                     -- 동시출현 문서 수
  PRIMARY KEY (src_id, dst_id, kind)
);

-- 개념 후보 (정규화 실패분 — 사람 승인 대기, S4 §4)
CREATE TABLE IF NOT EXISTS concept_candidates (
  raw_norm   TEXT PRIMARY KEY,          -- 폴백 정규화 키
  sample     TEXT,                      -- 원문 표기 예
  doc_count  INTEGER DEFAULT 0,         -- 등장 문서 수 (우선순위)
  first_seen TEXT, last_seen TEXT
);
CREATE INDEX IF NOT EXISTS idx_candidate_count ON concept_candidates(doc_count DESC);

-- 시스템 메타
CREATE TABLE IF NOT EXISTS meta_kv (key TEXT PRIMARY KEY, value TEXT NOT NULL);

-- ─────────────────────────────────────────────────────────────────────────
-- dx_* — 진단툴 팩 SoT (SCHEMA_VERSION 2+, DIAGNOSIS_PACK_MGMT_TAB_DESIGN §3)
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dx_import (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_branch TEXT,
  source_commit TEXT,
  imported_at TEXT NOT NULL,
  note TEXT
);

CREATE TABLE IF NOT EXISTS dx_industry (
  code TEXT PRIMARY KEY,
  message_theme TEXT,
  priority_axes_json TEXT,
  ord INTEGER
);

CREATE TABLE IF NOT EXISTS dx_sub_industry (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  industry_code TEXT NOT NULL REFERENCES dx_industry(code),
  canon_code TEXT NOT NULL UNIQUE,
  ord INTEGER
);

CREATE TABLE IF NOT EXISTS dx_sub_bridge (
  sub_id INTEGER NOT NULL REFERENCES dx_sub_industry(id) ON DELETE CASCADE,
  scheme TEXT NOT NULL,
  external_code TEXT NOT NULL,
  PRIMARY KEY (sub_id, scheme, external_code)
);
CREATE INDEX IF NOT EXISTS idx_dx_bridge_scheme ON dx_sub_bridge(scheme, external_code);

CREATE TABLE IF NOT EXISTS dx_profile (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  industry_code TEXT NOT NULL REFERENCES dx_industry(code),
  scope TEXT NOT NULL,
  routing_code TEXT,
  flow_style TEXT,
  control_unit TEXT,
  UNIQUE (industry_code, scope)
);

CREATE TABLE IF NOT EXISTS dx_profile_item (
  profile_id INTEGER NOT NULL REFERENCES dx_profile(id) ON DELETE CASCADE,
  block TEXT NOT NULL,
  code TEXT NOT NULL,
  weight REAL,
  ord INTEGER,
  PRIMARY KEY (profile_id, block, code)
);

CREATE TABLE IF NOT EXISTS dx_routing_pack (
  routing_code TEXT PRIMARY KEY,
  flow_style TEXT,
  control_unit TEXT,
  priority_axes_json TEXT,
  routing_theme TEXT
);

CREATE TABLE IF NOT EXISTS dx_routing_effect (
  routing_code TEXT NOT NULL REFERENCES dx_routing_pack(routing_code) ON DELETE CASCADE,
  kind TEXT NOT NULL,
  block TEXT NOT NULL,
  code TEXT NOT NULL,
  value REAL,
  PRIMARY KEY (routing_code, kind, block, code)
);

CREATE TABLE IF NOT EXISTS dx_code (
  kind TEXT NOT NULL,
  code TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  PRIMARY KEY (kind, code)
);

CREATE TABLE IF NOT EXISTS dx_code_alias (
  kind TEXT NOT NULL,
  alias_code TEXT NOT NULL,
  canon_code TEXT NOT NULL,
  PRIMARY KEY (kind, alias_code)
);

CREATE TABLE IF NOT EXISTS dx_question_metric (
  sub_id INTEGER NOT NULL REFERENCES dx_sub_industry(id) ON DELETE CASCADE,
  question TEXT NOT NULL,
  metric_key TEXT NOT NULL,
  value REAL,
  notes TEXT,
  PRIMARY KEY (sub_id, question, metric_key)
);

CREATE TABLE IF NOT EXISTS dx_scoring_param (
  key TEXT PRIMARY KEY,
  value REAL
);

CREATE TABLE IF NOT EXISTS dx_label (
  entity_kind TEXT NOT NULL,
  entity_key TEXT NOT NULL,
  lang TEXT NOT NULL,
  label TEXT,
  explain TEXT,
  PRIMARY KEY (entity_kind, entity_key, lang)
);

CREATE TABLE IF NOT EXISTS dx_text (
  key TEXT NOT NULL,
  lang TEXT NOT NULL,
  template TEXT,
  PRIMARY KEY (key, lang)
);

CREATE TABLE IF NOT EXISTS dx_apply_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  applied_at TEXT NOT NULL,
  commit_sha TEXT,
  message TEXT,
  files_json TEXT,
  validation_json TEXT
);

CREATE VIEW IF NOT EXISTS v_dx_coverage AS
SELECT
  s.industry_code,
  s.canon_code,
  s.id AS sub_id,
  q.question,
  CASE WHEN EXISTS (
    SELECT 1 FROM dx_question_metric m
    WHERE m.sub_id = s.id AND m.question = q.question
  ) THEN 1 ELSE 0 END AS has_metric
FROM dx_sub_industry s
CROSS JOIN (
  SELECT 'Q2' AS question UNION ALL
  SELECT 'Q3' UNION ALL
  SELECT 'Q4' UNION ALL
  SELECT 'Q5_REC' UNION ALL
  SELECT 'Q5_MGMT'
) q;
