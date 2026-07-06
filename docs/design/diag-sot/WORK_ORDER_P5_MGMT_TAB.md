# WORK ORDER — P5 진실원 관리 탭 UI

- **발행:** 2026-07-06 · Gatekeeper(Claude) → **실행: M5 Cursor**
- **선행:** P4-core PASS · 설계 `P5_MGMT_TAB_SPEC.md`
- **repo:** iris-hub `feat/diag-sot` (dev=`0Dev/iris-hub`) · **앱 코드 변경 → `sync-iris-hub.sh` 필수**
- **성격:** DIAG-SOT 최종 산출물(제1동인 가시화). MVP = **가시화 + 편집위치 안내**(인라인 편집 제외).

---

## 대상 파일 (예상)

| 파일 | 변경 |
|---|---|
| `src/store/` (신규 로더, 예: `diag_sot.py`) | MANIFEST/LINEAGE/INVENTORY read-only 로더 + `@st.cache_data`(mtime 무효화) |
| `src/tabs/diagnosis_mgmt.py` | `_render_sot_management()` 서브뷰 추가, 기존 render()에 분기(라디오/expander) |
| `src/ui_kit.py` | status→badge 매핑 확장(byte0/partial/residual/legacy/fixture) |

경로 해석: `src/diagnosis_git.py`의 `DEV_ROOT/"diagnosis-tool"` 재사용. 하드코딩 금지.

---

## 단계

### S1 — 데이터 로더 (read-only)
1. `DEV_ROOT/diagnosis-tool/scripts/data_poc/DIAG_SOT_MANIFEST.json`·`DIAG_SOT_LINEAGE.json` 로드 함수. 파일 부재 시 `None` + 사유.
2. `@st.cache_data`, 파일 mtime을 캐시 키에 포함(갱신 반영).
3. INVENTORY(`docs/diag-sot/reports/P4_INVENTORY.json`)는 드릴다운 시 lazy 로드.
4. **스키마 방어:** 필드 없으면 "—". 임의 매핑/추론 금지.

### S2 — 요약 배지 + dx 그리드 (§2.1–2.2)
1. 배지: pack_count · covered/total · orphan_live · archive 후보 수 · issue total (MANIFEST.meta + LINEAGE.issue_rollup).
2. 그리드 8컬럼(SPEC §2.2). status/loader는 badge. 행 선택 가능(`st.dataframe` selection 또는 카드+선택 state).
3. 필터(coverage_status·loader_reference_status·chapter·"archive 후보만"·검색) + 정렬(잔여/legacy 상단).

### S3 — lineage 상세 패널 (§2.3, 제1동인)
1. 선택 행 `pack_id`로 `pack_level_lineage` 조회 → 4블록 렌더:
   - 어디서 편집(`edit_where`) / 무엇 생성(`generates`) / 어디서 사용(`used_by_loaders`+`consumer_chapters`) / 무엇 위험(`risk`+연결 issue+loader status).
2. dx-covered 팩이면 `core_lineage_row_level`의 해당 phase artifact 링크 + row_count 표시(row 드릴다운은 링크·카운트로 MVP).
3. issue: `issue_rollup.issues`에서 팩/소스 연관분 필터 표시.

### S4 — 편집위치 안내
각 행/패널에 dx_artifact 경로 표시 + 복사 가능. "실편집은 diagnosis-tool authoring→byte-0 재조립" 안내 문구. **UI에서 SoT 직접 쓰기 금지.**

### S5 — 검증 + 배포
1. Streamlit 로컬 구동 → 그리드 39팩 렌더·필터·선택·lineage 4블록 표본 확인.
2. 데이터 미배치 케이스 graceful 확인.
3. `sync-iris-hub.sh` 실행 → live(:8765) 반영 확인.

---

## 금지사항

- ❌ SoT 데이터 직접 쓰기(수기편집 금지 규율).
- ❌ lineage를 실제 경로와 불일치 표기(§8 계약 필드만).
- ❌ MANIFEST/LINEAGE 스키마 변형·임의 추론 매핑.
- ❌ 신규 최상위 nav 추가(진단툴 하위 뷰).
- ❌ diagnosis-tool 경로 하드코딩.

## Gatekeeper 점검항목 (제출 시)

- [ ] 39팩 전건 렌더 · 필터/정렬 동작.
- [ ] lineage 4블록 §8.2 정합(표본 3팩 대조: ch2_systems_catalog·ch4_plan_defaults·system_catalog_root_legacy).
- [ ] "어디서 사용?" loader 경로 표본 grep 일치.
- [ ] 데이터 fallback 안내.
- [ ] read-only(쓰기 0) 확인 — 코드 grep으로 write/dump/open('w') 부재.
- [ ] dev→live sync 완료.

## Exit 게이트

1. dx 그리드 + lineage 4블록 렌더 · §8 정합.
2. read-only 무결성.
3. 소스 fallback.
4. sync 반영.

## 롤백

단일 탭 서브뷰 추가라 격리 rollback 용이(분기 제거). 커밋 분리(S1 로더 / S2-3 UI / S5 sync).

## 보고 형식 (M5 → Gatekeeper)

`변경 파일 · 스크린샷(그리드+lineage 패널) · read-only grep 결과 · sync 결과 · 미커밋 경로/해시`.
