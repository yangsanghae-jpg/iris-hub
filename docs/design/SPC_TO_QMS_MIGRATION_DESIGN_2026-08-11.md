# iris-spc → iris-qms 이관 설계서 (QMS 범주 기능 회수)

- 작성일: 2026-08-11
- 개정 이력
  - r1 (2026-08-11) — 최초 작성
  - r2 (2026-08-11) — 이관 항목을 "절단 / 화면 신설 후 절단 / 신규 개발" 3분류로 재정리, §6 순서 교체
  - **r3 (2026-08-11) — iris-spc UI 재편(`80d252c`·`44dd734`) 반영. 이관 항목을 사이드바 항목·패널 ID 단위의 구체 변경지시로 전환**
- 대상 저장소: `/Users/iris/0Dev/iris-spc` (포트 3340, HEAD `44dd734`) · `/Users/iris/0Dev/iris-qms` (포트 3350)
- 문서 위치 근거: 두 저장소에 걸치는 설계이므로 iris-hub 설계서 디렉터리에 보관
- 관련 소스: [iris-spc services/spc.py](../../../iris-spc/src/iris_spc/services/spc.py) · [iris-spc api/spc.py](../../../iris-spc/src/iris_spc/api/spc.py) · [iris-spc web/index.html](../../../iris-spc/web/index.html) · [iris-spc web/actual.js](../../../iris-spc/web/actual.js) · [iris-qms web/qms.js](../../../iris-qms/web/qms.js)

---

## 0. 이 문서만 읽고 실행할 수 있도록 하는 환경 정보

| 항목 | iris-spc | iris-qms |
|---|---|---|
| 실행 | `IRIS_SPC_PORT=3340 ./scripts/dev.sh` | `IRIS_QMS_PORT=3350 ./scripts/dev.sh` |
| venv | `.venv/bin/python` (저장소 내) | `.venv/bin/python` (저장소 내) |
| 테스트 | `.venv/bin/python -m pytest -q` → **46 passed** (2026-08-11 검증) | `.venv/bin/python -m pytest tests -q` → **21 passed** |
| DB | `data/iris_spc.db` | `data/qms.db` |
| 헬스 | `http://127.0.0.1:3340/health` → 200 | `http://127.0.0.1:3350/health` → 200 |

운영 전제 (2026-08-11 확정):

1. iris-spc는 **당분간 독립 서비스로 계속 운영**한다. 이관 후에도 단독 기동·판정이 가능해야 한다.
2. 최종적으로는 **iris-qms가 SPC를 포함**하는 구조로 간다. 이관은 그 준비 작업이다.
3. **마스터 데이터·샘플 raw 데이터의 중복은 승인**되었다. 이 문서의 범위 밖이다(§7).

### 0.1 r3에서 반영한 iris-spc 변경

| 커밋 | 내용 | 이 설계서에 미치는 영향 |
|---|---|---|
| `80d252c` feat: streamline rule and workspace controls | 사이드바를 **마스터 데이터 / 실제 조작 / 관리성 화면 / 반도체 전용 / 자동차 전용** 5그룹으로 재편. 조회조건 접기 토글 추가 | 이관 대상을 **사이드바 항목 단위로 지목 가능**해짐 |
| `44dd734` refactor: separate master settings from query scope | 마스터·통제 패널에 `data-filter-scope="none"` 부여, 조회 범위와 분리 ([actual.js:1520](../../../iris-spc/web/actual.js:1520)) | 계획측/실행측 분리 방향과 **일치**. §3.4 참조 |

**두 커밋 모두 `web/`과 `tests/`만 수정했고 `src/iris_spc/`는 변경되지 않았다.** 따라서 §3의 서버측 이관 항목 13건은 그대로 유효하며, 달라진 것은 각 항목이 화면에서 어디에 붙어 있는가뿐이다.

`AUTOMOTIVE_PROFILE_LOCKED` 위치가 [actual.js:31 → 34](../../../iris-spc/web/actual.js:34)로 이동했다.

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
- **자동차 QMS 시장의 실제 구분**: QMS(경영시스템 — 문서·감사·교육·CAPA) vs CAQ(현장 품질보증 — 측정수집·SPC·게이지·검사평가).
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

**"QMS에 수용처가 있다"는 말은 세 가지 층으로 나눠 봐야 한다.** 테이블만 있는 것과 조작 화면까지 있는 것은 전혀 다르다.

