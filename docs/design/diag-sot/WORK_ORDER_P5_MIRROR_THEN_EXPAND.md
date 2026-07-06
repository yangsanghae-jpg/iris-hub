# WORK ORDER — P5 미러 수정 → Q2·Q4 확산 (단계 실행 지시서)

- **발행:** 2026-07-06 · Gatekeeper(Claude) → **실행: M5 Cursor**
- **선행:** 파일럿 q3 PASS(`P5_TAB_REDESIGN_GUIDE.md` §6-1). 대상 repo: iris-hub `feat/diag-sot`, diagnosis-tool `feat/diag-sot-sync`.
- **상위 규정:** `P5_TAB_REDESIGN_GUIDE.md` §1~5. 충돌 시 가이드 우선.

---

## ⚠ 실행 규약

**단계 안에서는 사람 승인을 기다리지 마라.** 각 단계 = 구현 → **self-test 직접 실행** → GREEN이면 커밋·푸시·sync → 제출. **STEP 1과 STEP 2 사이에만 Gatekeeper 체크포인트**(byte-0 재검증)가 있다 — STEP 1 제출 후 대기, PASS 통지 받으면 STEP 2 착수. self-test FAIL이면 그 지점에서 멈추고 실제 출력과 함께 보고.

금지: self-test 생략 · FAIL 은폐 · runtime 직접 편집(재생성 결과물만) · 잠금/whitelist 우회 · Q1·Q5 손대기(별건).

---

## STEP 1 — server/client 미러 동시 반영 (BLOCKER, q3에서 수정)

### 문제 (재확인)
`save`가 `runtime = member_paths[0]`(server)만 재생성 → `client/data/step3/scale_profile_v3.json`(질문지 UI `q3_taxonomy_v3.js`가 읽음) stale. parity 붕괴 + 반영 배너가 server만 보고 "일치" 오표기.

### 요구 동작
편집 저장 시 **논리 팩의 server·client 미러를 함께** 처리:
1. `apply_q3_grid_edits`가 dx의 `_server`·`_client` **양쪽 pack_id 행**에 동일 편집 적용(같은 sub_code·field → 같은 값).
2. rebuild + 쓰기를 **server·client 두 runtime** 모두: `server/data/step3/scale_profile_v3.json` + `client/data/step3/scale_profile_v3.json`.
3. `runtime_sync_status`/반영 배너: **두 경로 모두 byte-0 일치**일 때만 "일치". 하나라도 다르면 "미반영".

### 구현 방향 (기전은 Cursor 재량, §4)
- 팩→미러 매핑을 **config로**(하드코딩 금지): 예 `iris-hub` data에 `q_pack_runtime_map.json` = `{q3_scale_profile: {dx_pids:[..._server,..._client], runtime_rels:[server 경로, client 경로]}}`. 또는 MANIFEST `member_paths`에 client 경로 추가.
- `save_q3_and_rebuild` 시그니처를 미러 리스트 받도록 일반화(단일 runtime_rel → 매핑).
- 터치포인트: `src/store/dx_editor.py`(save/rebuild), `src/store/dx_index.py`(`apply_q3_grid_edits`·`runtime_sync_status`), `src/tabs/diagnosis_sot.py:578`(runtime 선택).

