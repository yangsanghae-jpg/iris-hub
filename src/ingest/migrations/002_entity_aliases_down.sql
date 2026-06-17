-- Rollback 002: entity_aliases 제거

BEGIN;

DROP INDEX IF EXISTS idx_alias_text;
DROP INDEX IF EXISTS idx_alias_entity;
DROP TABLE IF EXISTS entity_aliases;

UPDATE meta_kv SET value = '001' WHERE key = 'schema_version';

COMMIT;
