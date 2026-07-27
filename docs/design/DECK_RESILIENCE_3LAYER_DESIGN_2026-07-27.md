# 덱 생성 3중 방어(예방·조정·폴백) 설계 및 구현 지시서

- 작성일: 2026-07-27
- 대상 실행자: Cursor AI (M5)
- 설계 책임: Claude (설계·검증 전용, 구현 안 함)
- 대상 저장소: `/Users/iris/0Dev/iris-hub` (dev), 브랜치 `feat/agent-monitor-integration`
- 관련 설계서: [DECK_V3_DESIGN.md](./DECK_V3_DESIGN.md)
- 관련 소스: [pattern_contract.py](../../src/engine/output/deck/pattern_contract.py) · [designer.py](../../src/engine/output/deck/designer.py) · [expander.py](../../src/engine/output/deck/expander.py) · [pptx_export.py](../../src/engine/output/deck/pptx_export.py)

---

## 0. 이 문서만 읽고 실행할 수 있도록 하는 환경 정보

- Python(venv): `/Users/iris/iris-local/venv/iris-hub/bin/python3`
- 테스트: `/Users/iris/iris-local/venv/iris-hub/bin/python3 -m pytest tests/ -q` (cwd=저장소 루트)
- 실행 중 dev 서버: v31 셸 `http://localhost:8767` ( `bash v31/start.sh` , src를 --reload 감시)
- LLM: Ollama `http://localhost:11434`, 검증용 모델 `qwen3:30b` (설치됨). 기본 config 모델 `qwen3:8b`은 **미설치**이므로 API 호출 시 반드시 `"model":"qwen3:30b"`를 명시할 것.
- 파이프라인 3단계: `/api/expand`(확장) → `/api/design`(설계) → `/api/render`(렌더). 상태는 `v31/server.py`의 `_state`에 단계별로 저장됨.

---

## 1. 배경 — 지금 무엇이 왜 실패하는가

룰엔진은 현재 **"검증 후 거부(reject)"** 모델이다. 소스 데이터가 규칙 상한을 넘으면 변환하지 않고 전체 덱 생성을 실패시킨다. 확장기(계약 발행)와 룰엔진(거부권) 사이에 **조정 계층이 없다.**

관측된 실패 (2026-07-27, 赛美特 SGM 소스):
```
설계 실패: 2번(table): column은 2~6개, 현재 8개
```
- 소스에 8열 표가 있음 → 확장기가 8열 table을 그대로 계약에 넣음
- 디자이너가 8열 table로 슬롯 채움 → 룰엔진 `validate_table_data`([pattern_contract.py:607](../../src/engine/output/deck/pattern_contract.py:607))가 "열 2~6개" 규칙으로 반려
- 단일 슬라이드 1회 재교정도 원본이 실제 8열이라 재차 8열 → 최종 하드 실패

이 실패 계열은 표뿐 아니라 **"데이터 > 상한"인 모든 제약**에서 동일하게 발생한다. 목표는 이 계열을 3중 방어로 근본 해소하는 것.

### 1.1 현재 룰엔진 제약 인벤토리 (구현 시 참고)

**항목 개수(splittable — 초과 시 이번 작업의 조정 대상):**
- table: columns **2~6**(하드 반려), rows≥2
- card-grid-4: cards **3~8**
- phase-roadmap: phases **3~8**
- dimension-5: dimensions **4~8**
- metrics-row: metrics **3~6**
- summary: points **3~8**
- narrative: paragraphs **1~5**
- agenda: items≥2 (상한 없음)
- exec-summary / compare-2col: 좌/우≥1

**표 상한 3중 불일치(반드시 통일할 것):** `MAX_TABLE_COLS=5`([:80](../../src/engine/output/deck/pattern_contract.py:80), 분할 트리거, 현재 dead code) vs `max_items.columns=6`([:148]) vs `validate_table_data` 하드 6열([:607]). → **정본을 6열로 통일**하고 `MAX_TABLE_COLS`를 6으로 맞춘다(또는 상수 하나로 단일화).

**기타(이번 작업에서 건드리지 않음, 참고만):** 어휘 화이트리스트(패턴11/role11/body_type4/색상5), 필수 슬롯, 콘텐츠 풍부함, 구조·순서(1번 cover 등), 의미 일관성(pattern↔role), body_type↔pattern 일치.

**또 다른 하드 실패 경로(폴백 대상 §4에 포함):** 정보 보존 coverage — 누락 슬라이드가 절반 이상이면 `PatternContractError`로 전체 반려 ([designer.py:335](../../src/engine/output/deck/designer.py:335)).

