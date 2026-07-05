# 작업지시서 — DIAG-SOT / P1 (M2 Cursor 전용)

- **발행:** 2026-07-05 · Gatekeeper(Claude) → Executor(M2 Cursor)
- **선행:** **P0 게이트 = PASS** (아래 §A). 본 지시서로 P1 착수 허가.
- **기준 문서(절대):** [`P1_SPEC.md`](./P1_SPEC.md) · [`00_MANIFEST.md`](./00_MANIFEST.md). 본 지시서는 P1_SPEC의 **STAGE-ENTRY 확정본**을 포함한다.
- **접근:** M2는 로컬 접근 불가 → **diagnosis-tool `feat/diag-sot-sync`** clone/pull 후 작업, 같은 브랜치에 push. C-Server/prod 무접촉.

---

## A. P0 게이트 판정 (Gatekeeper 독립 검증)

**판정: PASS.** SELF-STATUS를 신뢰하지 않고 Gatekeeper가 직접 재현·확인함.

| 점검(P0_SPEC §6/§7) | 결과 |
|----|------|
| 게이트 머신 diff 0 | ✅ **Gatekeeper 직접 재실행** `run_data_poc.sh` → `PASS q5_recommendation`, `PASS q1_taxonomy(canonical)`, `Q5 74/74`, `PoC PASS` 재현 |
| checksum 113팩 | ✅ 113줄 |
| 골든 픽스처 | ✅ 12 sub(A~I + B02·E02·H02), ko/zh, `_payloads.json` 재현정보 |
| DECISIONS 전 팩 | ✅ 113팩 분류 |
| data/src 인벤토리·무이동 | ✅ 7파일, 무이동 |
| 브랜치 격리 | ✅ `feat/diag-sot-sync` from v1.5 |

**경미사항(P1으로 승계, P0 통과에 영향 없음):**
- `poc_health_2026-07-05.log` 미커밋 — Gatekeeper가 직접 재현했으므로 무의미. P1부터는 게이트 로그도 커밋할 것.
- `run_data_poc.sh`가 `WARN q1_taxonomy: client/server legacy already differ` 를 정확히 포착 = 알려진 taxonomy 드리프트. → §C-2에서 처리.

## B. M2 질문 답변 (P0 보고서 §5)

1. **골든 12 sub 확정:** **승인.** 이 목록으로 고정한다(A~I 대표 9 + B02·E02·H02).
2. **render HTML이 DOM 아닌 decision 파생 스냅샷:** **P1엔 이대로 승인.** P1 게이트의 실질 기준은 `decision.json` 동일성(byte-diff 0 → decision 동일)이다. 실제 A1 DOM 캡처는 **P3**(렌더/콘텐츠 변경 단계)에서 도입.
3. **`data/src` 재생성분 원복 방침:** **승인.** P0 무변경 원칙에 맞음.
4. **DECISIONS 정적 초안 → 런타임 소비 검증 P1 이관:** **승인.** 단 P1에서 **lineage 실검증(I4)** 으로 확정한다(§C-3).

## C. Gatekeeper 확정·정정 (P1 전제)

**C-1. 분류 정정:** `server/data/industry_master.json` = **① 척추**(Core Rule Engine Metadata; `ch2_system/engine_bridge`·`step3_engine` 소비). DECISIONS의 ③ 표기 정정.

**C-2. 불확실 항목 처리(사장 검토점):**
| 항목 | 확정 |
|------|------|
| `industry_scale_model_v1` vs `scale_profile_v3` | **둘 다 live, 다른 엔진**(`core/scale_engine.py` vs `rules/step3_v3_interpret.py`). **통합 금지, 각각 byte-identical 유지.** |
| `system_catalog.json`(루트) | **SQLite `system_catalog` 테이블 경유 소비**(`core/knowledge/sqlite_knowledge_store.py`). JSON↔DB 관계를 **P1 lineage로 검증**(어느 쪽이 소스인지) — ③ 성격이라 이관은 P3, P1은 기록만. |
| `ch1_industries` vs `ch1/industry_packs` vs `ch1_mgmt_model` | **P1 통합 금지.** industry_packs+ch1_industries=한 로더(`ch1_mgmt/engine.py`)의 fallback 2경로, ch1_mgmt_model=별도 로더(`ch1_mgmt/compose.py`). **각각 그대로 byte-identical 재현.** 통합은 P4. |
| `ch1/catalog` vs `ch1/catalogs` | 별개 디렉터리(catalog=drivers/keywords/kpis, catalogs=*_codes). P1 lineage 기록만, 통합은 P4. |
| **Ch2 DB SoT vs JSON SoT** | **P1 범위 아님(③ 질문) → P3로 이연.** P1은 ①② 한정. |

## D. P1 스코프 (확정 — P1_SPEC §2 갱신)

게이트가 이미 **Q1 taxonomy·Q5 recommendation을 diff 0으로 증명**했으므로 순서를 조정한다:

