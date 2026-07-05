# 작업지시서 — DIAG-SOT / P4 (잔여 이관·legacy 격리·MANIFEST·lineage = 추적성 완성)

- **발행:** 2026-07-06 · Gatekeeper(Claude) → Executor(M2 Cursor)
- **선행:** P0~P3 완료. **P4 = DIAG-SOT 마무리 + 제1 동인(추적성) 결실.**
- **접근:** diagnosis-tool `feat/diag-sot-sync`. **C-Server/prod 무접촉.**

---

## A. P4 목적

1. **잔여 팩 이관** — 아직 dx SoT에 없는 팩을 편입(byte-0, P1식).
2. **legacy·중복 격리** — 중복/구버전/변종을 `_archive`로(로더 무참조 확인 후).
3. **생성기 은퇴** — `_generate_*.py`(8개) 중 DECISIONS 확정분 격리(재생성이 SoT 덮지 않게).
4. **MANIFEST 통합** — 스테이지별 `dx_pack_manifest` → **단일 MANIFEST**(status·consumers·**live=로더 100%**).
5. **lineage 완성(제1 동인)** — 스테이지별 `dx_lineage` → **단일 lineage**(필드→팩path→소비챕터). = "어디 고치면 어디 반영되는지"가 드러남.

## B. 현 편입 상태 (Gatekeeper 실측, 참고)

- **dx 편입 완료:** registry(industry/sub·alias), Q1~Q5 matrix, fixed_labels, Ch3/6 sub_override, Ch2 system/module/sub_override. `dx_lineage`(_p1b·_p3a), `dx_pack_manifest`(스테이지별) 존재.
- **전체:** server 97 + client 16 = 113 팩. `_generate_*.py` 8개.

## C. P4-0 — 선행 plan/inventory draft (M2 → Gatekeeper 확정)

**M2 산출:** `docs/diag-sot/reports/P4_PLAN_DRAFT.md`
1. **편입 vs 잔여 인벤토리:** 113팩 각각 **dx 편입됨 / 잔여** 표시. 잔여 팩(예: ch4 plan_defaults·ch5 team_governance(py dict)·roi 잔여·catalogs·루트 산재) 목록 + 이관 방식(byte-0 or 구조상이).
2. **legacy·중복 격리 대상:** keywords_map×3·drivers×2·sub_industry×3·ch1 3변종·ch2 v2/v3·`_archive` 등, **각 로더 참조 여부**(참조 있으면 격리 금지). MANIFEST live=로더 대조로 판정.
3. **생성기 은퇴:** `_generate_*.py` 8개 중 은퇴 대상(DECISIONS P0 확정 반영). 은퇴 시 **커버리지 공백 0** 확인.
4. **MANIFEST 통합안:** 스테이지별 manifest → 단일 스키마(pack_id·status·consumers·source·byte0 여부·live/loader).
5. **lineage 통합안:** `dx_lineage` 합본 + **관리탭 lineage 뷰 데이터 계약**(셀/노드 → 팩path → 소비챕터). iris-hub 관리탭 UI가 소비할 형태.
6. 위험/질문(ch5 py dict 이관 형태 등).

## D. 방식·게이트 (P4 구현 시)

- **격리 = `_archive` 이동**(복원가능), 삭제 아님. **로더 참조 0 확인 후에만.**
- **잔여 이관 = byte-0**(dx-only, P1식 acid-test). 구조상이 팩은 정책 명시.
- **MANIFEST live = 실제 로더 100% 일치**(고아팩 0).
- **lineage = 전 팩 필드→팩→소비 매핑 완비.**
- prod 무접촉, 기존 zh 보존, `data` 수기편집 금지 CI.

## E. 금지 (plan 단계)

- ❌ 구현(이관·격리·삭제·MANIFEST·CI) 착수 — plan draft만.
- ❌ 로더 참조 있는 팩 격리 / prod 반영 / 기존 콘텐츠 삭제 / 추정 매핑.

## F. 후속 (P4 밖, 참고)

**iris-hub 관리 탭 UI**(dx_* 그리드 + lineage 뷰 + 편집→sync)는 이 lineage 데이터를 소비하는 **원 목표 산출물**. P4가 그 데이터·MANIFEST 기반을 완성하면, 관리탭 UI 구현이 이어짐.

## G. git·보고서

`P4_PLAN_DRAFT.md`만 커밋(`[DIAG-SOT][P4] plan draft`). git 막히면 경로·해시 통지 → Gatekeeper 대행.

**PASS/확정 판정은 Gatekeeper. plan 확정 전 P4 구현 금지.**
