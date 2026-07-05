# 진단툴 진실원(SoT) 단계별 실행·점검 설계 — 역할 분리판

> ⛔ **대체됨 (2026-07-05).** 이 고수준 단일 계획은 Executor(Cursor)가 세부를 임의 판단할 여지를 남김. **분할 세부 스펙 폴더로 대체:** [`diag-sot/`](./diag-sot/00_MANIFEST.md) (신규 버전 선언 + P0~P4 단계별 세부 스펙). 방법·역할·불변 원칙은 그 폴더로 승계.

- **작성일:** 2026-07-05
- **성격:** 실행 착수용 단계 설계. **실행 = M2 Cursor(gpt-5.5), 점검·게이트 = Claude.**
- **상위 설계:** [`DIAGNOSIS_TOOL_SOT_TARGET_DESIGN_2026-07-05.md`](./DIAGNOSIS_TOOL_SOT_TARGET_DESIGN_2026-07-05.md) (3축·요구5·결정D1~D3·§0.5 추적성)
- **방법:** 평행운영(parallel-run) + **byte-diff 게이트** + 팩 단위 컷오버 + 브랜치 롤백.

---

## 0. 역할 분리 (핵심)

| 역할 | 담당 | 책임 | 하지 않는 것 |
|------|------|------|-------------|
| **실행자(Executor)** | **M2 Cursor (gpt-5.5)** | SoT 스키마·sync·migration 코드 작성, 실행, diff/회귀 실행, 커밋 | 게이트 자체 판정(통과 선언)은 못 함 |
| **점검자·게이트(Gatekeeper)** | **Claude** | 단계별 exit 게이트 판정, 산출물 검증, 다음 단계 승인/반려, 설계 갱신 | **실행 코드 작성 안 함** (설계·검증만) |

**단계 진행 프로토콜 (매 단계 반복):**
```
Executor: 해당 단계 작업 → 산출물 + 게이트 증거(diff 리포트·회귀 결과) 제출
Gatekeeper(Claude): 점검항목 대조 → PASS면 다음 단계 승인 / FAIL이면 반려사유+수정지시
※ Gatekeeper PASS 전에는 다음 단계 착수 금지.
```

---

## 1. 불변 원칙 (전 단계 공통 — 타협 없음)

| # | 원칙 |
|---|------|
| I1 | **prod 무접촉** — 외부 배포 서버가 쓰는 것과 다른 브랜치. main 병합은 게이트 통과분만 |
| I2 | **byte 동일성 우선** — 구조가 바뀌어도 **출력 팩은 diff 0**(behavior 무변경)을 기본값으로. 의도적 변경은 P2부터 명시적으로만 |
| I3 | **정본 단일(D1)** — iris-hub가 SoT. diagnosis-tool `data`는 sync 생성물, 수기편집 금지 |
| I4 | **추적성(§0.5)** — 모든 편집은 lineage(필드→팩path→소비챕터)를 드러냄 |
| I5 | **롤백 = 브랜치 드롭** — 각 단계는 원복 가능하게 격리 |

---

## 2. 브랜치 (cross-repo)

| repo | 현재 | 작업 브랜치 | 역할 |
|------|------|-------------|------|
| iris-hub | `feat/hub-rebuild` | `feat/diag-sot` | SoT(dx_*)·관리탭·sync 발신 |
| diagnosis-tool | `v1.5` | `feat/diag-sot-sync` | sync 수신처(생성물)·diff게이트·회귀 |

- 롤백 = 두 브랜치 드롭, `v1.5`/`feat/hub-rebuild` 그대로.
- **선재 사실:** diagnosis-tool에 `data/src`(2026-06-29 PoC 산출) + `scripts/run_data_poc.sh`·`scripts/data_poc/`가 이미 존재 → P0에서 재활용/처리 판정.

---

## 3. 단계 개요