| 층 | 확인 방법 |
|---|---|
| 테이블 | `qms.db` 스키마 |
| API | `iris_qms/api/qms.py` 라우트 |
| **화면** | [`web/qms.js`](../../../iris-qms/web/qms.js)의 `actionButton()` 대상 컬렉션 |

2026-08-11 기준 iris-qms에서 **운영 버튼이 붙어 있는 컬렉션은 `ncrs` · `capas` · `approvals` · `inspections` 넷뿐**이다. 자동차 워크스페이스는 [`qms.js:96`](../../../iris-qms/web/qms.js:96) `automotiveRows()`로 렌더되며 **운영 컬럼 자체가 없다.** `quality_cases` · `eight_d` · `mrb_dispositions` · `msa_studies`는 테이블과 API는 있으나 조작 화면이 없다. `qms_event_history`는 **조회 API조차 없다.**

반면 iris-spc의 Investigation · Action은 **실제로 동작하는 화면**이다 (조작 호출 16곳, 감사 이벤트 88건, Hold→Investigation→Action→verified 완주 이력 존재).

> **규칙: 받을 화면이 QMS에 생긴 뒤에 SPC에서 자른다.**
> 이 순서를 어기면 동작하는 기능이 사라지고 시스템 전체가 퇴보한다.

---

### 3.1 A그룹 — SPC 절단만 (QMS 준비 불필요, 즉시 착수 가능)

| # | SPC 서버측 | SPC 화면측 (사이드바 > 패널) | QMS 수용처 (테이블/API/화면) |
|---|---|---|---|
| 1 | [`spc.py:147`](../../../iris-spc/src/iris_spc/services/spc.py:147) `control_plans` 하드코딩 dict | 자동차 전용 > 자동차 프로파일 → `automotivePanel` 내 **"Control Plan · 특수특성"** 블록 | ✅ / ✅ / ✅ 읽기 |
| 2 | [`spc.py:160`](../../../iris-spc/src/iris_spc/services/spc.py:160) `automotive_payload`의 `ppap` 블록 | 자동차 전용 > 자동차 프로파일 → `automotivePanel` 내 **"PPAP · 초기능력"** 블록 | ✅ / ✅ / △ 생성 버튼만 |
| 4 | [`spc.py:119`](../../../iris-spc/src/iris_spc/services/spc.py:119) `automotive_controls` 배열 | 마스터 데이터 > 업종 프로파일 → `profilePanel` 내 자동차 컨트롤 목록 | — (단순 삭제) |

**변경지시 A**

1. `automotive_payload`에서 `control_plans` dict와 `control_plan` 반환 키를 삭제하고, QMS `GET /api/qms/core-tools?kind=control_plans`(또는 신설 단건 조회) 결과를 `control_id` 기준으로 조회해 대체한다.
2. `ppap` 반환 키를 **완전히 삭제**한다. `automotivePanel`의 PPAP 블록은 QMS 링크로 대체한다.
3. `profile_payload`의 `automotive_controls` 배열을 삭제한다.
4. 절단 후 `automotive_payload`에 남는 것: `cavities` · `characteristic` · `chart` · `capability` · `summary` — **순수 통계 판정만.**
5. 완료 확인: `grep -rn "CP-AX-\|PPAP-AUTO-\|OEM Tier-1" src/` → 0건.

---

### 3.2 B그룹 — QMS 화면 신설 후 절단

**절단 자체는 간단하나, 지금 자르면 기능이 사라진다.**

| # | SPC 서버측 | SPC 화면측 (사이드바 그룹 > 항목 → 패널) | QMS 선행 작업 |
|---|---|---|---|
| 5 | [`api/spc.py:537`](../../../iris-spc/src/iris_spc/api/spc.py:537) `/investigations` GET·POST·PATCH | **실제 조작 > Investigation** → `investigationPanel` | `quality_cases` + `eight_d` **운영 화면 신설** (D1~D8 입력·상태전이) |
| 6 | [`api/spc.py:586`](../../../iris-spc/src/iris_spc/api/spc.py:586) `/actions` GET·POST·PATCH | **실제 조작 > Action · 검증** → `actionPanel` | `eight_d` D5/D6 시정·검증 입력 화면 신설 |
| 7 | `holds.disposition` 컬럼 | **실제 조작 > Hold · Disposition** → `holdPanel` 의 처분 컬럼 | `mrb_dispositions` 요청·승인 화면 신설 |
| 8 | [`api/spc.py:255`](../../../iris-spc/src/iris_spc/api/spc.py:255) `/audit-log` | **관리성 화면 > 감사로그** → `auditPanel` | `qms_event_history` **조회 API + 화면 신설** |
| 9 | [`spc.py:249`](../../../iris-spc/src/iris_spc/services/spc.py:249) `msa_payload` 의 스터디 판정 | **관리성 화면 > MSA · Gage R&R** → `msaPanel` (판정부만) | `msa_studies` 등록·판정 화면 신설 |
| 3 | [`spc.py:111`](../../../iris-spc/src/iris_spc/services/spc.py:111) `governance` 블록 | **마스터 데이터 > 업종 프로파일** → `profilePanel` 거버넌스 영역 | 프로파일에 거버넌스 계약 필드 보강 |

