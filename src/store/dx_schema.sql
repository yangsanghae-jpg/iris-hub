-- dx_* — 진단툴 팩 SoT (DIAGNOSIS_PACK_MGMT_TAB_DESIGN §3)
-- SCHEMA_VERSION 2+. documents/concepts 와 네임스페이스 분리.

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
