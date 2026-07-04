# 진단툴 관리 탭 상세 설계서 (Diagnosis Pack Management Tab)

**문서 버전**: v0.1 (설계 초안)
**작성 기준**: diagnosis-tool `origin/v1.5` (9산업 A~I) · iris-hub `origin/feat/hub-rebuild`
**목적**: iris-hub에 진단툴의 **진실원(SoT)** 을 관리하는 신규 탭을 설계한다. DB를 중간축으로 두고,
그리드로 **육안 점검·수정**한 뒤 "적용" 명령으로 진단툴의 팩(JSON)을 **리빌드**한다. 진단툴 런타임은 무변경.

---

## 0. 구상 요약 (Vision)

```
[미래]  iris-hub 지식볼트  ──(에이전트: 수동/자동, 후속)──▶  ┐
                                                          │
[지금]  사람이 그리드로 육안 점검·수정  ───────────────▶  [iris-hub DB = 진단툴 진실원(SoT)]
                                                          │
                                          "적용" 명령  ──▶ 리빌드 ──▶ [진단툴 팩(IND_*, RT_*, catalogs, stepN 수치)]
                                                                        └ 진단툴 런타임/엔진은 무변경
```

- **DB가 안정된 중심축.** 입력이 지금은 "사람 손", 나중엔 "볼트+에이전트"로 바뀌어도 출력(팩 리빌드)·진단툴은 안 바뀐다.
- 관리 대상은 **세 팩 = 필드 차원 교차 관심사**: 🔢 수치팩 · 📦 내용팩 · 🌐 언어팩.

| 팩 | 정의 | 예 |
|----|------|-----|
| 🔢 **수치팩** | 룰엔진 수학을 움직이는 튜닝 숫자 | profile weight, routing boost, 임계값(0.85/0.55), 개수캡, scale band, Q2~Q5 하위산업 수치 |
| 📦 **내용팩** | 의미·구조(무엇이 무엇에 속하나) | 코드 목록·status, 프로필 코드 멤버십, 산업/하위산업 taxonomy, routing 배정, alias, 브릿지 |
| 🌐 **언어팩** | 사람이 보는 모든 텍스트 | label ko/zh/en, context_explain, summary 템플릿, messages, description, i18n |

---

## 1. 현 데이터 분석 (Current Data Analysis)

### 1.1 진단툴 Ch1 엔진은 "조립식" — 결과는 저장이 아니라 계산됨

`server/assemble/ch1_mgmt/engine.py` → `compose_ch1_four_blocks()`:

```
블록별 점수 = default_profile(×1.0) + sub_profile(×0.25) + routing(adjustments + overlay +0.05)
             │ 4블록: mvp · modules · direction · kpi
→ 점수 ≥ CORE_MIN(0.85) → core,  ≥ SUPPORT_MIN(0.55) → support   (BLOCK_COUNTS 개수캡)
→ code → label_zh → 룰 기반 summary 문장
```

- **데이터팩(IND_*)은 "결과"가 아니라 "가중치 입력".** 최종 core/support·문장은 팩 어디에도 저장되지 않고 엔진이 매번 계산한다.
- **함의**: 그리드에서 가중치를 고쳐도 결과는 안 보인다 → **미리보기(compose 재실행)** 가 필요(§4.4).
- **함의**: 임계값 `0.85 / 0.55 / sub×0.25 / BLOCK_COUNTS`는 **엔진 코드 상수**(데이터 아님). 이걸 관리하려면 진단툴을 소폭 바꿔 외부화해야 한다(§6, D-B).

### 1.2 데이터 인벤토리 — 세 팩 분해 (v1.5)

세 팩은 별도 파일이 아니라 **거의 모든 파일에 섞여** 있다. 관리툴의 본질은 이를 DB에서 정규 분리하는 것.

**Ch1 (산업팩 — 1차 대상)**