**변경지시 B**

1. **사이드바 항목 제거**: 실제 조작 그룹의 `Investigation` · `Action · 검증`, 관리성 화면 그룹의 `감사로그`. 해당 `sidebar-item` 요소와 패널(`investigationPanel` · `actionPanel` · `auditPanel`)을 함께 제거한다.
2. **`Hold · Disposition` → `Hold`** 로 라벨을 바꾸고 처분 컬럼·입력을 제거한다. 서버측은 `holds` 테이블에서 `disposition` 컬럼을 삭제하고 테이블명을 `process_holds`로 변경한다. **`holds` 테이블 자체는 SPC 잔류다** — `alarm_key`·`subgroup_id`에 붙은 **공정·설비 정지**이지 물량 보류가 아니다. **Lot 보류의 유일 정본은 `qms_auto_lots.state`.**
3. **`msaPanel`은 유지**하되 스터디 등록·합격 판정 영역만 제거한다. **MSA 계산 엔진은 SPC 잔류.**
4. `profile_payload`에서 `governance` 블록을 제거하고 QMS 프로파일 조회로 대체한다.

---

### 3.3 C그룹 — QMS 신규 개발 (수용처가 아예 없음)

| # | SPC 서버측 | SPC 화면측 | QMS 현재 |
|---|---|---|---|
| 10 | [`spc.py:367`](../../../iris-spc/src/iris_spc/services/spc.py:367) `/permissions` | **관리성 화면 > 권한** → `permissionsPanel` | **인증 개념 자체가 없음** (모든 이력 actor = `qms-api` 고정) |
| 11 | [`api/spc.py:183`](../../../iris-spc/src/iris_spc/api/spc.py:183) `PATCH /rule-profile` | **마스터 데이터 > Rule Profile** → `ruleProfilePanel` 의 **저장 버튼만** | 없음 |
| 12 | [`spc.py:661`](../../../iris-spc/src/iris_spc/services/spc.py:661) `ocap_payload` 의 조사·조치·종결 조인부 | **실제 조작 > CIM OCAP · 이력** → `ocapPanel` | 없음 (§8 미결) |
| 13 | [`spc.py:377`](../../../iris-spc/src/iris_spc/services/spc.py:377) `/integrations` | **관리성 화면 > 연동 상태** → `integrationsPanel` | 없음 |

**변경지시 C**

1. `permissionsPanel` · `integrationsPanel`과 해당 사이드바 항목을 **전부 제거**한다.
2. `ruleProfilePanel`은 **조회 전용으로 유지**하고 저장(PATCH) 경로만 제거한다. 룰 정의·계산은 SPC 잔류, **활성화 승인만 QMS**.
3. `ocapPanel`은 **4단계까지 임시 잔류**한다(§8 ②).
4. **#10은 단순 이관이 아니라 신규 설계 과제다.** iris-qms에 권한 체계 자체를 먼저 세워야 한다.

---

### 3.4 새 사이드바 그룹에 대한 판정 — "마스터 데이터" 그룹은 다시 쪼개야 한다

`44dd734`가 만든 **마스터 데이터** 그룹의 4개 항목은 성격이 서로 다르다.

