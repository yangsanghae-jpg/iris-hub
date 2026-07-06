# WORK ORDER — DIAG-SOT P4-cleanup (격리·residual byte-0·generator 은퇴)

- **발행:** 2026-07-06 · Gatekeeper(Claude) → **실행: M5 Cursor**
- **선행:** P4-core PASS(`P4_CORE_GATE_VERDICT.md`) · repo `diagnosis-tool` `feat/diag-sot-sync`
- **성격:** 부차·이연 가능. **각 배치 = proof 제출 → Gatekeeper 승인 → 실행.** wholesale 금지.
- **원칙:** 격리는 내용 낡음이 아니라 `loader_reference_status=unreferenced` 증명으로만. 이동은 `_archive/`(복원 가능)만, 삭제 금지.

---

## 공통 규율 (전 배치)

- ❌ 로더가 (직접·간접) 참조하는 팩 이동 금지. `DIAG_SOT_MANIFEST.json`의 `live_*` 팩 불가침.
- ❌ generator 위험 실행 금지(출력 경로가 런타임 팩을 덮어쓸 수 있는 실행). hash 비교는 temp 출력으로만.
- ❌ prod(C-Server) 무접촉. `DIAG_SOT_DEV=1` flag-off = baseline 동일 유지.
- ✅ 모든 이동은 아래 형식의 archive manifest row 동반:
  ```json
  {"path":"server/data/system_catalog.json",
   "archive_path":"_archive/diag-sot/2026-07-06/server/data/system_catalog.json",
   "archive_reason":"legacy_duplicate_unreferenced",
   "loader_reference_proof":"grep server+client (tool/test 제외) 매치 0; 재현 명령 포함",
   "live_replacement":"server/data/ch2/catalog/systems_catalog.json",
   "restorable":true}
  ```
- ✅ 각 배치 후 golden 회귀 + flag-off delta test 무변경 확인.

---

## 배치 A — archive 3후보 격리 (최소·저위험)

**대상 (P4-core 무참조 확정):**
1. `server/data/system_catalog.json` (live 대체=`ch2/catalog/systems_catalog.json`)
2. `server/data/ch1/catalog/drivers.json` (live 대체=`ch1/catalog/drivers_catalog.json`)
3. `server/data/tools/diagnose_req_ch2.json` (tool fixture)

**방법:**
1. 각 파일 무참조 재증명:
   ```bash
   grep -rn "<basename>" server client --include=*.py --include=*.js --include=*.mjs \
     | grep -viE "_backup|/archives/|/tests/|test_|/data/tools/|/_legacy|/scripts/"
   # 결과 0줄 확인 (증거로 첨부)
   ```
2. `_archive/diag-sot/2026-07-06/<원경로>`로 **이동**(git mv), archive manifest row 추가.
3. golden 회귀 + flag-off delta test 실행 → 무변경 확인.
4. **proof(무참조 grep 출력 + 회귀 결과)를 Gatekeeper에 제출 → 승인 후 커밋.**

**금지:** 3건 외 어떤 파일도 이 배치에 포함 금지. `ch1_industries`/`stack_library` 등 오해 금지(live_indirect).

**Exit:** 3파일 `_archive/` 이동, 런타임 로드 경로에서 사라짐, 회귀 green, archive manifest 갱신.

---

## 배치 B — residual byte-0 이관 (승인된 residual-live만)

**우선 후보 (MANIFEST coverage_status=residual_live 중 load-bearing):**
- `ch4_plan_defaults` (`server/data/ch4/plan_defaults.json`) — Ch4 런타임 콘텐츠.
- `step5_2_management_analysis` (`management_analysis_v3.json` + `_i18n_zh.json`) — ko-primary + zh 미러, **slug parity risk** 주의.
- `ch0_exec_subs` (`ch0_exec_subs.json`) — sub_override seed.

**방법 (팩 단위, 독립 diff 게이트):**
1. dx authoring 산출(`scripts/data_poc/_p4/dx_<pack>.json`) 작성 → P1 방식 재조립.
2. **byte-0 acid-test**(legacy 숨김·dx-only 재현) + load-bearing 필드는 **mutation test**.
3. 언어/구조 상이 팩(zh 미러)은 "의도된 diff만" 정책 적용, slug parity 검증.
4. MANIFEST 해당 팩 `coverage_status` → `dx_covered_byte0`(또는 partial), `dx_artifacts`·`generated_path` 채움. LINEAGE row-level 추가.
5. **팩별 proof → Gatekeeper 승인 → 커밋.**

**금지:** Ch2 card masters(`10_card*_master*`)·Card1 V3 byte-0 이관 **금지**(Gatekeeper Q3: lineage-only 유지, byte-0는 P3b-6/후속). ch5 team_governance(Python dict)는 §7 확정본 없이 강행 금지.

**Exit:** 승인 팩 byte-0 green, MANIFEST/LINEAGE 갱신, flag-off 무변경.

---

## 배치 C — generator 은퇴

**대상 (실측 7):** `docs/by_step/data/_generate_{ch0_subs,factors,step3_v3,step4_v3,step4_v3_1_repack,sub_pack,sub_profiles}.py`
(주: `*_generate_*.py` glob 8건 중 1건은 `server/.venv` pydantic 오탐 → 제외.)

**은퇴 게이트 (generator별):**
1. 선언된 출력 경로 식별.
2. temp/격리 출력으로 재생성(런타임 팩 미덮어쓰기) → **hash 비교**로 현재 런타임/SoT 팩과 커버리지 일치 확인.
3. loader가 generator를 직접 import하지 않음 확인(`grep import _generate`).
4. 커버리지 공백 0 + no-import 증명 후에만: `_archive/`로 이동 **또는** 파일 상단 `RETIRED_DO_NOT_RUN` 헤더.
5. **generator별 proof → Gatekeeper 승인.**

**금지:** 커버리지 공백 방치 금지. 증명 전 은퇴 금지. 위험 실행(런타임 팩 덮어쓰기 가능 실행) 금지.

**Exit:** 은퇴 generator가 커버리지 공백 안 남김, retired report 작성.

---

## 전체 Exit (P4 마감 — `P4_FINAL_REPORT.md`)

1. 잔여 인벤토리 재조정(unclassified 0).
2. MANIFEST live=loader 100% 유지 · 고아 0.
3. 격리 legacy 런타임 미로드 · `data` 수기편집 금지 CI 가드 도입.
4. Gatekeeper 최종 검증 → DIAG-SOT DoD1~DoD6 대조.

## 롤백

팩·파일 단위 독립. archive는 `_archive/` 이동이라 복원 가능. 각 배치 커밋 분리.

## 보고 형식 (M5 → Gatekeeper)

배치별로: `대상 · 무참조/hash proof · 회귀/mutation 결과 · MANIFEST/LINEAGE diff · 미커밋 경로/해시`. git 막히면 경로·해시 통지(Gatekeeper 대행 커밋).