- **P1-a (proven 우선):** `step1_5/industry_product_taxonomy_v3.json`(Q1) + `q5/recommendation_by_subindustry_v1.json`(Q5) 를 **dx_* SoT 파이프라인으로 정식 편입.** 이미 round-trip 되므로 SoT 소유·lineage 확립 + end-to-end 루프 증명이 목적.
- **P1-b (확장):** ① `industry_master`·`ch1/catalogs/industry_codes`·`ch1/catalogs/sub_industry_codes` + ② `step2/routing_product_nature_v3`·`step3/scale_profile_v3`·`step4/automation_profile_v3` 를 같은 머신으로 확장, 각 **byte-diff 0**.

**정확한 팩 최종목록은 P0 `checksums_v1.5.txt` 기준으로 고정.** client 사본 있는 팩은 client도 재현 대상.

## E. dx_* ↔ data/src ↔ packs 관계 (P1 확정)

```
관리탭 편집 → dx_*(iris-hub, 편집 SoT) → export → data/src(build 스테이징, 검증된 머신 재사용)
              → build_data.py → 팩 → raw byte-diff vs legacy = 0
```
- **dx_* = 편집 정본**(D1). **data/src = 직렬화 스테이징**(폐기된 게 아니라 build 입력으로 재사용). **packs = 생성물.**
- P1은 무손실 이관: dx_*·data/src에 원본 구조 보존. **Q4 도메인 flat 정규화(F8) 금지**(byte 파괴). 의미분해는 P3+.

## F. 실행 절차 (Executor)

1. **dx_* 스키마 초안**(P1_SPEC §3 기준) → 보고서에 제시, **Gatekeeper 승인 후 고정**(임의 확정 금지).
2. **P1-a:** Q1 taxonomy·Q5 recommendation → dx_* import → export→data/src→build → **raw byte-diff 0**. `dx_lineage` 채움.
   - **taxonomy 드리프트(§A):** **client 사본을 정본으로 확정**(2026-06-29 방침 승계). server는 client와 일치하도록 재생성(드리프트 봉합) — 단 이 변경은 **의도된 diff로 별도 표기**(P1-a 게이트에서 "server=client 수렴" 1건만 허용, 그 외 0).
3. **P1-b:** ①②확장 팩 → 동일 파이프 → **raw byte-diff 0**.
4. **골든 회귀:** 12 sub `/api/diagnose` 재실행 → decision **무변화**(P0 골든 대비). *(taxonomy 봉합으로 server가 바뀌면 관련 decision 변화가 의도된 것인지 Gatekeeper 확인.)*
5. **lineage 실검증(I4):** §C-2 항목(system_catalog JSON↔DB, ch1 3변종 로더, catalog/catalogs) 실제 소비 경로 확인해 `dx_lineage`·DECISIONS에 반영.
6. **"Z99 추가" 스모크:** 가짜 sub 1행 dx_* 추가→export→build→해당 팩만 반영 확인 후 원복.
7. **게이트 로그·산출 커밋**(경미사항 반영), push.

## G. 금지사항 (Executor)

- ❌ Q4 도메인 flat 정규화·필드 재구성 (byte 파괴).
- ❌ 엔진(`assemble`·`rules`·`core/engine.py`) 수정 (단 taxonomy 봉합의 server 재생성은 **데이터 재생성**이지 엔진수정 아님 — 엔진 코드 불변).
- ❌ ch1 3변종·catalog/catalogs **통합**(P4).
- ❌ Ch2/③ 콘텐츠·systems_catalog·management_analysis 접촉 (P3).
- ❌ Q5 groups 구조 재설계 (무손실 이관만).
- ❌ dx_* 스키마 임의 확장 (Gatekeeper 승인본 외).
- ❌ v1.5 팩 in-place 덮어쓰기 (게이트 PASS 전; 산출은 `build/v2`).
- ❌ 빈칸 임의판단 — 중단·질문(R3).

## H. git·보고서 (P0와 동일 규율)

- diagnosis-tool `feat/diag-sot-sync`에 커밋+push. 메시지 `[DIAG-SOT][P1] ...`.
- **게이트 로그 커밋**(P0 누락 교정): `scripts/data_poc/_baseline/poc_health_p1_<date>.log` + raw byte-diff 리포트.
- 결과 보고서: `docs/diag-sot/reports/P1_RESULT_REPORT.md` — P0 보고서와 동일 항목 + 각 팩 byte-diff 결과표 + lineage 검증 결과 + `P1 SELF-STATUS`.
- dx_* 스키마 초안은 **먼저 제출→승인 후 진행**(F-1).

## I. Exit 게이트 (Gatekeeper 판정)

1. P1 대상 전 팩 **raw byte-diff 0** (taxonomy는 client 기준 + server 수렴 1건 의도표기)
2. 골든 회귀 무변화(의도된 taxonomy 수렴 제외)
3. dx_* 단일정본 + `dx_lineage` 완전 + §C-2 검증 반영
4. "Z99" 국소반영 스모크 통과
5. Q4 도메인 flat 보존 확인

→ PASS 시 P2 지시서 발행. **PASS 판정은 Gatekeeper만.**
