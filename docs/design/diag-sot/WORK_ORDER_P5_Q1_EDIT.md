# WORK ORDER — P5 Q1 편집 (server 수렴 + 라벨 에디터)

- **발행:** 2026-07-06 · Gatekeeper(Claude) → **실행: M5 Cursor**
- **선행:** P5 Q2·Q3·Q4·Q5 PASS. repo: iris-hub `feat/diag-sot`, diagnosis-tool `feat/diag-sot-sync`.
- **상위 규정:** `P5_TAB_REDESIGN_GUIDE.md` §1~5.

---

## 0. Gatekeeper 분석 (실측 — Cursor 재조사 불필요)

Q1(`q1_industry_product_taxonomy`) 진단 결론:

- **server byte-0 MISMATCH의 정체 = stale mirror.** dx == client(canonical). server와 client 차이는 **딱 10개 pointer, 전부 `/metadata/step_ui/` UI 라벨**(예: "Step 1 —" ↔ "Q1 —", "다음 단계" ↔ "다음"). **택소노미 `industries`(9산업 트리)는 완전 동일.**
- 원인: client가 "Step→Q" 리네이밍 반영(2026-06-29), server 사본은 그 전(2026-06-24)에서 멈춤.
- **server 사본은 런타임 무참조**(client `q1_taxonomy_v3.js`만 로드; server는 파일명 grep 0건). `payload_normalize.py:29 ("step1_5","q1_detail")`는 스테이지명 매핑 추정 → **STEP 0에서 파일 로드 아님 확정 필요.**
- P1a가 이미 기록: `intentional_diff: true, "server mirror converges to client canonical per P1 approval"`. 즉 **알려진·승인된 미수렴.**
- 구조: `metadata`+`industries` 중첩 트리 → per-sub 그리드 부적합. **편집 표면 = `metadata` UI 라벨 leaf(문자열)**, 택소노미 트리는 구조라 잠금.

미러 모델: Q1은 단일 dx(`dx_q_framework` q1 rows) → `rebuild_q1_from_dx` → server·client 동일 payload 2파일(Q5와 유사).

---

## ⚠ 실행 규약
단계 내 사람 승인 대기 없음 · self-test 직접 실행 · GREEN이면 진행. **STEP A 제출 후 Gatekeeper 체크포인트 1회**(수렴 검증 + 편집 whitelist 승인) → PASS 후 STEP B. FAIL이면 멈추고 실제 출력 보고. 택소노미 `industries` 트리 편집 금지 · runtime 직접 수기편집 금지.

---

## STEP 0 — server 무참조 확정 (pre-check)
```bash
# payload_normalize.py의 step1_5 참조가 파일 로드인지 스테이지 매핑인지
sed -n '20,40p' diagnosis-tool/server/payload_normalize.py
grep -rn "industry_product_taxonomy\|step1_5" diagnosis-tool/server --include=*.py | grep -viE "test|_backup"
```
- [ ] ST0: server가 `industry_product_taxonomy_v3.json`을 **파일 로드하지 않음** 확정(스테이지명 매핑뿐). 만약 로드하면 STOP+보고(수렴 영향 재평가).

## STEP A — 1회 server 수렴 (stale 해소)
**목적:** dx→server 재생성으로 server를 client/dx canonical로 수렴(P1a 의도). 읽는 코드 없어 안전.
1. `rebuild_q1_from_dx` 재현/재사용으로 payload 생성 → **server·client 두 runtime 재생성**.
2. 변경은 **server 파일 1개**(client·dx는 이미 일치). 의도된 수렴이므로 커밋 메시지에 명시.

### self-test STA (GREEN 필수)
- [ ] STA-a: 수렴 후 `rebuild_q1 == server == client` byte-0 (세 개 일치).
- [ ] STA-b: 변경 파일 = server runtime 1개뿐(diff는 10개 metadata 라벨이 client값으로 수렴).
- [ ] STA-c: `industries` 트리 무변경(diff에 등장 안 함).

### STEP A 제출 (→ 체크포인트)
```
[STEP A Q1 server 수렴 완료]
- STA-a/b/c 결과 · server diff 요약(10 라벨) · 커밋 해시
- [편집 whitelist 후보] metadata 내 편집 가능 leaf pointer 목록(제안) — 예: step_ui.*.title.{ko,en,ja,zh}, next_button, required_hint 등
```
→ **대기.** Gatekeeper가 수렴 byte-0 재검증 + **편집 pointer whitelist 승인** 후 STEP B.

## STEP B — Q1 라벨 에디터 (whitelist 승인 후)
**모델:** per-sub 그리드 아님. **pointer 기반 라벨 에디터** — 승인된 whitelist leaf만 행으로.
1. dx 소스 = `dx_q_framework` q1 rows(metadata/industries 블록). 편집은 **metadata 블록 value_json에 nested pointer로 set**.
2. 그리드 행 = 승인 whitelist pointer. 컬럼 = `항목(한글 의미)` | `값(text)` | `어디에 반영`. metadata 섹션별 그룹핑.
3. **`industries` 트리 = 잠금/미노출.** whitelist 밖 pointer 자동 잠금(fail-safe).
4. 저장 = metadata row 갱신 → `rebuild_q1` → server·client 두 runtime 재생성. `pack_mirror_sync_status` 두 경로 byte-0 후 "일치".
5. `pack_scope.json`: q1을 `pilot_packs`에 추가(편집 개방). 서버측 재검증(`validate_q1_edits`): 값은 문자열, whitelist pointer만 허용.

### self-test STB (GREEN 필수)
- [ ] STB-a: 무편집 rebuild_q1 == server·client byte-0(STEP A로 이미 수렴).
- [ ] STB-b: 라벨 1건 편집(예: step_ui.step1.title.ko)→저장→server·client 둘 다 갱신·배너 "일치".
- [ ] STB-c: `industries` 및 whitelist 밖 pointer 편집 위젯 미제공.
- [ ] STB-d: whitelist 밖 값 저장 시도 서버측 거부.
- [ ] STB-e: 쓰기 대상 = dx_q_framework + q1 server/client runtime만 추가.
- [ ] STB-f: Q2~Q5 회귀 synced 유지.

### STEP B 제출
```
[STEP B Q1 라벨 에디터 완료]
- STB-a..f 결과 · Q1 편집 1건 시연(server·client diff) · 라벨 에디터 스크린샷
- 변경 파일 + 커밋 해시 + :8765 code
```
→ Gatekeeper 최종 검증.

---

## 범위 밖
- **택소노미 트리(`industries`) 편집** = 이 WO 아님(구조·고위험). 필요 시 별도 tree 에디터 설계.
- 산업/세부산업 표시명 편집 = v2 후보(이견 시 whitelist 확대 별도 승인).
- **[MINOR]** `apply_q5_grid_edits` 중복 정의(dx_index.py 611·638) 정리 — 이 WO 커밋에 곁들여 제거 권고.
- **[MINOR 추적]** rebuild_q1도 iris-hub 재구현 → 원 파이프라인 공유가 장기 이상.

## 커밋·sync (Cursor)
iris-hub `feat/diag-sot` + diagnosis-tool `feat/diag-sot-sync`(STEP A는 server runtime 변경 있음) 커밋·푸시 + `sync-iris-hub.sh`(:8765 200). 메시지 끝 `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
