# Gatekeeper 판정 — DIAG-SOT P3b (2차, compose fix)

- **판정일:** 2026-07-06 · Gatekeeper(Claude) · compose fix commit `f9bc90a`
- **판정: ✅ P3b PASS** (dx-side + compose flag-off no-op). P3(P3a+P3b) core 완료.

---

## A. compose.py flag-off leak 수정 검증 (Gatekeeper 독립)

- **결정적 delta test:** flag-off에서 **P3b compose.py == baseline compose.py** 전체 decision **12/12 동일**(git stash로 baseline 교체·같은 경로 비교, 후 복원 확인). → **P3b는 `DIAG_SOT_DEV` off면 완전 no-op = prod 무노출 확정.**
- 구조: `system_code`/`p3b_dev_modules`는 flag-on `enriched_section`에만, 매칭 code는 `section_codes` 병렬리스트, flag-off는 `return sections` no-op. (지적한 무조건 `system_code` 추가 제거됨.)
- 무접촉: compose.py 외 금지영역 무편집.

> 참고: 초기 "flag-off ch2 ≠ golden(0/12)"는 **`run_engine` 직접호출 ≠ `api_diagnose`(골든 생성경로)** 하네스 차이였고 P3b와 무관. 유효 검증은 **P3b vs baseline 동일성(12/12)**.

## B. dx-side (1차에서 PASS, 유지)

systems_catalog dx-only byte-0, base systems 0, module_id 결정론(`{system}.cap_{index}`), sub_override SUB_* 0. (commit `f97c42a`.)

## C. 후속 확인 (P3b PASS의 블로커 아님 · dev)

- **flag-on enrichment 노출:** Gatekeeper의 `run_engine` 프로브에선 12 골든 sub의 ch2에 `p3b_dev_modules`가 표면화되지 않음(해당 경로가 Card1 1.2 variant를 트리거 안 하거나 sub_override 매칭 없음). M2의 **섹션빌더 레벨 테스트는 flag-on 부착 확인**. → **메커니즘은 정상, 실제 노출 커버리지는 dev 반복 작업**(P3b-5 후속). prod 게이트(flag-off no-op)는 충족.
- P3b-6(Ch2 전체·DB mode·tier 외부화)은 **이연 유지**(별도 승인).

## D. ⚠️ 재발방지 메모 (Gatekeeper)

1차 검증 중 `git checkout -- compose.py`로 M2 미커밋 변경을 유실시킨 실수 → 이후 **검증은 read-only git(diff/show/stash-pop 복원확인)만** 사용. 미커밋 산출물은 **먼저 커밋 보존 후 검증**.

## E. P3 core 완료 · 다음

- **P3a(Ch3/6 sub_override) + P3b(Ch2 system/module + Card1 dev consumer) = 완료.** 요구3(system→module→sub_override)의 dx 정본·byte-0·flag-gated 소비 확립.
- **다음 = P4**(잔여 이관·legacy 격리·MANIFEST live=로더 100%·lineage 뷰 완성) — plan/discovery-first로 착수 예정.

PASS 판정은 Gatekeeper.
