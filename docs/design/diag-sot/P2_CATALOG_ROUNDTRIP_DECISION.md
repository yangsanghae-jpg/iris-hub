# Gatekeeper 결정 — P2 fixed-label 카탈로그 byte-0 방침 (D1a 개정)

- **결정일:** 2026-07-05 · Gatekeeper(Claude)
- **계기:** M2가 P2 카탈로그 라운드트립 구현 중 `client/i18n/*.json`의 **중복키·빈줄** 때문에 strict byte-0 불가를 발견하고 **커밋 전 정지**(D1 순서 준수 — 옳음).

---

## 0. 확인된 사실 (Gatekeeper 독립 검증)

| 파일 | 결함 |
|------|------|
| `client/i18n/en/ui.json` | 중복키 3 (`q2.recommended_subindustry_prefix`, `a2.q5.current_level`, `a2.q5.datapack_pending`) |
| `client/i18n/ko/ui.json` · `ja/ui.json` | 중복키 2 (`a2.q5.current_level`, `a2.q5.datapack_pending`) |
| `client/i18n/ja/report.json` | 빈줄 5 |
| `client/i18n/zh/messages.json` | 빈줄 2 |

- **핵심:** `json.load`는 **last-wins**로 중복을 접는다 = **JS `JSON.parse`와 동일.** 즉 **런타임은 이미 마지막 값만 본다.** 앞선 중복 라인·빈줄은 죽은 바이트.
- 키는 **flat dot-key**(`routing.L1` vs `routing.L1.title` 공존) — unflatten하면 충돌. **flat opaque 유지**(M2 수정 방향 승인).

## 1. 판정 — 정규화(normalize), raw-lexical 아님

- **raw-lexical 보존(중복키·빈줄 byte 보존) 기각.** 이유: ① `dx_fixed_label`은 **id→값 테이블**이라 **중복키를 표현할 수 없음**(정규화가 모델상 강제). ② 결함을 SoT에 영속화 = 품질 목표에 역행.
- **채택: dedup-keep-last + blank-strip.** dedup은 **마지막 값 유지**(런타임 일치) → **파싱객체 불변 = 의미 무손.** 이건 잠재버그(중복키) **정리**이기도 하다.

## 2. D1a 개정 — 카탈로그 라운드트립 게이트

**strict byte-0 → "parsed-identical + 열거된 결함정규화만":**

| 조건 | 기준 |
|------|------|
| G1 | 전 16개 `client/i18n/**` 파일: **`json.load(export) == json.load(legacy)`** (의미 동일) |
| G2 | export vs legacy **byte diff는 오직** (a) 중복키 라인 제거(**last 값 유지**), (b) 빈줄 제거 — **그 외 diff 0** |
| G3 | 결함 없는 파일(대부분)은 **여전히 byte-0** |
| G4 | dedup/blank **전수 열거 리포트**: 파일·키·**중복값 동일여부**·keep=last·제거 빈줄 위치 |

- 이 정규화는 **P2의 tracked intended-diff**(품질 정리). export가 곧 clean 정본이 되고, 컷오버 시 malformed legacy를 대체.

## 3. 실행 순서 (변경 없음)

1. **카탈로그 라운드트립 게이트(G1~G4) PASS** ← 지금 단계
2. active key / ko 결측 산출·채움 (D2)
3. resolver ko-flip (`DEFAULT_LANG=ko`, chain `[lang, ko]`)
4. `index.html` shell ko (D4)
5. Ch2 렌더러·`lang_ko.py`·server 기본 **무변경 검증** (D3/D5)

## 4. Gatekeeper 재검증 방식

재제출 시 나는 **exporter를 dx 아티팩트만으로 실행** → 16파일 재생성 → 각 파일 `json.load` 동일성(G1) + byte diff가 **dedup/blank 한정**(G2)인지, 결함없는 파일 byte-0(G3)인지 직접 확인한다. 그 외 라벨 텍스트 변경이 1건이라도 있으면 실패.

## 5. 지시 (M2)

- 현재 미추적 산출물(`p2_fixed_label_catalog.py`, `_p2/`, roundtrip 리포트)을 위 G1~G4 충족하도록 보강 후 **커밋+push.**
- 결과 보고에 **dedup/blank 열거표**(§2 G4) + 재현 명령 포함.
- **아직 resolver/shell ko-flip 착수 금지**(순서 1 통과 후).

> 이 결정은 P2_DISCOVERY_APPROVAL D1a를 개정한다. 나머지 D1b~D5 불변.