---

## 2. 목표 아키텍처 — 3중 방어

```
확장기 expander (Stage 1)
   └─ ① 예방(Prevention): 프롬프트에 수치 제약 주입 → 애초에 위반 계약을 안 만들게
        └─ 디자이너 designer + LLM (Stage 2): 계약대로 슬롯 채움
             └─ ② 조정(Reconcile): 결정론적 변환으로 규칙에 맞게 자동 분할 (신규 계층)
                  └─ 룰엔진 검증
                       └─ ③ 폴백(Fallback): 그래도 실패하는 슬라이드만 안전 패턴으로 강등
                            → 덱 전체는 절대 하드 실패하지 않음
```

**불변 원칙:**
- 데이터 손실 금지(조정은 분할·재배치만, 삭제·날조 금지).
- 조정은 **결정론적**(LLM 호출 없음).
- 폴백은 **최후 수단**(예방·재교정·조정을 다 거친 뒤에만).
- 완료 후 `/api/design`은 유효 입력에 대해 **하드 실패하지 않는다**(품질 경고는 반환 가능).

---

## 3. 계층 ① 예방 (expander 프롬프트) — `expander.py`

`_PROMPT`의 형식 계약 규칙 블록(현재 `3b`/`4` 근처)에 **수치 상한과 초과 시 분할 지시**를 추가한다. (자연어 규칙만 추가; 코드 검증 로직은 기존 것 사용.)

추가할 규칙(요지):
- **표는 최대 6열.** 원본 표가 7열 이상이면 **첫 열(키/구분 열)을 반복**하고 나머지 열을 나눠 **2개 이상의 `table` 슬라이드**로 만든다(예: `제목 (1/2)`, `제목 (2/2)`).
- 항목 상한: card-grid-4 카드 ≤8, phase-roadmap 단계 ≤8, dimension-5 관점 ≤8, metrics-row 지표 ≤6, summary 불릿 ≤8, narrative 단락 ≤5. **초과하면 여러 슬라이드로 나눈다**(내용을 버리지 말 것).
- 표가 너무 길면(행 8개 이상) 의미 단위로 여러 표 슬라이드로 나눠도 좋다.

주의: 예방은 **확률적**(LLM이 안 지킬 수 있음)이므로 §4 조정이 백스톱이다. 디자이너(`designer._build_prompt`)는 required 모드에서 계약 장수를 못 바꾸므로 예방의 핵심은 **확장기**다. `PATTERN_SLOTS` 문구에 "범위 초과 금지"만 한 줄 보강(선택).

**검증:** 기존 확장 테스트 통과 + `/api/expand`로 8열 소스 투입 시 확장 결과가 2개 이상의 table로 쪼개지는지 육안 확인(확률적이라 실패해도 §4가 잡으면 OK).

---

## 4. 계층 ② 조정 (신규 결정론 모듈) — `src/engine/output/deck/deck_reconciler.py`

LLM 없이 Deck을 규칙에 맞게 기계적으로 변형하는 **신규 모듈**을 만든다.

### 4.1 공개 API

```python
def reconcile_deck(
    deck: Deck,
    contracts: list[SlideContract] | None,
) -> tuple[Deck, list[SlideContract] | None, list[str]]:
    """규칙 초과 슬라이드를 분할해 규칙에 맞는 새 Deck을 만든다.
    반환: (새 deck, 재생성된 contracts, 변경 로그)
    - 결정론적. LLM 호출 없음. 데이터 삭제·날조 금지.
    - 슬라이드 수가 늘어날 수 있으므로 contracts/expected를 반드시 재생성한다.
    """
```

### 4.2 슬라이드별 변환 규칙 (분할 = split_*)

각 슬라이드를 순회하며, 아래 조건에 걸리면 **여러 슬라이드로 치환**한다. 걸리지 않으면 그대로 통과. 분할된 슬라이드는 **원본의 pattern·body_type·roles를 그대로 상속**한다.

1. **넓은 표 (table, columns > 6)** — 신규 `split_table_by_columns(data, max_cols=6)`:
   - `columns[0]`을 키 열로 고정(모든 청크에 반복).
   - 데이터 열 `columns[1:]`를 **크기 5씩** 청크 분할(키1 + 데이터5 = 6열).
   - 각 청크: `columns=[key]+chunk_cols`, `rows`는 해당 key만 투영(`{k: row[k] for k in 유지열}`).
   - `title` → `f"{원제목} ({i}/{n})"`. `subtitle`은 전 슬라이드 유지, `footnote`는 마지막 슬라이드에만.
