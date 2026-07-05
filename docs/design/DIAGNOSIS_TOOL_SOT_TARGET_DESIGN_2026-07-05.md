# 진단툴 진실원(SoT) 목표 설계 — 운영 시나리오 기반

- **작성일:** 2026-07-05
- **상태:** 설계 제안 (운영 시나리오 검증 완료 · 아키텍처 결정 2건 잠금 · 구현 착수 전)
- **성격:** 진단툴 시스템 **자체**를 iris-hub 진실원 중심으로 재편하는 목표 설계. 2026-06-29 마이그레이션 설계가 놓친 **"내용이 무엇인지"** 를 실물 검증으로 채운 판.
- **선행 검증:** 운영 흐름(6스텝→ch0~ch6 조립)·3축·요구5개 모두 코드/데이터로 실측.
- **폐기 대체:** [`DIAGNOSIS_TOOL_DATA_TARGET_ARCH_2026-07-05.md`](./DIAGNOSIS_TOOL_DATA_TARGET_ARCH_2026-07-05.md) (파일 종합만 한 부결안)
- **참고:** 진단툴 내부 [2026-06-29 재설계 Rev2](../../../diagnosis-tool/docs/data_restructure/diagnosis_tool_data_restructure_design_M5_2026-06-29.md) — 단, SoT를 iris-hub로 이전하므로 그 `data/src` 위치 전제는 본 설계가 대체.

---

## 0. 전제 (사장 확정)

| # | 결정 | 값 |
|---|------|-----|
| D1 | **SoT 소유** | **iris-hub가 정본 소유**. 진단툴 `server/`·`client/data`는 **sync 생성물**(수기편집 금지) |
| D2 | **엔진 범위** | 원칙 **부분 보완**(A1/A2 세분화는 어차피 필요). 새 구조가 요구하면 **개편 허용** |
| D3 | **언어 기본** | **ko 기본** → 미작성 언어는 **ko fallback** → 점진 추가 시 노출 (현 `DEFAULT_LANG=zh` **뒤집음**) |

---

## 0.5 설계 제1 동인 — 추적성(edit → reflect)

> 이 프로젝트가 푸는 **진짜 문제**는 "편집 UI 부재"가 아니라 **추적성 부재**다.

현재 유지보수의 최대 고통: **현 데이터팩이 직관적이지 않아, "어디를 고치면 어디에 반영되는지(안 되는지)"가 불명확**하다. 같은 개념이 3홈·3변종·생성물/수기 혼재라, 한 곳 고쳐도 다른 소비자에 반영 안 되거나, 어느 게 정본인지 모른다.

**따라서 성공 기준 = "모든 편집이 반영 경로를 스스로 드러낸다":**

| 요건 | 구현 수단 (본 설계) |
|------|--------------------|
| 정본이 하나임이 자명 | D1 — iris-hub SoT 단일 소유 |
| 편집→팩 경로가 보임 | sync 매핑 (필드 → 팩 path → 소비 챕터엔진) 을 관리 탭에 **lineage로 표시** |
| 반영 여부가 확실 | 팩별 shape 타깃 + **byte-diff 게이트** (반영 성공/실패가 눈에 보임) |
| 반영 안 되는 것도 명시 | `consumers`/`status` 표기 — "이 팩은 client 전용" 등 |

**관리 탭 요건(추가):** 각 셀/노드에 **"이 값 → 어느 팩 path → 어느 챕터에서 소비"** 를 lineage로 노출. 그리드의 일부 복잡도는 수용하되(사장 확인), **추적성은 타협 없음**.

---

## 1. 검증된 운영 현실 — 데이터는 세 성격이다

진단툴은 파일 모음이 아니라 **조립 파이프라인**이고, 데이터는 세 성격으로 나뉜다. **하나의 획일 구조는 틀렸다.**

| 축 | 성격 | 실물 근거 | 관리 방식 |
|----|------|-----------|-----------|
| **①척추** | 9산업×74세부 **기본키**, 상시 증가(6→8→9…) | 모든 Q팩이 `A01~I08` 키잉 | **성장 우선** registry |
| **②평가매트릭스** | Q1~Q5 세부산업 **평가 수치** | Q2/Q3/Q4 = `framework + subindustry_profiles[74]`; 텍스트=프레임 라벨뿐 | **표/그리드**(언어 경량) |
| **③보고콘텐츠** | A1/A2 **다국어 서술** + 룰엔진 연동 | systems_catalog(zh원본)·mgmt(ko)·roi(ko+zh) 제각각 | **콘텐츠 팩**(언어 1급) |

