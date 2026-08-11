# iris-spc → iris-qms 이관 설계서 (QMS 범주 기능 회수)

- 작성일: 2026-08-11
- 개정: 2026-08-11 (r2 — 이관 항목을 "절단 / 화면 신설 후 절단 / 신규 개발" 3분류로 재정리, §6 순서 교체)
- 대상 저장소: `/Users/iris/0Dev/iris-spc` (포트 3340) · `/Users/iris/0Dev/iris-qms` (포트 3350)
- 문서 위치 근거: 두 저장소에 걸치는 설계이므로 iris-hub 설계서 디렉터리에 보관
- 관련 소스: [iris-spc services/spc.py](../../../iris-spc/src/iris_spc/services/spc.py) · [iris-spc api/spc.py](../../../iris-spc/src/iris_spc/api/spc.py) · [iris-qms services/qms.py](../../../iris-qms/src/iris_qms/services/qms.py) · [iris-qms web/qms.js](../../../iris-qms/web/qms.js)

---

## 0. 이 문서만 읽고 실행할 수 있도록 하는 환경 정보

| 항목 | iris-spc | iris-qms |
|---|---|---|
| 실행 | `IRIS_SPC_PORT=3340 ./scripts/dev.sh` | `IRIS_QMS_PORT=3350 ./scripts/dev.sh` |
| venv | `.venv/bin/python` (저장소 내) | `.venv/bin/python` (저장소 내) |
| 테스트 | `.venv/bin/python -m pytest -q` | `.venv/bin/python -m pytest tests -q` (2026-08-11 기준 21 passed) |
| DB | `data/iris_spc.db` | `data/qms.db` |
| 헬스 | `http://127.0.0.1:3340/health` | `http://127.0.0.1:3350/health` |

운영 전제 (2026-08-11 확정):

1. iris-spc는 **당분간 독립 서비스로 계속 운영**한다. 이관 후에도 단독 기동·판정이 가능해야 한다.
2. 최종적으로는 **iris-qms가 SPC를 포함**하는 구조로 간다. 이관은 그 준비 작업이다.
3. **마스터 데이터·샘플 raw 데이터의 중복은 승인**되었다. 이 문서의 범위 밖이다(§7).

---

## 1. 배경 — 왜 회수하는가

iris-spc가 SPC 범주를 넘어 확장되었다. QMS가 별도로 존재하므로, QMS 범주의 기능이 SPC에 남아 있으면 **정본이 둘로 갈라진다.**

2026-08-11 실측으로 확인된 충돌:

| 항목 | iris-qms | iris-spc |
|---|---|---|
| 보어 특성이 붙은 부품 | `AX-HSG-01` (Aluminium Housing) | `AX-CYL-03` (Cylinder) |
| Control Plan ID / Revision | `CP-AUTO-001` / R1 | `CP-AX-BORE-R3` |
| 샘플링 | `1st piece + 1/2h` | `5 pcs / 4시간` |
| PPAP 초기능력 합격선 | Cpk ≥ 1.33 (오류) | Ppk ≥ 1.67 (정확) |

동일 특성(보어 직경, 규격 19.95–20.05, 설비 CNC-04)에 대해 두 시스템이 **서로 다른 사실**을 보유한다. IATF 16949에서 Control Plan은 단일 정본이어야 하는 통제문서이므로, 이 상태는 그 자체로 부적합 사유다.

원인은 iris-spc가 [`spc.py:147`](../../../iris-spc/src/iris_spc/services/spc.py:147)에 Control Plan을 **하드코딩 dict로 자체 보유**하고, PPAP 패키지 정보까지 문자열로 들고 있기 때문이다.

### 산업 근거 (2026년 기준)

- **AIAG-VDA SPC 매뉴얼**(2026-07-01 공동 발간): SPC는 *FMEA·Control Plan·MSA/VDA 5와 연결되어야 한다*고 명시. 평가 축을 machine performance / process performance / process capability 3단계로 규정.
- **자동차 QMS 시장의 실제 구분**: QMS(경영시스템 — 문서·감사·교육·CAPA) vs CAQ(현장 품질보증 — 측정수집·SPC·게이지·검사평가). "한쪽은 감사 대응, 다른 쪽은 라인 데이터"가 경계.
- **Siemens Opcenter Quality 구조**: APQP 프로젝트 → Control Plan → inspection characteristics 전개 → Control 모듈(수집 + SPC)이 실행. **Control Plan은 계획측이 소유하고 수집·SPC는 실행측이 소유한다.**
- **Q-DAS AQDEF**(자동차 측정데이터 교환 표준): 측정기와 통계SW 사이 경계를 포맷으로 고정. 표준 키 필드에 K0007 Cavity, K0008 작업자, K0010 기계, K0006 배치 포함.

