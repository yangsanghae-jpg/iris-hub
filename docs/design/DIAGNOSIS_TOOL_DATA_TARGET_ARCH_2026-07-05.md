# 진단툴 데이터 목표 구조 (운영 지향) 제안

> ⛔ **부결·폐기 (2026-07-05).** 이 문서는 진단툴의 **실제 운영 시나리오를 보지 않고 순수 파일 종합만으로** 작성되어 부결됨. 핵심 오류: ① 데이터가 (챕터엔진 × 머지티어) 축으로 조직된 걸 무시하고 엔티티 레지스트리 정규화를 제안 → 캐스케이드 머지 의미론 파괴. ② 인라인 `LocalizedText` 획일 적용은 기존/신규 방향과 상충. ③ 이미 존재하는 2026-06-29 재설계·PoC를 못 봄. **대체 문서:** [`DIAGNOSIS_TOOL_SOT_TARGET_DESIGN_2026-07-05.md`](./DIAGNOSIS_TOOL_SOT_TARGET_DESIGN_2026-07-05.md) (운영 시나리오·3축·요구5개 기반).

- **작성일:** 2026-07-05
- **상태:** ⛔ 부결·폐기 (위 참조)
- **목적:** 진단툴을 **운영**(편집·검증·버전관리·다국어·무드리프트)하기 위한 미래 데이터 구조 설계.
- **근거:** [`DIAGNOSIS_TOOL_DATA_FULL_AUDIT_2026-07-05.md`](./DIAGNOSIS_TOOL_DATA_FULL_AUDIT_2026-07-05.md) 발견 F1~F9 해소를 설계 목표로 삼음.
- **관련:** [`DIAGNOSIS_TOOL_DATA_STRUCTURE_EVAL_2026-07-05.md`](./DIAGNOSIS_TOOL_DATA_STRUCTURE_EVAL_2026-07-05.md) · [`DIAGNOSIS_PACK_MGMT_MOCKUP_DISCOVERY_REPORT_2026-07-05.md`](./DIAGNOSIS_PACK_MGMT_MOCKUP_DISCOVERY_REPORT_2026-07-05.md)

---

## 0. 설계 목표 ↔ 발견 매핑

| 목표 | 해소 발견 |
|------|-----------|
| 단일 i18n 규약 | F1 |
| 엔티티당 **정본 1개**(SoT) | F2, F4, F5 |
| 파일마다 동일한 **봉투(envelope)** | F3, F6, F7 |
| 정규화된 payload (도메인·레벨) | F8 |
| 크기·로딩 정책 | F9 |

핵심 명제: **불일치를 렌더러가 흡수하게 두지 말고, 데이터가 스스로 일관되게 만든다.** 그래야 관리 탭의 M2→M5 churn(팩마다 특수분기)이 사라진다.

---

## 1. 4대 원칙

1. **봉투 표준화** — 모든 파일은 동일한 최상위 봉투(`kind`·`id`·`version`·`schema`·`status`·`updated` + `data`)를 갖는다. 렌더러·검증기·import는 봉투만 보고 분기한다.
2. **3계층 분리** — ①**Registry**(엔티티 정본) ②**Catalog**(코드북) ③**Pack**(스텝별 내용). Pack은 엔티티를 **id로 참조**할 뿐 라벨·정의를 재선언하지 않는다.
3. **단일 SoT + 파생물** — `data/` 한 트리가 정본. client 사본은 **빌드 산출물**(스크립트 생성)이며 수기 편집 금지 → 드리프트 원천 제거.
4. **다국어 1급 타입** — 모든 표시 텍스트는 `LocalizedText = {ko,zh,en,ja}` 한 형태. `*_zh`/`*_cn`/`name_*` 등 폐기, `cn→zh` 정규화.

---

## 2. 봉투(Envelope) 표준

모든 JSON은 아래 최상위 형태를 따른다:

```json
{
  "kind":    "industry_pack",         // 팩 종류 — 렌더러/스키마 선택 키
  "id":      "industry/A",            // 전역 안정 id (경로 규약)
  "version": "4.0.0",                 // semver 고정
  "schema":  "diag/industry_pack@4",  // 검증할 JSON Schema 참조
  "status":  "active",                // active | draft | deprecated | archived
  "updated": "2026-07-05",
  "source":  "ch1_rebuild",           // 선택: provenance
  "data":    { /* 정규화 payload */ }
}
```

- 코드에서 항상 `doc["data"]`, `doc["kind"]`, `doc["version"]`. **메타 키 6종(F3)·버전 문자열 난립(F6) 소멸.**
- 최상위 list였던 카탈로그(F7)도 `data.entries[]`로 감싸 통일.

## 3. 디렉터리 레이아웃 (목표)