| 파일 | 🔢 수치 | 📦 내용 | 🌐 언어 |
|------|--------|--------|--------|
| `ch1/industry_packs/IND_*.json` (9) | mvp/module `weight` | industry_code, priority_axes, characteristics, sub_industries[code], routing/flow_style/control_unit, mvp/dir/kpi 멤버십 | industry_label_ko/zh, sub_industries[].label_ko/zh, message_theme |
| `ch1/routing_packs/RT_*.json` (5) | overlay `boost`, adjustments `weight` | routing_code, axes, flow_style, overlay/adjust 코드 | routing_label_ko/zh, description |
| `ch1/catalogs/*.json` (11) | — | code 목록 + status | label_ko/zh/en, context_explain(_ko) |
| `ch1/ch1_code_alias.json`, `sub_industry_aliases.json` | — | 코드 별칭 매핑 | — |
| `ch1/contract/scoring_policy.json` | label_caps, min_score, dedup, sort | — | — |

**Ch2~Ch4 · Step 파이프라인 · Q5 · ROI (후속 대상)**

| 파일 | 🔢 수치 | 📦 내용 | 🌐 언어 |
|------|--------|--------|--------|
| `step2/routing_product_nature_v3` | (Q2 특성치) | subindustry_profiles(74) | — |
| `step3/scale_profile_v3` | scale_bands, intensity | subindustry_profiles(74), signal_dict | — |
| `step4/automation_profile_v3` | level_framework, factor_profiles | subindustry_profiles(74) | evidence 텍스트 |
| `step5_2/management_analysis_v3` | scale/routing_modifiers, weights | subindustry_overrides(**53**) | — |
| `step5_2/…_i18n_zh.json` | — | — | **명시적 언어팩** |
| `q5/recommendation_by_subindustry_v1` | q5_1·q5_2(74) | axes, recommendations | 추천 문구 |
| `roi/roi_logic_catalog_v1` | ROI 로직 수치 | by_industry | comment |
| `ch2/catalog/stack_library/stack_*` (8, **I 없음**) | — | recommended_systems | 카드 텍스트 |
| `industry_master.json` | — | 산업 레지스트리 A~I | 산업명 |
| `rule_params.json` / `scale_master.json` | step3/step5 강도·상한 / signals | signal_dict | — |
| `knowledge/system_dictionary_v1.sqlite` | — | **이미 DB** system dictionary | 사전 라벨 |

> **선례**: 진단툴에 이미 ① 명시적 i18n 언어팩(`…_i18n_zh.json`), ② 지식 DB(`system_dictionary_v1.sqlite`)가 존재 — 본 설계와 결이 맞다.

### 1.3 핵심 문제 — 하위산업 taxonomy 분열 & 커버리지 미강제

하위산업 식별 체계가 **4~5개로 갈라져** 있고 서로 키가 안 겹친다.

| 체계 | 개수 | 쓰는 곳 |
|------|------|---------|
| `A01`형 | **74** | Q2/Q3/Q4/Q5추천 (step2·step3·step4·q5rec — 코드 집합 완전 동일) |
| 이름형(`aerospace_equipment`) | **60** | IND_* Ch1 팩 |
| 이름형(`logic_foundry`) | **53** | Q5 management(step5_2) |
| `SUB_A_*`형 | **20** | `catalogs/sub_industry_codes.json` |
| bridge(`semiconductor_frontend`→`["B03","B04"]`) | 부분 | `ch2/card2/subindustry_bridge` |

- **A01형(74) ∩ 이름형(60) = 0.** "세부 산업이 몇 개냐"부터 파일마다 다르다.

**Q2~Q5 수치 커버리지 실측**

| 질문 | 데이터 | 커버리지 |
|------|--------|----------|
| Q2 | step2/routing_product_nature_v3 | 74/74 ✓ |
| Q3 | step3/scale_profile_v3 | 74/74 ✓ |
| Q4 | step4/automation_profile_v3 | 74/74 ✓ |
| Q5(추천) | q5/recommendation_by_subindustry_v1 | 74/74 ✓ |
| Q5(management) | step5_2/management_analysis_v3 | **53/60 ✗** |