---

## 2. 이관 판정 기준

> **SPC는 감지하고 세운다. QMS는 조사하고 고치고 닫는다.**

- 알람 판정(감지)과 공정·설비 정지(hold)까지 → **iris-spc**
- 원인조사·시정조치·승인·처분·종결 → **iris-qms**

보조 기준 (위에서부터 우선 적용):

1. 출하·고객에 영향을 주는가 → **QMS**
2. 승인·결재가 필요한가 → **QMS**
3. 측정·계산에서 나오는 값인가 → **SPC**

---

## 3. 이관 대상 (13건)

### 3.0 착수 순서 규칙 — 이 문서에서 가장 중요한 절

**"QMS에 수용처가 있다"는 말은 세 가지 층으로 나눠 봐야 한다.** 테이블만 있는 것과, 조작 화면까지 있는 것은 전혀 다르다.

| 층 | 확인 방법 |
|---|---|
| 테이블 | `qms.db` 스키마 |
| API | `iris_qms/api/qms.py` 라우트 |
| **화면** | [`web/qms.js`](../../../iris-qms/web/qms.js)의 `actionButton()` 대상 컬렉션 |

2026-08-11 기준 iris-qms에서 **운영 버튼이 붙어 있는 컬렉션은 `ncrs` · `capas` · `approvals` · `inspections` 넷뿐**이다. 자동차 워크스페이스는 [`qms.js:96`](../../../iris-qms/web/qms.js:96) `automotiveRows()`로 렌더되며 **운영 컬럼 자체가 없다.** `quality_cases` · `eight_d` · `mrb_dispositions` · `msa_studies`는 테이블과 API는 있으나 조작 화면이 없다. `qms_event_history`는 **조회 API조차 없다** (기록은 쌓이나 읽는 경로 부재).

반면 iris-spc의 `investigations` · `actions`는 **실제로 동작하는 화면**이다 (조작 호출 16곳, 감사 이벤트 88건, Hold→Investigation→Action→verified 완주 이력 존재).

> **규칙: 받을 화면이 QMS에 생긴 뒤에 SPC에서 자른다.**
> 이 순서를 어기면 동작하는 기능이 사라지고 시스템 전체가 퇴보한다.

이에 따라 13건을 성격별 3그룹으로 분류한다.

---

### 3.1 A그룹 — SPC 절단만 (QMS 준비 불필요, 즉시 착수 가능)

| # | SPC 위치 | 근거 | QMS 테이블 | API | 화면 |
|---|---|---|---|---|---|
| 1 | [`spc.py:147`](../../../iris-spc/src/iris_spc/services/spc.py:147) `control_plans` 하드코딩 dict | Control Plan은 IATF 통제문서·고객 승인 대상 | ✅ `qms_auto_control_plans` | ✅ | ✅ 읽기 |
| 2 | [`spc.py:160`](../../../iris-spc/src/iris_spc/services/spc.py:160) `automotive_payload`의 `ppap` 블록 (`"PPAP-AUTO-02-L3"`, `psw`, `customer` 전부 하드코딩) | PPAP·PSW·고객 결정은 전적으로 QMS | ✅ `qms_auto_ppap_packages` / `ppap_elements` | ✅ | △ 생성 버튼만 |
| 4 | [`spc.py:119`](../../../iris-spc/src/iris_spc/services/spc.py:119) `automotive_controls` 배열 (control-plan·ppap 항목) | 위와 동일 | — | — | — (단순 삭제) |

**#1·#2 절단 후 `automotive_payload`에 남는 것**: `cavities`(Cavity별 Cpk) · `characteristic` · `chart` · `capability` · `summary`. 즉 **순수 통계 판정만 남는다.** Control Plan 분류(CC/SC)·규격·샘플링·반응계획은 QMS에서 조회해 표시만 한다.

---

### 3.2 B그룹 — QMS 화면 신설 후 절단

