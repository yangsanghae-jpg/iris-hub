# P4 — 잔여 이관 · legacy 격리 · lineage 완성 (세부 스펙)

- **상태:** 골격 확정 · **정밀 목록은 P3 PASS 후 Gatekeeper 확정**
- **선행 게이트:** P3 PASS
- **출력 변화:** 정리 (이관 완료·legacy 격리)
- **엔진:** 정리 (잔여 로더 정합)

> 마지막 단계. "모든 편집이 반영 경로를 드러낸다"(제1 동인)를 관리탭 lineage 뷰로 완성.

---

## 1. 목적 (요구5·D1·I4)

P1~P3에서 빠진 잔여 팩을 SoT로 이관, legacy·중복(3홈·v2/v3·생성물) 격리, 관리탭 **lineage 뷰** 완성, MANIFEST를 로더 100% 정합으로 마감.

## 2. 대상 (확정 범위)

- 잔여 팩: Q5(`recommendation_by_subindustry`), ch4(`plan_defaults`), ch5(`team_governance` — Python dict, 이관 형태 별도 판정), catalogs 잔여, 기타 루트 산재 팩.
- 격리 대상: 중복(`keywords_map`×3, `drivers`×2, `sub_industry`×3), ch1 3변종·ch2 v2/v3, 은퇴 확정 `_generate_*.py` 산출.
- 관리탭: iris-hub lineage 뷰(셀/노드 → 팩path → 소비챕터).

## 3. 골격 설계 (확정)

- **MANIFEST(정합):** 팩별 `status(live|in_migration|deprecated)`·`src`·`build_outputs`·`consumers`. **live = 실제 로더와 100% 일치.**
- **legacy 격리:** deprecated 팩·중복·생성물 legacy를 `_archive/`로. 런타임 로드 경로에서 제외.
- **생성기 은퇴:** DECISIONS(P0)에서 "은퇴" 확정된 `_generate_*.py`는 산출을 SoT로 승격 후 스크립트 격리(재생성 시 SoT 덮어쓰기 방지).
- **lineage 뷰:** 관리탭에서 각 값의 반영경로 표시(I4).

## 4. 방법 (확정)

1. 잔여 팩 SoT 이관(P1 방식: 무손실 → byte-diff 0; 단 언어/구조 상이 팩은 해당 단계 정책 적용).
2. MANIFEST 완성 + `validate`(live=로더) CI.
3. 중복·legacy `_archive/` 격리, 로더 경로 정리.
4. 은퇴 생성기 격리 + "data 수기편집 금지" CI 가드.
5. lineage 뷰 배선·검증.

## 5. 금지사항 (Executor)

- ❌ 로더가 아직 참조하는 팩을 격리 (MANIFEST live=로더 확인 전).
- ❌ 생성기 은퇴 시 커버리지 공백 방치.
- ❌ ch5 team_governance(Python dict) 이관을 스펙 없이 강행 (§7 확정본 대기).
- ❌ lineage 뷰를 실제 경로와 불일치로 표기.

## 6. Gatekeeper 점검항목

- [ ] MANIFEST live가 실제 로더와 **100% 일치**
- [ ] 고아팩(로더 없는 live) 0
- [ ] 은퇴 생성기가 커버리지 공백 안 남김
- [ ] 격리된 legacy를 런타임이 로드 안 함
- [ ] `data` 수기편집 금지 CI 강제
- [ ] lineage 뷰가 실제 반영경로와 일치

## 7. STAGE-ENTRY 확정본 (⚠ P3 PASS 후 Gatekeeper가 채움)

> - 잔여 팩 전수 목록·이관 정책(팩별 byte 0 or 구조전환)
> - ch5 team_governance(Python dict) 이관 형태 결정
> - 격리 대상·은퇴 생성기 최종 목록(DECISIONS 확정 반영)
> - lineage 뷰 데이터 계약(필드→팩→소비 매핑 소스)

## 8. Exit 게이트

1. 전체 인벤토리 재조정(잔여 0)
2. MANIFEST live=로더 100%, 고아 0
3. lineage 뷰 정확
4. data 수기금지 CI green

## 9. 롤백

- 팩 단위(각 이관 독립 diff 게이트). 격리는 `_archive` 이동이라 복원 가능.

---

## DIAG-SOT 완료 정의 (전체)

| # | 기준 |
|---|------|
| DoD1 | SoT 단일(iris-hub), diagnosis-tool `data`=생성물·수기금지 CI |
| DoD2 | P1 대상 byte-diff 0 이력 + 골든 회귀 무변화 |
| DoD3 | 언어 ko-master + fallback, 4언어 패리티 |
| DoD4 | A1/A2 세부산업 차별화 실재(이전 공백 해소) |
| DoD5 | 모든 편집이 lineage로 반영경로 노출(제1 동인) |
| DoD6 | prod 전 과정 무접촉, 롤백 가능 |