```
data/                         # ← 유일한 SoT
  registry/                   # 계층1: 엔티티 정본 (엔티티당 1파일)
    industries.json           #   A..I : id, label(LocalizedText), default_routing, subs[]
    sub_industries.json       #   A01..I08 : id, parent, factor_profile, label
    routings.json             #   5 라우팅
    domains.json              #   4 도메인 + level_framework(L1~L5)
  catalog/                    # 계층2: 코드북 — 전부 {meta, entries[]} 동일 shape
    mvp_codes.json  module_codes.json  kpi_codes.json ...
    keywords.json             #   ch1/ch2 중복 3종 → 1개로 통합(F5)
  packs/                      # 계층3: 스텝별 내용 (registry id 참조)
    ch1/industry/A.json ...   #   IND_* 풀팩. ch1_industries·ch1_mgmt_model 3중 → 여기 1계보(F2)
    step4/automation/A01.json #   Q4 sub — 정규화 payload(F8)
    step3/scale/... step5_2/management/...
  _archive/                   # 폐기·이력 (런타임 로드 제외, 명시적 격리)
build/ 또는 client/data/      # 파생 산출물 — sync 스크립트가 생성, .gitignore 또는 CI 검증
```

> **F2 해소:** 산업 A의 정본은 `packs/ch1/industry/A.json` 하나. 관리모델(`ch1_mgmt_model`)이 필요로 하던 `profiles`·`default`는 이 팩의 `data.management` 블록으로 흡수하거나, 정말 독립 관심사면 `packs/ch1/mgmt/A.json`으로 두되 **라벨은 registry 참조**(재선언 금지).

## 4. i18n 표준 — `LocalizedText`

```jsonc
// AS-IS (F1: 5+종)
"industry_label_zh": "项目型制造", "industry_label_ko": "프로젝트형 제조"
"industry_name_cn": "项目型制造"        // 다른 파일
"label": {"ko":..,"zh":..,"en":..,"ja":..}  // Q4만 nested

// TO-BE (전역 단일)
"label": { "ko": "프로젝트형 제조", "zh": "项目型制造", "en": "Project-based Mfg", "ja": "" }
```
- 규칙: 표시 텍스트 키는 **항상 객체**, 언어코드는 `ko|zh|en|ja` 고정(`cn` 금지). 빈 언어는 `""` 허용(부분 번역 가시화).
- **인라인 채택 이유:** 관리 탭이 "그리드에서 값 편집"(M5 정본)을 하므로 텍스트가 팩과 **같이 있어야** 편집 가능. 별도 메시지 카탈로그는 편집 UX를 깨뜨림. 장문 콘텐츠만 예외적으로 `i18n/` 오버플로 허용.

## 5. 정규화 payload — 플래그십 2종

### 5.1 산업 팩 (`packs/ch1/industry/A.json`)

```jsonc
{ "kind":"industry_pack","id":"industry/A","version":"4.0.0","schema":"diag/industry_pack@4",
  "status":"active","updated":"2026-07-05",
  "data": {
    "label": { "ko":"프로젝트형 제조", "zh":"项目型制造", "en":"...", "ja":"" },
    "default_routing": "routing/PROJECT",     // registry 참조 (코드 접두 통일: 'A' 아닌 'industry/A')
    "priority_axes": ["delivery_sync","..."],
    "theme": "DELIVERY_SYNC",
    "subs": ["subind/A01","subind/A02","..."],// registry sub_industries 참조
    "default_profile": { "mvp_functions":[...], "core_modules":[...] },
    "sub_profiles": { /* sub별 오버라이드, 없으면 생략 — legacy_* 폐기 */ }
  } }
```
- `legacy_sub_profiles`·`legacy_slug` 제거(마이그레이션 시 `_archive`로).

### 5.2 Q4 자동화 sub 팩 (`packs/step4/automation/A01.json`) — F8 해소

```jsonc
{ "kind":"automation_sub","id":"automation/A01","version":"4.0.0","schema":"diag/automation_sub@4",
  "status":"active","updated":"2026-07-05",
  "data": {
    "sub": "subind/A01",                      // registry 참조 (industry_code/label 재선언 안 함)
    "factor_profile": "F_PROJECT",
    "label": {"ko":..,"zh":..,"en":..,"ja":..},
    "domains": {                              // ★ 4도메인을 한 형태로 정규화 (AS-IS: planning_* flat)
      "planning": {
        "profile": "F_PROJECT_EPC",
        "importance": 5,
        "weight": 0.35,                       // 기존 weights.planning 흡수 → 이중표현 제거
        "levels": { "floor":"L2", "target":"L3", "ceiling":"L4" },  // *_levels 3티어 통일
        "horizon": "프로젝트·월/주간",
        "constraints": ["WBS","..."],
        "objects": ["자재검사","..."],
        "term_override": {"ko":..,"zh":..}    // 도메인별 용어 오버라이드도 여기로
      },
      "quality": { ... }, "equipment_control": { ... }, "logistics": { ... }
    }
  } }
```
- **효과:** 같은 축(도메인)이 한 방식으로만 존재 → 관리 그리드는 **도메인 sub-grid 1종 × 4반복**. M5의 "sub-grid 9개 수작업 분할"이 규칙 하나로 축소.
- `weights`·`recommended_levels`는 `domains[*].weight`·`levels.target`에서 **파생/집계**(중복 저장 폐지).

