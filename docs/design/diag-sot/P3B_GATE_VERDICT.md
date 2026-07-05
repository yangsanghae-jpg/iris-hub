# Gatekeeper 판정 — DIAG-SOT P3b (1차)

- **판정일:** 2026-07-06 · Gatekeeper(Claude)
- **판정: 🟡 dx-side PASS / compose.py 재적용+수정 필요 (P3b 미완).**

---

## A. ⚠️ 사고 disclosure (Gatekeeper 실수)

검증 중 Gatekeeper가 `git checkout -- server/assemble/ch2_system/compose.py`를 실행해 **M2의 미커밋 compose.py 엔진 변경을 되돌려 유실**시켰다. **내 실수다.**
- **무사:** dx 스크립트 `p3b_ch2_system_catalog.py`, `_p3b/` 아티팩트, roundtrip 리포트 (untracked였고 checkout 무영향, **커밋 `f97c42a`로 보존**).
- **유실:** compose.py의 `_is_diag_sot_dev_enabled`·`_load_p3b_dx_rows`·`_apply_p3b_dev_module_overrides`·호출부 (working tree only였음).
- **다행:** compose.py 변경엔 아래 §C 결함이 있어 **어차피 재작업 대상**이었다. 재적용 시 수정 포함.

## B. dx-side 검증: ✅ PASS (독립 재현)

| 게이트 | 결과 |
|--------|------|
| systems_catalog **dx-only byte-0** | ✅ (base `systems` 비움 → dx rows 재조립 → 원본 byte-0, 직접 cmp) |
| base emptied | ✅ base systems count **0** |
| module_id 결정론 | ✅ `{system_id}.cap_{index}`(예 `AMHS.cap_0`) — 정밀화 A 준수 |
| capabilities 보존 | ✅ legacy 배열 그대로, module은 dev 파생(정밀화 B) |
| sub_override SUB_* | ✅ 254행, **SUB_* sub_code 0**(P3a alias 재사용, 추정 없음) |

→ **dx-side(system/module 추출·byte-0·무손실)는 확립.**

## C. compose.py — 재적용 + 필수 결함 수정

**결함(재적용 전 반드시 수정):** `_build_card1_system_capabilities_variant`의 출력 섹션에 **`"system_code": code`를 flag 무관하게 무조건 추가**했다. baseline 섹션은 `{label, type, value}`이므로 **flag-off 출력이 바뀐다 = prod 무노출 위반.**
- (골든에 "system_code"가 있던 건 decision의 다른 부위 — 이 Card1 1.2 섹션엔 없었음을 baseline에서 확인.)

**수정 방침:**
1. **flag-off 출력 섹션은 `{label, type, value}` byte-identical 유지.** `system_code`를 출력 섹션에 넣지 말 것.
2. dev consumer가 system 매칭에 `code`가 필요하면 **병렬 채널**로 전달: 예) 섹션 리스트와 나란히 `section_codes` 리스트를 만들어 `_apply_p3b_dev_module_overrides(sections, section_codes, sub)`로 넘기고, 출력 섹션은 불변.
3. 또는 `system_code`를 **`DIAG_SOT_DEV=1`일 때 enriched_section에만** 부착(flag-off 절대 미부착).
4. `_apply_...`는 기존대로 flag-off 시 입력 그대로 반환(no-op).

## D. Exit 게이트 (재제출 시 Gatekeeper 재검증)

1. **flag-off = golden 12/12 decision byte-identical** ← 진짜 prod 무노출 증명. (M2의 "p3b_dev_modules 부재" probe는 불충분 — `system_code` leak을 놓쳤음. **전체 decision 대조**로 볼 것.)
2. flag-on(`DIAG_SOT_DEV=1`) = Card1에 `p3b_dev_modules` 적용.
3. compose.py diff가 승인서 §5.3 touch 경계 내(dev 로더 + Card1 helper만), 금지영역 무편집.
4. dx-side(§B) 유지.

## E. 지시 (M2)

- compose.py **재적용**(유실분) + §C 수정. dx-side는 `f97c42a`에 보존됐으니 **재작성 불필요** — pull 후 그 위에 compose.py만.
- 재검증: **flag-off golden 전체 decision 대조**(byte-identical) + flag-on 적용 + 무접촉.
- 커밋(`[DIAG-SOT][P3b] compose dev consumer (flag-gated, no flag-off leak)`) → push(막히면 통지).

> 실수 사과와 함께, dx-side는 온전히 보존됐고 compose.py는 소폭 재작업이면 됨을 명확히 한다. PASS 판정은 Gatekeeper.