→ Q5 management 수치가 **7개 하위산업 누락**(전부 의료계열):
`medical_imaging_equipment, medical_electronic_equipment, surgical_powered_equipment, rehabilitation_equipment, medical_consumables, medical_metal_materials, medical_polymer_ceramic_functional_materials`.
아무도 커버리지를 강제하지 않아 생긴 구멍.

### 1.4 문제 요약 → 관리툴이 풀 것

1. **taxonomy 분열** → 단일 정본 하위산업 + 체계 간 브릿지 테이블.
2. **커버리지 미강제** → Q2~Q5 수치 누락 자동 검출(그리드 하이라이트).
3. **수치 흩어짐 + 코드 하드코딩** → 수치팩 집약(엔진 상수 외부화는 선택).
4. **산업 I 미완결** → ch2 stack_library·ch1_mgmt_model에 I 없음. 산업 추가 시 다중 팩 누락 방지.

---

## 2. 목업 설계 (UI / Mockup)

### 2.1 탭 위치

- 기존 `🔧 진단툴`(마이그레이션 진도, `src/tabs/diagnosis_mgmt.py`)과 **별개로 신설**: **`🛠 진단툴 관리`**.
- `app.py`의 `NAV_ITEMS`에 항목 추가(`src/tabs/diagnosis_pack.py`).

### 2.2 화면 골격 — 좌측 섹션 내비 + 우측 그리드/폼

```
┌──────────────┬──────────────────────────────────────────────────────────────┐
│ 🛠 진단툴 관리 │  [정본: v1.5 · imported 07-04 · dirty ●]      [검증][미리보기][적용]│
│               ├──────────────────────────────────────────────────────────────┤
│ ▸ 대시보드     │  (선택 섹션의 그리드/폼)                                        │
│ ▸ 하위산업     │                                                              │
│ ▸ 프로필       │                                                              │
│ ▸ 라우팅       │                                                              │
│ ▸ 코드 카탈로그 │                                                              │
│ ▸ 언어팩(i18n) │                                                              │
│ ▸ Q2~Q5 수치   │                                                              │
│ ▸ 적용/이력     │                                                              │
└──────────────┴──────────────────────────────────────────────────────────────┘
```

### 2.3 섹션별 목업

**(a) 대시보드 — 커버리지 매트릭스 (§1.3의 구멍을 한눈에)**

```
산업 × Q 수치 커버리지          범례: 숫자=충족/전체 · 🔴=누락
        Q2    Q3    Q4    Q5추천  Q5관리
 A     12/12 12/12 12/12 12/12   5/12 🔴  ← 의료 7 누락
 B      8/8   8/8   8/8   8/8     8/8
 …
 I      4/4   4/4   4/4   4/4     4/4
 [🔴 누락 셀 클릭 → 해당 하위산업 Q5관리 수치 편집으로 이동]
```

**(b) 하위산업 — 정본 taxonomy + 체계 브릿지 그리드**

```
canon_code▼ | industry | label_ko       | label_zh | A01 | ch1팩이름           | step5이름   | SUB_형
aerospace…  | A        | 항공·우주 장비  | 航空…    | A01 | aerospace_equipment | (없음)🔴   | SUB_A_…
   (브릿지 빈칸 = 체계 간 매핑 누락 → 리빌드 시 경고)
```

**(c) 프로필 — default/sub 그리드 (델타 하이라이트)**

```
산업[A ▼]  프로필[default | aerospace_equipment ▼]      (sub는 default에 ×0.25 가산)
 블록[mvp]   code ▼ (카탈로그·라벨표시)  | weight | Δ(default 대비)
            进度监控 (MVP_PROGRESS_MON)  | 0.90   |
            供应协同 (MVP_SUPPLY_SYNC)   | 0.60   | ● 신규(sub에만)
 [+행]  ← code는 mvp_codes 카탈로그 드롭다운, 미존재 코드 입력 불가
```

**(d) 코드 카탈로그 — 내용(code/status) + 언어(label)**

