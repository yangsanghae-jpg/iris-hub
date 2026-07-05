# 작업지시서 — DIAG-SOT / P2 (+ P1 완료 판정)

- **발행:** 2026-07-05 · Gatekeeper(Claude) → Executor(M2 Cursor)
- **선행:** **P1 전체 = PASS/완료** (§A). P2 착수 허가.
- **접근:** diagnosis-tool `feat/diag-sot-sync` pull → 작업 → push. C-Server/prod 무접촉.

---

## A. P1 완료 판정 (Gatekeeper 독립 검증)

| 단계 | 판정 | 핵심 증거(Gatekeeper 직접) |
|------|------|---------------------------|
| P1-a (Q1·Q5) | ✅ PASS | legacy 숨김 acid-test → dx-only 재조립 4팩 byte-0 |
| **P1-b (registry+Q2/3/4)** | ✅ **PASS** | legacy 9팩 숨김 acid-test → **dx-only 재조립 9/9 byte-0** (직접 cmp) |

P1-b 세부: dx_q_matrix 444·dangling FK 0, dx_registry_framework 9(수정A), Q4 flat 보존(byte-0가 증명), SUB_*↔A01 추정없음(issue 2), Z99 스모크 `add_then_rollback` 기록·아티팩트 미잔존, 골든 12/12.

**→ P1 완료:** ①척추 + ②Q매트릭스(Q1~Q5)가 iris-hub dx 정본에서 **재조립되어 legacy와 byte-0**임이 acid-test로 증명. **방법(진실원→재구성→무변경)이 ①②에서 확립.**

---

## B. P2 목적 (요구1·4·D3)

Q1~Q5 UX·A1/A2 **고정 라벨**을 단일 언어팩(`id→{ko,zh,en,ja}`)으로 통합하고, resolver를 **ko 기본 + ko fallback**으로 전환한다(`DEFAULT_LANG=zh → ko`).

**P1과의 결정적 차이:** P2는 **byte-0가 아니다.** 출력이 **의도적으로** 바뀐다(zh 기본 → ko 기본). 따라서 게이트는 "diff 0"이 아니라 **"의도된 언어 diff만, 그 외 무단변경 0"**.

## C. P2-0 — 선행 DISCOVERY (M2 draft → Gatekeeper 확정)

P1이 스키마 초안→승인으로 시작했듯, P2도 **먼저 실태 인벤토리**를 draft하고 Gatekeeper가 P2 스키마·교체계획을 확정한다. **P2 구현은 확정 전 착수 금지.**

**M2 산출:** `docs/diag-sot/reports/P2_DISCOVERY_DRAFT.md`
1. **고정 라벨 원천 전수:** `client/i18n/**`, Q1~Q5 프레임 라벨, A1/A2 챕터/카드 고정 라벨이 **어느 파일·어느 키**에 있는지. (콘텐츠 본문 서술=③은 제외 — 경계를 명시)
2. **resolver 호출부 전수:** `i18n.js`, q1/q5 로더, `ch2_render`의 `_zh` 잔재, `lang_ko.py` 경계 — 언어 선택·fallback이 일어나는 **코드 위치**.
3. **`DEFAULT_LANG` 현 위치·소비처.**
4. **4언어 키 커버리지 현황**(ko/zh/en/ja 각 몇 개, ko-only/zh-only 편차).
5. **UI 크롬 vs 진단 도메인 라벨 경계**(요구1) 제안 분류.
6. **위험/질문**(예: `lang_ko.py`가 ko를 떠받치는 범위, ko 전환 시 노출 변화 큰 지점).

## D. P2 방식 (확정, 구현은 C 승인 후)

1. `fixed_labels` 카탈로그: `id → {ko(필수), zh?, en?, ja?}`. id는 dot 소문자(중국어 문자열 id 금지).
2. resolver `chain=[lang, "ko"]`, **ko 필수** CI 강제, `DEFAULT_LANG=ko`.
3. 4언어 키 패리티·커버리지 리포트.
4. 골든 **재베이스라인**: 언어 기본 변경은 **의도된 diff**로 표기, 콘텐츠(값) diff 0.

## E. 금지사항

- ❌ ③ 콘텐츠 본문(systems purpose·mgmt point·roi 서술·A1/A2 문장) 이동/편집 — **P3.**
- ❌ `lang_ko.py` 제거 (Ch2 ko 근간, P3+까지 유지).
- ❌ 라벨 **텍스트 내용 수정**(번역 개선 등) — P2는 **재배치·정책전환(ko기본)만.**
- ❌ P1 완료분(Q1~Q5 수치팩·registry) 재편.
- ❌ DISCOVERY 확정 전 P2 구현 착수 / 빈칸 임의판단(중단·질문).

## F. Exit 게이트 (최종 P2, Gatekeeper 판정)

1. diff = **오직 의도된 언어기본 전환**(콘텐츠 값 무단변경 0)
2. zh였던 자리에 ko 정상 노출 + 미작성 언어 ko fallback 스냅샷
3. ko 필수 CI green, 4언어 키 집합 동일(커버리지 리포트)
4. `lang_ko.py` 온존
5. 골든: 언어전환 영향분만 의도 표기, 그 외 무변화

## G. git·보고서

- `feat/diag-sot-sync`에 커밋+push, `[DIAG-SOT][P2] ...`.
- **먼저 `P2_DISCOVERY_DRAFT.md` 제출(구현 전) → Gatekeeper 확정.**
- 최종 결과 보고서 `docs/diag-sot/reports/P2_RESULT_REPORT.md` + `SELF-STATUS`.

**PASS 판정은 Gatekeeper. DISCOVERY 승인 전 구현 금지.**
