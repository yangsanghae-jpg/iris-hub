# 진단툴 관리 탭 UX 설계 — 팩 목록 + 그리드 편집 (사용자 확정 v1)

- **작성일:** 2026-07-05
- **지위:** `DIAGNOSIS_PACK_MGMT_TAB_DESIGN.md`(Claude v0.1)의 **화면(UX) 정본**. 백엔드·DB·리빌드는 Claude 설계 **그대로 인정**.
- **대상:** `src/tabs/diagnosis_pack.py` (신규·개편)
- **선행:** `DIAGNOSIS_PACK_MGMT_TAB_DESIGN.md` §0·§3·§4 (dx_* SoT, 세 팩, st.data_editor)

---

## 0. 한 줄

> **진단툴 v1.5 팩을 로드 → 왼쪽에서 팩 선택 → 가운데 그리드로 확인·수정 → 저장 → 진단툴에 적용.**

Claude가 정의한 `dx_*` DB·임포트·검증·리빌드 파이프라인은 유지하고, **화면만** 「섹션 내비 7개」가 아니라 **「팩 리스트 + 그리드」** 로 바꾼다.

---

## 1. 사용자 요구 (7단계 → UX 매핑)

| # | 사용자 요구 | UX 대응 |
|---|-------------|---------|
| 1 | 현재 디자인팩을 로딩해서 시작 | 탭 진입 시 **자동 임포트**(clone→DB). 없으면 `[팩 로드]` CTA |
| 2 | 왼쪽에 로딩된 **팩 리스트** | **좌 레일 240px** — 트리/플랫 목록 |
| 3 | 팩 선택 → 내용 출력 | **우측 메인** — 선택 팩 헤더 + 그리드 |
| 4 | **Grid** 필요 (기존 설계 토론) | `st.data_editor` — §4 그리드 스펙 계승 |
| 5 | 그리드에서 **확인·수정** | 읽기/편집 동일 surface, 변경 셀 하이라이트 |
| 6 | 완료 후 **저장** | `[저장]` → dx_* persist (dirty 해제) |
| 7 | **진단툴 데이터팩에 적용** | `[적용]` → 검증→리빌드→clone JSON (+ git commit) |

---

## 2. Claude 구조 인정 범위 (변경 없음)

| 계층 | 유지 |
|------|------|
| SoT | iris-hub `dx_*` SQLite (중간축) |
| 세 팩 | 🔢 수치 · 📦 내용 · 🌐 언어 (필드 차원) |
| 임포트 | diagnosis-tool v1.5 clone → JSON→DB |
| 검증 | 커버리지·참조·브릿지 (§4.3) |
| 미리보기 | compose 호출 (§4.4, P4) |
| 적용 | DB→IND_*/RT_*/catalogs 리빌드 (§4.5) |

**폐기 (Claude §2.2 UI):** 좌측 「대시보드·하위산업·프로필…」 **기능 섹션 내비 7개**.

---

## 3. 화면 골격 (확정 목업 v1)

### 3.1 레이아웃

```
┌ hub_pagebar ───────────────────────────────────────────────────────────────┐
│ 진단툴 관리 · Pack SoT          v1.5 · abc1234 · dirty ●        [Ready/Saved] │
├──────────────────────────────────────────────────────────────────────────────┤
│ .flow-row.pipeline (상태 요약, 4카드)                                        │
│  ① 로드됨 24팩  ② 선택 IND_A  ③ 미저장 3셀  ④ 검증 대기                      │
├──────────────┬───────────────────────────────────────────────────────────────┤
│ 좌: 팩 목록   │ 우: 편집 영역                                                  │
│ 240px        │                                                               │
│ [🔍 필터]    │ ┌ 선택 팩 헤더 ─────────────────────────────────────────────┐  │
│              │ │ IND_A · 산업 A · industry_packs/IND_A.json · 142행      │  │
│ ▼ Ch1 산업   │ │ [🔢 수치][📦 내용][🌐 언어]  ← 그리드 열 필터 (세 팩)    │  │
│   IND_A ●    │ └───────────────────────────────────────────────────────────┘  │
│   IND_B      │ hub_section("프로필 가중치")                                   │
│   …          │ ┌ Grid (st.data_editor) ──────────────────────────────────┐  │
│ ▼ 라우팅     │ │ block │ code ▼      │ weight │ Δ      │ label_ko (읽기) │  │
│   RT_PROJECT │ │ mvp   │ MVP_PROG… │ 0.90   │        │ 진도监控        │  │
│   …          │ │ mvp   │ MVP_SUPPLY│ 0.60   │ ● +0.1 │ 供应协同        │  │
│ ▼ 카탈로그   │ │ …     │           │        │        │                 │  │
│   mvp_codes  │ └─────────────────────────────────────────────────────────┘  │
│   …          │ [+ 행]  경고 2 · 오류 0                                        │
│              │ ───────────────────────────────────────────────────────────  │
│ [팩 로드]    │ [저장]  [검증]  [미리보기]  [진단툴에 적용 ▶]                  │
└──────────────┴───────────────────────────────────────────────────────────────┘
```

