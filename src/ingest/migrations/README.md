# L4-K Schema Migrations

V2.5.1 Phase 1 산출물. `meta_kv.schema_version` 기반 idempotent 마이그레이션.

## 정책

- 파일명: `NNN_<slug>.sql` (up) / `NNN_<slug>_down.sql` (down)
- 버전: 3자리 zero-padded (`001`, `002`, ...)
- 추적: `meta_kv` 테이블의 `schema_version` 키
- 트랜잭션: 각 SQL 파일은 `BEGIN; ... COMMIT;`으로 원자성
- 적용 순서: 버전 오름차순
- 롤백: 적용 역순으로 down 실행

## 명령

```bash
# 현재 버전 + 사용 가능 마이그레이션
make migrate-v2.6-status

# Dry run (SQL만 출력)
make migrate-v2.6-dry

# 최신까지 적용
make migrate-v2.6

# 특정 버전으로 롤백
make migrate-v2.6-down TO=001
```

직접 호출:
```bash
python3 -m apps.ingest.migrate status
python3 -m apps.ingest.migrate up --to 001
python3 -m apps.ingest.migrate down --to 000 --dry-run
```

## 현재 마이그레이션

| 버전 | 내용 | V2.5.1 매트릭스 |
|---|---|---|
| 001 | `documents.kind` + `documents.origin` 컬럼 + 인덱스 | §2.A "Source/Entity/Concept 3층" + §2.D "AI provenance" |
| 002 | `entity_aliases` 테이블 | §2.D "Entity 동의어/다국어 표기 분열" |

## 새 마이그레이션 추가 절차

1. 마지막 버전 확인: `ls apps/ingest/migrations/*.sql | tail -2`
2. 다음 번호로 신규 파일 작성:
   - `NNN_<slug>.sql` (up)
   - `NNN_<slug>_down.sql` (down)
3. 두 파일 모두 `BEGIN; ... COMMIT;` 감싸기
4. up 끝에 `meta_kv` schema_version을 `NNN`으로 갱신
5. down 끝에 `meta_kv` schema_version을 직전 버전으로 되돌림
6. M2에서 dry-run: `make migrate-v2.6-dry`
7. M5에서 실제 적용: `make migrate-v2.6`

## 안전 수칙

- **운영 DB는 M5에만 존재.** M2에서는 dry-run 또는 임시 DB로 테스트.
- 마이그레이션 실행 전 `_index.db` 백업 확인 (launchd plist가 매일 03:17 자동 수행).
- SQLite 3.35+ 필요 (ALTER TABLE DROP COLUMN). M5 = 3.51 ✅.
- FTS5 가상 테이블 `documents_fts`는 ALTER 불가 — 새 컬럼이 FTS 인덱싱 대상이면 별도 재구축 필요.

## 검증

마이그레이션 후 sanity:
```bash
# 컬럼/테이블 존재
sqlite3 knowledge/_index.db ".schema documents" | grep -E "kind|origin"
sqlite3 knowledge/_index.db ".schema entity_aliases"

# row 수 무변 (Phase 1 게이트)
sqlite3 knowledge/_index.db "SELECT COUNT(*) FROM documents;"  # 630 유지

# 기존 행 origin = 'human' 자동 채움
sqlite3 knowledge/_index.db "SELECT origin, COUNT(*) FROM documents GROUP BY 1;"
```
