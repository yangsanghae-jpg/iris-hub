# 진단툴 관리 탭 — 목업 탐색 보고서

- **작성일:** 2026-07-05
- **작성:** M5 (iris-hub · 진단툴 관리 탭 설계)
- **범위:** 목업 제작 과정에서 도출된 UX·데이터팩 현실 · **데이터팩 구조 재설계는 범위 외**
- **관련 문서**
  - UX 정본: [`DIAGNOSIS_PACK_MGMT_UX_DESIGN.md`](./DIAGNOSIS_PACK_MGMT_UX_DESIGN.md)
  - 데이터 구조 평가: [`DIAGNOSIS_TOOL_DATA_STRUCTURE_EVAL_2026-07-05.md`](./DIAGNOSIS_TOOL_DATA_STRUCTURE_EVAL_2026-07-05.md) — §5 권고는 현재 렌더러-only(옵션 A) 전제; 방향 결정 보류 중
  - 백엔드(Claude): `origin/claude/diagnostic-tool-pack-maintenance-x5gnem` — `docs/design/DIAGNOSIS_PACK_MGMT_TAB_DESIGN.md`
  - Q4 스키마: `diagnosis-tool/docs/by_step/data/step4_automation_profile_v3_schema.md`
- **목업 산출물:** Cursor Canvas [`diagnosis-pack-mgmt-ux-v1.canvas.tsx`](/Users/iris/.cursor/projects/Users-iris-0Dev/canvases/diagnosis-pack-mgmt-ux-v1.canvas.tsx) (최종: 데이터 그리드版)

---

## 0. Executive Summary

iris-hub **「진단툴 관리」** 탭을 설계·목업하는 과정에서, **「그리드 한 장으로 팩을 본다」는 가정이 진단툴 v1.5 데이터팩 현실과 맞지 않음**이 확인되었다.

| 핵심 발견 | 내용 |
|-----------|------|
| **팩 ≠ 엑셀 한 시트** | 단일 JSON 파일 안에 메타·프레임워크·용어집·74 sub 프로필·매핑 등 **여러 영역이 중첩** |
| **수치·내용·언어 혼재** | sub 1개(예: A01)만 26필드 — scalar / dict / list / 4언어가 **한 객체에 공존** |
| **그리드는 가능, 전제 필요** | flat 2D sheet 비현실 → **파일 트리 → 노드 선택 → sub-grid 전개 규칙** 전제 |
| **JSON 노출 ≠ 관리 UI** | `JSON.stringify`·원문 블록은 설계 검토용일 뿐, **운영 UI는 데이터 값만** 표시 |
| **Claude 백엔드 유지** | `dx_*` SoT·임포트·리빌드 파이프라인은 그대로; **화면만** 팩 목록+그리드 |

---

## 1. 목업 버전 이력 및 차이

### 1.1 버전 개요