### 3.2 hub UX 문법 (다른 탭과 동일)

| 요소 | 적용 |
|------|------|
| `hub_pagebar()` | 타이틀 · Pack SoT · git/dirty pill |
| `.flow-row.pipeline` | 로드/선택/미저장/검증 4카드 (PPT·흐름 탭과 동일 문법) |
| `hub_section()` | 그리드 위 소제목 (예: 「프로필 가중치」「코드 카탈로그」) |
| `hub_ui.css` | 좌 레일·그리드 툴바·dirty 하이라이트 |

---

## 4. 좌 레일 — 팩 목록

### 4.1 목록 구성 (로드 결과)

임포트 후 **편집 단위(팩)** 를 트리로 표시. 1차 범위(Ch1) 기준:

| 그룹 | 항목 | 개수 |
|------|------|------|
| Ch1 산업팩 | `IND_A` … `IND_I` | 9 |
| 라우팅팩 | `RT_FAB`, `RT_BATCH`, `RT_PROJECT`, `RT_JOBSHOP`, `RT_MIX` | 5 |
| 코드 카탈로그 | `mvp_codes`, `module_codes`, `direction_codes`, … | 11 |
| 메타 | `ch1_code_alias`, `sub_industry_aliases`, `scoring_policy` | 3 |

후속(P5): `step2`/`step3`/`q5` 등 step 수치팩 그룹 추가.

### 4.2 행 표시

```
IND_A          A · 142행   ● dirty
RT_PROJECT     routing · 38행
mvp_codes      catalog · 86행
```

- **●** = 해당 팩에 미저장 변경 있음
- **🔴** = 검증 오류 (커버리지·참조)
- 클릭 → `session_state.dx_selected_pack = "IND_A"` → 우측 그리드 갱신

### 4.3 `[팩 로드]`

- diagnosis-tool clone(`DIAGNOSIS_TOOL_GIT`)에서 **전체 Ch1 재임포트**
- 기존 `dx_import` 이력 + 확인( dirty 시 경고)
- 로드 완료 → 좌 목록 refresh, 첫 팩 또는 이전 선택 유지

---

## 5. 우측 — 선택 팩 + 그리드

### 5.1 팩 헤더

| 필드 | 예 |
|------|-----|
| pack_id | `IND_A` |
| 산업 | A (반도체) |
| 원본 파일 | `server/data/ch1/industry_packs/IND_A.json` |
| 행 수 | 프로필 142 / 서브산업 12 |
| import_at | 2026-07-04 12:30 |

### 5.2 세 팩 필터 (열 그룹 토글)

그리드 **한 surface**에서 열 가시성만 전환 (탭 분할 아님):

| 필터 | 보이는 열 | 팩 차원 |
|------|-----------|---------|
| 🔢 수치 | `weight`, `boost`, `value`, `metric_*` | 수치팩 |
| 📦 내용 | `code`, `block`, `status`, `routing_code`, `canon_code`, `bridge_*` | 내용팩 |
| 🌐 언어 | `label_ko`, `label_zh`, `label_en`, `explain`, `message_theme` | 언어팩 |
| **전체** | 위 열 합침 (기본) | — |

Claude §3.3 테이블 매핑과 1:1.

### 5.3 그리드 스펙 (Claude §4.2 계승 + DECK V3 st.data_editor 선례)

**위젯:** `st.data_editor` (Streamlit 1.50+)

**공통 규칙**

| 규칙 | 내용 |
|------|------|
| code 열 | `dx_code`(active) **SelectboxColumn** — 라벨(ko) 표시, 미등록 코드 입력 차단 |
| weight/value | `NumberColumn` 0.0~1.0 (또는 boost 범위) |
| status | `SelectboxColumn` active / deprecated |
| lang 열 | `TextColumn`, 다국어 병렬 열 |
| 읽기 전용 | import 메타, `Δ`(default 대비), compose preview 결과 |
| 변경 표시 | 수정 셀 → `.dx-cell-dirty` 배경 (hub_ui.css) |
| 행 추가 | `[+ 행]` — 팩 종류별 스�affold (프로필 item, catalog code 등) |

**팩별 그리드 뷰 (대표)**

#### IND_* — 프로필 가중치 (수치+내용)

| block | code ↓ | weight | Δ vs default | label_ko (RO) |
|-------|--------|--------|--------------|---------------|
| mvp | MVP_PROGRESS_MON | 0.90 | | 진도监控 |
| mvp | MVP_SUPPLY_SYNC | 0.60 | ● +0.10 | 供应协同 |

- `scope` 선택: `[default ▼]` / `[aerospace_equipment ▼]` — sub 프로필은 default 대비 ×0.25 의미 표시

#### IND_* — 하위산업·브릿지 (내용)

