# Gatekeeper 판정 — DIAG-SOT P4 plan

- **판정일:** 2026-07-06 · Gatekeeper(Claude) · 대상 commit `4bc848c`
- **판정: ✅ plan 승인 (스코프 명확화).** P4-core 구현 착수 허가.

---

## 0. 총평

plan 견고·보수적. 핵심 원칙 승인:
- **격리는 "내용 낡음"이 아니라 `loader_reference_status`(참조 여부)로 판정** — archive 금지 기본, unreferenced 증명 후만.
- **MANIFEST/lineage 먼저, 이관/격리 나중.**
- archive = `_archive/diag-sot/YYYYMMDD/` **복원가능 + proof row**.
- 관리탭 데이터 계약(§8)이 **추적성 제1동인**("어디 편집→무엇 생성→어디 사용→무엇 위험")을 정확히 구현.

## 1. 5개 질문 답변 (M2 권고 전부 승인)

| # | 질문 | 판정 |
|---|------|------|
| 1 | manifest/lineage 먼저 (residual byte-0 전) | ✅ YES — **추적성이 제1 동인, migration은 부차** |
| 2 | archive는 inventory 승인 후 별도(P4b) | ✅ YES — **move는 loader 무참조 증명 + 배치별 Gatekeeper 승인 후** |
| 3 | Ch2 card masters byte-0 vs lineage-only | ✅ **lineage-only(residual-live)** — byte-0 이관은 P3b-6/후속 |
| 4 | ch1_mgmt_model 이관 vs 이연 | ✅ **inventory+lineage 지금, 이관은 loader proof 후 이연** |
| 5 | lineage 입도 MVP | ✅ **field-group 전 팩 + row-level은 P1/P2/P3 core** |

## 2. P4 스코프 명확화 (핵심)

**P4-core(우선, 추적성 결실) = inventory → loader refs → MANIFEST → LINEAGE.** 이것이 관리탭 데이터 기반이자 제1 동인 완성. 여기까지가 P4의 실질 목표.

**P4-cleanup(부차, 각 배치 proof+승인 게이트, 이연 가능):**
- residual byte-0 이관(승인된 residual-live만) — P4-core 후.
- **archive move** — `loader_reference_status=unreferenced` 증명 + 배치별 Gatekeeper 승인 후에만.
- **generator 은퇴** — output coverage(hash 비교) + loader no-import 증명 후, `RETIRED_DO_NOT_RUN` 헤더 or archive.

→ **cleanup(격리·삭제·은퇴)은 하나도 wholesale 금지.** 각 파일/배치가 증명+승인.

## 3. 구현 순서 (승인, P4-core 집중)

| step | 산출 | 게이트 | 우선 |
|------|------|--------|------|
| P4-1 Inventory | `P4_INVENTORY.json` | 전 server/client/knowledge JSON 분류 | ★ core |
| P4-2 Loader refs | `P4_LOADER_REFERENCE_REPORT.md` | 각 archive 후보 loader 참조 0 증명 | ★ core |
| P4-3 MANIFEST | `DIAG_SOT_MANIFEST.json` | **live loader 경로 100% 커버**, status 부여 | ★ core |
| P4-4 LINEAGE | `DIAG_SOT_LINEAGE.json` | field-group 전팩 + row-level core, 관리탭 계약 충족 | ★ core |
| P4-5 Residual byte-0 | 승인 residual dx | byte-0+mutation | 부차 |
| P4-6 Archive | `_archive` move | 무참조 증명+승인+복원가능 | 부차(별도 승인) |
| P4-7 Generator 은퇴 | retired report | coverage+no-import 증명 | 부차(별도 승인) |
| P4-8 Final gate | `P4_FINAL_REPORT.md` | manifest live=loader 100%, lineage 충분 | core 마감 |

## 4. Exit 게이트 (P4-core 제출 시 Gatekeeper 재검증)

1. **MANIFEST live=로더 100%** — 고아팩(로더 없는 live) 0, 각 pack의 runtime_loader_paths가 실제 코드와 일치(내가 표본 grep 검증).
2. **LINEAGE:** field-group 전 팩, row-level P1~P3 core. 관리탭 §8 계약(edit→generate→use→risk) 충족.
3. issue(SUB_*·slug·alias)가 lineage issue-level에 집약.
4. **무변경:** P4-core는 **데이터/로더 무편집**(분류·매핑 산출만). prod 무접촉.

## 5. 금지

P4-core 단계에서 **파일 이동·삭제·loader 편집·generator 실행(위험) 금지.** archive/generator/residual은 P4-cleanup에서 배치별 승인 후.

## 6. 후속 (P4 밖 = 원 목표)

P4-core의 MANIFEST+LINEAGE 완성 → **iris-hub 관리 탭 UI**(dx 그리드 + lineage 패널 + 편집→sync)가 이를 소비 = DIAG-SOT의 최종 산출물(진실원 가시화).

> git: 막히면 경로·해시 통지 → Gatekeeper 대행. PASS 판정은 Gatekeeper.
