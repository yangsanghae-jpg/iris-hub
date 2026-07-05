# 작업지시서 — DIAG-SOT / P3 (+ P2 완료 판정)

- **발행:** 2026-07-05 · Gatekeeper(Claude) → Executor(M2 Cursor)
- **선행:** **P2 = PASS/완료** (§A). P3 착수 허가 (DISCOVERY 먼저).
- **접근:** diagnosis-tool `feat/diag-sot-sync` pull → 작업 → push. **C-Server/prod 무접촉.**

---

## A. P2 완료 판정 (Gatekeeper 독립 검증)

commit `0ed1748`. CONDITIONAL PASS 수정까지 확인:
- `domain_card_suffix` ko/zh/en/ja **전부 `""` 복원**(의도적 빈값 보존), 스모크에 all-lang-empty 규칙 추가로 ko_empty 0(억지채움 없음).
- flip 코어(`i18n.js` chain·`index.html` shell)·무접촉영역(server/·a1/2_system/·lang_ko) **무변경 유지.**
- 카탈로그 게이트 dx-only **16/16**, golden **12/12**.

**→ P2 완료:** 고정라벨 언어팩(dx SoT) + resolver **ko 기본·`[lang, ko]` fallback**(요구1·4·D3) 착지. 데이터/콘텐츠 무단변경 0.

---

## B. P3 목적 (요구3·4 + D3/D5 이연분 회수)

A1/A2 **보고 콘텐츠**를 **시스템 → 모듈(기능) → 세부산업 특화 오버라이드** 3층으로 세분화하고 **ko-master 콘텐츠**로. 엔진이 sub_override 델타를 소비하도록 **부분 개편**. P2에서 이연했던 **server lang 기본·Ch2 `_zh` 본문·`lang_ko.py`** 경계도 여기서 다룬다.

**방식(P1/P2와 다름):** P3는 **byte-0 아님.** new-shape 콘텐츠 = **dev 전용, prod는 legacy 유지(무노출).** 게이트 = 챕터 스냅샷 + sub_override 정확성 + **prod 무노출** + **기존 zh 손실 0** + 엔진 회귀.

## C. P3-0 — 선행 DISCOVERY (M2 draft → Gatekeeper 확정)

P1/P2처럼 **먼저 실태 인벤토리**. 구현은 확정 전 착수 금지.

**M2 산출:** `docs/diag-sot/reports/P3_DISCOVERY_DRAFT.md`
1. **③ 콘텐츠 팩 구조 전수:** `systems_catalog`(system 49: domain·label·purpose·**capabilities**·objects·interfaces·**maturity**·automation_fit), `domain_cards_catalog`, `stack_library/**`, `step5_2/management_analysis*`, `roi/roi_logic_catalog`, `ch0_exec_subs` — 각 필드가 **시스템/모듈/오버라이드 중 무엇**에 해당하는지 매핑 제안.
2. **엔진 소비·머지 경로:** `ch2_system/compose.py`(`CARD1_TIER_BY_CODE`·`CARD1_SCALE_TO_TIERS`·`pipeline_by_scale`), `ch3_scope`·`ch6_roi`의 **`by_sub_industry` 캐스케이드**(=sub_override 이식 참고형), `engine_bridge`의 SQLite(`system_catalog` 테이블) 관계.
3. **세부산업 특화 현황:** ch2엔 sub 차별화 없음 / ch3·6엔 by_sub_industry(부분충족) — **어디에 어떤 델타가 이미 있고 어디가 공백**인지.
4. **언어 실태(③):** systems_catalog(zh원본·ko없음)·mgmt(ko)·roi(ko+zh) 등 팩별 언어 커버리지 + `lang_ko.py`의 **실제 호출 경로·역할 범위**(어디까지 ko를 떠받치는지).
5. **server lang 기본 소비처:** `app.py`·`engine.py`의 `lang or "zh"`가 실제 언제 발동하는지(클라가 명시 lang 항상 보내는지 P2 확인 결과 반영).
6. **Pop→MES→G-MES 티어 로직:** 현재 하드코딩(compose.py dict) vs 데이터 분포 — 외부화 후보 여부.
7. **위험/질문:** 특히 엔진 개편 범위, zh 보존 방식, prod 무노출 보장 방법.

## D. 확정 대기 결정 (Gatekeeper가 DISCOVERY 후 채움)

- system/module/sub_override **정확 스키마·id 규칙**
- capabilities → module 분해 규칙
- sub_override **입도**((system×sub) vs (module×sub))
- 엔진 개편 지점·티어 매핑 외부화 여부
- 챕터 스냅샷 허용-diff 정의
- server lang 기본 전환 범위·시점
- Ch2 `_zh` 본문 이관 vs 유지 경계, `lang_ko.py` 처리

## E. 금지사항 (DISCOVERY 단계)

- ❌ 콘텐츠 팩·엔진·`lang_ko.py`·server 수정 (인벤토리만).
- ❌ prod 반영 (new-shape는 dev 전용, 이후 단계).
- ❌ 기존 zh 콘텐츠 삭제.
- ❌ 빈칸 임의판단 — 중단·질문.

## F. git·보고서

- `feat/diag-sot-sync`에 `P3_DISCOVERY_DRAFT.md`만 커밋+push(`[DIAG-SOT][P3] discovery`).
- 구현 스크립트·엔진 변경 **없음**(discovery 단계).

**PASS/확정 판정은 Gatekeeper. DISCOVERY 확정 전 P3 구현 금지.**
