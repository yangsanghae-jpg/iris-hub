# 작업지시서 — DIAG-SOT / P3b (+ P3a 완료 판정)

- **발행:** 2026-07-06 · Gatekeeper(Claude) → Executor(M2 Cursor)
- **선행:** **P3a = PASS/완료** (§A). P3b 착수 허가 (schema draft 먼저).
- **접근:** diagnosis-tool `feat/diag-sot-sync`. **C-Server/prod 무접촉.**

---

## A. P3a 완료 판정 (Gatekeeper 독립 검증)

commit `9c65425`. **PASS.**
- **G3/G4 byte-0:** Ch3·Ch6 dx-only 재조립 = 원본 byte-0(직접 cmp).
- **G5 dx-only 진짜 증명:** `dx_sub_override_base_catalog`의 by_sub_industry=**0(비움)** 확인 + `rebuild`가 source 카탈로그 미독(newline만) + **mutation test**(dx `field_rows` 값 변경 → 출력 반영, 재추출 안 함) → passthrough 아님 확정.
- **G2:** SUB_* 매핑 **0**(추정 없음), issue 13(alt_code_uncertain + catalog_slug_without_canonical). shared_slug `solar_pv` 등 **1회 방출**(중복 0). 빈 `{}` 32 보존.
- 무접촉(신규 파일만), 엔진 무변경.

**→ P3a 완료:** Ch3/6 sub_override가 **iris-hub dx 정본에서 재조립되어 byte-0**. **sub_override 오소링+게이트 모델 확립** + **P1 SUB_*↔A01 issue를 alias map으로 정식 관리**(추정 없이).

---

## B. P3b 목적 (요구3 본안 — Ch2 system→module→sub_override)

사장님이 원래 강조한 **"제안 시스템 → 기능(module) → 세부산업 특화(키워드/포인트)"** 를 Ch2에 구현. ko-master 콘텐츠. 엔진이 sub_override 델타 소비하도록 **부분 개편**.

**최대 난제(discovery 재확인):** Ch2 특화가 **분산**(systems_catalog·Card1 V3 master·scale overlay·zh overlay·stack library·engine bridge·DB mode). 단일 마이그레이션 위험 → **P3b도 내부 단계화** 예상.

## C. P3b-0 — 선행 스키마/접근 draft (M2 → Gatekeeper 확정)

**M2 산출:** `docs/diag-sot/reports/P3B_SCHEMA_DRAFT.md`
1. **system/module/sub_override 스키마:** `systems_catalog`(system) + `capabilities`→**module 엔티티화**(stable module id 규칙) + `maturity`/`automation_fit`. sub_override = system|module × sub 델타(키워드·포인트).
2. **Ch2 분산 소스 매핑:** systems_catalog·Card1 V3 master(`10_card1_master_v3_74.json`)·scale overlay·stack library가 각각 system/module/sub_override 중 무엇인지, 무엇을 정본으로 삼고 무엇을 파생/legacy로 둘지.
3. **sub_override 입도 결정 제안:** `system×sub` vs `module×sub`(실데이터 분포 근거). **canonical sub key = P3a alias map 재사용**(A01, slug는 alias).
4. **byte-0 roundtrip 계획:** 기존 Ch2 콘텐츠(zh-master systems_catalog 등)를 dx로 무손실 편입 → **기존 shape byte-0 재현**(P3a식 dx-only, 비운 base). 신규 sub_override/module = **dev 전용**.
5. **엔진 개편 범위 제안:** Card1만 우선인지 Ch2 전체인지. 기존 scattered sub 경로(Card1 V3·scale overlay) 활용 vs 신규 by_sub_industry. **최소 개편 우선.**
6. **prod 무노출 장치 설계:** env flag(예 `DIAG_SOT_DEV=1`) + dev 전용 pack 경로. prod runtime 경로 무변경 보장 방법.
7. **언어:** systems_catalog(zh-master)·card master(ko-master) 혼재 → ko-master 신규 + **기존 zh freeze**(손실 0). `lang_ko.py`는 legacy fallback 보존.
8. **위험/질문:** DB mode field loss, S5, tier 외부화 포함 여부(**기본 이연**).

## D. 확정된 제약 (P3b 전체)

- **이연 유지:** tier 외부화·DB(SQLite) mode 확장·server `lang` 기본 flip은 **P3b 기본 범위 밖**(필요 근거 있으면 별도 승인).
- canonical sub key = A01 + P3a alias map. SUB_*↔A01 임의매핑 금지(issue 유지).
- prod 무노출, 기존 zh 손실 0, `lang_ko.py` 미제거.
- 신규 콘텐츠(module/sub_override) = dev 전용, prod 미노출.

## E. 방식·게이트 (P3b 구현 시)

- 기존 Ch2 콘텐츠 = **byte-0 재현**(dx-only, 비운 base, mutation test로 dx 의존 증명 — P3a 방식).
- 신규 module/sub_override = dev 전용 + 챕터 스냅샷 + prod 무노출 확인.
- 엔진 개편분 = git-diff 명시 + 회귀(골든).

## F. 금지 (schema draft 단계)

- ❌ 구현(dx·sync·엔진·systems_catalog·Card1) 착수 — 스키마 draft만.
- ❌ tier/DB/server default 변경, `lang_ko.py` 변경, prod 반영, 기존 zh 삭제.
- ❌ 빈칸 임의판단 — 중단·질문.

## G. git·보고서

- `P3B_SCHEMA_DRAFT.md`만 커밋(`[DIAG-SOT][P3b] schema draft`). **git DNS 막히면 로컬 커밋+경로/해시 통지 → Gatekeeper 대행 push.**

**PASS/확정 판정은 Gatekeeper. 스키마 확정 전 P3b 구현 금지.**
