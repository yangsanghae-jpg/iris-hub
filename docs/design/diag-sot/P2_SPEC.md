# P2 — 고정라벨 언어팩 + resolver ko-기본 (세부 스펙)

- **상태:** 골격 확정 · **정밀스키마는 P1 PASS 후 Gatekeeper 확정**
- **선행 게이트:** P1 PASS
- **출력 변화:** **의도된 diff만** (언어 기본 zh→ko 전환에 기인). 그 외 무단변경 0.
- **엔진:** 경미(resolver/렌더 fallback)

> Executor는 §7 "STAGE-ENTRY 확정본"이 이 문서에 채워지기 전 착수 금지.

---

## 1. 목적 (요구1·4·D3)

Q1~Q5 UX·A1/A2 **고정 라벨**을 단일 언어팩(`id→{ko,zh,en,ja}`)으로 통합하고, resolver를 **ko 기본 + ko fallback**으로 전환한다. `DEFAULT_LANG=zh → ko`.

## 2. 대상

- 고정 라벨원: `client/i18n/**`(UI), Q1~Q5 프레임 라벨, A1/A2 챕터/카드 고정 라벨. (콘텐츠 본문 서술은 ③=P3, 여기 아님)
- resolver 소비자(2026-06-29 분석 기준): `i18n.js`, `q1`/`q5` 로더, `ch2_render`(`_zh` 잔재), `lang_ko.py` 경계.

## 3. 골격 설계 (확정)

- **fixed_labels 카탈로그:** `id → {ko(필수), zh?, en?, ja?}`. id 규칙은 dot 소문자(중국어 문자열 id 금지).
- **resolver 정책:** `chain = [lang, "ko"]`. ko 필수(CI 강제), 미작성 언어는 ko로 표시. 언어 추가 = 빈칸 채우면 자동 노출.
- **경계(요구1):** UI 크롬 = `client/i18n`, 진단 도메인 고정라벨 = fixed_labels. 콘텐츠 서술 = P3.
- **의도된 diff 관리:** P1 골든을 **재베이스라인**하되, 변경 셀이 **오직 언어 기본 전환**임을 diff로 입증.

## 4. 방법 (확정)

1. fixed_labels를 dx_* SoT에 추가, sync가 팩/뷰로 반영.
2. resolver를 `[lang, ko]`로 교체, `DEFAULT_LANG=ko`.
3. **의도-diff 게이트:** 콘텐츠(값) diff 0, 라벨은 "zh였던 자리에 ko" 패턴만 허용. 그 외 변경은 FAIL.

## 5. 금지사항 (Executor)

- ❌ ③ 콘텐츠 본문(systems purpose·mgmt point·roi 서술) 이동/편집 (P3).
- ❌ `lang_ko.py` 제거 (2026-06-29: Ch2 ko 근간, P3+까지 유지).
- ❌ 라벨 텍스트 **내용 수정**(번역 개선 등) — 여기선 **재배치·정책전환만**. 내용 변경은 별도.
- ❌ 4언어 키 집합 비대칭 방치.

## 6. Gatekeeper 점검항목

- [ ] diff가 **오직 의도된 언어기본 전환**뿐 (콘텐츠 값 무단변경 0)
- [ ] zh였던 자리에 ko 올바로 노출
- [ ] 미작성 언어 → ko fallback 스냅샷 확인
- [ ] ko 필수 CI 실제 강제
- [ ] 4언어 키 집합 동일(커버리지 리포트)
- [ ] `lang_ko.py` 온존

## 7. STAGE-ENTRY 확정본 (⚠ P1 PASS 후 Gatekeeper가 채움 — Executor 작성 금지)

> P1의 registry/sync 계약 확정 후, Gatekeeper가 아래를 이 문서에 추가한다:
> - fixed_labels 정확 스키마·id 네임스페이스 표
> - 대상 라벨 원본 파일·키 목록(전수)
> - resolver 교체 지점 파일·함수 목록
> - 의도-diff 허용 패턴 정의(정규식 수준)
> - 골든 재베이스라인 절차

## 8. Exit 게이트

1. diff=의도분만
2. 4언어 패리티 + ko fallback 검증
3. ko 필수 CI green

## 9. 롤백

- resolver·DEFAULT_LANG 원복(설정 1점) + 브랜치 드롭.
