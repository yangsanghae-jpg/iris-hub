# Gatekeeper 판정 — P2 fixed-label 카탈로그 게이트 + flip 인가

- **판정일:** 2026-07-05 · Gatekeeper(Claude) · 대상 commit `0ee73f6`
- **판정: ✅ PASS.** 카탈로그 라운드트립 게이트(G1~G4) 독립 검증 통과. **resolver/shell ko-flip 착수 인가.**

---

## A. 카탈로그 게이트 검증 (Gatekeeper 독립)

`--build-from-dx`가 `_p2/dx_fixed_label.json`만으로 `data/build/v2/client/i18n/**` 재생성 → legacy와 비교:

| 게이트 | 결과 |
|--------|------|
| **G1** 전 16파일 `json.load(export)==json.load(legacy)` | ✅ |
| **G2** byte diff = dedup+blank 한정 | ✅ (정밀검증: 아래) |
| **G3** 결함없는 11파일 byte-0 | ✅ 11/16 |
| **G4** dedup/blank 열거 + 중복값 동일여부 | ✅ 리포트 존재 |

**정밀 검증(오탐 해소):** dedup 3파일(en/ja/ko ui.json)에서 나이브 line-diff는 "add/mod"로 보였으나, 실제는 **dedup이 "첫 위치에 마지막 값"으로 나타난 것**. 정밀 확인 결과:
- **키 순서 재배열 없음**(export_order == legacy first-occurrence order)
- **값 = keep-last**(런타임 last-wins 일치)
- 특히 `a2.q5.datapack_pending`은 first/last 값이 **달랐고**, keep-last가 런타임 값을 보존(keep-first였으면 런타임 변화 = 버그였을 것). **M2 정확.**
- blank 2파일(zh/messages, ja/report) 순수 빈줄 제거.

→ **정규화는 dedup-keep-last(무재배열) + blank-strip 한정, parsed-identical.** 라벨 텍스트 변경 0.

## B. active-key / ko 커버리지 (D2)

```
active_key_count = 256, ko_missing issues = 0
ui: active 228 (union 581, ko 522) — zh-only 58키는 전부 非active
labels 134/134/134/134 · messages/report ko full parity
```
- **active 집합 전부 ko 보유 → ko-flip 안전.** zh-only 58 UI키는 비-active(legacy)라 fallback 정책 변경 영향권 밖.

## C. flip 인가 (P2 순서 3~4) + 안전장치

카탈로그 게이트 PASS이므로 이제 **의도된 diff 단계** 착수 허가:

1. `client/assets/i18n.js`: **`DEFAULT_LANG = "ko"`**, `resolveValue` chain을 **`[lang, "ko"]`** 로 명시화.
2. `client/index.html`: `<html lang="ko">`, 초기 static 타이틀/텍스트 ko (zh flash 제거).
3. ko mandatory CI: **active 256 집합** 기준(현재 ko_missing 0).

**안전장치(필수):** flip 후 **빈-라벨 스모크** — Q1~Q5 각 step + A1/A2 렌더에서 `[lang, ko]` fallback으로 **빈 문자열/키명 노출 0** 확인. active 탐지가 놓친 키가 실제 렌더에서 비면 이걸로 잡는다. 발견 시 해당 키 ko 채움 or issue.

**무접촉 재확인(D3/D5):** `server/app.py`·`engine.py`의 `lang or "zh"` 기본, `lang_ko.py`, Ch2 렌더러 `_zh` 본문, ③ 콘텐츠 — **전부 P2 미접촉.**

## D. 최종 P2 Exit 게이트 (flip 제출 시 Gatekeeper 재검증)

1. 카탈로그 게이트 G1~G4 유지(이미 PASS)
2. flip diff = **오직 언어정책(ko default/chain) + shell ko** — 콘텐츠/라벨 텍스트 무단변경 0
3. 빈-라벨 스모크 0
4. Ch2 렌더러·`lang_ko.py`·server 기본 **무변경**(git diff로 확인)
5. 골든 회귀: 언어전환 영향분만 의도표기

## E. 지시 (M2)

- 카탈로그 게이트분은 이미 커밋됨(`0ee73f6`) — 그 위에 **flip(§C 1~3) + 빈-라벨 스모크** 구현.
- `P2_RESULT_REPORT.md`에 flip diff 요약 + 스모크 결과 + Ch2/server/lang_ko git-diff 없음 증거 + `SELF-STATUS`.
- push 후 Gatekeeper가 §D 재검증 → P2 완료 판정.

> PASS 판정은 Gatekeeper. flip은 §C 범위 한정, 그 외 확장 금지.
