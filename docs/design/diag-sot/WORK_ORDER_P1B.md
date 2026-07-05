# 작업지시서 — DIAG-SOT / P1-b (+ P1-a 재제출 PASS 판정)

- **발행:** 2026-07-05 · Gatekeeper(Claude) → Executor(M2 Cursor)
- **선행:** **P1-a 재제출 = PASS** (아래 §A). P1-b 착수 허가.
- **접근:** diagnosis-tool `feat/diag-sot-sync` clone/pull → 작업 → push. C-Server/prod 무접촉.

---

## A. P1-a 재제출 판정: ✅ PASS (Gatekeeper 독립 acid-test)

commit `c2fd806`. SELF-STATUS PASS를 신뢰하지 않고 직접 검증:

- **Acid test(예고했던 방식):** legacy 원본 4팩을 **숨긴 상태**로 `--build-from-dx` 실행 → **dx 아티팩트(`_p1a/*.json`)만으로** `data/build/v2/**` 재조립됨. 백업 legacy와 **Gatekeeper가 직접 cmp → 4팩 전부 byte-0**. (끝의 FileNotFoundError는 legacy 없는 diff 단계일 뿐, 재조립은 그 전에 완료.)
- **R1~R5 이행 확인:**
  | 요구 | 결과 |
  |------|------|
  | R1 재구성(passthrough 제거) | ✅ `copy_legacy_shape` 제거, `rebuild_*_from_dx`가 `_p1a/*`만 읽음. acid-test 증명 |
  | R2 spine+FK | ✅ `dx_industry`=9, `dx_sub_industry`=74, `dx_q5_recommendation`=74, **dangling FK=0** |
  | R3 Q1 분해 | ✅ `dx_q_framework`에 Q1 top-level 2블록(`metadata`,`industries`) 전량, source order 보존 |
  | R4 note 정합 | ✅ 재구성 실구현으로 "dx artifacts only" 사실화 |
  | R5 SUB_* | ✅ `dx_lineage_issue` 1건(`alt_code_mapping_uncertain`), **alt_code 추정 안 함** |
- 드리프트 봉합(Q1 server→client) 무해(step UI 라벨), 골든 12/12 PASS.

**→ 방법의 핵심(진실원 dx → 재조립 → byte 동일)이 Q1·Q5에서 증명됨.** P1-b로 확장.

---

## B. P1-b 스코프 (확정)

| 축 | 팩 | client/server |
|----|-----|---------------|
| ① | `server/data/industry_master.json` (+ `dx_registry_framework` 채움) | server only |
| ① | `server/data/ch1/catalogs/industry_codes.json` | server only |
| ① | `server/data/ch1/catalogs/sub_industry_codes.json` (SUB_* 계) | server only |
| ② | `step2/routing_product_nature_v3.json` | both |
| ② | `step3/scale_profile_v3.json` | both |
| ② | `step4/automation_profile_v3.json` | both |

## C. 불변 규율 (P1-a에서 확립 — 그대로 적용)

1. **dx-only 재조립.** build는 `_p1a/*.json`(및 P1-b 추가 dx 테이블)만 읽어 재조립 → legacy와 byte-0. **passthrough·legacy 재읽기 금지(R1).** Gatekeeper는 P1-b도 **legacy 숨김 acid-test**로 재검증한다.
2. **Q4 도메인 flat 보존.** `planning_*` 등 flat 접두 정규화 **금지**. `value_json`에 원본 그대로.
3. **통합 금지.** `industry_scale_model_v1`(P1-b 대상 아님, live, `core/scale_engine.py` 소비)과 `scale_profile_v3`는 별개 — lineage 기록만. `ch1_industries`/`industry_packs`/`ch1_mgmt_model` 미접촉.
4. **FK 정합.** Q2/Q3/Q4 matrix 행은 `dx_sub_industry`(74) 참조 → **dangling 0** 유지.
5. **container 이름 통일 금지.** subindustry profile container 이름이 팩마다 달라도 JSON pointer로 보존.

## D. 세부 지시

1. **dx_registry_framework 채움(수정 A):** `industry_master`의 `schema_policy`·`meta`·`focus_definitions` 등 sub 무관 블록 → **별도 `dx_registry_framework`**(q='registry' 오버로드 금지).
2. **① registry 확장:** `industry_master.industries.{A..I}` → `dx_industry`(P1-a 9행과 정합/병합), `industry_codes` `IND_*` → `dx_industry.alt_code`.
3. **`sub_industry_codes`(SUB_*) 처리:** 여기서 `SUB_*`↔`A01` 매핑 근거를 재확인(`sub_industry_aliases`/`sub_industry_meta` 포함). 근거 있으면 `dx_sub_industry.alt_code` 연결 + lineage, **없으면 issue 유지(추정 금지).**
4. **② Q2/Q3/Q4:** framework → `dx_q_framework`, subindustry profiles → `dx_q_matrix`(sub별, field_path + source_json_pointer). Q4 flat 보존.
5. **build/diff:** 각 대상 팩 client+server → dx-only 재조립 → **raw byte-diff 0**. drift 있는 팩은 정본측 확정 후 수렴 1건만 의도 표기.
6. **골든 회귀:** 12 sub decision 무변화(P1-b 팩 변경이 decision에 영향 주면 의도 여부 Gatekeeper 확인).
7. **lineage 실검증:** industry_master(engine_bridge·step3_engine), scale_profile_v3(step3_v3_interpret), routing/automation 소비 경로 `dx_lineage` 기록.
8. **Z99 스모크(P1 마무리):** P1-b 후 가짜 sub 1행 → dx → 재조립 → **해당 팩만** 반영 확인 후 원복. `dx_smoke_change_log` 기록.

## E. 금지사항

- ❌ Q4 flat 정규화 / container 의미통일 / ch1 3변종·catalog 통합 / 엔진 수정 / v1.5 in-place 덮어쓰기 / passthrough build / SUB_* 임의매핑 / dx 스키마 임의확장.

## F. git·보고서

- `feat/diag-sot-sync`에 커밋+push. `[DIAG-SOT][P1-b] ...`.
- **게이트 로그 + raw byte-diff 리포트 커밋 필수.**
- 결과 보고서 `docs/diag-sot/reports/P1B_RESULT_REPORT.md`: 팩별 byte-diff표 + **dx-only 재조립 재현 명령** + spine/FK 정합 + lineage + Q4 flat 보존 증거 + Z99 스모크 결과 + `SELF-STATUS`.

## G. Exit 게이트 (Gatekeeper 판정)

1. P1-b 전 팩 **dx-only 재조립 byte-diff 0**(legacy 숨김 acid-test 통과)
2. Q4 도메인 flat 보존 확인
3. dangling FK 0, `dx_registry_framework` 채움
4. 골든 무변화 / Z99 국소반영 스모크 통과
5. SUB_* 근거 or issue(추정 없음)

→ PASS 시 **P1 전체 완료**, P2 지시서 발행. PASS 판정은 Gatekeeper.
