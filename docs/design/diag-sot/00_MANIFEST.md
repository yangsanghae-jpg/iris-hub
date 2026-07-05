# DIAG-SOT — 진단툴 진실원(SoT) 신규 버전 선언·매니페스트

- **선언일:** 2026-07-05
- **코드네임:** **DIAG-SOT**
- **성격:** 진단툴 데이터 아키텍처를 iris-hub 진실원 중심으로 재편하는 **신규 버전 프로젝트**. 현 `v1.5` 위에 in-place 수정이 아니라, **별도 버전으로 평행 진행**함을 선언한다.
- **상위 배경 설계(읽기 전용, 이 폴더가 실행 정본):**
  - 목표 설계: [`../DIAGNOSIS_TOOL_SOT_TARGET_DESIGN_2026-07-05.md`](../DIAGNOSIS_TOOL_SOT_TARGET_DESIGN_2026-07-05.md)
  - 배경(운영검증): 목업탐색·구조평가·전수감사 (`../DIAGNOSIS_*_2026-07-05.md`)
  - ⛔ 폐기: `../DIAGNOSIS_TOOL_DATA_TARGET_ARCH_*`(파일종합안), `../DIAGNOSIS_TOOL_SOT_STAGED_PLAN_*`(고수준 초안 → 본 폴더 분할판으로 대체)

---

## 0. 이 문서의 목적

이 폴더(`diag-sot/`)는 **DIAG-SOT의 유일 실행 정본**이다. 각 단계 세부 스펙은 **Gatekeeper(Claude)가 확정**하며, Executor(M2 Cursor)는 스펙을 **문자 그대로** 실행한다. **스펙에 없는 판단·확장·구조변경은 금지**한다.

---

## 1. 신규 버전 선언 (시스템 + git)

| 구분 | 선언 | 값 |
|------|------|-----|
| **버전** | 데이터 아키텍처 신규 버전 | **DIAG-SOT / data-arch v2.0** (앱 v2.0 문서와 별개; 데이터 계보) |
| **git · iris-hub** | 브랜치 | **`feat/diag-sot`** (from `feat/hub-rebuild`) — SoT(dx_*)·관리탭·sync 발신 |
| **git · diagnosis-tool** | 브랜치 | **`feat/diag-sot-sync`** (from `v1.5`) — sync 수신처·게이트·회귀 |
| **시스템 · 정본 위치** | SoT 물리 소유 | **iris-hub** `dx_*` DB (+ export). diagnosis-tool `data`는 생성물 |
| **시스템 · 생성 네임스페이스** | sync 산출 루트 | **새 버전 루트에 생성**(v1.5 in-place 덮어쓰기 금지). 정확 경로는 P0에서 확정 |
| **롤백** | 원복 수단 | 두 브랜치 드롭 → `v1.5`/`feat/hub-rebuild` 무손 |
| **prod** | 외부 배포 서버 | **무접촉.** main/prod 병합은 게이트 통과분만 |

> **git 선언 실행:** 브랜치 2개 생성은 **P0의 첫 작업(Executor)**. 본 매니페스트가 그 이름·기점을 고정한다. Cursor는 다른 이름/기점 사용 금지.

---

## 2. 역할 분리 (불변)

| 역할 | 담당 | 권한 | 금지 |
|------|------|------|------|
| **Executor** | M2 Cursor (gpt-5.5) | 스펙대로 코드작성·실행·커밋 | 스펙 외 판단·구조변경·게이트 자체통과 선언 |
| **Gatekeeper** | Claude | 단계 스펙 확정, 산출물 점검, PASS/FAIL 판정, 다음단계 승인 | 실행 코드 작성 |

**단계 루프:** `Gatekeeper 스펙 확정 → Executor 실행+증거제출 → Gatekeeper 점검 → PASS 시 다음단계 스펙 확정`. **PASS 전 다음 단계 착수 금지.**

---

## 3. 불변 원칙 (전 단계)

| # | 원칙 |
|---|------|
| I1 | **prod 무접촉** |
| I2 | **byte 동일성 우선** — 출력 팩 diff 0 기본. 의도적 변경은 P2부터 명시적으로만 |
| I3 | **정본 단일** — iris-hub SoT. diagnosis-tool `data` 수기편집 금지(생성물) |
| I4 | **추적성** — 모든 편집이 lineage(필드→팩path→소비챕터) 노출 |
| I5 | **롤백 가능** — 각 단계 격리, 브랜치/팩 단위 원복 |
| I6 | **스펙 외 금지** — Executor는 본 폴더 스펙에 없는 어떤 결정도 하지 않음 |

---

## 4. 단계 인덱스 (분할 세부 스펙)

| 단계 | 문서 | 목적 | 출력변화 | 상태 |
|------|------|------|----------|------|
| **P0** | [`P0_SPEC.md`](./P0_SPEC.md) · [결과](./reports/P0_RESULT_REPORT.md) | 기반·게이트 건강검진·결정표 | 없음 | ✅ **PASS** (Gatekeeper 독립검증 2026-07-05) |
| **P1** | [`P1_SPEC.md`](./P1_SPEC.md) · [지시](./WORK_ORDER_P1.md) | ①척추 + ②Q매트릭스 SoT화(legacy-shape) | diff 0 | **진행 지시 발행** (P1-a: Q1·Q5 / P1-b: registry+Q2/3/4) |
| **P2** | [`P2_SPEC.md`](./P2_SPEC.md) | 고정라벨 언어팩 + resolver ko기본 | 의도된 diff만 | 골격 확정 · 정밀스키마 **P1 통과 후 Gatekeeper 확정** |
| **P3** | [`P3_SPEC.md`](./P3_SPEC.md) | ③보고콘텐츠 세분화 + 엔진 부분개편 | new-shape(dev) | 골격 확정 · 정밀스키마 **P2 통과 후 확정** |
| **P4** | [`P4_SPEC.md`](./P4_SPEC.md) | 잔여 이관·legacy 격리·lineage 완성 | 정리 | 골격 확정 · 정밀 **P3 통과 후 확정** |

> **정밀스키마 지연의 이유:** P2~P4의 정확 스키마는 선행 단계 산출(registry·sync 계약)에 의존한다. 그 상세를 지금 지어내면 근거 없는 스펙이 된다. 따라서 **골격·불변·게이트·금지사항은 지금 확정**하고, **정확 필드/경로는 선행 게이트 통과 시 Gatekeeper가 해당 문서에 추가**한다. Executor는 그 확정 전 해당 단계 착수 금지 — 이것이 improvisation 방지 장치다.

## 5. 개요·아키텍처

→ [`10_OVERVIEW.md`](./10_OVERVIEW.md)

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-07-05 | 선언 — 신규 버전 DIAG-SOT, 브랜치·역할·불변·단계 인덱스 |
