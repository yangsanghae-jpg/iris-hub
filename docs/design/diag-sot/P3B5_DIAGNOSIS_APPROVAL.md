# Gatekeeper 판정 — DIAG-SOT P3b-5 진단

- **판정일:** 2026-07-06 · Gatekeeper(Claude) · 대상 commit `79015d0`
- **판정: ✅ 진단 CONFIRMED · 구현 착수 허가.**

---

## 0. 진단 재현 (불일치 해소)

M2 정확 payload `{industry:B, subindustry_code:B01, scale_s1_s4:S1, automation_level:auto2, lang:ko}`로 Gatekeeper 재현:
- flag-on `decision.ch2.domain_cards.exec.cap.sections[0,1,2]`에 **p3b_dev_modules 6+4+4 = 14** 부착(M2 주장과 일치).
- **원인 = client renderer가 `p3b_dev_modules` 미소비** (compose·dx·매칭 정상).
- 앞서 Gatekeeper가 본 "0"은 **golden `pl['B01']`가 `{ko,zh}` 래퍼**라 payload로 잘못 투입한 내 실수였음(subindustry_code 미전달 → early return). 정정.

→ **M2 진단이 옳다. 문제는 서버가 아니라 UI 렌더 표면화 부재.**

## 1. 5개 질문 답변

| # | 질문 | 판정 |
|---|------|------|
| 1 | 표면화 위치 = Card1 cap sections 아래 | ✅ (p3b_dev_modules가 실제 붙는 지점) |
| 2 | `sub_overrides` 있는 module만 표시 | ✅ (B01: 14 module 중 3 override — noise 방지) |
| 3 | client renderer 변경을 P3b-5 범위 포함 | ✅ **이게 THE 수정.** client-only·flag-safe |
| 4 | marker class 추가(스냅샷 검증용) | ✅ (예 `p3b-dev-module-overrides`) |
| 5 | 미매칭 code(QMS 등)는 issue만, alias 이연 | ✅ (no-guess 유지) |

## 2. P3b-5 구현 스코프 (확정)

- **파일:** `client/src/ui/a1/a1_ch2_card_renderer_common.js` `renderVariantSection()` `mode==="list"` 분기.
- **동작:** 기존 `section.value` list 그대로 + **`sec.p3b_dev_modules` 있을 때만** dev block 추가. renderer는 **env 안 봄, payload 존재만** 봄 → flag-off(=payload 없음)면 HTML 무변화(구조적 flag-safe).
- **표시:** `sub_overrides` 있는 module만 → module title(`title.ko||title.zh||module_id`) + `keywords.ko` + `points.ko`. marker class 부여.
- **정렬:** exact `system_id` 매칭만. 미매칭 code(QMS 등) → **issue/report만, alias 매핑 이연**(추정 금지).
- CSS 대형 변경 금지(기존 스타일 재사용).

## 3. Exit 게이트 (구현 제출 시 Gatekeeper 재검증)

1. **flag-off 무변경:** golden 12 sub의 flag-off decision에 `p3b_dev_modules` **없음** + Card1 cap section shape `{label,type,value}` 유지 + **flag-off 렌더 HTML 무변화**(renderer가 없는 payload를 안 그림). (전체 decision baseline 동일은 이미 P3b에서 증명.)
2. **flag-on 표면화(요구3 실현):** B01 `DIAG_SOT_DEV=1` 렌더 HTML에 **세부산업 특화 keywords/points 실제 표시** + marker class. Gatekeeper가 실제 렌더로 확인.
3. no-guess: SUB_* 0, exact system_id, 미매칭 issue.

## 4. 검증 방식 (Gatekeeper)

client 렌더 변경이라 **실제 렌더 결과**로 본다:
- renderer diff가 "payload 있을 때만 추가" 구조인지(flag-off 무변화 구조적 보장) 검토.
- flag-on B01 렌더 산출(HTML/preview)에 keywords/points·marker 존재.
- flag-off 렌더 무변화.

## 5. 금지

server compose 재변경(이미 동작)·systems_catalog·tier·DB·server lang·`lang_ko.py`·SUB_* 임의매핑·flag-off 출력/렌더 변경.

> 이 단계 통과 = **B01 리포트에 세부산업 특화가 실제로 보임 = 요구3 실현 = P3 완료.** PASS 판정은 Gatekeeper.