2. **긴 표 (table, rows > 7)** — 기존 `split_table_slide_data`([pattern_contract.py:582 부근])를 **재사용·배선**. 열 분할을 **먼저**, 그다음 각 결과에 행 분할을 적용(중첩). `table_needs_split`도 이때 사용.
3. **항목 과다 패턴** — 신규 `split_items_slide(slide, contract, list_key, max_n)`:
   - card-grid-4 `cards`>8 → ≤8씩 분할. `intro`는 첫 장, `outro`는 마지막 장만.
   - phase-roadmap `phases`>8 → ≤8씩 분할(순서 연속 유지). `footer_note`는 마지막 장.
   - dimension-5 `dimensions`>8 → ≤8씩.
   - metrics-row `metrics`>6 → ≤6씩.
   - summary `points`>8 → ≤8씩.
   - narrative `paragraphs`>5 → ≤5씩.
   - 공통: 분할 슬라이드 title에 `(i/n)` 부여, subtitle 유지.
4. **미달(항목 부족)은 조정 대상 아님** — 데이터 날조 금지. 미달은 §5 폴백 또는 §3 예방이 담당.

### 4.3 계약·expected 재생성 (중요 — 안 하면 검증이 깨짐)

`validate_deck_patterns(deck, expected)`([pattern_contract.py:697])는 `actual == expected`를 검사한다. 조정이 슬라이드 수를 바꾸므로 **반드시 새 deck 기준으로 contracts와 expected를 다시 만든다.** 각 분할 슬라이드의 contract는 원본 contract를 복제하되 `index`만 갱신. `expected = [s.pattern for s in new_deck.slides]`.

### 4.4 파이프라인 배선 — `designer.design_deck`

`_slides_from_payload`로 deck을 만든 직후, **검증 전에** 조정을 삽입한다:

```python
slides = _slides_from_payload(data)
deck = Deck(...)
# ▼ 신규: 조정
deck, contracts, expected = reconcile_deck(deck, contracts)  # expected도 갱신
_validate_and_guard_deck(deck, md_text, contracts, expected)
return deck
```

- 단일 슬라이드 재교정(`_retry_single_slide`) 경로에서도 교정 후 재조정이 필요할 수 있으니, 재교정 결과에도 `reconcile_deck`을 통과시킨 뒤 검증할 것.
- `check_deck_coverage`는 슬라이드 수와 bodies 수가 어긋나면 이미 안전 폴백(`bodies=[source_md]*n`)이 있으므로 크래시하지 않는다(품질만 느슨해짐 — 허용).

### 4.5 표 상한 통일

`MAX_TABLE_COLS`를 **6**으로 맞추고, `validate_table_data`·`max_items.columns`·`split_table_by_columns(max_cols=6)`가 모두 같은 상수를 참조하도록 정리한다.

---

## 5. 계층 ③ 폴백 (안전망) — `designer.py`

예방·재교정·조정을 모두 거친 뒤에도 슬롯 검증에 실패하는 슬라이드는 **그 슬라이드만** 안전 패턴으로 강등하고, **덱 전체는 성공 반환**한다.

### 5.1 폴백 함수

```python
def fallback_slide(slide: Slide, contract, source_body: str) -> tuple[Slide, str]:
    """검증 불가 슬라이드를 안전 패턴으로 강등. (새 Slide, 경고문) 반환.
    - 표/도형형 데이터가 깨졌으면 → summary(핵심 불릿) 또는 narrative(문단).
    - title은 유지. 데이터에서 추출 가능한 텍스트를 불릿/문단으로 재구성(날조 금지).
    - 아무 텍스트도 못 살리면 source_body에서 문장을 뽑아 narrative로.
    """
```
강등 우선순위: 표는 열이 많아 못 살리면 → `summary`(행별 요약 불릿) → 안 되면 `narrative`.

### 5.2 배선

`design_deck` 말미에서 현재 `raise DesignError(...)`로 끝나는 경로를 **폴백 적용 후 반환**으로 교체한다:

```python
def _apply_fallbacks(deck, contracts, md_text) -> tuple[Deck, list[str]]:
    """각 슬라이드 validate_slide_slots 시도; 실패 시 fallback_slide로 치환.
    경고 목록과 함께 항상 유효한 deck 반환(하드 실패 없음)."""
```
- 2회 전체 재설계 + 단일 슬라이드 재교정 + 조정을 다 소진한 **최후에만** 호출.
- coverage 하드 실패(§1.1)도 **경고로 강등**한다: `_validate_and_guard_deck`에서 coverage 임계 초과 시 `raise` 대신 경고 누적으로 변경(폴백 철학 = never hard-fail).

