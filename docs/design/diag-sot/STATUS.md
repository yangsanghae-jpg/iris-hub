# DIAG-SOT 진행 대시보드

- **갱신:** 2026-07-05 · Gatekeeper(Claude)
- **역할:** 실행 = M2 Cursor / 점검·게이트 = Claude. **PASS 판정은 Gatekeeper만.**
- **브랜치:** iris-hub `feat/diag-sot` · diagnosis-tool `feat/diag-sot-sync` · prod(C-Server) 무접촉.
- **방법:** 진실원(iris-hub dx_*) → 재조립 → **byte-0 acid-test**(legacy 숨김 dx-only 재현). 단계마다 Gatekeeper 독립 검증.

## 단계 현황

| 단계 | 내용 | 판정 | 비고 |
|------|------|------|------|
| **P0** | 기반·게이트검진·결정표 | ✅ PASS | 113팩 인벤토리, 골든 12 sub, 게이트머신 green |
| **P1-a** | Q1·Q5 dx화 | ⚠️→✅ | **1차 반려**(passthrough 공허 byte0) → **재제출 PASS**(dx-only 재조립 acid-test) |
| **P1-b** | registry+Q2/3/4 dx화 | ✅ PASS | legacy 9팩 숨김 acid-test 9/9 byte-0, Q4 flat 보존, dangling 0 |
| **P2 Discovery** | 고정라벨·resolver 인벤토리 | ✅ 확정 | 5결정(D1~D5): dx_fixed_label·ko필수=active·server기본 P3이연·shell ko·Ch2 _zh 본문 P3 |
| **P2 catalog** | fixed-label 카탈로그 라운드트립 | ✅ PASS | dedup-keep-last+blank-strip 정규화, G1~G4 통과, active 256 ko_missing 0 |
| **P2 flip** | resolver/shell ko-flip | ▶ **진행중(인가됨)** | DEFAULT_LANG=ko·chain[lang,ko]·index.html ko + 빈-라벨 스모크 |
| P3 | ③ 보고콘텐츠 세분화(system→module→sub_override)+엔진 부분개편 | ⏳ 대기 | Ch2 _zh·lang_ko·server lang 기본 여기서 |
| P4 | 잔여 이관·legacy 격리·lineage 완성 | ⏳ 대기 | |

## 확립된 불변 규율

- **dx-only 재조립 byte-0** (passthrough 금지) — P1에서 확립, Gatekeeper가 legacy 숨김 acid-test로 재검증.
- **P2부터는 byte-0 아님** — "의도된 diff만"(언어정책·정규화), 그 외 무단변경 0.
- **통합 금지**: ch1 3변종·scale_model↔scale_profile·catalog/catalogs (P4까지 보존).
- **Q4 도메인 flat 보존**(정규화는 스키마 v4=별건).
- **추정 금지**: SUB_*↔A01 등 근거없으면 issue.

## 최신 커밋

| repo | HEAD |
|------|------|
| iris-hub `feat/diag-sot` | (본 커밋) |
| diagnosis-tool `feat/diag-sot-sync` | `0ee73f6` (P2 catalog) → flip 대기 |

## 다음 액션

- M2: P2 flip(§`P2_CATALOG_GATE_VERDICT.md` C) 구현 + 빈-라벨 스모크 → push.
- Gatekeeper: flip diff가 언어정책 한정인지 + Ch2/server/lang_ko 무변경 재검증 → P2 완료 판정 → P3 STAGE-ENTRY 확정.

## 문서 지도 (diag-sot/)

`00_MANIFEST` · `10_OVERVIEW` · `P0~P4_SPEC` · `WORK_ORDER_{P0,P1,P1B,P2}` · 판정: `P1A_GATE_VERDICT`(반려)·`P2_DISCOVERY_APPROVAL`·`P2_CATALOG_ROUNDTRIP_DECISION`·`P2_CATALOG_GATE_VERDICT` · 배경: `../DIAGNOSIS_TOOL_SOT_TARGET_DESIGN`