| canon_code | industry | A01_bridge | step5_bridge | SUB_bridge |
|------------|----------|------------|--------------|------------|
| aerospace_equipment | A | A01 | (empty)🔴 | SUB_A_01 |

#### catalog — 코드+언어

| kind | code | status | label_ko | label_zh | label_en |
|------|------|--------|----------|----------|--------|
| mvp | MVP_BATCH_TRACE | active | 배치추적 | 批次追溯 | Batch Trace |

#### RT_* — 라우팅 효과 (수치)

| kind | block | code | value |
|------|-------|------|-------|
| overlay | mvp | MVP_X | 0.05 |
| adjustment | modules | MOD_Y | 0.15 |

**커버리지 하이라이트 (Claude §1.3)**

- Q5_MGMT 누락 행 → 행 전체 `.dx-row-gap` (앰ber border)
- 좌 레일 `IND_A` 옆 🔴 뱃지 — 산업 단위 요약

---

## 6. 액션 바 (하단 고정)

| 버튼 | 동작 | 게이트 |
|------|------|--------|
| **저장** | 현재 팩(또는 전체 dirty) → `dx_*` UPDATE | 없음 |
| **검증** | §4.3 전체 검증, 결과 토스트+패널 | — |
| **미리보기** | 선택 산업·sub·routing으로 compose (§4.4) | 선택 팩이 IND_*일 때 |
| **진단툴에 적용 ▶** | 리빌드→clone JSON→commit | **검증 통과** + dirty 없음(또는 저장 후) |

**적용 확인 모달 (개념)**

```
적용 대상: ~/0Dev/diagnosis-tool (v1.5)
변경 파일: IND_A.json, RT_PROJECT.json, … (7)
overlay 모드: 변경분만 diff
[취소] [적용并 커밋]
```

---

## 7. 워크플로 (상태机)

```
[탭 진입]
    → clone 있음? ─no→ empty state + [팩 로드]
    → yes → auto import(멱등) → 팩 목록 표시
[팩 선택] → 그리드 로드 (dx query)
[셀 수정] → session dirty + 셀 highlight
[저장] → DB write → dirty clear (해당 팩)
[검증] → issues[] → 좌 레일 🔴 / 그리드 행 highlight
[적용] → validate OK → rebuild → git commit → success toast
```

---

## 8. Claude §2.3 섹션 → 본 UX 매핑

| Claude 섹션 | 본 UX에서의 위치 |
|-------------|------------------|
| (a) 대시보드 커버리지 | **flow 카드 ④** + IND_* 선택 시 그리드 gap 행 highlight. 별도 「대시보드」 메뉴 없음 |
| (b) 하위산업 | `IND_*` 팩 → 내용 필터 그리드 뷰 |
| (c) 프로필 | `IND_*` 팩 → 수치 필터 + scope selector |
| (d) 코드 카탈로그 | `mvp_codes` 등 카탈로그 팩 선택 |
| (e) 미리보기 | `[미리보기]` 버튼 → 우측 하단 패널 또는 slide-over |
| (f) 적용/이력 | `[진단툴에 적용]` + pagebar pill (commit hash) |

---

## 9. 데이터 바인딩 (구현 시)

```python
# 좌 레일
dx.list_packs() -> [{id, group, label, rows, dirty, errors}]

# 그리드
dx.grid_for_pack(pack_id, view="numeric"|"content"|"lang"|"all") -> DataFrame
dx.save_pack(pack_id, edited_df) -> SaveResult

# 액션
dx_import.import_from_repo(repo)
dx_validate.validate() -> ValidationResult
dx_preview.compose(industry, sub, routing) -> ComposeResult
dx_apply.apply_rebuild(mode="overlay") -> ApplyResult
```

탭은 store/dx DAL만 호출 — Claude §3.1 원칙 유지.

---

## 10. 1차 범위·열린 결정

| 항목 | v1 결정 |
|------|---------|
| 팩 목록 | Ch1 (IND+RT+catalogs) 만 |
| 그리드 | 팩 1개 = 그리드 1개 (복수 서브그리드는 scope/kind 토글) |
| 저장 단위 | **현재 팩** 저장 (전체 저장은 후속) |
| 미리보기 | IND_* 선택 시만 |
| 대시보드 독립 화면 | **없음** — 커버리지는 gap highlight로 흡수 |

---

## 11. 검증 (설계 완료 기준)

- [x] 사용자 7요구 전부 매핑
- [x] Claude 백엔드/세 팩/dx_* 유지
- [x] hub_pagebar + flow pipeline + hub_section 문법
- [x] 그리드 §4.2 스펙 + st.data_editor 선례
- [x] 섹션 내비 7개 → **팩 목록**으로 대체

→ **목업 작성 진행 (§12).**

---

## 12. UX 목업

별도 Canvas: `diagnosis-pack-mgmt-ux-v1.canvas.tsx` — §3.1 레이아웃 시각화.
