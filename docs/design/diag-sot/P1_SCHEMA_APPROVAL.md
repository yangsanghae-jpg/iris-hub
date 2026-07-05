# Gatekeeper 판정 — DIAG-SOT P1 dx_* 스키마 초안

- **판정일:** 2026-07-05 · Gatekeeper(Claude)
- **대상:** `docs/diag-sot/reports/P1_SCHEMA_DRAFT.md` (commit `cd2c783`)
- **판정: ✅ 승인 (수정 4건 반영 조건).** 수정 반영 후 **P1-a 구현 착수 허가.**

---

## 0. 총평

초안은 P1 원칙(무손실·byte-repro·통합금지·no-guess)을 정확히 지켰다. 특히:
- `dx_pack_manifest.writer_profile_json`(key order/indent/ensure_ascii/trailing newline) = **raw byte-diff 0의 정확한 전제**. 승인.
- `dx_lineage_issue`로 "빈칸은 추정 말고 이슈화" = R3 규율 준수. 승인.
- Q5를 별도 테이블로 분리한 판단 = shape 상이 반영, 옳음.

## 1. 승인 요청 5건 답변

| # | 질문 | 판정 |
|---|------|------|
| 1 | `dx_pack_manifest` 공통 manifest 테이블 | ✅ **승인.** byte-repro엔 직렬화 정책 추적이 필수. |
| 2 | Q5를 `dx_q_matrix`에 합치지 않고 `dx_q5_*` 별도 | ✅ **승인.** Q5는 `recommendations[]`+`groups` 구조라 Q2/3/4 matrix와 다름. 억지 편입 금지. |
| 3 | `industry_master` shared blocks 위치 | ⚠️ **수정: 별도 `dx_registry_framework` 테이블.** (아래 §2-A) |
| 4 | `SUB_*`↔`A01` 근거 부족 시 issue 처리 | ✅ **승인 (단서 有).** (아래 §2-B) |
| 5 | build output root | ✅ **`data/build/v2/**` 채택** (PoC 관성 유지). 문서 예시를 이에 맞춤. |

## 2. 필수 수정 (4건)

### A. 레지스트리 프레임워크는 별도 테이블 (질문3)
`q='registry'`로 `dx_q_framework`에 얹지 말 것. **`dx_registry_framework(block, pack_id, value_json, source_json_pointer, PK(block,pack_id,source_json_pointer))`** 신설.
- **이유:** 이 프로젝트의 핵심 명제가 "①척추·②평가·③보고는 서로 다른 성격"이다. `q` 프레임(②)에 registry(①)를 섞으면 그 경계가 흐려진다. 테이블 1개 늘어도 **축 분리 유지**가 우선. `industry_master`의 `schema_policy`/`meta`/`focus_definitions`는 여기로.

### B. `SUB_*`↔`A01` — 먼저 alias/meta 팩 확인 후 issue (질문4)
임의 매핑 금지는 승인. **단, issue로 남기기 전에** `server/data/ch1/sub_industry_aliases.json`·`sub_industry_meta.json`에 매핑 근거가 있는지 먼저 확인할 것.
- 근거 있으면 → 그 팩을 lineage 출처로 alt_code 연결.
- 근거 없으면 → `dx_lineage_issue(issue_kind='alt_code_mapping_uncertain')`. **추정 금지.**

### C. 재구성 충실도 — export 소스는 raw, label_*는 파생 (전 테이블 공통)
byte-diff 0의 안전을 위해 **P1 export/build는 `raw_json`/`value_json` 무손실 번들에서 재구성**한다.
- `dx_industry.label_ko/zh/...` 등 정규화 컬럼은 **P1에서 파생(읽기) 투영**일 뿐, **export 소스가 아니다.** (편집 경로로의 승격은 P2+ 관리탭 편집 착지 때.)
- 기존 PoC가 q1/q5에서 decompose→reassemble로 byte-0을 이미 달성했다. Q2/3/4·registry도 **같은 방식으로 재조립해 byte-0**을 낸다.
- **어떤 팩이 재조립으로 byte-0에 도달 못 하면** → passthrough로 위장하지 말고 `dx_lineage_issue`로 **flag+defer**. (P1은 되는 것만 통과시킨다.)

### D. build root 문구 정합 (질문5)
`data/build/v2/**`로 확정. 초안 §5.2의 이중표기 제거.

## 3. 그대로 승인 (수정 불필요)

- `dx_industry`/`dx_sub_industry`/`dx_q_framework`/`dx_q_matrix`/`dx_q5_framework`/`dx_q5_recommendation`/`dx_lineage`/`dx_lineage_issue`/`dx_smoke_change_log` 구조·PK·컬럼.
- writer_profile, raw byte-diff rule, import mapping 초안, lineage 검증 계획(§6).
- P1-a taxonomy 드리프트 = client 정본 + server 수렴 1건 의도 diff 표기.

## 4. 진행 허가 + 재확인 게이트

**수정 A~D 반영 → P1-a 착수 허가.** 순서: 스키마 확정(A~D) → P1-a(Q1·Q5) import→export→build→**raw byte-diff 0** + 골든 무변화 → 보고. **P1-b는 P1-a 통과 보고 후 진행**(한 번에 몰아서 금지, 단계 내에서도 a→b 순).

재확인 시 Gatekeeper가 볼 것:
- 수정 A~D 반영 여부
- P1-a raw byte-diff 0 (taxonomy 의도 diff 1건 외 0)
- 골든 회귀 무변화(taxonomy 수렴 영향분은 의도 표기)
- `dx_lineage` 채움 + SUB_*↔A01 처리(근거/이슈)
- 재조립 실패 팩의 flag+defer 여부

> **주의(경미사항 재발 방지):** P1 게이트 로그(`poc_health_p1_*.log`)와 raw byte-diff 리포트를 **반드시 커밋**할 것(P0에서 로그 누락 있었음).

**SELF-STATUS는 Executor까지. PASS 판정은 Gatekeeper.**