```
kind[mvp ▼]  code            | status  | label_ko | label_zh | label_en
             MVP_BATCH_TRACE | active  | 배치추적 | 批次追溯 | Batch Trace
             [deprecated 토글 → 리빌드 시 제외]
```

**(e) 미리보기 — compose 결과**

```
[산업 A · 하위산업 aerospace_equipment · routing RT_PROJECT]  [▶ 미리보기 실행]
 mvp     core: 进度监控, 进度可视化    support: 供应协同
 modules core: …
 (진단툴 compose_ch1_four_blocks 호출 결과 — 가중치 편집 효과 확인)
```

**(f) 적용/이력**

```
[검증 통과 ✓ 0오류 2경고]  대상: diagnosis-tool v1.5 clone (DIAGNOSIS_TOOL_GIT)
 리빌드 파일: IND_A.json … (9), RT_*.json(5), catalogs(11), step5_2 override(+7)
 [적용 → 브랜치 커밋]   최근 이력: 07-04 12:30 "pack rebuild: Q5 medical 7 backfill"
```

---

## 3. DB 구조 설계

### 3.1 원칙

- iris-hub `src/store` SQLite 확장(`db.get_conn()` 게이트웨이·`schema.sql`·WAL·`meta_kv` 버전). 탭은 sqlite 직접 열지 않음.
- 테이블 접두사 `dx_`(diagnosis). 문서/개념층 테이블과 네임스페이스 분리.
- **세 팩을 스키마로 분리**: 수치=값 컬럼/수치 테이블, 내용=구조 테이블, 언어=`dx_label`/`dx_text` 단일 i18n.
- **단일 정본 하위산업** + 체계 브릿지로 taxonomy 분열 해소.

### 3.2 스키마 (DDL 스케치)

```sql
-- ── 메타 ──────────────────────────────────────────────
CREATE TABLE dx_import (               -- 팩 적재/릴리스 이력
  id INTEGER PRIMARY KEY, source_branch TEXT, source_commit TEXT,
  imported_at TEXT, note TEXT);

-- ── 📦 내용: taxonomy ─────────────────────────────────
CREATE TABLE dx_industry (             -- 산업 A~I
  code TEXT PRIMARY KEY,               -- 'A'.. (IND_A)
  message_theme TEXT, priority_axes_json TEXT, ord INTEGER);

CREATE TABLE dx_sub_industry (         -- 정본 하위산업 (단일 SoT)
  id INTEGER PRIMARY KEY,
  industry_code TEXT REFERENCES dx_industry(code),
  canon_code TEXT UNIQUE,              -- 정본 코드(이름형 채택 권장)
  ord INTEGER);

CREATE TABLE dx_sub_bridge (           -- 체계 간 매핑(74/60/53/20 화해)
  sub_id INTEGER REFERENCES dx_sub_industry(id),
  scheme TEXT,                         -- 'A01'|'ch1name'|'step5name'|'SUB'
  external_code TEXT,
  PRIMARY KEY(sub_id, scheme, external_code));

-- ── 📦 내용 + 🔢 수치: 프로필/라우팅 ────────────────────
CREATE TABLE dx_profile (
  id INTEGER PRIMARY KEY, industry_code TEXT REFERENCES dx_industry(code),
  scope TEXT,                          -- 'default' | canon_code
  routing_code TEXT, flow_style TEXT, control_unit TEXT);

CREATE TABLE dx_profile_item (
  profile_id INTEGER REFERENCES dx_profile(id),
  block TEXT,                          -- 'mvp'|'modules'|'direction'|'kpi'  📦
  code TEXT,                           -- 📦 카탈로그 참조
  weight REAL,                         -- 🔢 수치
  ord INTEGER);

CREATE TABLE dx_routing_pack (
  routing_code TEXT PRIMARY KEY, flow_style TEXT, control_unit TEXT,
  priority_axes_json TEXT, routing_theme TEXT);
CREATE TABLE dx_routing_effect (       -- overlay(boost) + adjustments(weight) 통합
  routing_code TEXT REFERENCES dx_routing_pack(routing_code),
  kind TEXT,                           -- 'overlay'|'adjustment'
  block TEXT, code TEXT, value REAL);  -- 🔢 boost/weight

-- ── 📦 내용: 코드 카탈로그 ─────────────────────────────
CREATE TABLE dx_code (
  kind TEXT, code TEXT, status TEXT,   -- 'active'|'deprecated'
  PRIMARY KEY(kind, code));
CREATE TABLE dx_code_alias (
  kind TEXT, alias_code TEXT, canon_code TEXT,
  PRIMARY KEY(kind, alias_code));

-- ── 🔢 수치: Q2~Q5 하위산업 수치 (커버리지 매트릭스 원천) ──
CREATE TABLE dx_question_metric (
  sub_id INTEGER REFERENCES dx_sub_industry(id),
  question TEXT,                       -- 'Q2'|'Q3'|'Q4'|'Q5_REC'|'Q5_MGMT'
  metric_key TEXT, value REAL, notes TEXT,
  PRIMARY KEY(sub_id, question, metric_key));

CREATE TABLE dx_scoring_param (        -- 엔진 상수 외부화(선택, §6 D-B)
  key TEXT PRIMARY KEY, value REAL);   -- CORE_MIN, SUPPORT_MIN, SUB_SCALE …

-- ── 🌐 언어: 단일 i18n ────────────────────────────────
CREATE TABLE dx_label (
  entity_kind TEXT,                    -- 'code'|'industry'|'sub_industry'|'routing'
  entity_key TEXT, lang TEXT,          -- 'ko'|'zh'|'en'
  label TEXT, explain TEXT,
  PRIMARY KEY(entity_kind, entity_key, lang));
CREATE TABLE dx_text (                 -- summary/message 템플릿
  key TEXT, lang TEXT, template TEXT, PRIMARY KEY(key, lang));
```