**절단 자체는 간단하나, 지금 자르면 기능이 사라진다.** 아래 "QMS 선행 작업"을 먼저 완료해야 한다.

| # | SPC 위치 | QMS 수용처 | 테이블 | API | 화면 | QMS 선행 작업 |
|---|---|---|---|---|---|---|
| 5 | [`api/spc.py:537`](../../../iris-spc/src/iris_spc/api/spc.py:537) `/investigations` GET·POST·PATCH | `qms_auto_quality_cases` + `qms_auto_eight_d` | ✅ | ✅ | ❌ | **품질사건·8D 운영 화면 신설** (D1~D8 입력, 상태전이) |
| 6 | [`api/spc.py:586`](../../../iris-spc/src/iris_spc/api/spc.py:586) `/actions` GET·POST·PATCH | `capas` + `qms_auto_eight_d` D5/D6 | ✅ | ✅ | △ CAPA만 | **8D D5/D6 시정·검증 입력 화면 신설** |
| 7 | `holds.disposition` 컬럼 | `qms_auto_mrb_dispositions` | ✅ | ✅ | ❌ | **MRB 처분 요청·승인 화면 신설** |
| 8 | [`api/spc.py:255`](../../../iris-spc/src/iris_spc/api/spc.py:255) `/audit-log` | `qms_event_history` | ✅ | **❌ 없음** | ❌ | **감사이력 조회 API + 화면 신설** |
| 9 | [`spc.py:249`](../../../iris-spc/src/iris_spc/services/spc.py:249) `msa_payload`의 스터디 판정·관리 | `qms_auto_msa_studies` | ✅ | ✅ | ❌ | **MSA 스터디 등록·판정 화면 신설** |
| 3 | [`spc.py:111`](../../../iris-spc/src/iris_spc/services/spc.py:111) `profile_payload`의 `governance` 블록 | 프로파일 거버넌스 | △ 부분 | △ | ❌ | 프로파일에 거버넌스 계약 필드 보강 |

**#7 주의**: `holds` 테이블 자체는 SPC 잔류다. **공정·설비 정지**이지 물량 보류가 아니다(`alarm_key`·`subgroup_id`에 붙어 있음). `disposition` 컬럼만 제거하고, 테이블명을 `process_holds`로 바꿔 의미를 명확히 한다. **Lot 보류는 `qms_auto_lots.state`가 유일 정본.**

**#9 주의**: MSA **계산 엔진은 SPC 잔류**. QMS로 가는 것은 스터디 등록·합격 판정·증적 링크다.

---

### 3.3 C그룹 — QMS 신규 개발 (수용처가 아예 없음)

| # | SPC 위치 | 근거 | QMS 현재 |
|---|---|---|---|
| 10 | [`spc.py:367`](../../../iris-spc/src/iris_spc/services/spc.py:367) `/permissions` (역할 4개 하드코딩) | 사용자·역할·전자서명은 전사 단일 | **인증 개념 자체가 없음** (모든 이력 actor = `qms-api` 고정) |
| 11 | [`api/spc.py:183`](../../../iris-spc/src/iris_spc/api/spc.py:183) `PATCH /rule-profile` | 어떤 룰을 켤지는 계획측 결정. 특수특성은 승인 대상 | 없음 |
| 12 | [`spc.py:661`](../../../iris-spc/src/iris_spc/services/spc.py:661) `ocap_payload`의 조사·조치·종결 조인부 | OCAP 정의(반응계획)는 계획측 문서 | 없음 (§8 미결) |
| 13 | [`spc.py:377`](../../../iris-spc/src/iris_spc/services/spc.py:377) `/integrations` (커넥터 5종 하드코딩) | 시스템 연동 현황은 관리 계층 | 없음 |

**#10은 단순 이관이 아니라 신규 설계 과제다.** iris-qms에 인증·사용자 개념이 전무하므로 권한 체계 자체를 먼저 세워야 한다.

---

## 4. SPC 잔류 (이관 금지)

