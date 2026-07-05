# 작업지시서 — DIAG-SOT / P3a (+ P3 Discovery 판정·스코프 결정)

- **발행:** 2026-07-05 · Gatekeeper(Claude) → Executor(M2 Cursor)
- **선행:** P3 Discovery(`6fc6a56`) 검토 완료. **P3 스코프 분할 확정.**
- **접근:** diagnosis-tool `feat/diag-sot-sync`. **C-Server/prod 무접촉.**

> ⚠️ **git workflow:** M2 환경에서 git 명령이 막혀 이번 discovery draft는 Gatekeeper가 1Dev clone에서 대행 커밋함. **P3a부터는 실제 코드 변경이 생기므로 M2 git 복구 필요**(안 되면 Gatekeeper가 계속 대행하되, M2는 산출 파일 경로·상태를 정확히 통지).

---

## A. P3 Discovery 판정: ✅ 우수 · 승인

draft가 매우 철저하며 P3의 복잡도(Ch2 특화 분산·sub key 파편화·언어 master 혼재·prod 무노출 부재·tier 하드코딩)를 정확히 드러냄. 이 철저함이 **P3 분할**의 근거.

## B. 스코프 결정 (확정)

- **P3a = Ch3(scope) + Ch6(ROI)** ← **먼저**(사장 확정: 안전 우선). 이미 `by_industry.<x>.by_sub_industry.<slug>` 캐스케이드 존재 → 엔진 최소변경으로 sub_override 모델 증명.
- **P3b = Ch2 system→module→sub_override + 엔진 개편** ← 나중(가장 분산·위험).

**기술 결정(스코프 무관, 확정):**
| 항목 | 결정 |
|------|------|
| canonical sub key | **`subindustry_code`(A01/B01)** + alias map으로 slug·SUB_* 연결. **P1의 SUB_*↔A01 open issue를 여기서 해소.** |
| `lang_ko.py` | legacy fallback 보존(제거·bypass 금지) |
| 기존 zh | sibling 보존 + legacy freeze(손실 0) |
| prod 무노출 | env flag + dev 전용 pack 경로(prod runtime 무변경) |
| **이연(P3b/후반)** | tier 외부화 · DB(SQLite) mode 확장 · server `lang` 기본 flip |

## C. P3a 목적

Ch3/Ch6의 **기존 `by_sub_industry` 델타를 dx sub_override 정본으로 편입** + **canonical sub alias map** 구축. 엔진은 기존 캐스케이드를 그대로 소비 → 최소변경. 저위험으로 **sub_override 오소링+게이트 모델 증명.**

## D. P3a-0 — 선행 스키마 draft (M2 → Gatekeeper 승인)

**M2 산출:** `docs/diag-sot/reports/P3A_SCHEMA_DRAFT.md` (구현 전, 승인 후 착수)
1. **canonical sub alias map:** `A01 ↔ slug(logic_foundry) ↔ SUB_*(SUB_B_WAFER)`. 근거 = `sub_industry_aliases.json`·`sub_industry_meta.json` + scope/roi catalog의 실제 slug 목록. **근거 없으면 추정 말고 issue**(P1 issue와 연계). 74 sub 매핑 커버리지 보고.
2. **dx sub_override 스키마:** `(chapter, sub_code, section, delta_json, lang_fields)`. Ch3=`mvp/expand/boundary(+_ko)`, Ch6=`quant/proof/boundary(+_ko/_zh)`. **append/extend semantics 보존.**
3. **roundtrip 계획:** dx → sync → `ch3/scope_catalog.json`·`roi/roi_logic_catalog_v1.json` **기존 델타 byte-0 재현**(P1식 dx-only acid-test 적용).
4. **ko-master + zh 보존 정책:** 기존 `*_ko` sibling·zh base 보존 방식 명시.
5. **위험/질문**(slug drift 등).

## E. 방식·게이트 (P3a 구현 시)

- **기존 sub 델타 = byte-0 재현**(dx-only, legacy 숨김 acid-test). 이게 "기존 콘텐츠 무손실 편입" 증명.
- **신규 델타(추가 시) = dev 전용**, prod 무노출, 챕터 스냅샷.
- **엔진 무변경 우선**(캐스케이드 존재). 변경 필요시 범위 명시·승인.
- prod 무노출, **zh 손실 0**, alias map 근거/issue 명확.

## F. 금지사항

- ❌ Ch2·systems_catalog·Card1·engine_bridge 접촉(P3b).
- ❌ tier 외부화·DB mode·server `lang` 기본 변경(이연).
- ❌ `lang_ko.py` 변경.
- ❌ prod 반영 / 기존 zh 삭제 / SUB_*↔A01 임의매핑.

## G. git·보고서

- `P3A_SCHEMA_DRAFT.md`만 커밋+push(`[DIAG-SOT][P3a] schema draft`). **git 안 되면 파일 경로·상태 통지 → Gatekeeper 대행.**
- 구현은 승인 후.

**PASS/확정 판정은 Gatekeeper. 스키마 확정 전 P3a 구현 금지.**
