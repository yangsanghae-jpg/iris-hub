# 작업지시서 — DIAG-SOT / P0 (M2 Cursor 전용)

- **발행:** 2026-07-05 · Gatekeeper(Claude) → Executor(M2 Cursor, gpt-5.5)
- **범위:** **P0 단계만.** P1 이후는 P0 게이트 PASS 후 **별도 지시서로 발행**한다. 앞서가지 말 것.
- **기준 문서(절대):** [`P0_SPEC.md`](./P0_SPEC.md) · [`00_MANIFEST.md`](./00_MANIFEST.md) · [`10_OVERVIEW.md`](./10_OVERVIEW.md)

---

## ⚠️ 0. 최상위 선언 — C-Server(배포서버)와 무관

- 본 작업은 **외부 배포 서버(C-Server)와 전혀 무관한 별도 개발 작업**이다.
- **C-Server / 프로덕션 / 배포 파이프라인 일절 접촉 금지.** 배포·재기동·환경변수·원격서버 명령 금지.
- 작업은 **로컬 개발 브랜치**에서만. main/prod 병합 금지(게이트 통과 후 Gatekeeper 승인 시에만).
- **P0은 데이터·엔진을 아무것도 바꾸지 않는다** (측정·기반 구축만).

---

## 1. 절대 규칙 (위반 시 즉시 중단·보고)

| # | 규칙 |
|---|------|
| R1 | **설계 문서가 유일 기준.** `P0_SPEC.md`에 없는 판단·확장·리팩터·구조변경 **금지**. |
| R2 | 스펙 §4 **금지사항** 준수 (팩 수정·이동·삭제 금지, 엔진 접촉 금지, `data/src` 재구성 금지, 골든 sub 임의확정 금지). |
| R3 | 판단이 필요한 빈칸이 생기면 **스스로 채우지 말고 중단 → 보고서에 질문으로 기재**. Gatekeeper가 답한다. |
| R4 | **C-Server/prod 무접촉** (§0). |
| R5 | 결과는 **git 반영 + 결과 보고서**로만 인계 (구두/추정 금지). |

---

## 2. 브랜치 (고정 — 변경 금지)

- **iris-hub `feat/diag-sot`** = Gatekeeper가 이미 생성·푸시함(설계 문서 포함). **pull 해서 기준으로 사용.** 재생성/이름변경 금지.
- **diagnosis-tool `feat/diag-sot-sync`** = `v1.5`에서 **네가 생성.** 모든 P0 산출물은 이 브랜치에.

---

## 3. 작업 항목 (P0_SPEC §3 그대로 — 각 항목 PASS/FAIL 표기)

> 완료 시 아래 표를 **결과 보고서에 그대로 복사**하고 상태·증거경로를 채운다.

| ID | 작업 | 산출물(경로) | 상태 | 증거 |
|----|------|--------------|------|------|
| T0-1 | diagnosis-tool `feat/diag-sot-sync` 생성 (iris-hub 브랜치는 pull만) | 브랜치 | ⬜ PASS / ⬜ FAIL | 브랜치명·기점 |
| T0-2 | 현 팩 checksum 베이스라인 | `scripts/data_poc/_baseline/checksums_v1.5.txt` | ⬜ / ⬜ | 파일수·해시 |
| T0-3 | 게이트 머신 건강검진 `bash scripts/run_data_poc.sh` | `scripts/data_poc/_baseline/poc_health_<date>.log` | ⬜ / ⬜ | diff 0 여부 |
| T0-4 | 골든 픽스처 구축 (sub 목록은 **Gatekeeper 승인 후 고정**) | `scripts/data_poc/_golden/**` + `_payloads.json` | ⬜ / ⬜ | sub 수·재현성 |
| T0-5 | `data/src` 자산 인벤토리 (이동 금지) | `scripts/data_poc/_baseline/data_src_inventory.md` | ⬜ / ⬜ | 목록 |
| T0-6 | `DECISIONS.md` 초안 (전 팩 분류, 빈칸 금지) | `docs/design/diag-sot/DECISIONS.md`(iris-hub) 또는 인계 | ⬜ / ⬜ | 팩 수 |
| T0-7 | 증거 묶음 + 결과 보고서 | §5 | ⬜ / ⬜ | 링크 |

> T0-4 주의: 골든 대표 sub 목록은 **초안 제안만** 하고 **Gatekeeper 승인 전 고정하지 말 것**(R3). 제안 목록을 보고서에 적어 승인 요청.

---

## 4. git 반영 규칙 (Gatekeeper 확인 가능하게)

- 모든 산출물을 **diagnosis-tool `feat/diag-sot-sync`** 에 커밋 후 **origin에 push**.
- 커밋 메시지: 접두 `[DIAG-SOT][P0]` + 항목 태그. 예:
  `[DIAG-SOT][P0] T0-3 gate health check — poc diff 0 (PASS)`
- `DECISIONS.md`는 iris-hub `feat/diag-sot`에 커밋(설계 폴더 내) 하거나, 접근 불가 시 diagnosis-tool 브랜치에 두고 보고서에 경로 명시.
- **push 완료 후** 보고서에 커밋 해시·브랜치·원격 경로 기재 → Gatekeeper가 pull 하여 점검.

---

## 5. 결과 보고서 (필수 — 없으면 미완료 처리)

- **위치:** `docs/design/diag-sot/reports/P0_RESULT_REPORT.md` (iris-hub `feat/diag-sot`) — 접근 불가 시 diagnosis-tool 브랜치에 쓰고 경로 통지.
- **필수 항목:**
  1. **작업 요약** + §3 상태표(각 T0-x PASS/FAIL + 증거경로)
  2. **게이트 결과:** `run_data_poc.sh` diff 0 재현 여부 (P0 Exit 게이트 §7 대조)
  3. **git 반영:** 브랜치·커밋 해시·push 여부
  4. **Gatekeeper 승인 요청 항목:** 골든 sub 제안 목록, DECISIONS의 "DB정본/은퇴" 제안(=Gatekeeper가 확정할 부분)
  5. **막힌 점·질문** (R3로 중단한 빈칸)
  6. **다음 단계 제안** (P1 착수 가능 여부에 대한 Executor 소견 — 결정은 Gatekeeper)
- 보고서 끝에 **`P0 SELF-STATUS: PASS / FAIL / BLOCKED`** 한 줄 명시.

---

## 6. 완료 후 흐름

```
Executor: T0-1~T0-7 실행 → git push → P0_RESULT_REPORT.md 작성 → "완료" 통지
Gatekeeper(Claude): 브랜치 pull → P0_SPEC §6 점검항목 대조 → PASS면 P1 지시서 발행 / FAIL이면 반려사유
```

**PASS 판정은 Gatekeeper만 한다. Executor는 SELF-STATUS까지.** P1은 지시서 받기 전 착수 금지.
