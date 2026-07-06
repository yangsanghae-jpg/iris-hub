# 진단툴 탭 v2 — 설계서 (DB SoT · 팩목록/그리드)

- **상태:** 목업 컨펌 대기 — **구현 금지** (본 문서·Canvas 승인 후 착수)
- **작성:** 2026-07-06 · M5
- **목업:** [diagnosis-tool-tab-v2.canvas.tsx](/Users/iris/.cursor/projects/Users-iris-0Dev/canvases/diagnosis-tool-tab-v2.canvas.tsx)
- **대체 대상:** 현재 `diagnosis_sot.py` (P5 read-only MANIFEST/LINEAGE 뷰)
- **계승:** `DIAGNOSIS_PACK_MGMT_UX_DESIGN.md` 좌목록+우그리드 · `diag-sot/00_MANIFEST` dx_* DB SoT

---

## 0. 재정의 — 5원칙

| # | 원칙 | v2 대응 |
|---|------|---------|
| 1 | **DB 상태를 알 수 있어야** | Zone A: `dx_sot.db` 경로·테이블별 행 수·dirty·import HEAD·동기 상태 항상 표시 |
| 2 | **DB↔실데이터팩 직접 연결** | Zone C1 브릿지: 테이블↔`member_paths` JSON·행↔`json_pointer`·양쪽 hash MATCH/MISMATCH |
| 3 | **요약이 친절해야** | 팩 목록에 **한글명·행 수·소비 챕터**; 그리드에 **「의미」컬럼**(schema glossary) |
| 4 | **목록 | 그리드 분리** | Zone B(좌 260px 팩 목록) · Zone C(우 편집·브릿지) — 한 화면에 섞지 않음 |
| 5 | **필수필드 잠금** | PK·FK·`source_json_pointer`·`pack_id` 등 = `lock` · 값 필드만 `edit` |

---

## 1. 화면 구조 (목업 Zone)

```
┌─ Zone A: DB 상태 (전폭) ─────────────────────────────────────────────┐
│ dx_sot.db · 39팩 · dirty 2 · import e8bd8aa                            │
│ [dx_industry 9] [dx_sub_industry 74] [dx_q_matrix 444 dirty] …           │
├─ Zone B: 팩 목록 ────┬─ Zone C: 선택 팩 ───────────────────────────────┤
│ 260px               │ C1 DB↔런타임 브릿지 (hash·경로·매핑규칙)          │
│ 한글명 + pack_id    │ C2 편집 그리드 (권한|필드|의미|값|DB컬럼|반영경로) │
│ 행수 · dirty pill   │ [되돌리기][저장][검증][런타임 JSON 재생성]         │
└─────────────────────┴──────────────────────────────────────────────────┘
```

### Zone A — DB 상태

- **소스:** `iris-data/diagnosis/dx_sot.db` (또는 `IRIS_DATA_ROOT/diagnosis/`)
- **표시:** `dx_*` 테이블별 `COUNT(*)` · 마지막 import git HEAD · 팩 단위 dirty 행 수
- **동기:** `dx_pack_manifest` 기준 런타임 JSON 존재·hash 대조 요약 (미동기 팩 수)

### Zone B — 팩 목록

- **데이터:** `dx_pack_manifest` + MANIFEST 메타(한글 display_name은 glossary 또는 `content_kind` 매핑)
- **행 구성:** `한글명` · `pack_id` · `N행` · `consumer` · status pill (`synced` / `dirty` / `archived`)
- **동작:** 클릭 시 Zone C만 교체 (목록은 고정)

### Zone C1 — DB↔런타임 브릿지

선택 팩마다 **1:1 연결을 명시**:

| 항목 | 예 (q3_scale_profile) |
|------|------------------------|
| DB 테이블 | `dx_q_matrix` |
| 런타임 JSON | `server/data/step3/scale_profile_v3.json` |
| 매핑 | `sub_code` + `field_path` → JSON pointer |
| hash | DB export hash vs disk file hash → **MATCH / MISMATCH** |

수정 후 **「런타임 JSON 재생성」** → hash 재계산 → MATCH면 반영 확인 완료.

### Zone C2 — 편집 그리드