| 단계 | 목적 | 출력 변화 | 엔진 | Exit 게이트 |
|------|------|-----------|------|-------------|
| **P0** | 기반·게이트 건강검진 | 없음 | 무 | 현상태 diff 0 + 골든 픽스처 확보 |
| **P1** | ①척추 + ②Q매트릭스 SoT화 | **diff 0** | 무변경 | 전 P1팩 byte-diff 0 + 골든 무변화 |
| **P2** | 고정라벨 언어팩 + resolver ko기본 | **의도된 diff만** | 경미 | diff=의도분만 + 4언어 키 패리티 |
| **P3** | ③보고콘텐츠 세분화 + 엔진 부분개편 | new-shape(dev only) | 부분개편 | 챕터 스냅샷 + sub_override 검증 + prod 무노출 |
| **P4** | 잔여 이관·legacy 격리·lineage 완성 | 정리 | 정리 | MANIFEST live=로더 100% + 고아팩 0 |

---

## 4. 단계별 상세 (Executor 작업 ↔ Gatekeeper 점검)

### P0 — 기반·게이트 건강검진
**Executor:**
1. 브랜치 2개 생성(§2).
2. **골든 픽스처 구축:** 대표 세부산업(축별 커버) N개로 `/api/diagnose` 실행 → `decision.json`·렌더 HTML 저장(회귀 기준선).
3. 현재 전 팩 checksum 베이스라인.
4. `run_data_poc.sh` 재실행 → **현재 상태에서 diff 0 재현되는지** 확인. `data/src`·`data_poc` 자산 상태 정리.
5. **결정표 초안:** "생성물 vs DB정본" 팩별(어느 팩을 DB정본 승격, 어느 `_generate_*.py` 은퇴) + `data/src` 처리(iris-hub 이관 vs sync스테이징 유지).

**Gatekeeper(나) 점검:** 브랜치가 main/prod와 격리됐나 · 골든 픽스처가 3축·대표 sub를 덮나 · diff 도구가 현상태 green인가 · 결정표가 모든 팩을 빠짐없이 분류했나.
**Gate:** 베이스라인 diff 0 + 골든셋 존재 + 결정표 완결.
**Rollback:** 브랜치 드롭.

### P1 — ①척추 + ②Q매트릭스 (legacy-shape sync, 엔진 무변경)
**Executor:**
1. iris-hub `dx_*`에 registry(industries/sub_industries) + Q2/Q3/Q4 매트릭스 스키마 생성, 현재 팩에서 **import**.
2. **sync 작성:** DB → **현재 팩 파일과 동일 경로·동일 shape**로 역생성.
3. diff 게이트: 생성팩 vs 현재 팩 = **byte-diff 0**.
4. 골든 회귀: `/api/diagnose` 재실행 → decision **무변화**.
5. lineage 메타 부착(필드→팩path→소비 챕터).

**Gatekeeper 점검:** P1 대상 전 팩 diff 0인가 · 골든 decision 무변화인가 · SoT가 단일 소유(중복 편집원 없음)인가 · lineage 매핑 실재·정확한가 · 척추 "세부산업 추가"가 실제 1행 연산인가(75번째 추가 테스트).
**Gate:** diff 0 + 골든 무변화 + lineage 검증.
**Rollback:** 브랜치 드롭(팩 원본 그대로).

### P2 — 고정라벨 언어팩 + resolver ko-기본 (요구1·4·D3)
**Executor:**
1. `fixed_labels` 카탈로그 통합(id→{ko,zh,en,ja}), Q1~Q5 UX·A1/A2 라벨 연결.
2. resolver `chain=[lang, ko]`, **ko 필수** 강제, `DEFAULT_LANG=zh → ko` 전환.
3. 4언어 키 패리티·커버리지 리포트.
4. 골든 **재베이스라인**(언어 기본 변경은 의도된 diff).