### 3.3 세 팩 ↔ 테이블 매핑

| 팩 | 테이블/컬럼 |
|----|-------------|
| 🔢 수치 | `dx_profile_item.weight`, `dx_routing_effect.value`, `dx_question_metric.value`, `dx_scoring_param.value` |
| 📦 내용 | `dx_industry`, `dx_sub_industry`, `dx_sub_bridge`, `dx_profile`, `dx_profile_item.code/block`, `dx_routing_pack`, `dx_code`, `dx_code_alias` |
| 🌐 언어 | `dx_label`, `dx_text` |

### 3.4 커버리지 뷰 (누락 자동 검출)

```sql
CREATE VIEW v_dx_coverage AS
SELECT s.industry_code, s.canon_code, q.question,
       CASE WHEN m.sub_id IS NULL THEN 0 ELSE 1 END AS has_metric
FROM dx_sub_industry s
CROSS JOIN (SELECT DISTINCT question FROM dx_question_metric) q
LEFT JOIN (SELECT DISTINCT sub_id, question FROM dx_question_metric) m
       ON m.sub_id = s.id AND m.question = q.question;
-- has_metric=0 → 대시보드 🔴 (예: Q5_MGMT × 의료 7건)
```

---

## 4. 기능 설계

### 4.1 임포트 (JSON → DB seed)
- 진단툴 v1.5 클론에서 IND_*/RT_*/catalogs/stepN/q5 로드 → `dx_*` 적재.
- **taxonomy 화해**: 이름형(60)을 정본 후보로, `dx_sub_bridge`에 A01(74)·step5(53)·SUB_(20) 매핑 기록. 매핑 안 되는 항목은 "미해결"로 표시.
- 재임포트 멱등(정본 갱신 시 재적재). `dx_import`에 이력.

### 4.2 편집 (그리드)
- `st.data_editor` 그리드 per 테이블. code 컬럼 = `dx_code`(active) **드롭다운(라벨 표시)** → 미존재 코드 차단.
- 프로필: default 대비 **델타 하이라이트**(sub는 ×0.25 가산 의미). weight 범위·형 검증.
- 하위산업 추가 → 대응 `dx_profile(scope=canon)` 골격·브릿지 행 자동 스캐폴드.