### 5.3 경고 노출

폴백/조정으로 생긴 경고를 `/api/design` 응답에 `"warnings": [...]`로 담아 UI가 표시할 수 있게 한다(`v31/server.py run_design`). `Deck`에 `warnings: list[str]` 필드를 추가하거나 반환 튜플로 전달. UI는 배지/토스트로 "N개 슬라이드 자동 조정/강등됨" 표시(UI 변경은 선택, 최소한 API에 실어줄 것).

---

## 6. 엣지 케이스 (반드시 처리)

- 표 열이 정확히 6이면 분할 안 함. 7이면 6+2가 아니라 6(키1+데5)+2(키1+데1) → **모든 청크 ≤6**인지 확인.
- 키 열 자체가 없거나 열이 1개면 표로 부적합 → 폴백(summary).
- 분할로 슬라이드가 과도하게 늘면(예: 12열+20행) 상한(예: 한 표 최대 4청크)로 캡하고 경고.
- 분할 슬라이드 title 중복 시 `(i/n)` suffix로 구분.
- body_type↔pattern 일치 규칙([pattern_contract.py 파싱])을 분할 후에도 위반하지 않게(pattern 상속하므로 자동 충족).
- cover 슬라이드는 조정·폴백 대상 아님.
- 빈 rows/cards 등 미달은 조정하지 말 것(폴백 또는 통과).

---

## 7. 테스트 요구사항 (`tests/`)

신규 `tests/test_deck_reconciler.py` + 기존 회귀:

**조정(단위):**
1. 8열 표 → 2개 table 슬라이드, 각 ≤6열, **모든 셀 데이터 보존**(원본 값 합집합 == 분할 후 합집합).
2. 7열/9열/12열 경계값 각각 청크 수·열수 검증.
3. 20행 표 → 행 분할, 헤더 반복.
4. 12열+15행 → 열·행 중첩 분할, 데이터 보존.
5. card 12개 → 2슬라이드(≤8), intro=첫장·outro=마지막장.
6. phases 10개 / metrics 8개 / points 10개 / paragraphs 7개 각각 분할.
7. body_type·roles 상속 확인.
8. contracts/expected 재생성: `len(expected)==len(new_deck.slides)`, `expected==[s.pattern...]`.

**폴백(단위):**
9. 살릴 수 없는 표(열 1개) → summary/narrative로 강등, 예외 없음.
10. coverage 임계 초과 → `raise` 대신 경고 반환.

**회귀:**
11. 기존 46개 덱/계약/확장 테스트(`tests/test_pattern_contract.py`, `test_deck_expander.py`, `test_table_pattern.py`) 전부 통과 유지.

**e2e(수동/스크립트):**
12. 8열 표 포함 소스로 `/api/expand`(model=qwen3:30b) → `/api/design`(model=qwen3:30b)가 **HTTP 200**으로 성공하고 `warnings`에 조정 내역이 담기는지. `/api/render`(PPTX)까지 렌더되는지.

---

## 8. 비목표 (이번 작업 범위 밖)

- 어휘 화이트리스트·필수 슬롯·의미 일관성 규칙 변경 없음.
- 표 열 상한 자체를 6에서 올리지 않음(가독성 정책 유지, 통일만 함).
- pptx_export 레이아웃 로직 변경 없음(신규 패턴 빌더는 이미 존재).
- 미달(항목 부족) 데이터의 자동 보강/날조 없음.
- body_type 축 자체 재설계 없음(2026-07-27 커밋 `ceae1eb`로 확정됨).

---

## 9. 완료 기준 (acceptance)

1. `deck_reconciler.py` 신규 + `designer.design_deck` 배선 + 폴백 배선 완료.
2. 표 상한 3중 불일치 해소(단일 상수 6).
3. `tests/` 신규·회귀 전부 green (`pytest tests/ -q`).
4. e2e: 8열 표 소스가 `/api/design`에서 **더 이상 하드 실패하지 않고**, 조정/경고와 함께 성공.
5. 유효 입력에 대해 `/api/design`이 하드 실패하지 않음(불변 원칙).

## 10. 실행 순서 권고

① 표 상한 통일(§4.5, 가장 작음) → ② `deck_reconciler.py` + 단위 테스트(§4,§7) → ③ designer 배선(§4.4) → ④ 폴백(§5) → ⑤ 예방 프롬프트(§3) → ⑥ e2e 검증(§7.12).

작업은 `feat/agent-monitor-integration` 브랜치에서 진행하고, 완료 후 커밋·푸시·(필요 시)live 동기화는 실행자(Cursor) 책임.
