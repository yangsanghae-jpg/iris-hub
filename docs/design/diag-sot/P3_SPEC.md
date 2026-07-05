# P3 — ③보고콘텐츠 세분화 + 엔진 부분개편 (세부 스펙)

- **상태:** 골격 확정 · **정밀스키마는 P2 PASS 후 Gatekeeper 확정**
- **선행 게이트:** P2 PASS
- **출력 변화:** new-shape 콘텐츠 (**dev 전용**, prod 미전송)
- **엔진:** **부분개편** (A1/A2 소비부, D2 허용)

> 여기서부터 "정보 수준 향상"의 실제 작업. 단, prod는 legacy로만 서빙(무노출).

---

## 1. 목적 (요구3·4)

A1/A2 챕터 데이터를 **시스템 → 모듈(기능) → 세부산업 특화 오버라이드** 3층으로 세분화하고, 콘텐츠를 **ko-master**로. 엔진이 sub_override 델타를 소비하도록 부분개편.

## 2. 대상 (확정)

- 콘텐츠 원천: `ch2/catalog/systems_catalog.json`(49시스템, zh원본), `domain_cards_catalog`, `stack_library/**`, `step5_2/management_analysis*`, `roi/roi_logic_catalog`, `ch0_exec_subs`.
- 엔진: `server/assemble/ch2_system/compose.py`(티어 로직 `CARD1_TIER_BY_CODE`/`CARD1_SCALE_TO_TIERS`), `ch3_scope`/`ch6_roi`(기존 `by_sub_industry` 캐스케이드=이식 참고형).

## 3. 골격 설계 (확정)

```
system(거시)   : id, chapter, domain, label{ko..}, purpose{ko..},
                 maturity_ladder[], automation_fit{}, modules[→module.id]
module(미시)   : id, system→, label{ko..}   (= 기존 capabilities 엔티티화)
sub_override   : target(system|module), sub_industry→, add_keywords{ko..}, add_points{ko..}, importance?
                 (base 위 "델타"만. 전량 재기술 아님. 차별화 있는 곳만 sparse)
```
- **언어(요구4):** 콘텐츠 인라인 `{ko(필수),zh?,en?,ja?}`, fallback→ko. 기존 zh 원본은 zh 슬롯에 **보존**(손실 0), ko는 신규/이관.
- **룰엔진 연동:** 규모/자동화→시스템 티어(Pop→MES→G-MES)는 `maturity_ladder`+`CARD1_SCALE_TO_TIERS`. sub_override는 기존 누적 로직에 **합류**(ch3/6 캐스케이드와 동형).

## 4. 방법 (확정)

1. 콘텐츠 모델을 dx_* SoT에 구축, systems_catalog 등 이관(zh 보존 + ko 채움).
2. 엔진 부분개편: `ch2_system`이 `by_sub_industry` 오버라이드 소비(현재 ch2엔 없음 — 이 공백이 목표).
3. new-shape 팩 = `build/v2` **dev 전용**. prod 서빙은 **legacy 유지**.
4. 챕터 HTML 스냅샷 회귀(허용범위 = 의도된 세분화·언어전환).

## 5. 금지사항 (Executor)

- ❌ **prod에 new-shape 전송** (dev 전용, 무노출 절대).
- ❌ 기존 zh 콘텐츠 **삭제/덮어쓰기** (zh 슬롯 보존, ko는 병렬 추가).
- ❌ sub_override를 "전량 재기술"로 (반드시 base 위 **델타**).
- ❌ 티어 매핑 로직을 스펙 없이 재작성 (외부화 여부는 §7 확정본 결정).
- ❌ P1/P2 확정 계약(registry·resolver) 위반.

## 6. Gatekeeper 점검항목

- [ ] sub_override 델타가 base 위에 올바로 합류(이중기술·누락 없음)
- [ ] ch2 세부산업 차별화가 실제 생김(이전 공백 해소)
- [ ] Pop→MES→G-MES 티어가 maturity/scale과 정합
- [ ] ko-master + fallback 준수, **기존 zh 손실 0**
- [ ] **prod 무노출 확인** (legacy만 서빙)
- [ ] 챕터 스냅샷 회귀가 의도 범위 내

## 7. STAGE-ENTRY 확정본 (⚠ P2 PASS 후 Gatekeeper가 채움)

> - system/module/sub_override 정확 스키마·id 규칙
> - systems_catalog→새모델 필드 매핑표(capabilities→module 분해 규칙)
> - sub_override **입도 결정**: (system×sub) vs (module×sub) — 실데이터로 산정
> - 엔진 개편 지점(compose.py 함수)·티어 매핑 외부화 여부
> - 챕터 스냅샷 허용-diff 정의

## 8. Exit 게이트

1. 챕터 스냅샷 리뷰 통과
2. sub_override 검증
3. prod 무노출 + zh 손실 0

## 9. 롤백

- new-shape는 dev(`build/v2`)에만 → 폐기 + 엔진 개편 커밋 revert + 브랜치 드롭. prod 무영향.
