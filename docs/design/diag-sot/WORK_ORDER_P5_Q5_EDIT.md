# WORK ORDER — P5 Q5 편집 확장 (STEP 3)

- **발행:** 2026-07-06 · Gatekeeper(Claude) → **실행: M5 Cursor**
- **선행:** P5 Q2·Q3·Q4 PASS(`P5_TAB_REDESIGN_GUIDE.md` §6-3). repo: iris-hub `feat/diag-sot`, diagnosis-tool `feat/diag-sot-sync`.
- **상위 규정:** `P5_TAB_REDESIGN_GUIDE.md` §1~5.

---

## 0. Gatekeeper 인벤토리 (실측 — Cursor 재조사 불필요)

| 항목 | Q5 (q5_recommendation_by_subindustry) | Q1 (q1_taxonomy) |
|---|---|---|
| dx 소스 | `_p1a/dx_q5_recommendation.json`(74 per-sub) + `_p1a/dx_q5_framework.json`(8 블록) | `_p1a/dx_q_framework.json` q1 rows(2 블록) |
| 구조 | **per-sub 74행** (Q2~Q4와 유사) | `metadata`+`industries` 중첩 트리 — **행 그리드 부적합** |
| rebuild | `rebuild_q5_from_dx`(framework events + recommendations 배열) | `rebuild_q1_from_dx` |
| dx pack_id 미러분리 | **없음** — 단일 `q5_recommendation` rows → server·client 동일 payload 2파일 | — |
| runtime | server+client `q5/recommendation_by_subindustry_v1.json` | server+client `step1_5/industry_product_taxonomy_v3.json` |
| **at-rest byte-0** | **server·client 둘 다 MATCH** ✅ | client MATCH / **server MISMATCH** ❌ |

**결론:** 이 WO 범위 = **Q5만.** Q1은 §5로 이연(이중 블로커).

---

## ⚠ 실행 규약 (STEP 1/2와 동일)
단계 안에서 사람 승인 대기 없음 · self-test 직접 실행 · GREEN이면 커밋·푸시·sync·제출 · FAIL이면 그 지점 멈추고 실제 출력 보고. runtime 직접 편집 금지(재생성 결과물만) · 잠금/whitelist 우회 금지 · Q1·q5_axes 손대지 마라.

---

## 1. 요구 동작 (Q5)

### 1-1. dx 소스 확장
현재 편집기는 `dx_q_matrix.json`만 로드. **Q5는 다른 dx 소스**(`dx_q5_recommendation.json` + `dx_q5_framework.json`)라 인덱스/편집/저장 경로가 이를 읽고 쓰도록 확장. (q_matrix 계열과 분기, 공통 인터페이스 유지.)

### 1-2. rebuild 재현 (iris-hub)
`rebuild_q5_from_dx` 알고리즘을 iris-hub에 재현(또는 공유):
- framework rows → `(source_index, key=source_json_pointer, value_json)` 이벤트
- recommendation rows(74) → `recommendation_index` 순 정렬 → `recommendations` 배열
- source_index 순 정렬로 payload 조립.
- **검증:** 무편집 rebuild == server·client 두 runtime byte-0(이미 MATCH). mismatch면 STOP.

### 1-3. 미러 모델 (Q5 특수)
Q5는 dx가 server/client로 안 갈림 — **단일 dx rows → 동일 payload를 server·client 두 runtime에 기록.** `q_pack_runtime_map.json`에 q5 엔트리 추가하되, 편집은 단일 dx rows에 적용하고 두 runtime 모두 재생성.

### 1-4. 편집 그리드 (per-sub 74행)
- 행 = sub_code(A01…). 셀 = **중첩 leaf 경로**를 dotted로 평탄화:
  - `q5_2.recommended_levels.{C,D,Q,I,R,P,E}` — **enum select L1~L5**
  - `q5_1.default_axis_weight.{...}` — **enum select primary/secondary/optional**
  - `q5_1.axis_roles.{C,D,...}` — **긴 텍스트**(text area)
- **v1 편집 범위 = 위 scalar/enum leaf만.** `q5_1.priority_axes`(list) 등 리스트/구조 필드는 **이번 제외**(리스트 에디터 별도) → whitelist에서 빼고 잠금 표시.
- 키/구조(`subindustry_code`, 축 문자 자체, `source_json_pointer`) = 잠금 고정.

### 1-5. 잠금·검증
- 팩타입 whitelist(`q5_field_locks`/editors 신설)에 위 leaf 경로만 등재. 없는 필드 자동 잠금(fail-safe).
- 저장 전 서버측 재검증(`validate_q_pack_edits`에 q5 분기): level ∈ {L1..L5}, weight ∈ {primary,secondary,optional}, sub_code ∈ 척추.

### 1-6. 반영 배너·모드
- 저장→dx rows 갱신→server·client 재생성→`pack_mirror_sync_status`가 두 경로 byte-0 확인 후 "일치".
- `pack_scope.json`: `q5_recommendation_by_subindustry`를 `pilot_packs`에 추가(편집 개방). `q5_axes`는 **추가 금지**(별건).

---

## 2. self-test ST3 (전부 GREEN)
- [ ] ST3-a: 무편집 rebuild_q5 == server·client 두 runtime byte-0 MATCH.
- [ ] ST3-b: enum/text leaf 1건씩 편집→저장→server·client 둘 다 갱신(둘 다 diff). 예: A01 `q5_2.recommended_levels.C` L4→L3.
- [ ] ST3-c: 잠금 필드(subindustry_code·priority_axes·source_json_pointer) 편집 위젯 미제공.
- [ ] ST3-d: 서버측 재검증 — 범위 밖 값(L9, "always") 저장 거부.
- [ ] ST3-e: 쓰기 대상 = dx + q5 server/client runtime만 추가(audit_allowed_write_targets 갱신, 그 외 0).
- [ ] ST3-f: q5 편집 개방 · Q1/q5_axes/A/척추 read-only 유지.
- [ ] ST3-g: Q2·Q3·Q4 기존 편집 회귀 없음(무편집 synced 유지).

## 3. 제출 형식
```
[STEP3 Q5 편집 완료]
- ST3-a..g 결과(핵심 출력)
- Q5 편집 1건 시연(server·client diff) + enum select·잠금 스크린샷
- 변경 파일 + 커밋 해시(iris-hub) + :8765 code
```
→ Gatekeeper 실측 검증(rebuild byte-0·양쪽 미러·enum 범위·회귀).

---

## 4. 커밋·sync (Cursor)
iris-hub `feat/diag-sot` 커밋·푸시 + `sync-iris-hub.sh`(:8765 200). diagnosis-tool는 dx/runtime 무변경 예상. 메시지 끝 `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.

---

## 5. 범위 밖 (이 WO 아님)
- **Q1 편집 = 이연(이중 블로커):**
  1. 구조가 `metadata`+`industries` 중첩 트리 → **행 그리드 부적합**(nested 에디터 or 심층 pointer whitelist 별도 설계 필요).
  2. **server runtime이 dx에서 byte-0 재현 안 됨**(MISMATCH) → 재생성 시 diff 발생. **먼저 server mismatch 원인 규명·해소**가 선행.
  → Q1은 별도 인벤토리·설계 WO. 이 WO에서 손대지 마라.
- **q5_axes**(management_axes/axis_domain_map) = residual(비 dx-covered) → dx화 선행 후 별건.
- **[MINOR 추적]** rebuild_q5도 iris-hub 재구현 → diagnosis-tool build와 공유가 장기 이상(sync byte-0이 방어).