| 잔류 대상 | 이유 |
|---|---|
| chart 4모드(Xbar-R/S, I-MR, 계수형) · baseline · **관리한계 계산·동결** | 데이터에서 산출되는 값. 규격(QMS)과 다른 개념 |
| capability / distribution / trends 계산 | 통계 엔진 |
| **MSA 계산 엔진** | 판정만 QMS, 계산은 SPC |
| alarms · WE/Nelson 신호 판정 · **알람 acknowledge** | 감지가 SPC의 존재 이유 |
| **holds (공정·설비 정지)** | 출하가 아닌 공정 상태. `disposition` 컬럼만 제거 |
| `GET /rule-profile` · 룰 계산 | 활성화 승인만 QMS |
| source-data · subgroups · filter-options · scope-options | 원시 데이터 접근 |
| process-master · product-master · 설비/라우트 마스터 | 중복 승인 대상(§7) |
| tool-chamber · wafer-uniformity · requalification **판정** | 반도체 공정 특화. 합격 기준값만 QMS(§8) |
| `GET /report` (SPC 통계 보고서) | PPAP 제출 패키지만 QMS |
| `GET /administration` (서비스 자체 상태) | 자기 헬스체크 |

---

## 5. 이관 후 SPC 자립 방안

독립 운영이 전제이므로 필수 조건이다.

### 5.1 계획값 캐시

QMS에서 내려받는 계획값(규격 USL/LSL/Target·`spec_revision`·CC/SC 분류·샘플링·반응계획·`control_id`)은 **로컬 캐시에 저장**한다.

- QMS 미기동 시에도 SPC는 캐시값으로 계속 판정한다.
- 캐시 사용 중임을 화면 상단에 명시한다(`계획값 최종 수신: YYYY-MM-DD HH:MM`).
- 캐시는 **읽기 전용**이다. SPC에서 편집 경로를 만들지 않는다.

### 5.2 조사·조치 이관 후의 SPC 화면