> 핵심: ②는 숫자 매트릭스라 M5 목업의 "그리드"가 맞고 언어 분리 불필요. ③은 다국어 콘텐츠라 언어 정책이 핵심. **둘을 같은 틀로 관리하려던 게 그동안의 혼선.**

---

## 2. 목표 아키텍처 — iris-hub SoT 3계층 + sync

```
┌─────────────────── iris-hub (진실원 · 정본 소유) ───────────────────┐
│  ① SPINE   registry: industries / sub_industries  (성장 지점)        │
│  ② MATRIX  eval:     q1..q5 × sub_industry × 수치/레벨               │
│  ③ CONTENT report:   system → module → sub_override  (+ 다국어)      │
│  ─ LABELS  fixed_labels: id → {ko,zh,en,ja}  (Q UX·챕터 고정라벨)    │
│                          ↓  dx_* DB + 관리 탭 편집                    │
└──────────────────────────────┬───────────────────────────────────────┘
                     sync (pack builder, per-pack shape target)
                                ↓ (diff-gated)
        diagnosis-tool/server/data + client/data  (생성물, 수기편집 금지)
                                ↓
                     기존/개편 엔진(compose ch0~ch6) — 무변경 or 부분보완
```

### 2.1 ① SPINE (registry) — 성장 우선 설계

```jsonc
// registry/sub_industries : "세부산업 추가"가 1급 연산
{ "id":"subind/B01", "code":"B01", "parent":"industry/B",
  "label": {"ko":"웨이퍼 Fab","zh":"晶圆厂","en":"","ja":""},
  "added_in":"v9.0", "status":"active" }
```
- 산업/세부 **추가 = registry 한 행 추가**. ②③는 이 id를 참조만 → 74→75 확장이 국소 변경.
- 코드 이중(`A` vs `IND_A`)·파일명 불일치는 registry가 유일 코드원천으로 흡수.

### 2.2 ② MATRIX (Q1~Q5 수치팩) — 통일 스키마 (요구2)

Q2/Q3/Q4가 이미 `framework + subindustry_profiles` 패턴 → **정식화**:
```jsonc
{ "q":"q4", "framework": { /* domains, levels, dictionary — 공유 정의 */ },
  "profiles": {
    "subind/A01": {                      // 세부산업 키 (척추 참조)
      "domains": {                       // ★ Q4 flat 접두(planning_*) → 도메인 정규화(F8)
        "planning":{"importance":5,"weight":0.35,"levels":{"floor":"L2","target":"L3","ceiling":"L4"}},
        "quality":{...}, "equipment_control":{...}, "logistics":{...}
      } } } }
```
- 성격상 **언어 경량**: 값은 숫자·level-id·code-ref. 표시 텍스트는 framework 라벨(→ LABELS로).
- **엔진 무변경 경로:** sync가 현행 `automation_profile_v3.json` **동일 shape로 역생성**(D2 부분보완) → step4 해석기 그대로.

### 2.3 ③ CONTENT (A1/A2 보고팩) — System→Module→Sub-override (요구3)

현재 공백을 채운다: 시스템은 `systems_catalog`에 있으나 **capabilities가 평평한 문자열**이고 **세부산업 특화가 ch2엔 없음**(ch3/6엔 `by_sub_industry` 캐스케이드 존재).

```jsonc
// system (거시): 기존 systems_catalog 정규화
{ "id":"sys/MES", "chapter":"ch2", "domain":"exec",
  "label":{"ko":"MES","zh":"制造执行系统","en":"MES","ja":""},
  "purpose":{"ko":"...","zh":"连接计划与现场执行的中枢..."},   // ko 기본, 기존 zh 보존
  "maturity_ladder":["기초 바코드 report","공정레벨 실행+이상 폐루프","설비/품질/물류 연동","APS/AI 폐루프"],
  "automation_fit":{"exec":["AUTO1","AUTO2","AUTO3","AIPLUS"]},
  "modules":["mod/MES.wip","mod/MES.trace","..."] }

// module (미시 = 기존 capabilities를 엔티티화)
{ "id":"mod/MES.trace", "system":"sys/MES",
  "label":{"ko":"배치/시리얼 추적","zh":"批次/序列号追溯"} }

// sub_override (세부산업 특화 — 요구3 핵심): 같은 품질관리도 74산업이 균일하지 않음
{ "target":"sys/MES" | "mod/MES.trace",
  "sub_industry":"subind/B01",
  "add_keywords":{"ko":["Lot 추적 강화"]},          // 키워드/포인트 "추가" (base 위 델타)
  "add_points":{"ko":["관건 부품 바인딩 필수"]},
  "importance_override": 5 }
```
- **룰엔진 연동(요구3):** 규모/자동화 → 시스템 티어(Pop→MES→G-MES)는 현재 `compose.py`의 `CARD1_TIER_BY_CODE`/`CARD1_SCALE_TO_TIERS` + `maturity_ladder`가 담당. sub_override는 **델타만** 얹어 엔진의 기존 누적 로직과 합류(ch3/6 캐스케이드와 동형).

