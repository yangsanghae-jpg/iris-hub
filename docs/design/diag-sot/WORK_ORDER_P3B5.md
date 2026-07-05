# 작업지시서 — DIAG-SOT / P3b-5 (sub_override 실제 표면화 = 요구3 실현)

- **발행:** 2026-07-06 · Gatekeeper(Claude) → Executor(M2 Cursor)
- **선행:** P3b core PASS(dx byte-0 + compose flag-off no-op). **이 단계가 P3의 "가시 효과" 실현.**
- **접근:** diagnosis-tool `feat/diag-sot-sync`. **flag-off = prod 무노출 유지, C-Server 무접촉.**

---

## A. 왜 필요한가 (문제 진단)

P3b까지 **배관은 완성**됐으나 **flag-on에서 sub_override가 실제 리포트에 표면화되지 않는다.**
- Gatekeeper 확인: `run_engine`·golden decision의 `ch2`(`blocks=[by_domain, systems, domain_cards]`)에 `p3b_dev_modules`가 없음. M2가 수정한 `_build_card1_system_capabilities_variant` 출력이 **decision.ch2에 나타나는지 자체가 불명확**.
- 즉 요구3("제안 시스템→기능(module)→세부산업 특화")의 **가시 효과 = 0**. 이걸 실현해야 P3 완료.

## B. P3b-5-0 — 실제 앱 진단 (먼저, 필수)

**M2는 서버리스 추정 말고 진짜 리포트 경로로 확인:**
1. **flag-on으로 실제 진단 실행:** `DIAG_SOT_DEV=1` 환경에서 target sub(예 **B01 logic_foundry**) 1건 `/api/diagnose`(또는 실제 compose 경로) 실행.
2. **A1/A2 리포트(또는 decision) 어디에 sub_override가 나와야 하는지 확정:**
   - `_build_card1_system_capabilities_variant` 출력이 **decision의 어느 경로**로 들어가는지(ch2.blocks? a1 렌더? 별도 카드?).
   - 안 들어가면 **어느 함수/구조가 실제 리포트의 "시스템별 기능"을 만드는지** 역추적.
3. **코드 정렬 확인:** Card1/리포트 섹션의 system code(MES·DISPATCH·ROUTE_EXEC·EAP·QMS·FDC 등) ↔ `dx_ch2_module.system_id`(DISPATCH·EAP·FDC·ERP·MES 등 실재) **교집합** 산출. 미정렬 코드(ROUTE_EXEC·QMS 등)는 alias/매핑 필요 여부 기록.
4. 결과를 `P3B5_DIAGNOSIS.md`로 제출 → Gatekeeper가 표면화 지점·정렬 방식 확정.

## C. P3b-5 구현 (진단 확정 후)

1. **표면화 배선:** 확정된 실제 출력 지점에 `DIAG_SOT_DEV=1`일 때만 module/sub_override(키워드·포인트)를 부착. flag-off는 여전히 no-op.
2. **코드 정렬:** 리포트 system code ↔ module system_id 매칭(필요시 alias). 근거 없는 매핑 금지(issue).
3. **가시 데모:** **target sub 최소 1개(B01)** 에서 flag-on 시 세부산업 특화 키워드/포인트가 **실제 리포트에 표시**됨을 스냅샷으로 증명.
4. **sub_override 콘텐츠:** B01 등 target에 대해 ko-master 키워드/포인트 실제 채움(요구3의 "품질관리 등에 세부산업별 키워드/포인트 추가"). 근거 = Card1 V3 profile 등.

## D. 게이트

1. **flag-off = baseline 전체 decision 동일**(12/12, P3b 방식) — prod 무노출 불변.
2. **flag-on = target sub 리포트에 sub_override 실제 표시**(스냅샷 증명).
3. 코드 정렬 근거/issue 명확, SUB_* 추정 0, 기존 zh 보존.

## E. 금지

Ch2 전체 카드 교체·tier·DB·server lang flip·`lang_ko.py` 변경·prod `systems_catalog` 편집·flag-off 출력 변경.

## F. git·보고서

`P3B5_DIAGNOSIS.md`(진단) → 승인 → 구현 → `P3B5_RESULT_REPORT.md`(flag-on 스냅샷 + flag-off 무변경 + 정렬근거). git 막히면 경로·해시 통지 → Gatekeeper 대행.

> **핵심:** 이 단계 통과 = **세부산업 특화가 실제 리포트에 보임** = 요구3 실현 = P3 완료. flag-off 무노출은 절대 불변. PASS 판정은 Gatekeeper.