B그룹 절단(#5·#6) 시 OCAP 화면이 비게 된다. 대응:

- SPC에는 **"1차 현장 확인 메모" 한 칸만** 남긴다(자유 텍스트, 승인 없음).
- 정식 원인조사·시정조치는 **QMS 링크로 이동**시킨다.
- 감지 → 정지까지는 SPC 안에서 완결되므로 현장 운영은 끊기지 않는다.

### 5.3 자동차 프로파일 잠금 조건 정의

[`web/actual.js:31`](../../../iris-spc/web/actual.js:31)의 `AUTOMOTIVE_PROFILE_LOCKED = true`를 유지하되, **해제 조건을 명문화**한다.

```
해제 조건 = QMS Control Plan 연결 완료 (§6 1단계 완료)
```

현재는 "반도체 SPC 완성 전까지"라는 모호한 사유로 잠겨 있다. 이관 1단계 완료를 해제 조건으로 재정의한다.

---

## 6. 이관 순서와 완료 판정

| 단계 | 성격 | 대상 | 완료 판정 기준 |
|---|---|---|---|
| **1** | **SPC 절단** | A그룹 #1 · #2 · #4 | `grep -rn "CP-AX-\|PPAP-AUTO-\|OEM Tier-1" iris-spc/src/` 결과 0건. `automotive_payload`가 QMS `control_plans` 조회로 동작. §1의 정본 충돌 4건 소멸 |
| **2** | **QMS 화면 신설** | 품질사건·8D · MRB 처분 · MSA 스터디 운영 화면, `qms_event_history` 조회 API | `automotiveRows()`에 운영 컬럼 존재. `qms_event_history`에 `record.updated` 계열 이벤트가 실제로 쌓임(현재 0건) |
| **3** | **SPC 절단** | B그룹 #5 · #6 · #7 · #8 · #9 · #3 | SPC에 `root_cause`·`evidence`·`disposition` 컬럼 부재. 폐루프가 QMS 한 곳에서 종결 |
| **4** | **QMS 신규 개발** | C그룹 #10 · #11 · #12 · #13 | QMS가 SPC를 포함할 준비 완료 |

**1단계는 순수 삭제 + 조회 전환이다.** 하드코딩 dict 3개를 제거하고 QMS 조회로 바꾸는 것이 전부이며, §1에서 관측된 정본 충돌(부품·revision·샘플링·PPAP 기준)이 이것만으로 해소된다.

**2단계가 이 이관의 실질적 본체다.** 절단 작업(1·3단계)의 코드량은 작고, QMS 화면 신설이 대부분의 공수를 차지한다.

### 선결 조건 — 연결 키

이관 1단계 전에 **`control_id ↔ characteristic_id` 매핑 키**를 세워야 한다. 이것이 두 시스템의 척추다.

SPC `subgroups` 테이블은 이미 AQDEF와 거의 같은 형태이므로 추가 부담이 작다:

| AQDEF 표준 키 | iris-spc 현재 | 조치 |
|---|---|---|
| K0001 측정값 | `measurements.value` | 그대로 |
| K1001 부품번호 | `characteristics.product_id` | QMS `parts.part_number`와 값 일치시킴 |
| K0006 배치 | `subgroups.lot_id` | QMS `qms_auto_lots.lot_id`와 연결 |
| K0007 Cavity | `subgroups.chamber_id` | 그대로 (QMS 측 Cavity 축은 별도 과제) |
| K0008 작업자 | `subgroups.operator_id` | 그대로 |
| K0010 기계 | `subgroups.equipment_id` | QMS `process_flows.equipment`와 연결 |
| — (계획 연결) | **없음** | **`control_id` 신설 — 최우선** |

---

## 7. 범위 밖 (2026-08-11 승인)

다음은 문제로 취급하지 않는다:

- iris-qms와 iris-spc의 **마스터 데이터 중복** (부품·공정·설비·라우트)
- **샘플 raw 데이터 중복** — `qms_spc_*` 스냅샷 테이블(측정 60,000행·부분군 12,000행 포함)
- 두 저장소가 각자 SQLite를 보유하는 구조

이 항목들은 iris-qms가 iris-spc를 흡수하는 시점에 자연 해소된다.

---

## 8. 미결 쟁점

### ① `requalification` (반도체 재자격) — 기준값만 이관

[`spc.py:431`](../../../iris-spc/src/iris_spc/services/spc.py:431)이 baseline 동결 여부 · Cpk ≥ 1.33 · %GRR 합격 3개 조건을 **자체 기준값으로** 판정한다.

- **제안: 판정 로직은 SPC 잔류, 합격 기준값만 QMS로 이관.**
- 근거: 기준을 지키는 쪽이 기준을 소유하면 규격(#1·#2)과 동일한 통제 붕괴가 발생한다.

### ② `/ocap` 이관 시점

OCAP은 반도체 계획측의 핵심이지만 **QMS에 OCAP 모델이 아직 없다.** 지금 이관하면 기능이 공중에 뜬다.

- **제안: 4단계로 미루고, 그 전까지 SPC 잔류를 임시조치로 명시.**
- 반도체 계획측은 자동차의 Control Plan이 아니라 **Recipe + OCAP**이 중심이므로, QMS에 반도체 계획측 모델을 신설할 때 함께 설계한다.

### ③ 2단계(QMS 화면 신설)의 범위

B그룹 절단을 위해 QMS에 만들어야 할 화면이 5종이다. 이 중 어디까지를 이관 전제 조건으로 볼지 확정이 필요하다.

- **최소안**: 품질사건·8D·MRB 3종만 만들고 절단. MSA·감사이력은 절단을 미룸.
- **완전안**: 5종 전부 만든 뒤 B그룹 일괄 절단.

---

## 9. 참고 — 이 설계의 판단 근거가 된 실측

2026-08-11 기준 측정값:

| 항목 | 값 |
|---|---|
| iris-spc 라우트 | GET 28 · POST 5 · PATCH 5 (총 38) |
| iris-spc 이관 대상 | 13건 = 라우트 10개(`/investigations` 3, `/actions` 3, `/audit-log`, `/permissions`, `/integrations`, `PATCH /rule-profile`) + 페이로드 블록 4개 + 컬럼·판정 로직 3건 |
| 그룹별 분포 | **A(절단만) 3건 · B(화면 신설 후 절단) 6건 · C(신규 개발) 4건** |
| iris-qms 변경 엔드포인트 | 62개 (POST 32 · PATCH 30) |
| iris-qms UI가 호출하는 변경 엔드포인트 | **7개 (11%)** |
| iris-qms 운영 버튼 보유 컬렉션 | `ncrs` · `capas` · `approvals` · `inspections` **4종뿐** |
| iris-qms `qms_event_history` 조회 경로 | **없음** (API·화면 모두 부재) |
| iris-spc `audit_events` | 88건 (actor: qa-test·operator·test 등 테스트 주체) |
| iris-qms `qms_event_history` | 27건 전부 `auto.record.created` / actor `qms-api` (조작 이력 0건) |
| iris-qms 자동차 테이블 | 38개 중 30개 0행 |