- **전개:** 팩 schema에 따른 행 펼침 (M5 목업의 sub-grid 규칙 계승 — scalar/dict/list별 테이블)
- **컬럼:** `권한` · `필드` · **`의미`(한글)** · `값` · `DB컬럼` · **`반영 경로`**(JSON pointer)
- **권한:**
  - `lock` — PK, FK, `source_json_pointer`, 코드 식별자, archived 팩 전체
  - `edit` — `value_num`, `value_text`, `label_*` 등 비즈니스 값
- **UI:** Streamlit `st.data_editor` + `disabled` 컬럼 또는 column_config

---

## 2. 데이터 계약

### SoT (편집)

| 계층 | 위치 | 역할 |
|------|------|------|
| **편집 SoT** | iris-hub `dx_*` SQLite | 사용자가 수정·저장하는 유일한 쓰기 대상 |
| **런타임** | diagnosis-tool `server/data/**` | export·byte-0 재생성 **결과물** (탭에서 직접 편집 금지) |
| **추적** | MANIFEST/LINEAGE | 팩 메타·lineage (read-only 보조, Zone A/B 목록 소스) |

### 파이프라인 (버튼)

```
[저장]        → dx_* UPDATE (트랜잭션)
[검증]        → FK·범위·커버리지·issue rollup
[런타임 재생성] → dx export → diagnosis-tool JSON · hash 비교
```

P4 byte-0·`DIAG_SOT_DEV` 규율 유지 — prod 직접 쓰기 없음.

---

## 3. 현재(P5)와 차이

| | P5 (현재) | v2 (목표) |
|---|-----------|-----------|
| 소비 | MANIFEST/LINEAGE JSON | **dx_* DB** + manifest 메타 |
| 레이아웃 | KPI + dataframe + selectbox lineage | **목록 \| 브릿지+그리드** |
| 라벨 | `coverage_status`, `pack_id` | **한글 팩명·필드 의미** |
| 편집 | read-only | **값만 편집, 식별자 lock** |
| 반영 확인 | lineage 텍스트 | **hash MATCH + pointer** |

P5 `diagnosis_sot.py`는 v2 구현 후 **교체**(archive 또는 삭제).

---

## 4. 필드 잠금 규칙 (초안)

| 유형 | 예 | 이유 |
|------|-----|------|
| PK | `sub_code`, `field_path`, `lineage_id` | 행 식별 — 변경 시 FK 붕괴 |
| FK | `parent_code`, `industry_code` | spine 참조 |
| provenance | `source_json_pointer`, `source_ref` | 추적·byte-0 재현 |
| manifest | `pack_id`, `phase_introduced` | 팩 정체성 |
| **editable** | `weight`, `value_text`, `label_ko`, … | 비즈니스 값 |

schema별 lock 목록은 `dx_*` DDL + P1_SCHEMA 승인본에서 **팩 타입별 JSON**으로 관리.

---

## 5. 구현 단계 (컨펌 후)

| 단계 | 내용 |
|------|------|
| S0 | `dx_sot.db` 스키마·import 경로 확정 (diagnosis-tool HEAD 연동) |
| S1 | Zone A DB 상태 패널 |
| S2 | Zone B 팩 목록 (glossary) |
| S3 | Zone C1 브릿지 + hash |
| S4 | Zone C2 그리드 + lock + 저장 |
| S5 | 검증·export·sync-iris-hub |

---

## 6. Gatekeeper / 사용자 컨펌 체크리스트

- [ ] Zone 분리(목록 vs 그리드) 승인
- [ ] DB 상태 표시 범위(테이블 목록·dirty·hash) 승인
- [ ] 필드 잠금 정책 승인
- [ ] 첫 구현 팩 범위 (예: Ch1 3팩 vs Q3 1팩 파일럿)
- [ ] P5 MANIFEST 뷰 완전 폐기 vs 「고급·lineage」탭 잔존 여부

---

## 7. 관련 문서

- 목업 v1 (그리드 전개): `DIAGNOSIS_PACK_MGMT_UX_DESIGN.md` · `diagnosis-pack-mgmt-ux-v1.canvas.tsx`
- DIAG-SOT: `docs/design/diag-sot/00_MANIFEST.md` · `P1_SPEC.md` (dx_* DDL)
- 폐기 이력: `M5_적용_iris-hub_진단툴탭_폐기_2026-07-06.md` (구 마이그레이션 탭)
