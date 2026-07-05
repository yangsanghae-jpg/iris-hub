# Gatekeeper 판정 — DIAG-SOT P2 flip

- **판정일:** 2026-07-05 · Gatekeeper(Claude) · 대상 commit `d469775`
- **판정: 🟡 CONDITIONAL PASS.** flip 메커니즘·범위 검증 통과. **수정 1건**(domain_card_suffix) 반영 후 P2 완료.

---

## A. 검증 통과 (Gatekeeper 독립)

| 항목 | 결과 |
|------|------|
| `i18n.js` resolver | ✅ `DEFAULT_LANG="ko"` + chain `[lang, ko]` 정확 구현(그 외 로직 변경 0) |
| `index.html` | ✅ lang 속성 + static 텍스트(zh→ko)만, **코드/스크립트 변경 0** |
| 무접촉 영역 | ✅ `server/**`·`a1/2_system/**`·`lang_ko.py`·Ch2 렌더러 **git diff 없음** |
| 카탈로그 게이트 | ✅ ko 보강 반영 후에도 dx-only 재생성 16/16, active 256 |
| `a2.q5.*` 5키 ko 채움 | ✅ **정당** — zh에도 없던 진짜 결측(렌더 시 키명 노출됐던 것). ko 채움 = 기준, 타 언어는 ko fallback(요구4) |
| 빈-라벨 스모크 | ✅ ko_missing 0 / ko_key_exposed 0 / index 실패 0 |

## B. 수정 필요 1건 — `report.ch2.domain_card_suffix`

**문제:** 이 키는 **zh·en·ja 모두 `""`(의도적 빈값)** 인데 M2가 **ko만 "영역"** 으로 채움.
- 결측 채움이 아니라 **의도적으로 비어있던 라벨에 ko-only 콘텐츠 삽입** → 언어 비대칭.
- **`client/src/ui/a1/2_system/ch2_render.js:642`가 소비**(`t("report.ch2.domain_card_suffix")`) → ko 렌더에 도메인카드 접미사 "영역"이 **새로 붙음** = **Ch2 렌더 콘텐츠 행위변경**(D5상 Ch2 콘텐츠는 P3 영역).
- P2는 "언어정책 전환"만 — **콘텐츠/행위 변경 금지.**

**지시:**
1. `client/i18n/ko/report.json`의 `report.ch2.domain_card_suffix`를 **`""`로 되돌림**(전 언어 빈값 = 기존 동작 보존).
2. **빈-라벨 스모크 규칙 보강:** "active 키가 **전 지원언어에서 empty**"면 **의도적 빈값**으로 분류 → `ko_empty` 결함 아님. (`q4.domain.` 템플릿 오탐과 **별개 규칙**으로 명시.)
3. 재실행: ko_empty 0 유지, 카탈로그 게이트 16/16 재확인.
- 참고: all-empty active 키는 `domain_card_suffix` 1개뿐(나머지 `q4.domain.`=오탐)이라 영향 국소.

## C. 확인 요청 (경미)

- 결과 보고서 경로가 `docs/diag-sot/P2_RESULT_REPORT.md`(지시서는 `reports/` 하위)로 상이. **`reports/`로 이동** 또는 경로 확정.
- 보고서에 **golden 회귀 12/12** 명시(현재 확인 안 됨). flip은 명시 lang 요청엔 무영향이나, 결과에 포함할 것.

## D. 완료 절차

**B-1~3 + C 반영 → 재제출.** Gatekeeper 재검증:
- `domain_card_suffix` 전 언어 `""` 복원 확인
- 스모크 규칙 보강 후 ko_empty 0 (억지 채움 없음)
- 카탈로그 게이트 16/16, 무접촉 영역 무변경 유지
- golden 12/12

→ 통과 시 **P2 완료**, P3 STAGE-ENTRY 확정 발행.

> flip 메커니즘 자체는 정확. 본 수정은 "언어정책 전환이 콘텐츠 행위까지 바꾸지 않도록" 경계를 지키는 것. PASS 판정은 Gatekeeper.