### 2.4 언어 모델 (요구1·4) — 두 종류로 분리

| 종류 | 대상 | 저장 | 이유 |
|------|------|------|------|
| **고정 라벨** | Q1~Q5 UX, A1/A2 챕터 라벨 | `fixed_labels`: `id→{ko,zh,en,ja}` 카탈로그 | 재사용·UI, 값 아님 (요구1) |
| **콘텐츠** | system.purpose, module.label, sub_override 포인트 | **엔티티 인라인** `{ko,zh,en,ja}` | 관리 탭 그리드에서 **엔티티+언어 동시 편집**(M5 교훈) |

- **resolver 정책(요구4):** `chain = [lang, ko]`. **ko 필수**(CI 강제), 나머지 optional·빈값 허용→ko로 표시. 언어 추가 = 빈칸 채우면 자동 노출.
- 2026-06-29의 "전면 L3 id분리 + zh fallback"과 다른 선택: **고정라벨만 id분리, 콘텐츠는 인라인, fallback=ko**. 관리 탭이 편집 SoT라서 인라인이 편집상 자연스럽고, D3(ko기본)를 따름.

---

## 3. sync — 진실원 → 팩 (요구5, D1)

- iris-hub `dx_*`(정본) → `sync` → 진단툴 `server/data`·`client/data` **생성**. 진단툴 data는 read-only.
- **팩별 shape 타깃**(MANIFEST식):
  - `legacy-shape`: Q2~Q5·ch0/ch1 등 **엔진 무변경** 팩 → 현행 파일명·구조로 역생성, **byte-diff 게이트**.
  - `new-shape`: A1/A2 세분화(요구3) 적용 팩 → 엔진 부분개편과 함께.
- **드리프트 소멸(구 F4):** server/client 둘 다 sync 산출 → 수기 이중관리 제거.

---

## 4. 단계 (저위험 → 고위험, 각 단계 diff 게이트)

| 단계 | 내용 | 엔진 | 게이트 |
|------|------|------|--------|
| **P1** | ① SPINE + ② MATRIX(Q2~Q4)를 iris-hub SoT로, **legacy-shape sync** | 무변경 | 생성팩 byte-diff 0, 진단 회귀 |
| **P2** | fixed_labels 통합(요구1) + **resolver ko기본**(요구4·D3) | 무변경~경미 | 4언어 키 동일, ko fallback 스냅샷 |
| **P3** | ③ CONTENT 모델(요구3): system/module/sub_override, ko-master 콘텐츠 | **부분개편**(A1/A2) | 챕터 HTML 스냅샷, ch2 세부산업 델타 검증 |
| **P4** | Q5·잔여 보고팩 이관 + legacy `_archive` 격리 | 정리 | MANIFEST live=로더 100% |

- **P1이 SoT→sync 루프를 저위험으로 증명**(엔진 안 건드리고 Q매트릭스만). 여기 통과가 전체 전제.
- 각 단계 전까지 진단툴은 **현행 그대로 가동**(무중단).

---

## 5. 미결 / 다음 확인

- [ ] ③ sub_override **입도**: (system×sub) 단위인지 (module×sub)까지 내려가는지 — P3 착수 시 실데이터로 범위 산정
- [ ] 룰엔진 Pop→MES→G-MES 매핑을 **데이터로 외부화**할지(현 `compose.py` 하드코딩 dict 잔존) vs 코드 유지
- [ ] iris-hub `dx_*` 스키마를 본 3계층에 맞춰 확장 (관리 탭 구현과 연동)
- [ ] fixed_labels vs 기존 `client/i18n` 경계 (UI크롬 vs 진단라벨)
- [ ] Q1 정체(taxonomy=산업선택) — ②에 포함 여부

## 부록. 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-07-05 | 초판 — 운영검증 기반. 3축·요구5·결정3. 폐기된 파일종합안 대체 |