## 6. 카탈로그 통일 (F5, F7)

```jsonc
{ "kind":"catalog","id":"catalog/mvp_codes","version":"4.0.0","schema":"diag/catalog@4",
  "status":"active","updated":"2026-07-05",
  "data": { "entries": [ { "code":"MVP_...", "label":{...}, "...":"..." } ] } }
```
- `keywords_map`(ch1·ch2·_merged 3종) → `catalog/keywords.json` 1개, 출처는 `source`로 표기.
- `drivers`·`drivers_catalog` → 1개. top-level list 카탈로그(direction/kpi/module/mvp) → `data.entries`로 감쌈.

## 7. SoT·드리프트·검증·버전 (운영 요건)

| 관심사 | 목표 |
|--------|------|
| **SoT** | `data/`만 정본. client/build 사본은 `scripts/build_client_data.py` 산출물, CI가 "재생성 후 diff 0" 검증 → F4 원천 차단 |
| **검증** | `kind`별 JSON Schema(`schemas/diag/*.json`). CI에서 전 팩 validate. 봉투 필수필드·LocalizedText 언어코드 lint |
| **버전** | 봉투 `version` semver + `schema` major. 파일 내부 자유 버전문자열 폐지 |
| **참조 무결성** | Pack의 registry 참조 id(`industry/A`,`routing/PROJECT`,`subind/A01`)가 registry에 존재하는지 CI 체크 |
| **크기(F9)** | `process_detail`(2.2MB) 등은 엔티티 단위 분할(`packs/step3/process/A.json`) → 관리 탭 lazy load. 대형 단일 JSON 지양 |
| **iris-hub 연동** | 이 봉투 스키마 = `dx_*` import의 **계약(contract)**. DB는 런타임/편집 스토어, JSON은 정본/교환 포맷. 왕복 시 봉투 보존 |

## 8. 관리 탭이 얻는 것

- 렌더러가 **`kind`→스키마→그리드** 단일 파이프라인. 팩 종류별 특수분기 소멸(A/B/C 옵션 중 **B의 상위호환**).
- i18n 그리드 1벌, 도메인 그리드 1벌, 카탈로그 그리드 1벌 → **재사용 확정**.
- "A산업 편집" 시 대상 파일이 **자명**(정본 1개). 저장 경로 모호성 해소.

## 9. 마이그레이션 경로 (단계적, 무중단)

| 단계 | 내용 | 산출 |
|------|------|------|
| **M-0** | JSON Schema(`diag/*@4`) + 봉투 정의 작성, 검증기 스캐폴드 | 스키마 세트 |
| **M-1** | **어댑터 레이어** — 런타임은 그대로 두고 로드시 AS-IS→봉투 정규화(i18n·meta). 즉시 관리 탭 이득 | `normalize.py` |
| **M-2** | Registry 추출 — industries/subs/routings/domains 정본화, 3중 산업(F2) 계보 정리 | `data/registry/*` |
| **M-3** | Q4 도메인 정규화(F8) + 카탈로그 통합(F5) → 파일 실제 이동, 런타임 참조 갱신 | `packs/*` |
| **M-4** | client 사본 → 빌드 산출물화, 드리프트 CI(F4). `_archive` 격리 | sync 스크립트·CI |

> M-1까지만 해도 관리 탭 착수 가능(어댑터=평가문서 옵션 B). M-2~4는 진단툴 런타임과 조율 필요한 별 트랙.

---

## 10. 미결 / 결정 필요

- [ ] **i18n:** 인라인 `LocalizedText`(권고) vs 분리 메시지 카탈로그 — 관리 UX상 인라인 권고
- [ ] **Q4 weights:** 파생 계산(권고) vs 명시 저장 유지
- [ ] **관리모델(ch1_mgmt_model):** 산업 팩에 흡수 vs 별 pack 유지(라벨은 registry 참조)
- [ ] **DB vs JSON SoT:** JSON 정본 + dx_* 편집스토어(권고) 확정 여부
- [ ] 스키마 major 시작 번호(`@4`가 v1.5 진단툴과 헷갈리면 조정)

## 부록. 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-07-05 | 초판 — 봉투 표준·3계층·LocalizedText·정규화 payload·마이그레이션 M0~M4 |
