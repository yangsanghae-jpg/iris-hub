# DIAG-SOT — 개요·아키텍처 (요약)

> 전체 근거는 [`../DIAGNOSIS_TOOL_SOT_TARGET_DESIGN_2026-07-05.md`](../DIAGNOSIS_TOOL_SOT_TARGET_DESIGN_2026-07-05.md). 여기선 실행에 필요한 요약만.

## 1. 문제 (제1 동인 = 추적성)

현 데이터팩은 직관적이지 않아 **"어디를 고치면 어디에 반영되는지(안 되는지)"가 불명확**하다. 같은 개념이 3홈·3변종·생성물/수기 혼재. → 성공기준 = **모든 편집이 반영 경로를 스스로 드러낸다.**

## 2. 데이터 3성격 (획일 구조 금지)

| 축 | 성격 | 실물 | 관리 |
|----|------|------|------|
| ①척추 | 9산업×74세부 기본키, 상시증가 | 모든 Q팩 `A01~I08` 키 + `industry_master`/`sub_industry_codes`(SUB_X_YYY 별도 코드계) | registry |
| ②평가매트릭스 | Q1~Q5 세부산업 평가수치 | Q2/Q3/Q4 = `metadata+framework+subindustry_profiles[74]` | 표/그리드(언어경량) |
| ③보고콘텐츠 | A1/A2 다국어 서술+룰엔진 | systems_catalog(zh)·mgmt(ko)·roi(ko+zh) 제각각 | 콘텐츠팩(언어1급) |

## 3. 방법 = 평행운영 + byte-diff 게이트

```
새 브랜치
 ├ iris-hub: 새 SoT 구조 NEW 구축 (기존 팩 in-place 변형 안 함)
 ├ sync: 팩을 "같은 위치·같은 shape"로 생성
 └ 게이트: 생성팩 vs 현재 팩 = byte-diff 0  ← 확실성의 근거
그다음 팩 단위 컷오버 (각 컷오버 = diff 0 증명 후에만)
```
- **게이트 머신 실재:** `diagnosis-tool/scripts/data_poc/`(`migrate_legacy_to_src.py`·`build_data.py`·`diff_test_pack.py`·`common.py`) + `run_data_poc.sh`. 2026-06-29 Q5+taxonomy에서 diff 0 통과 이력.
- **선재 자산:** `diagnosis-tool/data/src/`(structure/content/{ko,zh,en,ja}) — P0에서 재활용/이관 판정.

## 4. 단계 흐름

```
P0 기반·게이트·결정표 ──PASS──► P1 척추+Q매트릭스(diff0,엔진무변경)
   ──PASS──► P2 언어팩+ko기본(의도된 diff) ──PASS──► P3 보고콘텐츠 세분화+엔진부분개편(dev)
   ──PASS──► P4 잔여·legacy격리·lineage완성
```

각 단계: **Executor 실행 → 게이트 증거 → Gatekeeper 점검 → PASS 시 다음.** P1이 방법 자체를 증명하는 관문.

## 5. 저장소 지도 (작업 대상)

| repo/경로 | 역할 | 브랜치 |
|-----------|------|--------|
| iris-hub `dx_*` + 관리탭 + sync발신 | SoT 정본 | `feat/diag-sot` |
| diagnosis-tool `server/data`·`client/data` | sync 생성물(수기금지) | `feat/diag-sot-sync` |
| diagnosis-tool `scripts/data_poc` | 게이트 머신 | `feat/diag-sot-sync` |
| diagnosis-tool `server/assemble/ch*`·`server/rules` | 엔진(P1 무변경, P3 부분개편) | `feat/diag-sot-sync` |
