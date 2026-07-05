# Gatekeeper 판정 — DIAG-SOT P2 Discovery

- **판정일:** 2026-07-05 · Gatekeeper(Claude) · 대상 commit `4458600`
- **판정: ✅ Discovery 확정 (5개 결정 반영 조건).** 확정 반영 후 **P2 구현 착수 허가.**

---

## 0. 총평

Discovery 정확. Gatekeeper 독립 확인: `i18n.js DEFAULT_LANG="zh"`(global 고정라벨 resolver) vs `q1_taxonomy_v3.js:34 obj[lang]||obj.ko||obj.zh...`(이미 ko fallback) — **정책 분리 실재**. `ui.json` ko=522/zh=572(zh-only ~58) = ko 전환 최대 리스크. 모두 사실.

**핵심 통찰 승인:** P2는 단순 `DEFAULT_LANG` 치환이 아니라 **global fixed-label resolver를 data-pack resolver의 ko-fallback과 정렬**하는 것.

---

## 1. 5개 결정

### D1. fixed-label catalog path/schema
- **SoT:** iris-hub `dx_fixed_label(id PK, ns, ko, zh, en, ja, source_ref, status)`. `ns ∈ {ui, labels, messages, report}`.
- **export 타깃:** 기존 **`client/i18n/{ko,zh,en,ja}/{ns}.json` 구조 그대로**. P2에서 물리 파일 구조 **재편 금지**(대량 diff 방지).
- **P2 이중 성격 분리:**
  - **(a) 카탈로그 라운드트립 = byte-0.** dx_fixed_label import → export → `client/i18n/**` 재생성이 **현재와 byte 동일**(P1식 dx-only acid-test 적용). 콘텐츠 무변경 증명.
  - **(b) resolver ko-flip = 의도된 diff.** (a)와 분리해 별도 표기.

### D2. ko mandatory CI active key subset
- **ko 필수 = "active key"에만.** active = 실제 shipped 코드/HTML이 참조하는 키(`data-i18n` in 배포 HTML + `window.t/label/message/reportText` 호출로 도달). 
- **active인데 ko 결측:** **ko를 채운다**(고정 라벨 작성은 P2 범위 — ③ 본문 아님). 단 특정 라벨이 도메인 번역 판단을 요하면 **추정 말고 `dx_fixed_label_issue(ko_missing)`** 로 남기고 그 키만 전이적으로 zh 유지.
- **비-active/legacy 키**(예 `_legacy_step6_20260605`, 미참조 zh-only): `status='legacy'`로 제외, ko 필수 대상 아님.
- 즉 **union 전체가 아니라 active 집합**에 ko 필수. M2는 active 집합·active-ko-결측 수를 산출해 보고.

### D3. server-side zh defaults → **P2 제외(이연)**
- `server/app.py`·`engine.py`의 `lang or "zh"` 기본은 **P2에서 건드리지 않음.** 이유: 서버 lang 기본은 `lang_ko.py`·Ch2 ③ 콘텐츠와 얽힘 → **P3 영역.**
- P2는 **client resolver + client payload 기본**만. **단서:** client가 항상 명시 lang을 payload에 실어 보내는지 확인(그래야 서버 기본 zh가 실질 미발동). 안 실리는 경로 있으면 issue.

### D4. index.html static zh fallback
- **P2에서 ko로 전환:** `<html lang="zh-CN"> → "ko"`, 초기 static 타이틀/텍스트 ko. pre-JS 상태를 ko 기본과 일치(zh flash 제거). 고정 shell = P2 범위, 의도된 diff.

### D5. Ch2 `_zh` fixed label vs ③ content 경계
- **P2는 fixed-label resolver 경로만 건드린다.** 구체적으로 **`i18n.js`(DEFAULT_LANG/chain) + `client/i18n` 카탈로그 + index.html shell + `data-i18n` DOM 라벨**로 한정.
- **Ch2 렌더러의 `_zh`/`name_zh`/`label_zh`/`purpose` 등 콘텐츠 fallback은 P2 미접촉(P3).** `a1/2_system/*`·`ch2_render.js`·`a1_ch2_*_renderer*.js`의 본문 `_zh` 로직 **수정 금지.**
- M2는 각 `_zh` 출현을 **chrome 고정라벨 vs ③ 본문**으로 분류만 하고, 본문은 P3 표시.

## 2. P2 확정 스코프 (구현 대상)

| 대상 | 처리 |
|------|------|
| `dx_fixed_label` (iris-hub SoT) | client/i18n import → export byte-0 (D1a) |
| `client/assets/i18n.js` | `DEFAULT_LANG=ko`, `resolveValue` chain 명시화 `[lang, ko]` (active-ko 결측은 D2대로 전이 zh) |
| `client/index.html` | shell ko 전환 (D4) |
| `client/i18n/{lang}/*.json` | export 산출(구조 유지), active-ko 채움 |
| ko mandatory CI | active 집합 (D2) |

**미접촉(P2 금지):** ③ 콘텐츠 본문·Ch2 렌더러 `_zh` 본문·`lang_ko.py`·server lang 기본·P1 완료 수치/registry 팩·라벨 텍스트 내용 개선.

## 3. Exit 게이트 (최종 P2)

1. **(a) 카탈로그 라운드트립 byte-0** — dx_fixed_label → `client/i18n/**` 재생성이 현재와 byte 동일(dx-only acid-test). Gatekeeper 재현.
2. **(b) 의도 diff만** — resolver ko-flip·shell ko 외 콘텐츠 값 무단변경 0.
3. ko fallback 스냅샷: zh였던 자리에 ko, active-ko 완비(또는 issue 명시).
4. ko mandatory CI(active) green, 4언어 active 키 패리티 리포트.
5. Ch2 렌더러·`lang_ko.py`·server 기본 **무변경 확인.**

## 4. 진행 허가

**D1~D5 반영 → P2 구현 착수.** 순서 권고: (1) dx_fixed_label 카탈로그 import→export **byte-0 먼저 증명**(P1식), (2) active 집합·ko 결측 산출·채움, (3) resolver/shell ko-flip(의도 diff), (4) 골든/스냅샷.

재제출 시 Gatekeeper는 **카탈로그 dx-only 재생성 byte-0**(acid-test) + **의도 diff가 언어정책 한정인지** + Ch2/server 무변경을 직접 확인한다.

> git·보고서 규율 동일. `P2_RESULT_REPORT.md` + 게이트 로그/스냅샷 커밋. PASS 판정은 Gatekeeper.
