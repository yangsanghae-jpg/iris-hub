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
| **P2 flip** | resolver/shell ko-flip | ✅ **PASS/완료** | ko 기본+chain[lang,ko]+shell. domain_card_suffix 복원 확인, 게이트16/16, golden12/12 |
| **P3(분할)** | ③ 보고콘텐츠 세분화 | ▶ **분할 확정** | Discovery 완료→P3 too big→분할. canonical key=A01+alias(P1 issue 해소), lang_ko 보존, prod 무노출=env flag. tier/DB/server flip 이연 |
| └ **P3a** | Ch3(scope)+Ch6(ROI) sub_override | ✅ **PASS/완료** | dx-only byte-0(base 비움+mutation test 증명), SUB_* no-guess, shared_slug 1회, 빈{} 보존. alias map으로 P1 issue 관리 |
| └ **P3b** | Ch2 system→module + Card1 dev consumer | ✅ **PASS/완료** | dx byte-0·module_id 결정론·SUB_* 0 + compose flag-off no-op(P3b==baseline 12/12). flag-on 노출 커버리지는 dev 후속. P3b-6(Ch2전체/DB/tier) 이연 |
| └ **P3b-5** | sub_override 실제 표면화(요구3 가시효과) | ✅ **PASS** | blocks.exec에 cap+p3b 부착 수정→**실제 렌더 HTML에 세부산업 특화 keywords/points 표시**(Gatekeeper node 렌더 확인). flag-off 12/12 무변경. **요구3 실현** |
| **P4** | 잔여 이관·legacy 격리·MANIFEST·lineage 뷰 | ▶ **다음(plan-first)** | P3 완료 → DIAG-SOT 마무리(추적성 완성) |

## ⚠️ workflow 이슈
M2 환경에서 git 명령 제약 → discovery draft는 Gatekeeper가 1Dev clone에서 대행 커밋(`6fc6a56`). P3a부터 실제 코드 변경 → **M2 git 복구 필요**(아니면 Gatekeeper 대행 지속).

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