| 항목 | 실제 성격 | 판정 |
|---|---|---|
| 업종 프로파일 | 계획측 + SPC 표시 혼재 | `governance` 블록만 QMS (#3) |
| 공정 마스터 | 제조 마스터 | **SPC 잔류** (중복 승인, §7) |
| **기준선 · 관리한계** | **데이터에서 산출되는 값 — 마스터가 아님** | **SPC 잔류. "실제 조작" 그룹으로 이동 권고** |
| Rule Profile | 정의·계산 = SPC / 활성화 승인 = QMS | 조회 잔류, 저장 제거 (#11) |

**기준선·관리한계를 "마스터 데이터"에 둔 것은 개념상 어긋난다.** 규격(USL/LSL·QMS 소유)은 사람이 정하는 마스터이지만, 관리한계(UCL/LCL)는 공정 데이터에서 산출되는 결과물이다. 둘을 같은 그룹에 두면 "규격을 넓혀 합격시키는" 조작이 화면상 구분되지 않는다. **"실제 조작" 그룹으로 옮길 것을 권고한다.**

방향 자체는 옳다 — `data-filter-scope="none"`으로 마스터·통제 화면을 조회 범위에서 분리한 것은 **계획측/실행측 분리와 정확히 같은 방향**이다.

---

## 4. SPC 잔류 (이관 금지)

| 잔류 대상 | 사이드바 위치 | 이유 |
|---|---|---|
| 관리도 4모드 · **관리한계 계산·동결** | 실제 조작 / 마스터 데이터 | 데이터에서 산출되는 값. 규격(QMS)과 다른 개념 |
| 공정능력 · 분포 분석 · 추이 비교 | 관리성 화면 | 통계 엔진 |
| **MSA 계산 엔진** | 관리성 화면 > MSA | 판정만 QMS, 계산은 SPC |
| Alarm Center · **알람 acknowledge** | 실제 조작 | 감지가 SPC의 존재 이유 |
| **Hold (공정·설비 정지)** | 실제 조작 | 출하가 아닌 공정 상태. `disposition` 컬럼만 제거 |
| Rule Profile **조회·계산** | 마스터 데이터 | 활성화 승인만 QMS |
| Measurement Explorer · 부분군 데이터 | 실제 조작 | 원시 데이터 접근 |
| 공정 마스터 | 마스터 데이터 | 중복 승인 대상(§7) |
| Tool·Chamber · Wafer 균일도 · 재자격평가 **판정** | 반도체 전용 | 공정 특화. 합격 기준값만 QMS(§8 ①) |
| Report Center | 관리성 화면 | PPAP 제출 패키지만 QMS |
| Administration (서비스 상태) | 관리성 화면 | 자기 헬스체크 |

---

## 5. 이관 후 SPC 자립 방안

### 5.1 계획값 캐시

QMS에서 내려받는 계획값(규격 USL/LSL/Target·`spec_revision`·CC/SC 분류·샘플링·반응계획·`control_id`)은 **로컬 캐시에 저장**한다.

- QMS 미기동 시에도 SPC는 캐시값으로 계속 판정한다.
- 캐시 사용 중임을 화면 상단에 명시한다(`계획값 최종 수신: YYYY-MM-DD HH:MM`).
- 캐시는 **읽기 전용**이다. SPC에서 편집 경로를 만들지 않는다.

### 5.2 이관 후 사이드바 예상 구조 (3단계 완료 시점)

```
마스터 데이터
  업종 프로파일        (governance 제거, QMS 조회 표시)
  공정 마스터          (유지)
  Rule Profile         (조회 전용 — 저장 버튼 제거)

실제 조작
  관리도 (계량형)
  관리도 (계수형)
  기준선 · 관리한계     ← 마스터 데이터에서 이동 (§3.4)
  Alarm Center
  Hold                 ← "Hold · Disposition"에서 개칭, 처분 제거
  CIM OCAP · 이력       (4단계까지 임시 잔류)
  Measurement Explorer
  부분군 데이터
  [제거] Investigation  → QMS 링크
  [제거] Action · 검증  → QMS 링크

관리성 화면
  폐루프 현황           (QMS 사건 요약 조회로 축소)
  공정능력 / 분포 분석 / 추이 비교
  MSA · Gage R&R        (계산·스크리닝만, 스터디 판정 제거)
  Report Center
  Administration        (서비스 상태만)
  [제거] 감사로그       → QMS
  [제거] 권한           → QMS
  [제거] 연동 상태      → QMS

반도체 전용            (유지 — 재자격평가는 기준값만 QMS 조회)
자동차 전용            (Control Plan · PPAP 블록 제거, Cavity·통계만 잔류)
```

**제거 5건 · 개칭 1건 · 이동 1건 · 축소 4건.** 사이드바 항목 수는 29 → 24로 줄어든다.

### 5.3 조사·조치 절단 후의 화면 공백 대응

- SPC에는 **"1차 현장 확인 메모" 한 칸만** 남긴다(자유 텍스트, 승인 없음). 위치는 `holdPanel` 하단.
- 정식 원인조사·시정조치는 **QMS 링크로 이동**시킨다.
- 감지 → 정지까지는 SPC 안에서 완결되므로 현장 운영은 끊기지 않는다.

### 5.4 자동차 프로파일 잠금 조건 정의

[`actual.js:34`](../../../iris-spc/web/actual.js:34)의 `AUTOMOTIVE_PROFILE_LOCKED = true`를 유지하되 **해제 조건을 명문화**한다.

```
해제 조건 = QMS Control Plan 연결 완료 (§6 1단계 완료)
```

현재는 "반도체 SPC 완성 전까지"라는 모호한 사유로 잠겨 있다. 1단계 완료를 해제 조건으로 재정의한다.

---

## 6. 이관 순서와 완료 판정

| 단계 | 성격 | 대상 | 완료 판정 기준 |
|---|---|---|---|
| **1** | **SPC 절단** | A그룹 #1 · #2 · #4 | `grep -rn "CP-AX-\|PPAP-AUTO-\|OEM Tier-1" iris-spc/src/` → 0건. `automotive_payload`가 QMS `control_plans` 조회로 동작. §1의 정본 충돌 4건 소멸. `pytest -q` 46건 유지 |
| **2** | **QMS 화면 신설** | 품질사건·8D · MRB 처분 · MSA 스터디 화면, `qms_event_history` 조회 API | `automotiveRows()`에 운영 컬럼 존재. `qms_event_history`에 `record.updated` 계열 이벤트가 실제로 쌓임(현재 0건) |
| **3** | **SPC 절단** | B그룹 #3 · #5~#9 + §3.4 그룹 재배치 | 사이드바에서 Investigation·Action·감사로그 제거. `holds`에 `disposition` 컬럼 부재. 폐루프가 QMS 한 곳에서 종결 |
| **4** | **QMS 신규 개발** | C그룹 #10~#13 | QMS가 SPC를 포함할 준비 완료 |

**1단계는 순수 삭제 + 조회 전환이다.** 코드량이 작고, §1에서 관측된 정본 충돌이 이것만으로 해소된다.

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

- **제안: 4단계로 미루고, 그 전까지 `ocapPanel` 잔류를 임시조치로 명시.**
- 반도체 계획측은 자동차의 Control Plan이 아니라 **Recipe + OCAP**이 중심이므로, QMS에 반도체 계획측 모델을 신설할 때 함께 설계한다.

### ③ 2단계(QMS 화면 신설)의 범위

B그룹 절단을 위해 QMS에 만들어야 할 화면이 5종이다.

- **최소안**: 품질사건·8D·MRB 3종만 만들고 #5·#6·#7 절단. #8·#9는 미룸.
- **완전안**: 5종 전부 만든 뒤 B그룹 일괄 절단.

### ④ 기준선·관리한계 그룹 재배치 (§3.4)

`44dd734`가 "마스터 데이터"에 배치했으나 산출물 성격이다. **"실제 조작"으로 이동 권고** — 확정 필요.

---

## 9. 참고 — 이 설계의 판단 근거가 된 실측

2026-08-11 기준 측정값:

| 항목 | 값 |
|---|---|
| iris-spc HEAD | `44dd734` · pytest **46 passed** · health 200 |
| iris-spc 라우트 | GET 28 · POST 5 · PATCH 5 (총 38) — `80d252c`·`44dd734`로 **변동 없음** (web/·tests/만 수정) |
| iris-spc 사이드바 항목 | 29개 (마스터 4 · 실제조작 9 · 관리성 10 · 반도체 3 · 자동차 2 + 폐루프현황) |
| iris-spc 이관 대상 | 13건 = 라우트 10개 + 페이로드 블록 4개 + 컬럼·판정 로직 3건 |
| 그룹별 분포 | **A(절단만) 3건 · B(화면 신설 후 절단) 6건 · C(신규 개발) 4건** |
| 이관 후 사이드바 | 29 → 24 (제거 5 · 개칭 1 · 이동 1 · 축소 4) |
| iris-qms 변경 엔드포인트 | 62개 (POST 32 · PATCH 30) |
| iris-qms UI가 호출하는 변경 엔드포인트 | **7개 (11%)** |
| iris-qms 운영 버튼 보유 컬렉션 | `ncrs` · `capas` · `approvals` · `inspections` **4종뿐** |
| iris-qms `qms_event_history` 조회 경로 | **없음** (API·화면 모두 부재) |
| iris-spc `audit_events` | 88건 |
| iris-qms `qms_event_history` | 27건 전부 `auto.record.created` / actor `qms-api` (조작 이력 0건) |
| iris-qms 자동차 테이블 | 38개 중 30개 0행 |
