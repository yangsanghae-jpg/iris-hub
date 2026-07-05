# P0 — 기반·게이트 건강검진·결정표 (세부 스펙)

- **상태:** 확정 (실행 가능)
- **선행 게이트:** 없음 (착수 단계)
- **출력 변화:** 없음 (측정·기반만)
- **엔진:** 무접촉

> Executor(Cursor)는 아래 절차를 **문자대로** 수행한다. 번호 외 작업·구조변경·리팩터 금지(I6).

---

## 1. 목적

이후 모든 단계의 **검증 기반**을 만든다: (a) 격리된 브랜치, (b) 회귀 판정용 골든 픽스처, (c) diff 게이트 머신이 현 상태에서 green임을 재확인, (d) "생성물 vs DB정본" 결정표. **여기서 아무 데이터도 바꾸지 않는다.**

## 2. 입력

- diagnosis-tool `v1.5` 현재 상태 (전 팩)
- `scripts/data_poc/` 게이트 머신, `scripts/run_data_poc.sh`
- 선재 `data/src/`

## 3. 실행 절차 (Executor)

**T0-1. 접근·브랜치 (이름·기점 고정, 변경 금지)**
- M2는 로컬 접근 불가 → **diagnosis-tool을 git clone** 후 작업.
- **diagnosis-tool `feat/diag-sot-sync`** = Gatekeeper가 **선생성·푸시**(설계 스펙 미러 `docs/diag-sot/` 포함). Executor는 clone 후 **이 브랜치로 pull**. 재생성/이름변경 금지.
- iris-hub는 설계 정본 보관소(Gatekeeper 관리) — Executor 접근 불필요.

**T0-2. 현 팩 checksum 베이스라인**
- 대상: `server/data/**/*.json` + `client/data/**/*.json` 전부.
- 산출: `scripts/data_poc/_baseline/checksums_v1.5.txt` (path + sha256, 정렬).

**T0-3. 게이트 머신 건강검진**
```
bash scripts/run_data_poc.sh
```
- 기대: 현 상태에서 **migrate→build→diff canonical = 0**, Q5 validate PASS(=2026-06-29 재현).
- 결과 로그를 `scripts/data_poc/_baseline/poc_health_<date>.log`로 저장.
- **실패 시:** 여기서 중단하고 Gatekeeper에 로그 제출. (게이트가 안 돌면 이후 전 단계 불가)

**T0-4. 골든 픽스처 구축 (회귀 기준선)**
- 대표 세부산업 선정: **축별 커버 최소 9개** — 산업 A~I 각 1 sub + 언어 편차 큰 3 sub(B01 반도체, systems_catalog zh 원본 계열 등). 정확 목록은 T0-6 결정표에서 확정 후 Gatekeeper 승인.
- 각 sub에 대해 `/api/diagnose` 호출(대표 payload: 산업·sub·routing·scale·automation·keywords 고정) → 저장:
  - `scripts/data_poc/_golden/<sub>/decision.json`
  - `scripts/data_poc/_golden/<sub>/render_<ko|zh>.html` (A1 렌더 결과)
- payload·호출 스크립트도 `_golden/_payloads.json`으로 고정(재현 가능해야 함).

**T0-5. 선재 `data/src` 자산 상태 정리 (판정만, 이동 금지)**
- `data/src/` 하위 실재 팩·언어·커버리지 목록화 → `_baseline/data_src_inventory.md`.
- **이동·삭제·재구성 금지.** 목록화만.

**T0-6. 결정표 초안 작성** → `docs/diag-sot/DECISIONS.md` (diagnosis-tool 동일 브랜치): 아래 §5 양식대로 **전 팩 분류**. 빈칸 없이.

**T0-7. 증거 묶음 제출** — 브랜치명, checksums, poc health 로그, 골든 목록, data_src 인벤토리, DECISIONS 초안.

## 4. 금지사항 (Executor)

- ❌ 어떤 팩도 **수정·이동·삭제** 금지 (측정만).
- ❌ 엔진(`server/assemble`,`server/rules`) 접촉 금지.
- ❌ 브랜치 이름·기점 변경 금지.
- ❌ 골든 sub 목록을 임의 확정 금지 (Gatekeeper 승인 후 고정).
- ❌ `data/src` 재구성 금지.

## 5. `DECISIONS.md` 양식 (전 팩)

| 팩 path | 축(①②③) | 소비 로더/엔진 | 생성기(`_generate_*`) 유무 | **DB정본 승격?** | **생성기 은퇴?** | `data/src` 처리 | 비고 |
|---------|----------|----------------|---------------------------|------------------|------------------|-----------------|------|

- 모든 `server/data`·`client/data` 팩 1행씩. 빠짐 금지.
- "DB정본 승격/생성기 은퇴/`data/src` 처리"는 **초안 제안**만 — 확정은 Gatekeeper.

## 6. Gatekeeper 점검항목 (Claude)

- [ ] 브랜치가 main/prod와 격리됐고 이름·기점이 매니페스트와 일치
- [ ] `run_data_poc.sh`가 현 상태 diff 0 재현 (health 로그 확인)
- [ ] checksum 베이스라인이 전 팩(102개 상당) 포함
- [ ] 골든 픽스처가 3축·대표 sub·2언어(ko/zh) 커버, payload 재현 가능
- [ ] `DECISIONS.md`가 전 팩을 **빠짐없이** 분류, 생성물/수기 구분 정확
- [ ] `data/src` 인벤토리 정확, 무이동 확인

## 7. Exit 게이트 (PASS 조건)

**전부 충족 시 PASS → P1 스펙 확정·착수 승인:**
1. 브랜치 2개 격리 확인
2. 게이트 머신 green (현 상태 diff 0)
3. 골든 픽스처셋 존재·재현 가능
4. DECISIONS 전 팩 분류 완결 + Gatekeeper가 "DB정본/은퇴" 확정 기입

## 8. 롤백

- 브랜치 드롭. 데이터 무변경이라 부작용 없음.