### 4.3 검증 (적용 게이트)
- **커버리지**: `v_dx_coverage` 0건 → 경고/오류(정책化).
- **참조 무결성**: 모든 `code` ∈ `dx_code(active)`; routing_code ∈ `dx_routing_pack`.
- **브릿지 완전성**: 엔진이 쓰는 체계(A01·이름형)에 정본 하위산업이 모두 매핑됐는가.
- **산업 완결성**: A~I가 IND_*·ch2 stack·mgmt_model에 모두 존재(산업 I 갭 검출).
- 진단툴의 `pack_maintenance.py`(별도 리포) 개념과 정합 — 최종 산출 JSON도 재검증.

### 4.4 미리보기 (compose 재실행)
- **채택안(b)**: 진단툴 `ch1_mgmt.engine.compose_ch1_four_blocks`를 **얇게 호출**(단일 진실). 진단툴에 preview 진입점 1개만 노출.
- 대안(a): 스코어링 로직 이식(진단툴 무의존, 이중관리 위험).

### 4.5 적용 / 리빌드 (DB → 팩)
```
dx_* 조회 → IND_*.json·RT_*.json·catalogs·stepN 수치·step5_2 override 재생성
        → §4.3 검증 통과 시에만
        → diagnosis_git(DIAGNOSIS_TOOL_GIT 클론)에 파일 쓰기 → 브랜치 커밋(→ 선택 PR)
        → 진단툴 런타임/엔진 무변경 (동일 스키마 JSON 재생성일 뿐)
```
- `src/diagnosis_git.py`(DiagnosisRepo·dirty·unpushed 감지) 재사용.

### 4.6 미래 훅 (지금 구현 X)
- 지식볼트 → (에이전트) → `dx_*` 인입 인터페이스 placeholder. DB가 축이라 상·하류 교체에 열려 있음.

---

## 5. 단계별 실행 계획

| 단계 | 내용 | 산출 |
|------|------|------|
| **P1** | `dx_*` 스키마 + 임포터(IND_*/RT_*/catalogs) + taxonomy 브릿지 | schema.sql 확장, `src/store` DAL, seed |
| **P2** | 탭 신설 + 대시보드(커버리지) + 하위산업/프로필/코드 그리드(읽기·편집) | `src/tabs/diagnosis_pack.py` |
| **P3** | 검증 + 리빌드(Export) + diagnosis_git 커밋 | 적용 파이프라인 |
| **P4** | 미리보기(compose 호출) | 진단툴 preview 진입점 |
| **P5(선택)** | Q2~Q5 수치·언어팩(i18n)·엔진 상수 외부화 확장 | 전체 팩 커버 |

---

## 6. 미해결 결정 (Open Decisions)

| # | 결정 | 선택지 | 권장 |
|---|------|--------|------|
| **D-범위** | 1차 범위 | Ch1(IND_*+routing+catalogs)만 vs 전 데이터 | **Ch1 우선**(루프 증명 후 확장) |
| **D-taxonomy** | 하위산업 통합 | 단일 정본+브릿지로 통합 vs 현행 병존+점검만 | **단일 정본+브릿지** |
| **D-A 미리보기** | compose 방식 | (a)로직 이식 vs (b)진단툴 호출 | **(b) 호출** |
| **D-B 수치경계** | 엔진 상수(0.85 등) | 외부화해 관리 vs 코드 유지 | 후속(P5) |
| **D-정본코드** | 하위산업 정본 코드계 | 이름형(60) vs A01(74) | **이름형**(엔진·팩 기준), A01은 브릿지 |

---

## 7. 정본 브랜치 / 적용 대상

- **diagnosis-tool**: `origin/v1.5` (9산업 A~I). `main`(3월·8산업)은 폐기.
- **iris-hub**: `origin/feat/hub-rebuild` (본 문서 기준). 대상 모듈(diagnosis_*·store·config)은 main과 동일.
- 리빌드 출력은 diagnosis-tool 클론의 작업 브랜치로 커밋(진단툴 런타임 무변경).