### self-test ST1 (전부 GREEN 필수)
```bash
cd <repo>/diagnosis-tool
python3 - <<'PY'
import json,subprocess
from pathlib import Path
# 무편집 상태: q3 server·client 두 runtime 모두 rebuild==파일 (byte-0)
# (Cursor는 iris-hub의 rebuild+미러매핑을 호출해 검증하는 등가 스크립트로 대체 가능)
for rel in ["server/data/step3/scale_profile_v3.json","client/data/step3/scale_profile_v3.json"]:
    assert Path(rel).is_file(), rel
    print("exists", rel)
print("ST1-a: 두 미러 파일 존재")
PY
```
- [ ] ST1-a: server·client 두 runtime 존재.
- [ ] ST1-b: **무편집 저장(또는 sync 체크) 시 두 경로 모두 byte-0 일치** → 배너 "일치".
- [ ] ST1-c: **값 1개 편집→저장** 후 server·client **둘 다** 그 값으로 갱신(둘 다 diff에 등장).
- [ ] ST1-d: 편집 후 반영 전 배너 "미반영", 반영 후 "일치".
- [ ] ST1-e: 잠금 필드 편집 위젯 미제공 유지 · 저장 전 서버측 재검증 통과.
- [ ] ST1-f: 쓰기 경로 = dx JSON + 두 runtime뿐(그 외 직접 쓰기 0 — grep).

### STEP 1 제출 (→ Gatekeeper 체크포인트)
커밋·푸시·sync 후 제출:
```
[STEP1 미러 수정 완료]
- ST1-a..f 결과(각 1~2줄)
- 변경 파일 + 커밋 해시(iris-hub, diagnosis-tool)
- q3 편집 1건 시연: 편집 전/후 server·client diff 요약
- :8765 code
```
→ **여기서 대기.** Gatekeeper가 두 미러 byte-0 + 배너 로직 재검증 → PASS 통지 후 STEP 2.

---

## STEP 2 — Q2·Q4 확산 (STEP 1 PASS 후)

### 범위
`q2_routing_product_nature`, `q4_automation_profile`. **동일 dx_q_matrix 구조 + byte-0 이미 MATCH** 확인됨. Q1·Q5 제외(별건).

### 요구 동작
1. 두 팩을 편집 개방(선택기에서 `파일럿 대기` → 편집 가능). STEP 1의 미러 매핑에 Q2·Q4 항목 추가(server·client 경로·dx pids).
2. **팩별 게이트:** 편집 열기 전 "무편집 synced"(server·client 둘 다 rebuild==runtime) 확인. mismatch면 그 팩은 열지 말고 보고.
3. 편집·저장·반영은 STEP 1과 동일 경로 재사용(팩별 특수 코드 최소화).

### self-test ST2 (전부 GREEN)
- [ ] ST2-a: Q2·Q4 각각 무편집 synced(server·client byte-0) — 하나라도 mismatch면 STOP+보고.
- [ ] ST2-b: Q2·Q4 각각 값 1건 편집→저장→server·client 둘 다 갱신·배너 "일치".
- [ ] ST2-c: 잠금·whitelist·서버측 재검증 Q3와 동일 적용.
- [ ] ST2-d: 선택기에 Q2·Q4 편집 가능 표시, A1/A2·척추·Q1·Q5는 read-only 유지.
- [ ] ST2-e: 쓰기 dx+runtime뿐, 파생인덱스/척추 직접 쓰기 0.

### STEP 2 제출
```
[STEP2 Q2·Q4 확산 완료]
- ST2-a..e 결과
- Q2·Q4 각 편집 1건 시연(server·client diff)
- 변경 파일 + 커밋 해시 + :8765 code + 스크린샷(Q2 또는 Q4 편집 화면)
```
→ Gatekeeper 확산 검증 → PASS 시 P5 편집 = Q2/Q3/Q4 완료.

---

## 범위 밖 (이 지시서 아님)
- **Q1·Q5:** dx_q_matrix 아님, 구조별 rebuild + byte-0 증명 별도 지시서 후.
- **A1/A2·척추:** read-only 유지.
- **[MINOR 추적]** rebuild 알고리즘 iris-hub 재구현 → 장기적으로 원 파이프라인 공유(비차단).

## 커밋·sync (각 STEP Cursor 수행)
- iris-hub `feat/diag-sot` + diagnosis-tool `feat/diag-sot-sync` 각 커밋·푸시.
- 앱 코드 변경 → `sync-iris-hub.sh` 실행(:8765 200 확인).
- 커밋 메시지 끝: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