**Gatekeeper 점검:** diff가 **오직 의도된 언어기본 변경**뿐인가(콘텐츠 무단변경 0) · zh였던 자리에 ko가 올바로 노출되나 · 미작성 언어가 ko fallback 되나 · ko 필수 CI가 실제 강제되나 · 4언어 키 집합 동일한가.
**Gate:** diff=의도분만 + 패리티 리포트 + ko fallback 스냅샷.
**Rollback:** 브랜치 드롭.

### P3 — ③보고콘텐츠 세분화 + 엔진 부분개편 (요구3·D2)
**Executor:**
1. 콘텐츠 모델 구축: `system → module(=capabilities 엔티티화) → sub_override(키워드·포인트 델타)`. systems_catalog 등 이관, **ko-master 콘텐츠**.
2. 엔진 부분개편: A1/A2가 sub_override 델타 소비(ch2에 `by_sub_industry` 추가 — ch3/6 캐스케이드와 동형).
3. new-shape 팩 = **dev 전용**, prod 미전송.
4. 챕터 HTML 스냅샷.

**Gatekeeper 점검:** sub_override 델타가 base 위에 올바로 합류하나 · ch2 세부산업 차별화가 실제 생기나(이전 공백) · Pop→MES→G-MES 티어가 maturity/scale로 정합한가 · ko-master+fallback 지켜지나 · **prod가 여전히 legacy로만 서빙되나(무노출 확인)** · 챕터 스냅샷 회귀 허용범위인가.
**Gate:** 챕터 스냅샷 리뷰 + sub_override 검증 + prod 무노출.
**Rollback:** 브랜치 드롭(new-shape는 dev에만 존재).

### P4 — 잔여 이관·legacy 격리·lineage 완성
**Executor:**
1. 잔여 팩(Q5·ch4/5·roi·catalogs) 이관, `_generate_*.py` 은퇴 대상 정리, legacy·중복(3홈·v2/v3) `_archive` 격리.
2. 관리탭 **lineage 뷰** 완성(셀/노드 → 팩path → 소비챕터 표시).
3. MANIFEST: live=로더 100%, consumers/status 완비.

**Gatekeeper 점검:** MANIFEST live가 실제 로더와 100% 일치하나 · 고아팩(로더 없는 live) 0인가 · 은퇴한 생성기가 커버리지 공백 안 남기나 · lineage 뷰가 실제 경로와 일치하나 · `data` 수기편집 금지(생성물)임이 CI로 강제되나.
**Gate:** 전체 인벤토리 재조정 완료 + lineage 정확.
**Rollback:** 팩 단위(각 이관이 독립 diff 게이트 통과분).

---

## 5. 산출물·결정 아티팩트 (Executor 생성 → Gatekeeper 승인)

| 아티팩트 | 단계 | 내용 |
|----------|------|------|
| 골든 픽스처셋 | P0 | 대표 sub × `/api/diagnose` decision·HTML 기준선 |
| **생성물 vs DB정본 결정표** | P0 | 팩별: DB정본 승격 여부 · `_generate_*.py` 은퇴 여부 · `data/src` 처리 |
| sync 매핑(lineage) | P1~ | 필드 → 팩path → 소비 챕터엔진 |
| diff 리포트 | 매 단계 | 게이트 증거 |
| MANIFEST | P1~P4 | src·build_outputs·consumers·status |

---

## 6. 커밋·병합 규약

- Executor는 **작업 브랜치에만** 커밋. 단계 게이트 PASS 후 Gatekeeper 승인 → main 병합 후보.
- prod 배포 브랜치는 **P1(diff 0) 병합까지도 behavior 무변경** → 안전. P2 이후 병합은 의도된 변경 검토 후.
- 커밋 메시지: 단계 태그(`[P1]` 등) + diff게이트 결과 첨부.

## 부록. 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-07-05 | 초판 — 역할분리(Cursor 실행/Claude 점검)·P0~P4·게이트·브랜치 규약 |
