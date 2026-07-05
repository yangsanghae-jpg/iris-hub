# DIAG-SOT 진행 대시보드

- **갱신:** 2026-07-06 · Gatekeeper(Claude)
- **역할:** 실행 = M2 Cursor / 점검·게이트 = Claude. **PASS 판정은 Gatekeeper만.**
- **브랜치:** iris-hub `feat/diag-sot` · diagnosis-tool `feat/diag-sot-sync` · prod(C-Server) 무접촉.
- **방법:** 진실원(iris-hub dx_*) → 재조립 → **byte-0 acid-test**(legacy 숨김 dx-only 재현) / P3b-5부터 **실제 렌더 검증**. 단계마다 Gatekeeper 독립 검증.

## 단계 현황

| 단계 | 내용 | 판정 | 비고 |
|------|------|------|------|
| **P0** | 기반·게이트검진·결정표 | ✅ PASS | 113팩 인벤토리, 골든 12 sub, 게이트머신 green |
| **P1-a** | Q1·Q5 dx화 | ⚠️→✅ PASS | **1차 반려**(passthrough 공허 byte0) → **재제출 PASS**(dx-only 재조립 acid-test) |
| **P1-b** | registry+Q2/3/4 dx화 | ✅ PASS | legacy 9팩 숨김 acid-test 9/9 byte-0, Q4 flat 보존, dangling 0 |
| **P2** | 고정라벨 언어팩 + resolver ko기본 | ✅ PASS/완료 | Discovery 5결정 → catalog(dedup+blank 정규화 16/16) → flip(ko 기본, domain_card_suffix 복원, golden 12/12) |
| **P3a** | Ch3+Ch6 sub_override | ✅ PASS/완료 | dx-only byte-0(base 비움+mutation 증명), SUB_* no-guess, shared_slug 1회, 빈{} 보존, alias map(P1 issue 관리) |
| **P3b** | Ch2 system→module dx + flag-gated 소비 | ✅ PASS/완료 | systems_catalog byte-0·module_id 결정론·SUB_* 0 + compose flag-off no-op(12/12) |
| **P3b-5** | sub_override 실제 표면화(요구3 가시효과) | ⚠️→✅ PASS | **1차 FAIL**(domain_cards엔 있으나 렌더되는 blocks엔 없음) → **재수정 PASS**: blocks.exec.cap에 부착→**실제 렌더 HTML에 세부산업 특화 keywords/points 표시** + flag-off 12/12 무변경. **요구3 실현** |
| **P4** | 잔여 이관·legacy 격리·MANIFEST·lineage | ▶ **P4-core 진행** | plan 승인. P4-core(inventory→loader→MANIFEST→LINEAGE)=추적성 제1동인. cleanup(archive/generator/residual)=배치별 승인 이연 |
| 후속 | **iris-hub 관리 탭 UI** | ⏳ 대기 | P4-core의 MANIFEST+LINEAGE 소비. 진실원 그리드+lineage 뷰+편집→sync = **원 목표 산출물** |

**요구 5개 착지 현황:** ①척추(registry) ✅ · ②Q1~Q5 수치팩 ✅ · ③A1/A2 system→module→sub_override ✅(P3) · ④ko 기본+fallback ✅(P2) · ⑤진실원↔sync ✅(dx SoT+byte-0 파이프라인). 남은 것 = 추적성 가시화(P4)+관리탭 UI.

## 확립된 불변 규율

- **dx-only 재조립 byte-0**(passthrough 금지) — Gatekeeper가 legacy 숨김 acid-test로 재검증.
- **P2부터 byte-0 아님** — "의도된 diff만", 그 외 무단변경 0.
- **prod 무노출** — `DIAG_SOT_DEV=1` flag-on만 신규, flag-off=baseline 동일(delta test).
- **통합 금지**: ch1 3변종·scale_model↔scale_profile·catalog/catalogs (P4 archive는 loader 무참조 증명 후만).
- **Q4 도메인 flat 보존** / **추정 금지**(SUB_*↔A01 등 근거없으면 issue).
- **검증 교훈:** piece-wise 통과 ≠ end-to-end → "client가 실제 읽는 표현"에서 검증(P3b-5).

## 최신 상태

| repo | 브랜치 | HEAD |
|------|--------|------|
| diagnosis-tool | `feat/diag-sot-sync` | `a2492fc` (P4 plan 승인 수령) |
| iris-hub | `feat/diag-sot` | P4 plan 승인 커밋 |

## 다음 액션

- **M2:** P4-core 착수 — P4-1 inventory → P4-2 loader refs → P4-3 `DIAG_SOT_MANIFEST.json`(live=로더) → P4-4 `DIAG_SOT_LINEAGE.json`(field-group 전팩 + P1~P3 core row-level). **archive/삭제/loader편집/generator실행 금지.**
- **Gatekeeper:** P4-core 제출 시 MANIFEST live=로더 표본 grep 검증 + LINEAGE 완비 확인 → DIAG-SOT 데이터 기반 완성 → 관리탭 UI 단계.

## ⚠️ workflow 메모

M2 환경 git이 간헐적으로 막힘(DNS). 미커밋 산출물은 **Gatekeeper가 1Dev clone(`~/Documents/1Dev/diagnosis-tool`)에서 대행 커밋·push**. 검증은 **read-only git + 미커밋물 선(先)커밋 보존** 원칙(P3b에서 checkout 유실 사고 재발방지).

## 문서 지도 (diag-sot/)

- **설계:** `00_MANIFEST` · `10_OVERVIEW` · `P0~P4_SPEC` · `../DIAGNOSIS_TOOL_SOT_TARGET_DESIGN`(배경)
- **작업지시:** `WORK_ORDER_{P0,P1,P1B,P2,P3,P3A,P3B,P3B5,P4}`
- **판정/승인:** `P1A_GATE_VERDICT`(반려) · `P2_DISCOVERY_APPROVAL` · `P2_CATALOG_ROUNDTRIP_DECISION` · `P2_CATALOG_GATE_VERDICT` · `P2_GATE_VERDICT` · `P3A_SCHEMA_APPROVAL` · `P3A_GATE_VERDICT`... · `P3B_SCHEMA_APPROVAL` · `P3B_GATE_VERDICT(_2)` · `P3B5_DIAGNOSIS_APPROVAL` · `P3B5_GATE_VERDICT(_2)` · `P4_PLAN_APPROVAL`
- **M2 산출(diagnosis-tool `docs/diag-sot/reports/`):** `P0~P4` result/draft·diagnosis 보고서
