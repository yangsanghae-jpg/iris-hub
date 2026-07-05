# Gatekeeper 판정 — DIAG-SOT P3b 스키마 draft

- **판정일:** 2026-07-06 · Gatekeeper(Claude) · 대상 commit `a0aafc3`
- **판정: ✅ 승인 (정밀화 2건 반영 조건).** P3b 구현(P3b-1~5 순차) 착수 허가.

---

## 0. 총평

draft가 보수적·정합적. system→module→sub_override 3층, module×sub 입도, Card1-only 최소개편, DIAG_SOT_DEV flag(fail-closed), DB/tier/server flip 이연, 기존 zh freeze, SUB_* no-guess(P3a alias 재사용), P3a acid-test(빈 base + mutation) 계승 — 전부 옳음.

## 1. Gatekeeper 질문 8개 답변

| # | 질문 | 판정 |
|---|------|------|
| 1 | `module×sub` 주 + `system×sub` 보조 | ✅ 승인(요구3 "기능→세부산업" 정합) |
| 2 | Card1-only 1차 구현 | ✅ 승인 |
| 3 | `DIAG_SOT_DEV=1` prod 무노출 flag | ✅ 승인(fail-closed·flag-off 스냅샷 게이트) |
| 4 | dx 물리 경로 | ✅ **`scripts/data_poc/_p3b/`** (runtime 트리 밖 유지). `server/data/ch2/dev/` **불가**(prod 데이터 트리 오염 위험). dev 로더도 `_p3b/`에서 읽음 |
| 5 | 1차 byte-0 대상 | ✅ **`systems_catalog.json`만.** `10_card1_master_v3_74.json`·overlay·stack library는 **read-only 증거**(byte-0 대상 아님, 편집 안 하므로 불필요) |
| 6 | DB mode 미지원(1차) | ✅ 승인(이연) |
| 7 | server lang flip·`lang_ko.py` 무변경 | ✅ 승인 |
| 8 | stack library evidence-only | ✅ 승인 |

## 2. 정밀화 2건 (구현 반영)

### A. module_id는 추출 시 결정론적, 의미 slug는 큐레이션 단계
`capabilities[]`는 zh 문자열 → module_id를 **번역 텍스트에서 자동 유도 금지**(draft도 명시). 단 추가로:
- **추출(P3b-1) 시 module_id = 결정론적 provisional**(예 `{system_id}.cap_{legacy_capability_index}`) — 재현 가능해야 함.
- **의미 slug(`execution_work_order` 등)로의 rename = 별도 큐레이션(dev) 단계**, 근거 기반, `legacy_capability_index` 보존. **추출이 사람 판단에 의존하면 재현성·byte-0 검증이 흔들림** → 추출은 기계적, 명명은 분리.

### B. systems_catalog byte-0 = capabilities 배열 legacy 보존
system baseline은 `capabilities[]`를 **legacy 배열 그대로**(zh·순서) 보존해 systems_catalog byte-0 재현. **module 행은 그로부터 파생된 신규 dev 레이어**(additive), byte-0 대상 아님. 즉 "systems_catalog byte-0(legacy 무손실) + module/sub_override는 dev 신규" 를 명확히 분리.

## 3. 승인된 P3b 구현 순서 (draft §9)

| step | 게이트 |
|------|--------|
| P3b-1 추출(system + module seed, provisional id) | 카운트·source 포인터, source 무편집 |
| P3b-2 base(대상 subtree 비움) | base-empty 증명 |
| P3b-3 dx-only rebuild | **systems_catalog byte-0** |
| P3b-4 mutation test | load-bearing dx 변경→출력 반영, 재추출 없음 |
| P3b-5 dev-only Card1 consumer | **flag-off prod 스냅샷 무변경** + flag-on module/sub_override 적용 |
| P3b-6 | 광범위 Ch2/DB/tier는 별도 승인 |

## 4. 금지 (유지)

Ch2 전체 카드 교체·tier 외부화·server lang flip·SQLite 확장·`lang_ko.py` 제거/bypass·prod `systems_catalog.json` in-place 편집·SUB_*↔A01 임의매핑·기존 zh 삭제·prod 반영(flag-off).

## 5. Exit 게이트 (제출 시 Gatekeeper 재검증)

- P3b-3 systems_catalog **byte-0**(dx-only, 빈 base) + **P3b-4 mutation으로 dx 의존 증명**(내가 직접 재현).
- **flag-off = prod 출력 무변경**(스냅샷), flag-on = module/sub_override 적용.
- module_id 결정론적·큐레이션 분리, sub_override 근거 기반(SUB_* 0), 기존 zh 보존, 엔진 touch가 §5.3 경계 내.

> git: M2 정상화됨. 막히면 로컬 커밋+경로/해시 통지 → Gatekeeper 대행. PASS 판정은 Gatekeeper.
