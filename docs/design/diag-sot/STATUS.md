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
| **P4-core** | 잔여 인벤토리·loader refs·MANIFEST·lineage | ✅ PASS | inventory→loader→MANIFEST→LINEAGE 4산출(diagnosis-tool `6230298`). live=loader 112/112, 고아-live 0. **재현 diff 0**. cleanup(archive/generator/residual)=배치별 승인 이연 |
| **P5** | **iris-hub 진실원 관리 탭 UI** | ✅ PASS/완료 | MANIFEST+LINEAGE 소비 그리드(39팩)+lineage 4블록(edit→generate→use→risk). read-only, 진단툴 하위 뷰. 라이브 :8765. **제1동인 가시화 = 원 목표 산출물 도달** |

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
| diagnosis-tool | `feat/diag-sot-sync` | `6230298` (P4-core 산출: inventory·loader-ref·manifest·lineage) |
| iris-hub | `feat/diag-sot` | P5 관리탭 구현 + 판정 |

## P4-core 산출 결과 (2026-07-06, diagnosis-tool `6230298`)

산출물(4) — 데이터/로더 무편집, generator 실행 0:
- `docs/diag-sot/reports/P4_INVENTORY.json` — runtime candidate 112(server/data 97 + knowledge 15) 분류
- `docs/diag-sot/reports/P4_LOADER_REFERENCE_REPORT.md` — loader 참조 결과
- `scripts/data_poc/DIAG_SOT_MANIFEST.json` — 39 pack, live=loader **112/112 커버·고아-live 0**
- `scripts/data_poc/DIAG_SOT_LINEAGE.json` — core row-level(P1 610·P2 828·P3a 190/P3b system 49·module 203·sub_override 254) + pack-level 39 + issue rollup 16
- (+ `p4_loader_scan.py`·`p4_build_manifest_lineage.py` read-only 재현 스캐너)

loader 분류: `live_loader_referenced` 71 · `live_indirect_referenced` 38(os.listdir 워크/동적 stack_id) · **archive·fixture 후보 3(런타임 무참조)**.

**archive 후보(P4-cleanup 별도 승인 대상, 이번 미이동):**
- `server/data/system_catalog.json` — root legacy 중복(런타임=`ch2/catalog/systems_catalog.json`). plan "root duplicate" 의심 **확인**.
- `server/data/ch1/catalog/drivers.json` — 런타임=`drivers_catalog.json`. drivers×2 중복 **확인**.
- `server/data/tools/diagnose_req_ch2.json` — 샘플 요청 fixture.

**plan 가정 정정:** `ch1_industries/`·`ch1/industry_packs/`·`ch1/routing_packs/`·`stack_library/`·`ch1_mgmt_model/industries/`는 이름상 legacy로 보이나 **`os.listdir` 동적로드로 live** → archive 금지. 실제 무참조는 위 3건뿐.

## P4-core / P5 판정 (2026-07-06)

- **P4-core ✅ PASS 확정** — `P4_CORE_GATE_VERDICT.md`. Exit 7/7 + **M5 재현 diff 0**(Gatekeeper 재실행 확인)으로 조건부 게이트 해소.
- **P5 관리탭 ✅ PASS** — `P5_MGMT_TAB_GATE_VERDICT.md`. 39팩 로드·§8.2 4블록 실측·read-only·라이브 :8765(200/ok). 제1동인 가시화 완성.
- ⚠ 절차 이례(P4-core Gatekeeper 직접 생성) → **역할 복원** 완료(실행=M5 Cursor, Claude=계획·지시·검증).
- MINOR(비차단): related_issues 과매칭 가능 · UI 픽셀 육안 미확인 · q1/q5 generated_path null · ch1_mgmt_model live/unknown → cleanup 보강.

## 다음 액션

- **M5 Cursor(부차, 배치별 승인):** `WORK_ORDER_P4_CLEANUP.md` — 배치A archive 3후보(proof 재첨부+회귀 green 제출→승인) · 배치B residual byte-0(ch4/step5_2/ch0) · 배치C generator 은퇴.
- **Gatekeeper(Claude):** 각 배치 제출물 표본 검증·판정. 실행 미수행.
- **원 목표 도달:** 데이터 기반(P1~P4-core) + 가시화(P5) 완성. cleanup은 부차·이연.

## 보류·백로그 (P4 이후 결정)

- **process_detail_v1** (`server/client/data/step3/process_detail_v1.json`) = **residual_live, 미dx화 부채·후속 dx화 대상**. 2026-07-06 B01~B08 A1 Ch3 백필 **L1 스크립트 stopgap** (`scripts/build_a1_ch3_b_process_detail_backfill.py`, 소스 v0.2, R1 industry 보존) — 관리탭 편집 미부착.
- **런타임 팩 구조 전환(스키마 v4)** = **보류.** authoring(dx)은 재설계됨·런타임은 byte-0 유지가 현 방향. 전환 시 엔진 결합도: Ch2 🔴(~5,500줄+DB mode, 별건) / Ch1 🟠(~1,570줄) / Q4 flat·Q3 🟢(~450줄, 선별전환 가성비 최고). 필요 시 "챕터별 전환 비용·순서표(v4 로드맵)" 작성.
- **A1/A2 재설계** = **향후 고려 가능성**(사장 플래그, 2026-07-06). P3는 A1/A2 *콘텐츠*를 system→module→sub_override로 세분화. A1(리포트)/A2(제안) 자체의 구조·UX 재설계는 별도 검토 대상 — P4 마무리 후 판단.

## ⚠️ workflow 메모

M2 환경 git이 간헐적으로 막힘(DNS). 미커밋 산출물은 **Gatekeeper가 1Dev clone(`~/Documents/1Dev/diagnosis-tool`)에서 대행 커밋·push**. 검증은 **read-only git + 미커밋물 선(先)커밋 보존** 원칙(P3b에서 checkout 유실 사고 재발방지).

## 문서 지도 (diag-sot/)

- **설계:** `00_MANIFEST` · `10_OVERVIEW` · `P0~P4_SPEC` · `../DIAGNOSIS_TOOL_SOT_TARGET_DESIGN`(배경)
- **작업지시:** `WORK_ORDER_{P0,P1,P1B,P2,P3,P3A,P3B,P3B5,P4}`
- **판정/승인:** `P1A_GATE_VERDICT`(반려) · `P2_DISCOVERY_APPROVAL` · `P2_CATALOG_ROUNDTRIP_DECISION` · `P2_CATALOG_GATE_VERDICT` · `P2_GATE_VERDICT` · `P3A_SCHEMA_APPROVAL` · `P3A_GATE_VERDICT`... · `P3B_SCHEMA_APPROVAL` · `P3B_GATE_VERDICT(_2)` · `P3B5_DIAGNOSIS_APPROVAL` · `P3B5_GATE_VERDICT(_2)` · `P4_PLAN_APPROVAL` · **`P4_CORE_GATE_VERDICT`**
- **P5 관리탭:** **`P5_MGMT_TAB_SPEC`**(설계) · **`WORK_ORDER_P5_MGMT_TAB`** · **`P5_MGMT_TAB_GATE_VERDICT`** · **`WORK_ORDER_P4_CLEANUP`**
- **M2 산출(diagnosis-tool `docs/diag-sot/reports/`):** `P0~P4` result/draft·diagnosis 보고서
