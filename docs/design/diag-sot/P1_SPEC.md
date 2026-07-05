# P1 — ①척추 + ②Q매트릭스 SoT화 (legacy-shape sync · 엔진 무변경) 세부 스펙

- **상태:** 확정 (P0 PASS 후 착수)
- **선행 게이트:** P0 PASS
- **출력 변화:** **없음 (byte-diff 0)** — 이 단계의 존재 이유가 "방법 증명"
- **엔진:** **무변경**

> 이 단계의 성패가 DIAG-SOT 전체를 좌우한다. 목표는 기능 추가가 아니라 **"SoT→sync가 현 팩을 글자까지 재현함"의 증명**이다.

---

## 1. 목적

①척추(registry)와 ②Q2/Q3/Q4 매트릭스를 iris-hub `dx_*` 정본으로 옮기고, sync가 **현재 팩과 byte 동일**하게 역생성함을 증명한다. Q5는 P2/P4(구조 상이). 콘텐츠(③)는 손대지 않는다.

## 2. 대상 팩 (P1 스코프 — 고정)

| 축 | 팩 path | 소비(무변경 대상) |
|----|---------|-------------------|
| ① | `server/data/industry_master.json` | 룰엔진 metadata |
| ① | `server/data/ch1/catalogs/sub_industry_codes.json` | sub 코드계(SUB_X_YYY) |
| ① | `server/data/ch1/catalogs/industry_codes.json` | 산업 코드 |
| ② | `server/data/step2/routing_product_nature_v3.json` | Q2 (+ client 사본) |
| ② | `server/data/step3/scale_profile_v3.json` | `rules/step3_v3_interpret.py:load_scale_profile_v3` (+ client) |
| ② | `server/data/step4/automation_profile_v3.json` | `rules/step4_v3_interpret.py`, `core/engine.py` (+ client) |

> **정확한 최종 목록·client 사본 포함 여부는 P0 checksum 베이스라인으로 확정**한다. 위는 기준. client 사본 있는 팩은 client도 동일 재현 대상(드리프트 봉합).

## 3. SoT 스키마 (iris-hub dx_*) — 확정

registry + 매트릭스를 아래 테이블로. **iris-hub가 정본.**

```
dx_industry(       code PK, label_ko, label_zh, label_en, label_ja, added_in, status, raw_json )
dx_sub_industry(   code PK,           -- A01.. (매트릭스 키)
                   alt_code,          -- SUB_X_YYY (sub_industry_codes 계)
                   parent_code FK→dx_industry,
                   label_ko, label_zh, label_en, label_ja, added_in, status, raw_json )
dx_q_matrix(       q ∈ {q2,q3,q4}, sub_code FK, field_path, value_json,
                   PRIMARY KEY(q, sub_code, field_path) )   -- 팩의 subindustry_profiles를 평탄 저장
dx_q_framework(    q, block, value_json )   -- metadata/domains/axes/levels/dictionary 등 sub 무관 공유부
dx_lineage(        sut_field, pack_path, consumer )   -- 추적성(I4): 필드→팩→소비
```

- **원칙:** P1은 **무손실 이관**이 목표다. `raw_json`/`value_json`으로 **원본 구조를 그대로** 보존(의미론적 분해는 P3+). Q4 도메인 flat 정규화(F8)는 **P1에서 하지 않음** — byte 재현을 깨므로 금지.
- **정확한 컬럼·타입 최종본은 Executor가 P0 DECISIONS 확정본 기준으로 초안 → Gatekeeper 승인 후 고정.**

## 4. sync (build) 계약 — legacy-shape 역생성

- 위치: iris-hub sync 발신 + diagnosis-tool 수신. 게이트는 `scripts/data_poc/` 재사용/확장.
- 규칙: `dx_* → 대상 팩 path`로, **키 순서·들여쓰기·인코딩·개행까지 원본과 동일**하게 직렬화.
  - JSON 직렬화 옵션(정렬·ensure_ascii·indent·말미개행)을 원본에 맞춰 `common.py`에 고정.
  - `diff_test_pack.py`의 canonical diff가 아니라 **raw byte diff**를 게이트로 사용(0이어야 함).
- **새 버전 루트 생성:** 산출은 우선 **버전 네임스페이스(예: `build/v2/…`)** 에 생성 후 byte-diff. v1.5 파일 in-place 덮어쓰기는 게이트 PASS 후에만(컷오버).

## 5. 실행 절차 (Executor)

1. dx_* 스키마 생성(§3 승인본) — iris-hub.
2. **import:** §2 팩 → dx_* 적재(무손실). 라인리지(`dx_lineage`) 채움.
3. **sync/build:** dx_* → `build/v2/**` 팩 생성(§4 규칙).
4. **byte-diff 게이트:** `build/v2/**` vs 현재 팩 = **0**. 리포트 산출.
5. **골든 회귀:** `build/v2`를 서빙에 임시 연결(dev) → 골든 sub `/api/diagnose` 재실행 → decision·HTML **P0 골든과 diff 0**.
6. "세부산업 추가" 스모크: 가짜 sub(예: `Z99`)를 dx_*에 1행 추가→sync→해당 팩에만 반영되는지 확인 후 원복(척추 1행 연산 증명).

## 6. 금지사항 (Executor)

- ❌ Q4 도메인 flat 정규화·필드 재구성 (byte 재현 파괴). P1은 **무손실 보존만**.
- ❌ 엔진(`assemble`,`rules`,`core/engine.py`) 수정.
- ❌ 콘텐츠 팩(③: systems_catalog·mgmt·roi 등) 접촉.
- ❌ v1.5 팩 in-place 덮어쓰기 (게이트 PASS 전).
- ❌ Q5 포함 (구조 상이 — P2/P4).
- ❌ 스키마 컬럼 임의 확장 (§3 승인본 외).

## 7. Gatekeeper 점검항목 (Claude)

- [ ] §2 대상 전 팩 **raw byte-diff 0** (client 사본 포함)
- [ ] 골든 회귀: 전 골든 sub의 decision·HTML **무변화**
- [ ] dx_*가 **단일 정본** — 동일 데이터의 편집원이 둘 이상 아님
- [ ] `dx_lineage`가 §2 전 팩의 필드→팩→소비를 정확히 담음
- [ ] "Z99 추가" 스모크가 **국소 1행 반영**으로 동작
- [ ] Q4 도메인 flat이 **그대로 보존**됐는지(정규화 안 함 확인)
- [ ] 산출이 `build/v2`에만, v1.5 무접촉

## 8. Exit 게이트 (PASS 조건)

1. §2 전 팩 raw byte-diff 0
2. 골든 회귀 무변화
3. lineage 완전 + 단일정본 확인
4. 척추 1행연산 증명

→ PASS 시 (선택) v1.5 컷오버 커밋 + **P2 스펙 확정**.

## 9. 롤백

- `build/v2` 폐기 + 브랜치 드롭. v1.5 무손(in-place 미변경).
