# Gatekeeper 판정 — DIAG-SOT P3a 스키마 draft

- **판정일:** 2026-07-05 · Gatekeeper(Claude) · 대상 commit `3c5a5f2`
- **판정: ✅ 승인 (정밀화 2건 반영 조건).** P3a 구현 착수 허가.

---

## 0. 총평

draft가 매우 엄격·정확. Gatekeeper 독립 확인:
- Ch3/Ch6 각 **53 slug(빈 `{}` 32 · 필드 21)** 일치.
- shared_slug 5종(`solar_pv`·`battery`·`drug_product`·`food_processing`·`consumer_goods`)·catalog_slug_issue 6종(`lcd`·`display_equipment`·I-family 4) 모두 실재.
- **canonical=`sub_code`(A01), SUB_*↔A01 추정 거부(P1 issue 유지), shared_slug 중복방출 금지, 빈 `{}` 보존, zh freeze** — 전부 옳음.

## 1. 승인 (그대로)

- canonical `sub_code` + `legacy_slug` emission 정책(§2.1).
- 미해결 `SUB_*`는 **P1 issue 유지**(추정 금지). §7 체크리스트 5항 전부 승인.
- `shared_slug`(복수 sub_code→1 slug)는 **legacy subtree 1회만 방출**, sub_code candidates 병기.
- 6 `catalog_slug_issue` 슬러그는 slug로 방출·mapping_status만 issue.
- `dx_sub_override` 스키마(§3), 빈 `{}` = `preserve_empty_object`, ko-master+zh freeze 정책(§5).

## 2. 정밀화 2건 (구현 시 반영)

### A. G5 "dx-only" 정밀 — passthrough 위장 방지 (P1-a 교훈)
카탈로그 파일은 `by_sub_industry`(dx 모델링분) **와** 나머지(default·by_industry base 등, P3a 범위 밖 passthrough)를 **한 파일**에 담는다. 따라서 "dx-only"는 파일 전체가 아니라 **`by_sub_industry` subtree가 dx 행에서 재조립됨**을 증명해야 한다.
- **acid-test 방식:** 원본에서 `by_sub_industry` subtree를 **비운 base**로 시작 → dx 행으로 채움 → **전체 파일 byte-0**. (나머지는 정당한 passthrough.)
- **추가 확증(권장):** mutation test — dx 행 1개 값 변경 → 출력의 해당 slug만 대응 변경(=dx 의존 증명). `copy 원본 by_sub_industry` 방식 금지.

### B. shared_slug 미래 한계 명시 (블로커 아님)
legacy 카탈로그는 slug 키라 shared_slug(D03/04/05→`solar_pv`)에 **slug당 델타 1개만** 담을 수 있다. P3a byte-0은 slug당 1회 방출로 정확하다. **단, 향후 sub_code별 차등 델타**(D03≠D04)는 legacy 구조상 불가 → **slug 분해/카탈로그 재구성이 필요한 별건**(P3b/후속). P3a 보고서에 이 한계를 명시만 할 것.

## 3. P3a 구현 스코프 (확정)

1. **alias map + `dx_sub_override`** 생성: Ch3/Ch6 기존 `by_sub_industry` 델타를 dx로 추출(§4.1). SUB_* 미해결·catalog_slug_issue·issue_no_slug는 issue로.
2. **roundtrip**: dx → sync → `ch3/scope_catalog.json`·`roi/roi_logic_catalog_v1.json` **기존 by_sub_industry byte-0 재현**(G1~G7, G5는 §2-A 방식).
3. **신규 델타 추가 없음**(P3a=기존 무손실 편입 증명). ko-master는 미래 authoring 정책으로 기록만.
4. **엔진 무변경**(캐스케이드 기존 소비). prod 무노출, zh 손실 0.

## 4. 금지 (유지)

Ch2·systems_catalog·Card1·engine_bridge·tier·DB mode·server `lang` 기본·`lang_ko.py` 미접촉. SUB_*↔A01 임의매핑·기존 zh 삭제·prod 반영 금지.

## 5. Exit 게이트 (구현 제출 시 Gatekeeper 재검증)

- G3/G4 Ch3·Ch6 **byte-0**, **G5 §2-A 방식으로 dx 의존 증명**(내가 by_sub_industry 비운 base로 재현 직접 확인).
- G1 전 slug(빈 `{}` 포함) 표현, G2 SUB_*/issue 추정 0, G7 zh 보존.
- prod 무노출, 엔진 무변경 git-diff, shared_slug 중복방출 0.

> git: M2 환경 DNS 이슈 지속 시 로컬 커밋 후 경로·해시 통지 → Gatekeeper가 origin에 대행 push. PASS 판정은 Gatekeeper.
