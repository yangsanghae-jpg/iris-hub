# Gatekeeper 판정 — DIAG-SOT P3b-5 (client renderer)

- **판정일:** 2026-07-06 · Gatekeeper(Claude) · renderer commit `b38bc39`
- **판정: ❌ FAIL — flag-on에서 실제로 표면화되지 않음.** (flag-off 안전은 유지) 수정 후 재제출.

---

## 0. 결정적 결함 — 데이터가 렌더러가 읽는 표현에 없다

**decision에 Ch2 cap이 두 표현으로 존재하는데, compose는 렌더 안 하는 쪽에 붙였다.**

| 표현 | p3b_dev_modules(flag-on B01) | client 렌더 대상? |
|------|:---:|:---:|
| `decision.ch2.domain_cards.exec.cap.sections` | **3 (있음)** | ❌ 아님 |
| `decision.ch2.blocks[type=domain_cards].domains.exec.cards.cap.variant.sections` | **0 (없음)** | ✅ **렌더 대상** |

- **client 렌더 경로(확인):** `client/src/ui/a1/2_system.js:247-248` 및 `a1_ch2_renderer.js:420-421` → `decision.ch2.blocks`에서 `type==="domain_cards"` 블록을 찾아 `domains.exec.cards`를 렌더. `payload.cards`(`a1_ch2_card1_renderer.js:32`)가 이 blocks 파생.
- **compose 부착 지점:** `_build_card1_system_capabilities_variant` → `ch2.domain_cards.exec.cap.sections` (standalone). **blocks 표현은 별도 객체(공유 아님)** — blocks JSON 내 p3b 카운트 0으로 확정.
- **결과:** 렌더러(`renderVariantSection`)가 받는 `sec`(blocks 파생)에는 `p3b_dev_modules`가 **없음** → flag-on이어도 **HTML에 아무것도 안 나옴.**

→ M2 진단의 "렌더러가 p3b_dev_modules를 무시한다"는 절반만 맞음. **진짜 원인은 데이터가 렌더러가 소비하는 blocks 표현에 부재.**

## 1. renderer 변경 자체는 정상 (유지)

`a1_ch2_card_renderer_common.js`의 fix는 **올바르고 flag-safe**:
- `renderVariantSection` list 분기: `${list||""}${p3bDevModules}`, `p3bDevModules=""`(없을 때) → **flag-off HTML 완전 동일**(구조적 증명).
- `renderP3bDevModuleOverrides`: sub_overrides 있는 module만, keywords/points, escape, marker class. 로직 정확.
- **이 파일은 유지.** 문제는 renderer가 아니라 데이터 도달.

## 2. 수정 (compose) — blocks 표현에 부착

**`p3b_dev_modules`를 client가 실제 렌더하는 표현에 부착:**
- `ch2.blocks[type=domain_cards].domains.<domain>.cards[key=cap].variant.sections` 의 각 system section에 flag-on일 때 붙일 것.
- 또는 domain_cards와 blocks의 cap sections가 **동일 객체(공유 참조)** 가 되도록 하여 한 번 부착으로 양쪽 반영.
- **flag-off no-op 불변**, exact system_id 매칭·SUB_* 0 유지.
- 부착 지점을 **client 렌더 경로 기준**으로 확정(2_system.js/a1_ch2_renderer.js가 읽는 blocks).

## 3. Exit 게이트 (재제출) — 이번엔 실제 렌더로

1. **flag-on 실제 렌더 확인:** `DIAG_SOT_DEV=1` B01의 **렌더된 HTML**(또는 브라우저 preview)에 keywords/points·marker(`p3b-dev-module-overrides`) **실제 표시**. compose가 blocks 표현에 부착됐는지 Gatekeeper가 `blocks` 하위 p3b 카운트 + 렌더 산출로 확인.
2. **flag-off 무변경:** blocks/domain_cards 어디에도 p3b 없음 + 렌더 HTML 무변화 + 전체 decision baseline 동일.
3. no-guess(SUB_* 0, exact match) 유지.

## 4. 재발 교훈

piece-wise 검증(렌더러 로직·compose 부착·배선)이 모두 통과해도 **표현 분기(domain_cards vs blocks)** 때문에 end-to-end가 깨질 수 있음. **P3b-5는 반드시 "client가 읽는 표현"에서 검증**해야 한다(내가 이번에 그 표현을 대조해 결함을 잡음).

> renderer는 유지, **compose 부착 지점만 blocks로 수정** 후 재제출. PASS 판정은 Gatekeeper(실제 렌더로).