| 버전 | 명칭 | 형태 | 데이터 출처 | 결과 |
|------|------|------|-------------|------|
| **M0** | Claude §2.2 UI | 좌측 **기능 섹션 7개** (대시보드·프로필·…) | feature branch 설계 | **기각** — 사용자 구상(팩 리스트)과 불일치 |
| **M1** | UX 설계 v1 | 좌 **팩 리스트** + 우 **그리드** (개념) | 설계 문서 | UX 방향 **확정** (7요구 매핑) |
| **M2** | Ch1 IND_A 목업 | IND_A 4행 weight 그리드 | `IND_A_project_special.json` **일부만** | **비현실** — 파일명·필드 구조 단순화 |
| **M3** | Q4 수치팩 목업 | 74 sub + weights/rec **4행 요약** | `automation_profile_v3.json` **일부만** | **오해 유발** — 「한 파일=4행」처럼 보임 |
| **M4** | 실제 파일 · 원문 | 트리 + **JSON 원문** + field/type/**raw JSON** | 파일 **그대로** | **기각** — 코드 노출; 그리드 목적과 상충 |
| **M5** | 실제 파일 · **데이터 그리드** | 트리 + **sub-grid 9개** (값만) | 파일 **그대로 load·전개** | **현재 정본 목업** |

### 1.2 버전별 상세

#### M0 — Claude 기능 섹션 내비 (기각)

```
좌: 대시보드 | 하위산업 | 프로필 | 라우팅 | 코드 | 미리보기 | 적용
우: 선택 섹션의 그리드
```

- **문제:** 사용자 요구는 「로딩된 **팩** 리스트」이지 「기능 메뉴」가 아님.
- **교훈:** iris-hub 탭은 **파일/팩 단위 탐색**이 먼저.

#### M1 — UX 설계 v1 (문서 확정)

- 사용자 7단계(로드→팩 목록→선택→그리드→수정→저장→적용) 매핑.
- `hub_pagebar` + flow pipeline + `st.data_editor` 문법.
- **한계:** Ch1 IND_* 가정; Q4 단일 대형 JSON 미검증.

#### M2 — Ch1 IND_A (부분 실데이터)

| 항목 | 목업 | 실제 |
|------|------|------|
| 파일명 | `IND_A.json` | `IND_A_project_special.json` |
| 그리드 | mvp weight 4~9행 | `default_profile` + `sub_profiles` + 12 `sub_industries` |
| 좌측 | 24팩 등 | Ch1 산업 9 + routing 5 + catalog 11 (별도 파일) |

- **교훈:** Ch1은 **파일 9개**; sub 1개 객체가 아님.

#### M3 — Q4 automation_profile (요약 과다)

- `subindustry_profiles` 74개 중 **weights / recommended_levels 4행**만 강조.
- 사용자 질문: 「**한 파일의 실제 모습**이냐?」→ **아니오** (전체의 ~5% 필드만).

#### M4 — 원문 + stringify 그리드 (기각)

- `subindustry_profiles.A01` JSON 113줄 **코드 블록** 노출.
- 26행 그리드 value = `JSON.stringify` blob.
- 사용자: 「**데이터만** 나와야 한다. 그래서 grid를 쓰는 것.」
- **교훈:** 설계 검토용 raw view ≠ 운영 UI.

#### M5 — 데이터 그리드 (정본 목업)

**전개 규칙 (파일 구조 변경 없음):**

| JSON 형태 | 그리드 표현 |
|-----------|-------------|
| scalar (str/int) | field / value 1행 |
| dict (고정키, 4언어) | lang / text 또는 area / weight |
| dict (`*_levels`) | tier / level (minimum_floor, recommended_target, …) |
| list | # / item 행 나열 |
| nested (term_override) | lang / terms (쉼표 연결) |

A01 기준 **9개 sub-grid**: 기본필드, label, weights+recommended, term_override, planning·quality·equipment·logistics 블록.

---

## 2. 목업 과정에서 도출된 설계 포인트

### 2.1 「한 파일」의 실체

Q4 정본 `automation_profile_v3.json` (254 KB, v3.1) **한 파일** 안:

```
metadata
domains                    ← 4영역 정의 (언어)
level_framework            ← 4×L1~L5 공통 프레임 (내용+언어)
evidence_dictionary        ← 47 codes
factor_profiles            ← 10개 용어 프로파일
subindustry_profiles       ← 74 keys (A01…I08)
domain_mapping_9           ← Step5 9도메인 가중
```

**엑셀 비유:** 통합 통합문서 1개에 **메타·코드북·74 시트분량·매핑표**가 들어 있음.  
**한 시트 = sub 1개**도 26필드·9 sub-grid 필요.

### 2.2 sub 1개(A01) 필드 구성 (실측)

| 구분 | 예시 필드 | 성격 |
|------|-----------|------|
| 🔢 수치 | `weights`, `recommended_levels`, `*_importance` | 1~5, L1~L5 |
| 📦 내용 | `*_profile`, `*_levels`, `*_objects`, `planning_constraints` | 구조·티어·객체 목록 |
| 🌐 언어 | `label`, `term_override` | ko/zh/en/ja |

→ Claude 설계의 **세 팩(수치/내용/언어)** 이 **한 sub 객체 안에 혼재**.  
iris-hub UI의 「수치/내용/언어 필터」는 **열 가시성**이지 파일 분리가 아님.

### 2.3 그리드 적합성 (구조 재설계 없이)

| 질문 | 답 |
|------|-----|
| flat 2D grid 1장으로 74 sub? | **부적합** — 수천 셀, nested 편집 불가 |
| sub 1개 편집? | **가능** — sub-grid 9~10개 + 스크롤 |
| 파일 전체 탐색? | **트리 필수** — top-level 7 + 74 keys |
| `st.data_editor` 단일 위젯? | scalar·단순 표는 OK; list/dict는 **전개 규칙** 또는 nested editor |

### 2.4 iris-hub 탭 UX 함의 (M1 + M5 결합)

1. **좌 레일:** 로드된 **파일/팩 트리** (JSON path 기준 — `step4/automation_profile_v3.json` → `subindustry_profiles` → A01)
2. **우측:** 선택 노드에 **전개 규칙 적용 그리드** (코드·JSON 원문 **미노출**)
3. **저장/적용:** Claude `dx_*` SoT 경유 (JSON 직접 편집 vs DB 리빌드는 구현 단계)
4. **범위 외:** v1.5 팩 JSON 스키마 통합·분할 **재설계**

---

## 3. 진단툴 v1.5 데이터팩 현황

> 기준 경로: `diagnosis-tool/server/data/` (client 동기본 존재하는 경우 `client/data/`)

### 3.1 Ch1 — 산업·라우팅·카탈로그

| 그룹 | 경로 | 개수 | 비고 |
|------|------|------|------|
| 산업팩 | `ch1/industry_packs/IND_*.json` | **9** | 파일명 `IND_A_project_special.json` 등 (코드≠파일명) |
| 라우팅팩 | `ch1/routing_packs/RT_*.json` | **5** | RT_BATCH, RT_JOBSHOP, RT_LINE, RT_PROJECT, RT_REENTRANT |
| 코드 카탈로그 | `ch1/catalogs/*.json` | **11** | mvp_codes, module_codes, … |

**IND_A 예 (`IND_A_project_special.json`):**

- 12 `sub_industries`, 8 `sub_profiles` (의료 4 sub **profile gap** — 실데이터)
- `default_profile`: mvp_functions + core_modules (block·code·weight)
- Ch1 UI: Step1 산업 A → `load_ch1_industry_pack("IND_A")`

### 3.2 Step4 — Q4 자동화 수준 (목업 검증 주력)

| 항목 | 값 |
|------|-----|
| 파일 | `step4/automation_profile_v3.json` |
| 크기 | **254 KB** |
| 버전 | **3.1** (2026-06-25) |
| sub | **74** (`subindustry_profiles`, A01~I08) |
| 영역 | planning, quality, equipment_control, logistics |
| 레벨 | L1~L5 |
| 런타임 | `http://localhost:3001/data/step4/automation_profile_v3.json` |
| UI | `client/src/ui/q4_taxonomy_v3.js`, `q4_levels/index.js` |

**역할:** Q4에서 고객 **현재 자동화 수준** 선택; `recommended_levels`·`weights`는 **힌트·해석** (미리채움 아님).

### 3.3 기타 Step 팩 (참고 — 이번 목업 미전개)

| Step | 대표 경로 | 비고 |
|------|-----------|------|
| Q1/Q3/Q5 | `client/data/q5/`, `step1_5/`, … | taxonomy·recommendation 등 |
| Step5_2 | `data/step5_2/management_analysis_v3.json` | A1 관리 분석 |
| Ch2~6 | `server/data/ch2/` … | systems, scope, plan, … |

→ 진단툴 전체는 **다수 JSON + 중첩 스키마**; Ch1·Step4만 봐도 「단일 flat sheet」 가정은 성립하지 않음.

### 3.4 iris-hub (Claude) 중간 SoT — 병행 축

| 항목 | 상태 |
|------|------|
| 브랜치 | `claude/diagnostic-tool-pack-maintenance-x5gnem` (M5 main **미병합**) |
| DB | `dx_*` SQLite — JSON 임포트 후 편집·리빌드 |
| 1차 범위 | Ch1 IND+RT+catalogs (P1~P4) |
| 본 보고서 | **JSON 파일 현실** = 임포트 **소스**; UI는 M5 목업(M5) 방향 |

---

## 4. 버전 간 의사결정 타임라인

```
M0 Claude 섹션내비 ──기각──► M1 팩리스트+그리드 (UX 문서)
                                    │
                    M2 IND_A 요약 ──► 실제 파일명·필드 불일치 발견
                                    │
                    M3 Q4 4행 요약 ──► 「한 파일 실제?」 질문
                                    │
                    M4 원문+JSON blob ──► 「코드 노출 말고 데이터」
                                    │
                    M5 데이터 sub-grid ──► 「엑셀 한 장 아님」 확정
```

---

## 5. 권고 (구현 착수 시 — 구조 변경 없음)

1. **목업 정본:** M5 Canvas + 본 보고서 §2.3 전개 규칙.
2. **좌측 네비:** JSON path 트리 (파일 → top-level → sub key).
3. **우측:** 노드 타입별 renderer (scalar grid / lang grid / numeric matrix / list grid).
4. **금지:** JSON 원문 패널을 기본 UI로 두지 않음.
5. **검증 팩:** Step4 `A01` + Ch1 `IND_A` — 유형 다른 **2종**으로 renderer 재사용성 확인.
6. **Claude 파이프라인:** `dx_*` import 시 **nested 필드 보존**; UI 전개는 view layer.

---

## 6. 미착수 / 범위 외

- [ ] iris-hub `diagnosis_pack.py` 구현
- [ ] 74 sub 연속 스크롤 목업
- [ ] 데이터팩 JSON 스키마 분할·통합 **재설계**
- [ ] M2 인계 (`~/Documents/0Dev/docs/system/`) — 본 문서 repo push 후 필요 시 복사

---

## 7. 부록

### A. M5 A01 sub-grid 목록

1. 기본 필드 (scalar 14)
2. label (4언어)
3. weights + recommended_levels (4영역)
4. term_override.planning (4언어)
5. planning (+ constraints, levels)
6. quality (+ objects, levels)
7. equipment_control (+ objects, levels)
8. logistics (+ objects, levels)
9. (접이) level_framework.planning.L1

### B. 참조 커맨드 (M5 실측)

```bash
# Q4 팩 HTTP
curl -s http://localhost:3001/data/step4/automation_profile_v3.json | python3 -c \
  "import json,sys; d=json.load(sys.stdin); print(d['metadata']['subindustry_count'], 'subs')"

# A01 필드 수
python3 -c "import json; d=json.load(open('diagnosis-tool/server/data/step4/automation_profile_v3.json')); print(len(d['subindustry_profiles']['A01']))"
```

### C. 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-07-05 | 초판 — M0~M5 목업 탐색·데이터팩 현황·설계 포인트 |
