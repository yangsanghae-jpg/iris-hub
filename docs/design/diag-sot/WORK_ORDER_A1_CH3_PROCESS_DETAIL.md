# WORK ORDER — A1 Ch3 process_detail_v1 B01~B08 백필 (scope 게이트 포함)

- **발행:** 2026-07-06 (rev.2 — scope 소비측 확인 반영)
- **Gatekeeper:** Claude → **실행: M5 Cursor**
- **대상:** `diagnosis-tool` `server/data/step3/process_detail_v1.json` (+ client mirror)
- **소스 MD:** `diagnosis-tool/docs/by_step/data/a1_ch3_B_process_detail_runtime_datapack_ko_zh_2026-07-06.md` (v0.2)
- **진실원 사본:** `iris-hub/docs/design/diag-sot/sources/a1_ch3_B_process_detail_runtime_datapack_ko_zh_v0_2_2026-07-06.md`
- **변환 스크립트:** `diagnosis-tool/scripts/build_a1_ch3_b_process_detail_backfill.py` (**R1 수정 필수**)

---

## 0. 규율

- `process_detail_v1.json`은 **residual_live**. 수기 복붙 금지 → **결정론적 MD→JSON 스크립트**만 사용.
- **B01~B08 8 slug만** 변경. 타 slug·타 팩·prod 무접촉.
- 후속 **dx화 대상**으로 기록(지금은 실용 백필).

---

## 1. 소비측 scope 처리 (G0 — 선행 확인 완료)

> Cursor는 적용 전 아래 표와 `classifyControlPoints` 구현을 **재확인**하고, 불일치 시 STOP+보고.

### 1.1 렌더 경로

```text
process_detail_v1.json
  → server/assemble/process_analysis.py (passthrough, scope 해석 없음)
  → client/src/ui/a1/1_1_process.js (Ch3 공정분석)
  → client/src/ui/a1/3_process_analysis.js :: classifyControlPoints
  → client/src/ui/a1/pflow/pflow_graph_adapter.js (managedSteps: process_step만)
  → client/src/ui/a1/2_mgmt_analysis.js :: resolveCommonControls (Ch2 관리분석)
```

### 1.2 scope별 실제 동작 (2026-07-06 코드 기준)

| JSON `scope` | `step_refs` | Ch3 공정도·관리점 카드 | Ch3 연결선·managed 배지 | Ch2 관리분석「공통 관리점」 |
|---|---|---|---|---|
| `process_step` | 있음 | ✅ `stepItems` 목록 + 단계 번호 | ✅ | ❌ (mapped 우선) |
| `process_step` | 없음 | ❌ | ❌ | fallback 시 `control_points_ko` |
| `process_common` | 없음 | ❌ | ❌ | ✅ `meta.common` |
| `process_common` | **있음** | ❌ | ❌ | ❌ **조용히 누락** |
| `industry` | 없음 | ❌ | ❌ | ✅ `meta.common` (scope=industry) |
| `industry` | **있음** | ❌ | ❌ (refs 무시) | ✅ **텍스트만 표시** |
| `common` | 없음 | ❌ | ❌ | ❌ **미지원 → 누락** |
| `common` | **있음** | ❌ | ❌ | ❌ **미지원 → 누락** |

**근거 코드**

- `3_process_analysis.js` L40-56: `process_step`+refs만 `stepItems`; `industry`|`process_common`|!refs만 `common`
- `pflow_graph_adapter.js` L17,35: `process_step`만 연결·managedSteps
- `1_1_process.js` L141-143: Ch3 관리점 카드 = `stepItems`만 (`common`/`industry` 미표시)
- `2_mgmt_analysis.js` L211-225: Ch2 = `meta.common`만 (industry 포함)

### 1.3 기존 R1 버그 (스크립트)

현재 `_apply_r1_scope()`:

```python
if step_refs:
    return "process_step"  # ← industry·common까지 강제 승격
```

