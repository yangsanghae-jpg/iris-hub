# 진단툴 데이터 구조 평가

- **작성일:** 2026-07-05
- **상태:** 평가 기록 · **방향 결정 보류** (관리 탭 착수 전 판단 근거용)
- **범위:** 진단툴 v1.5 데이터팩의 구조적 정합성 평가. 재설계·구현은 범위 외.
- **계기:** 「진단툴 관리」 탭 목업(M2→M5) 과정에서 "그리드 한 장으로 안 된다"가 반복 → 원인이 UI인지 데이터 구조인지 규명 필요.
- **관련 문서**
  - 목업 탐색: [`DIAGNOSIS_PACK_MGMT_MOCKUP_DISCOVERY_REPORT_2026-07-05.md`](./DIAGNOSIS_PACK_MGMT_MOCKUP_DISCOVERY_REPORT_2026-07-05.md)
  - UX 정본: [`DIAGNOSIS_PACK_MGMT_UX_DESIGN.md`](./DIAGNOSIS_PACK_MGMT_UX_DESIGN.md)

---

## 0. 결론

**M2→M5의 목업 churn은 UI 문제가 아니라 데이터 구조 불일치의 증상이다.**

"그리드 한 장으로 안 된다"는 데이터가 복잡해서가 아니라 **팩마다 규칙이 다르기 때문**이다. 복잡한 데이터는 정규화하면 렌더링되지만, 불일치는 렌더러를 **팩 종류 수만큼 특수분기**시킨다. 목업 탐색 보고서의 "구조 재설계 범위 외 / 렌더러만" 결론은 착수는 가능하나, 이 불일치를 **UI·import 레이어에 그대로 각인**시키는 선택이라는 점을 기록해 둔다.

> **방향 결정은 보류.** 본 문서는 판단 근거만 정리한다.

---

## 1. 실측으로 확인된 구조 불일치

> 근거 경로: `diagnosis-tool/server/data/` (2026-07-05 실측)

| 축 | 편차 | 증거 |
|----|------|------|
| **i18n 표기** | 2가지 혼재 | ch1 팩 = `industry_label_ko`/`_zh` (flat suffix) · Q4 = `label:{ko,zh,en,ja}` (nested dict) |
| **메타 관례** | 4가지 | `metadata`(step4) · `_meta`(step5_2) · `version`(catalogs·step3·q5) · **없음**(ch1 팩) |
| **코드 표기** | 접두사 불일치 | IND_A = `industry_code:"IND_A"` · Q4 = `industry_code:"A"` (같은 산업 A) |
| **파일명 ↔ 코드** | 불일치 | `IND_A_project_special.json` ≠ 코드 `IND_A` |
| **도메인 표현** | 한 객체 내 이중 | Q4 A01: `weights.planning`(nested) vs `planning_importance`(flat 접두) — 같은 4도메인 축을 두 방식으로 |
| **레거시 잔존** | 신·구 병존 | `legacy_sub_profiles`, `legacy_slug` |
| **server/client 사본** | 97 vs 16 파일 | 이중 사본 → 드리프트 위험 |

### 1.1 가장 뾰족한 지점 — Q4 A01 도메인 이중표현

`subindustry_profiles.A01` (26필드) 안에서 **같은 "4도메인(planning/quality/equipment_control/logistics)" 축이 두 방식으로 공존**한다:

- `weights` / `recommended_levels` → `{planning:…, quality:…}` (도메인이 **키**)
- 상세 필드 → `planning_profile`, `planning_importance`, `planning_levels`, `quality_profile`, … (도메인이 **접두사**로 flat하게 분산)

**결과:** M5에서 sub-grid를 9개로 쪼개야 했던 직접 원인. 데이터가 `domains:{planning:{profile,importance,levels,horizon,constraints}, …}`로 정규화됐다면 **sub-grid 1개 + 도메인 반복**으로 끝날 표현이었다.

---

## 2. 관리 탭에 미치는 영향 (렌더러-only 채택 시)

- i18n 렌더러 2벌, 메타 파서 4벌, 코드 정규화 로직을 **UI가 떠안음**
- "수치/내용/언어 필터"(목업 보고서 §2.2)는 열 가시성으로 구현되나, **팩마다 열 정의가 달라** 필터 규칙도 팩별 특수분기
- `dx_*` import가 nested 보존 외에 **표기 정규화 매핑을 팩 종류 수만큼** 유지해야 함

→ 재설계를 "범위 외"로 밀어도 비용은 사라지지 않고 **UI + import 레이어로 분산**된다.

---

## 3. 선택지 (보류 — 기록용)

| 옵션 | 내용 | 비용 | 리스크 |
|------|------|------|--------|
| **A. 렌더러-only** | 데이터 무손. 팩 종류별 특수분기 렌더러 | 낮음(착수) | 불일치 UI·import에 영구 각인 |
| **B. 최소 정규화 어댑터** | 파일 무손. i18n·meta·code 표기만 import 시 정규화 어댑터 한 겹으로 통일 → 렌더러 1벌 | 중 | Q4 도메인 flat은 남음 |
| **C. 스키마 v4 재설계** | 도메인 정규화 포함 전면 정리 | 높음 | 진단툴 런타임(`q4_taxonomy_v3.js`, `q4_levels/`) 동반 수정, 별도 트랙 |

**평가자 의견:** 착수 전제로는 **B(최소 정규화)** 가 A와 C의 절충. 단 C(도메인 flat 해소)는 스키마 v4 = 별건. 최종 방향은 미결.

---

## 4. 미결 / 후속

- [ ] 방향 결정 (A/B/C)
- [ ] 결정 시 목업 보고서 §5 권고와 정합화 (§5는 현재 A 전제)
- [ ] server/client 사본 이중화 정책 (SoT 일원화 여부)
- [ ] Q4 스키마 v4 검토는 진단툴 팀 트랙으로 분리

---

## 부록 A. 실측 커맨드

```bash
cd diagnosis-tool
# i18n/meta/code 관례 스캔
python3 -c "
import json,glob
for g in ['server/data/ch1/industry_packs/*.json','server/data/step4/*.json','server/data/step5_2/*.json']:
    f=sorted(glob.glob(g))[0]; d=json.load(open(f)); print(f, list(d.keys())[:6])
"
# Q4 A01 도메인 이중표현 확인
python3 -c "
import json; a=json.load(open('server/data/step4/automation_profile_v3.json'))['subindustry_profiles']['A01']
print('nested :', list(a['weights'].keys()))
print('flat   :', [k for k in a if k.startswith('planning')])
"
```

## 부록 B. 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-07-05 | 초판 — 실측 기반 불일치 7종·영향·선택지(보류) |
