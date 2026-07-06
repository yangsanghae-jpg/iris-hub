# P5 — 진실원 관리 탭 UI (설계서)

- **상태:** 골격 설계 · 실행 전 Gatekeeper 검토
- **선행:** P4-core PASS (MANIFEST+LINEAGE 데이터 계약 확정)
- **목적:** DIAG-SOT 제1동인 **"모든 편집이 반영경로를 드러낸다"** 를 iris-hub 관리 탭 **lineage 뷰**로 완성. = DIAG-SOT 최종 산출물.
- **repo:** iris-hub (Streamlit). dev=`0Dev/iris-hub` → 배포 sync 별도(§7).

---

## 1. 데이터 계약 (소스 = P4-core 산출물)

관리 탭은 **read-only 소비자**다. 데이터를 편집 UI가 쓰는 건 dx authoring(diagnosis-tool), 관리 탭은 그 **가시화 + 편집 진입점**.

| 소스 | 경로 (diagnosis-tool) | 용도 |
|---|---|---|
| MANIFEST | `scripts/data_poc/DIAG_SOT_MANIFEST.json` | 그리드 rows |
| LINEAGE | `scripts/data_poc/DIAG_SOT_LINEAGE.json` | lineage 상세 패널 |
| INVENTORY | `docs/diag-sot/reports/P4_INVENTORY.json` | (선택) row별 loader 근거 드릴다운 |

경로 해석: 기존 `src/diagnosis_git.py`의 `DEV_ROOT / "diagnosis-tool"` 재사용(형제 경로 또는 `DIAGNOSIS_TOOL_GIT` env). 파일 없으면 "P4-core 미배치" 안내.

## 2. 화면 골격

기존 **🔧 진단툴 탭(`src/tabs/diagnosis_mgmt.py`)** 의 하위 뷰로 추가(신규 최상위 탭 만들지 않음 — 진단툴 관리의 일부).

```
[🔧 진단툴]
 ├ (기존) migration flow / git header / phase items
 └ (신규) ▸ 진실원(SoT) 관리
      ├ 2.1 요약 배지  (pack N · live=loader 100% · 고아 0 · archive 후보 M · issue K)
      ├ 2.2 dx 그리드  (팩 목록 + 필터)
      └ 2.3 lineage 상세 패널 (그리드 행 선택 시)
```

### 2.1 요약 배지
MANIFEST.meta에서: `pack_count`, `covered/total`, `orphan_live`, `archive_candidate_packs` 수, LINEAGE.issue_rollup.total.

### 2.2 dx 그리드 (§8.1 계약)
| 컬럼 | 소스 |
|---|---|
| pack id | `pack_id` |
| status | `coverage_status` (badge: byte0🟢 / partial🟡 / residual🔵 / legacy⚫ / fixture⚪) |
| live loader | `loader_reference_status` (direct/indirect/none) |
| canonical path | `member_paths[0]`(+N) |
| dx artifact | `dx_artifacts` (없으면 —) |
| consumer | `consumer_chapters` |
| lineage | `lineage_status` |
| issues | 연결 issue 수 |

필터: `coverage_status`, `loader_reference_status`, chapter, "archive 후보만", 텍스트 검색.
정렬: status 우선(잔여/legacy 상단) → pack_id.

### 2.3 lineage 상세 패널 (§8.2 계약 = 제1동인)
선택 행의 `pack_level_lineage` + (dx-covered면) core row-level 링크로 4블록:

| 블록 | 소스 | 질문 |
|---|---|---|
| **어디서 편집?** | `edit_where` (dx_artifact / member_paths) | Where do I edit? |
| **무엇이 생성?** | `generates` (generated_path / member_paths) | What gets generated? |
| **어디서 사용?** | `used_by_loaders` + `consumer_chapters` | Where is it used? |
| **무엇이 위험?** | `risk`(notes) + 연결 issue rows + loader_reference_status | What is risky? |

row-level 드릴다운(P1~P3 core): core_lineage_row_level artifact 링크 → dx row → json_pointer → consumer(선택 구현, MVP는 링크·카운트).

## 3. 편집→sync 진입점 (MVP는 "진입", 실편집은 diagnosis-tool)

- 각 팩 행에 "dx에서 편집" 링크(dx_artifact 경로 표시/복사) — 실제 편집은 diagnosis-tool authoring.
- **인라인 편집은 P5 범위 밖(후속).** 이유: 편집은 byte-0 재조립 파이프라인을 거쳐야 하며(수기편집 금지 규율), UI 직접 쓰기는 SoT 무결성 위반. P5는 **가시화 + 편집 위치 안내**까지.

## 4. 방법 (권고)

1. `src/store`에 MANIFEST/LINEAGE 로더 추가(캐시 `@st.cache_data`, mtime 무효화). INVENTORY는 lazy.
2. `diagnosis_mgmt.py`에 `_render_sot_management()` 서브뷰 + 상단 라디오/expander로 기존 뷰와 분기.
3. 그리드는 `st.dataframe`(선택 가능) 또는 기존 `_render_html` 카드 패턴 재사용(테마 일관성). lineage 패널은 4블록 컬럼 레이아웃.
4. status→badge 매핑은 `ui_kit.py` 확장.

## 5. 금지사항 (Executor)

- ❌ 관리 탭에서 SoT 데이터 직접 쓰기(수기편집 금지 규율 위반).
- ❌ lineage 뷰를 실제 반영경로와 불일치로 표기(§8 계약 필드만 신뢰, 임의 추론 금지).
- ❌ MANIFEST/LINEAGE 스키마 변형 소비(필드 없으면 "—", 임의 매핑 금지).
- ❌ 신규 최상위 nav 항목 추가(진단툴 하위 뷰로).

## 6. Gatekeeper 점검항목

- [ ] 그리드가 MANIFEST 39팩 전건 렌더 · 필터/정렬 동작.
- [ ] lineage 패널 4블록이 §8.2 계약과 필드 정합(표본 팩 대조).
- [ ] "어디서 사용?"의 loader 경로가 실제 코드와 일치(표본 grep).
- [ ] 데이터 미배치/구버전 시 graceful 안내.
- [ ] read-only(쓰기 경로 0) · flag/무접촉 무관.
- [ ] 배포 sync(§7) 반영.

## 7. 배포 sync 주의

`0Dev/iris-hub`(dev) 편집 후 **live(`iris-local/iris-hub` :8765)** 반영은 `sync-iris-hub.sh` 필요(설계 문서는 무관, **앱 코드 변경은 필수**). 지시서 Exit에 sync 포함.

## 8. Exit 게이트

1. dx 그리드 + lineage 4블록 렌더, §8 계약 정합.
2. read-only 무결성(SoT 직접쓰기 0).
3. 데이터 소스 fallback 안내.
4. dev→live sync 확인.

## 9. 범위 밖 (후속)

인라인 dx 편집·편집→byte-0 재조립 트리거·동시출현/개념 그래프 연계·다이프 히스토리 뷰.