→ B08 `scope: industry` + refs `[1,9,10]` 이 **process_step으로 뭉개짐** (저자 의도 파괴).  
→ **rev.2에서 R1 교체 필수.**

---

## 2. MD scope 재집계 (G1 — 이 MD 기준)

`control_points_detail_ko` 기준 (**slug당 1회**, ko/zh는 동형):

| slug | code | process_step | common | industry | 합계 |
|------|------|-------------|--------|----------|------|
| logic_foundry | B01 | 6 | **2** | 0 | 8 |
| memory_dram_nand | B02 | 7 | **1** | 0 | 8 |
| analog_mixed | B03 | 6 | **1** | 0 | 7 |
| power_discrete | B04 | 5 | **1** | 0 | 6 |
| optical_sensor | B05 | 6 | 0 | 0 | 6 |
| compound_semi | B06 | 8 | 0 | 0 | 8 |
| assembly_packaging | B07 | 7 | **1** | 0 | 8 |
| test | B08 | 7 | 0 | **1** | 8 |
| **합계** | | **52** | **6** | **1** | **59** |

> ⚠️ 이전 계획의「common 5건」은 **오집계**. 정본은 **common 6 + industry 1**.

### 2.1 common 6건 (교차공정·genealogy)

| slug | step_refs | text 요약 |
|------|-----------|-----------|
| B01 | [1,10] | Lot Route/Split/Merge/Rework/Hold |
| B01 | [1,2,3,4,5,6,8] | Wafer slot/Chamber/Recipe/Reticle genealogy |
| B02 | [1,7,8,9] | Lot-Wafer-Die-Package genealogy |
| B03 | [8,10] | Analog 특성 불량 ↔ Step/Recipe/Mask |
| B04 | [1,5,6,7,9] | Front/Backside Die 승계 |
| B07 | [1,3,10] | Wafer Map Die 좌표 → Package/Test/Ship |

### 2.2 industry 1건

| slug | step_refs | text |
|------|-----------|------|
| B08 | [1,9,10] | 고객별 Test Program·수율·Failure data 접근권한 분리 |

---

## 3. 변환 규칙 (G2 — 확정)

### 3.1 필드 그대로

| 필드 | 처리 |
|------|------|
| `legacy_slug`, `label_ko/zh`, `routing` | MD yaml 그대로 |
| `process_steps_detail_ko/zh` | `{step, note}` 테이블 그대로 |
| `process_steps_detail_en/ja` | `[]` |
| `label_en/ja` | `""` |
| `data_capture_points` | yaml 리스트 |

### 3.2 R1 — `control_points_detail` scope (교체)

```python
def apply_scope(md_scope: str, step_refs: list[int]) -> tuple[str, list[int] | None]:
    s = md_scope.strip().lower()

    # R1a: industry — 절대 process_step으로 승격하지 않음
    if s == "industry":
        return "industry", step_refs or None

    # R1b: MD process_step — 그대로
    if s == "process_step":
        return "process_step", step_refs or None

    # R1c: MD common + step_refs — 소비측 미지원 → Ch3 가시성 workaround
    if s == "common" and step_refs:
        return "process_step", step_refs

    # R1d: common without refs (본 MD엔 없음) — 방어
    if s in ("common", "process_common"):
        return "process_common", None

    # fallback
    return "process_common", None
```

| MD scope | 변환 후 JSON | 근거 |
|----------|-------------|------|
| `process_step` | `process_step` | Ch3 mapped |
| `industry` | **`industry` (보존)** | Ch2 공통 관리점; Ch3 비표시가 저자 의도 |
| `common` + refs | **`process_step`** | `common` 미지원·누락 방지; **교차공정 의미는 MD에 보존**(메타/주석) |
| `common` 무 refs | `process_common` | Ch2 only |

**의도적 트레이드오프 (문서화)**

- common→process_step 승격 시 Ch3에 단계 번호가 붙어 **「공정 단계 관리점」처럼 보임**. 저자가 구분한 common/industry 레이어는 JSON `scope`에 **industry만 보존**, common은 workaround.
- 2차 고도화(범위 밖): `classifyControlPoints`에 `common` alias 또는 `process_common`+refs 다단계 연결 지원 → 그때 common 보존 재검토.

### 3.3 R2 — `control_points_ko/zh` 자동생성

- `control_points_{lang}` = `[item["text"] for item in control_points_detail_{lang}]` (**전 항목**, scope 무관).
- **idempotency:** 기존 slug 중 detail+control_points 둘 다 있는 항목에서 R2 재현 일치 확인 후 적용.

### 3.4 R3 — B07/B08 Fab 금지

- `process_steps_detail_*` step/note에 `FEOL`, `Lithography`, `Etch`, `BEOL`, `MOL` **독립 대단계명** 포함 시 FAIL.

---

## 4. self-test (전부 GREEN)

| ID | 검증 |
|----|------|
| ST-a | JSON 파싱·8 slug shape |
| ST-b | 소비측 `process_step` 분기 grep (`3_process_analysis.js`, `pflow_graph_adapter.js`) |
| ST-c | R2 idempotency (기존 보유 slug) |
| ST-d | B07/B08 Fab marker 0건 |
| ST-e | B01~B08 외 slug diff 0 |
| ST-f | 변환 후 scope 집계: process_step=58, industry=1 (ko 기준; common 6건은 R1c로 process_step 승격) |
| ST-g | B08 `industry` 1건 scope≠process_step assert |
| ST-h | 스크립트 2회 실행 동일 산출 |
| ST-i | (선택) B07/B08 A1 Ch3 렌더·api 재빌드 E2E |

### ST-f/ST-g 기대값 (ko)

```
process_step: 52 (MD 원본) + 6 (common 승격) = 58
industry: 1 (B08, 보존)
process_common: 0
```

---

## 5. 실행 순서 (Cursor)

1. **G0** — §1 소비측 표 재확인 (grep + `classifyControlPoints` 읽기)
2. **G1** — §2 scope 6+1 재집계 스크립트 출력 일치
3. **G2** — `build_a1_ch3_b_process_detail_backfill.py`의 `_apply_r1_scope` → §3.2 `apply_scope`로 교체
4. `--self-test` → ST-a~h
5. `--dry-run` diff 검토 → server/client JSON write
6. Gatekeeper 제출 (§6)

---

## 6. 제출 형식

```
[A1 Ch3 process_detail B01~B08 백필 완료 — rev.2]
- G0: 소비측 scope 표 일치 확인
- G1: common 6 + industry 1 집계 출력
- G2: R1a industry 보존 / R1c common→process_step / R2 idempotency
- ST-a..h 결과
- B07/B08 Fab 해소 전/후 (step[0] 샘플)
- B08 industry scope 보존 증빙 (JSON fragment)
- 변경 파일 · 커밋 해시
```

---

## 7. 커밋

- repo: `diagnosis-tool` (+ 필요 시 `iris-hub` 본 WORK ORDER)
- 메시지 예: `feat(a1): B01-B08 process_detail backfill with scope-safe R1`
- STATUS/백로그: process_detail_v1 residual → dx화 후보 1줄

---

## 8. 범위 밖

- `classifyControlPoints`에 `common` 네이티브 지원 (2차)
- RT 배지 숨김·multi-lane UI
- B01~B08 외 74개 세부산업
- 관리탭 편집기 (A1 read-only 유지)

---

## 9. 한 줄 요약

**MD 내용은 충분하나, JSON 변환만으로는 부족 — scope 규칙이 핵심이다.**  
`industry` 1건은 **보존**, `common` 6건은 **소비측 한계로 process_step 승격**, 기존「step_refs 있으면 무조건 process_step」R1은 **폐기**.
