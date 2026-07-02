# PPT 탭 V3.0 재설계서 — 3단 파이프라인 + 덱 린트

- 작성일: 2026-07-02
- 대상 버전: V2.8.2 (deck 엔진) → **V3.0**
- 관련 코드: `src/deck/*`, `src/tabs/pptx.py`, `src/llm.py`, `data/templates/slides/*`, `data/themes/iris.css`
- 근거 자료: 클로드 생성 덱(`종합지표관리체계.pdf`, 14장) vs iris-hub 생성 덱(`deck_2026-06-22_184705.pdf`, 25장) 비교 분석

---

## 0. 요약 (한 장)

| 항목 | 현행 V2.8.2 | V3.0 |
|---|---|---|
| 파이프라인 | 2단 (expander 확장 → designer 거대 JSON 1방) | **3단** (storyboard 설계 → slidegen 장당 생성 → render) |
| LLM 호출 | 덱당 2회, 두 번째가 32k 토큰 거대 JSON | 덱당 1 + N회, 전부 소형 JSON |
| 패턴 선택 | LLM 자유 → compare-2col로 붕괴 (25장 중 ~20장) | storyboard 산출물로 **고정** + 다양성 하드 제약 |
| 패턴 종류 | 8종 (표·플로우·계층 없음) | **12종** (+table, process-flow, stack, section-divider) |
| 품질 검증 | 없음 (모델 출력 무검증 통과) | **슬라이드 검증기 + 덱 린트** (block/warning, 자동 재생성) |
| 색 문법 | red/green 남용 (모든 2열이 빨강/초록) | 네이비 단색 기본 + accent 1색, 의미 있을 때만 대비색 |
| 사람 개입 | 없음 (입력 → 결과) | **스토리라인 확인·수정 단계** (UI 위저드 2단계) |
| 실패 처리 | 거대 JSON 잘림 → `_repair_truncated_json` 응급 복구 | 장당 재시도 2회 → 결정적 fallback (덱 생성 실패 없음) |
| 모델 | 로컬 deep 단일 | role `design` 신설, **Ollama/Claude API 선택형** (덱당 1회 호출만 클라우드 옵션) |

---

## 1. 배경 — 무엇이 왜 조악한가

### 1.1 증상 (SSIM 덱 실측)

1. 25장 중 로드맵 1장 제외 **약 20장이 동일한 compare-2col** (빨강/초록 2열 카드).
2. 항목 제목이 `目标一/原则一/流程一` 같은 **번호 필러** — 정보가 없는 제목.
3. 슬라이드 하단 40~60%가 빈 공간 (슬롯 4개 카드가 세로로 흘러내림).
4. 표지 제목 줄바꿈 깨짐 (`完整文/档`) — 글자수 대응 폰트 축소 없음.
5. 원문 표가 전부 2열 카드로 변환 — **표 패턴 자체가 없음**.
6. 스토리 부재: 섹션 순서 그대로 나열. 요약/기대효과/CSF 같은 재구성 없음.

### 1.2 근본 원인 (코드 기준)

| # | 원인 | 위치 |
|---|---|---|
| R1 | 30장 분량 거대 JSON 1방 생성 (`num_predict=32768`) → 후반 품질 붕괴·잘림 | `designer.py:202-206` |
| R2 | 패턴 선택을 LLM 자유에 위임, "표는 compare-2col로 전개" 지시 | `designer.py:91,97-104` |
| R3 | `{title, detail}` 슬롯이 제목 창작을 강요 → 로컬 모델이 번호 필러로 회피, **생성 후 검증 없음** | `designer.py:26-36`, 검증기 부재 |
| R4 | expander가 "정보 손실 금지·전 섹션 전개"만 강제 — 전사(transcription)이지 작문(authoring)이 아님 | `expander.py:50-63` |
| R5 | 색 규칙 "진단 red/해결 green"이 중립 내용에 남용 | `designer.py:95` |
| R6 | 템플릿 8종에 table/flow/stack/divider 부재 | `schema.py:12-21` |

### 1.3 클로드 덱이 좋은 이유 (벤치마크 분해)

- **장마다 다른 레이아웃**: 내용 구조(계층/비교/순환/일정/지표)를 판별해 형식을 맞춤.
- **스토리 아크**: 배경 → 체계 → 분류 → 정의 → 프로세스 → 거버넌스 → 로드맵 → 기대효과 → 요약.
- **재구성 산출물**: 원문에 없던 Executive Summary(WHY/WHAT/HOW/WHEN/EFFECT), 수치 카드.
- **절제된 색**: 네이비 단색 + 포인트 블루, 시맨틱 컬러는 PDCA/로드맵에서만.
- → V3.0의 설계 목표는 이 4가지를 **파이프라인 구조로 강제**하는 것. 모델 지능에 기대지 않는다.

---

## 2. 목표 / 비목표

### 목표
1. 같은 입력에서 **패턴 4종 이상, 동일 패턴 40% 이하**의 덱 산출.
2. 필러 제목 0건 (린트로 검출·재생성).
3. 덱 생성이 **절대 실패하지 않음** (장당 fallback).
4. 스토리라인에 사람이 개입 가능 (수정 후 생성).
5. 설계 1회 호출만 클라우드 모델 옵션 (비용 상한: 덱당 1회).

### 비목표 (V3.0에서 하지 않음)
- 편집 가능한 네이티브 PPTX (도형·텍스트박스) — PNG 임베드 유지. V3.1 후보.
- 이미지·차트 자동 생성 (matplotlib 차트 삽입) — V3.2 후보.
- Marp 엔진 변경 — 단순·빠름 용도로 현행 유지.
- 템플릿 테마 다중화 (라이트/다크 등) — iris 단일 테마 유지.

---

## 3. 아키텍처

### 3.1 현행 (V2.8.2)

```
사용자 md
  ↓ expander.expand_for_slides()   … LLM 1회, 자유 md 확장 (전사)
확장 md
  ↓ designer.design_deck()         … LLM 1회, 거대 JSON (30장 슬롯 채우기)
Deck ─→ renderer(PDF) / pptx_export(PPTX)
```

### 3.2 신규 (V3.0)

```
사용자 md
  ↓ ① sections.parse()             … LLM 없음. 헤딩 단위 섹션 분해 + id 부여
SectionSet {s1..sn}
  ↓ ② storyboard.plan()            … LLM 1회 (role=design). 덱 서사 + 장별 {메시지, 패턴, 섹션참조}
  ↓ ②' storyboard.enforce()        … LLM 없음. 패턴 다양성 하드 제약 후처리
DeckPlan  ←——— [UI: 사람 확인·수정 단계] ———
  ↓ ③ slidegen.generate()          … LLM N회 (role=deep, 장당 1회, 병렬 2~3)
  ↓ ③' validators.check() 장당     … 실패 → 재시도 2회 → deterministic fallback
Deck
  ↓ ④ lint.run()                   … LLM 없음. 덱 전체 품질 리포트 (block/warning)
  ↓ (block 슬라이드만 재생성 1회)
  ↓ ⑤ renderer(PDF) / pptx_export(PPTX)   … 현행 유지 + 폰트/자동축소 개선
```

### 3.3 모듈 배치

| 파일 | 상태 | 역할 |
|---|---|---|
| `src/deck/sections.py` | **신규** | md → 섹션 분해 (헤딩 트리, 표 보존, id 부여) |
| `src/deck/storyboard.py` | **신규** | DeckPlan 생성 + 다양성 제약 후처리 |
| `src/deck/slidegen.py` | **신규** | 장당 생성 + 슬롯 검증 + fallback |
| `src/deck/validators.py` | **신규** | 패턴별 슬롯 검증기 (순수 함수) |
| `src/deck/lint.py` | **신규** | 덱 린트 (품질 게이트) |
| `src/deck/schema.py` | 수정 | DeckPlan·SlideSpec 추가, 패턴 12종 |
| `src/deck/designer.py` | 유지(레거시) | UI에서 "V2 엔진"으로 선택 가능, V3.1에서 제거 |
| `src/deck/expander.py` | 유지(레거시) | 〃 |
| `src/deck/renderer.py` | 소폭 수정 | 폰트·pageno 유지 |
| `src/deck/pptx_export.py` | 유지 | |
| `src/llm.py` | 수정 | role `design` 추가, provider 분기 |
| `src/llm_cloud.py` | **신규** | Claude API 어댑터 (generate_json 동일 시그니처) |
| `src/tabs/pptx.py` | 재작성 | 4단 위저드 UI |
| `data/templates/slides/*.j2` | 추가 4종 + 전면 CSS 정비 | |

---

## 4. 스키마 정의

### 4.1 SectionSet (① 산출)

```python
@dataclass
class Section:
    sid: str            # "s1", "s2", ...
    level: int          # 헤딩 레벨 (1~4)
    title: str          # 헤딩 텍스트
    body_md: str        # 헤딩 아래 원문 (표·리스트 원형 보존)
    char_count: int
    has_table: bool
    has_numbers: bool   # 수치 포함 여부 (린트 수치검증 대상 선별용)

@dataclass
class SectionSet:
    sections: list[Section]
    toc: str            # "s1 제목 / s2 제목 ..." — storyboard 프롬프트용 목차 문자열
```

파서 규칙:
- `#`~`####` 헤딩 기준 분할. 헤딩 없는 서두는 `s0`(front) 처리.
- 표는 절대 분할하지 않음 (행 단위 쪼개기 금지).
- 한 섹션 3,000자 초과 시 문단 경계에서 `s3a/s3b`로 분할 (slidegen 입력 상한 보호).
- LLM 미사용 — 정규식·라인 파서만. 실패 요인 원천 제거.

### 4.2 DeckPlan (② 산출) — V3.0의 핵심 계약

```json
{
  "deck": {
    "title": "종합 지표 관리 체계",
    "audience": "경영진·전략기획",
    "language": "ko",
    "narrative": "지표 산재라는 문제에서 출발해 체계·프로세스·거버넌스를 제시하고 로드맵과 기대효과로 설득한다",
    "accent": "blue"
  },
  "slides": [
    {"no": 1,  "pattern": "cover",           "message": "",                              "section_refs": [],          "color_mode": "base"},
    {"no": 2,  "pattern": "agenda",          "message": "7개 장 구성",                    "section_refs": ["toc"],     "color_mode": "base"},
    {"no": 3,  "pattern": "compare-2col",    "message": "지표 산재·신뢰성 부족이 현재의 문제", "section_refs": ["s1"],   "color_mode": "contrast"},
    {"no": 4,  "pattern": "stack",           "message": "VISION-KPI 3계층-데이터 인프라의 프레임워크", "section_refs": ["s2"], "color_mode": "base"},
    {"no": 5,  "pattern": "table",           "message": "지표 정의서 8개 항목 표준",       "section_refs": ["s4"],      "color_mode": "base"},
    {"no": 6,  "pattern": "process-flow",    "message": "PDCA 4단계 순환 관리",            "section_refs": ["s5"],      "color_mode": "semantic"},
    {"no": 7,  "pattern": "phase-roadmap",   "message": "12개월 3단계 로드맵",             "section_refs": ["s7"],      "color_mode": "semantic"},
    {"no": 8,  "pattern": "metrics-row",     "message": "보고시간 30%↓ 등 4대 기대효과",   "section_refs": ["s8"],      "color_mode": "semantic"},
    {"no": 9,  "pattern": "exec-summary",    "message": "WHY/WHAT/HOW/WHEN/EFFECT 한 장 요약", "section_refs": ["s1","s2","s7","s8"], "color_mode": "base"},
    {"no": 10, "pattern": "closing",         "message": "",                              "section_refs": [],          "color_mode": "base"}
  ]
}
```

필드 규약:
- `message`: **이 슬라이드가 주장하는 한 문장.** slidegen 프롬프트에 주입되고, 렌더 시 subtitle로도 사용. 빈 문자열은 cover/closing만 허용.
- `section_refs`: slidegen이 받을 원문 섹션 id 목록. **여기 없는 원문은 slidegen에 입력되지 않는다** (환각 차단 + 프롬프트 소형화).
- `color_mode`: `base`(네이비 단색) / `semantic`(단계·상태 의미색) / `contrast`(As-Is/To-Be 대비). red/green 남용 차단 장치 — 템플릿이 이 모드 외 색을 받지 않음.

### 4.3 SlideSpec / Deck (③ 산출)

현행 `Slide(pattern, data)` 유지하되 `Slide.meta`에 `{message, section_refs, gen_model, retries, fallback_used}` 추가 (린트 리포트·디버깅용).

---

## 5. Stage ② storyboard 상세

### 5.1 프롬프트 설계 (요지)

입력: **전문이 아니라 목차 + 섹션별 3줄 발췌** (`SectionSet.toc` + 각 섹션 앞 200자). 전문을 넣지 않는 이유: 설계 단계는 구조 판단만 필요하고, 입력을 줄여야 로컬 모델도 안정적이다.

지시 골격:
1. 청중·목적 추정 → `deck.narrative` 한 문장.
2. 슬라이드 12~20장 (사용자 지정 시 override). **cover, agenda, 본문, exec-summary, closing 순서 강제.**
3. 장마다 `message`를 먼저 쓰고 그에 맞는 패턴을 고름 (메시지 우선 원칙).
4. 패턴 선택 기준표 제공 (표 → table, 순환/절차 → process-flow, 계층 → stack, 기간 → phase-roadmap, 수치 → metrics-row, 대비 → compare-2col, 나열 4~8개 → dimension-5/card-grid-4).
5. **동일 패턴 연속 2장 금지, 전체 40% 초과 금지**를 프롬프트에도 명시 (후처리와 이중 방어).
6. 출력은 DeckPlan JSON만. 소형이므로 잘림 위험 낮음 (`num_predict=8192`).

### 5.2 enforce() — 규칙 기반 후처리 (LLM 미사용)

모델이 제약을 어겨도 코드가 교정한다:

```
위반 검출:
  a. 같은 패턴 3연속        → 가운데 장을 대체 패턴으로 치환
  b. 단일 패턴 > 40%        → 초과분을 섹션 특성 기반 규칙으로 재배정
     (has_table → table / 항목 4~8개 → dimension-5 / 그 외 → card-grid-4)
  c. cover/agenda/closing 누락 → 자동 삽입
  d. section_refs 미참조 섹션 존재 → 경고 목록으로 UI에 표시 (자동 추가는 안 함 — 요약은 생략이 정상)
  e. slides > 25 → message 유사도 높은 인접 장 병합 제안 (UI 표시만)
```

### 5.3 모델·provider

- 신규 role `design`. `config.LLM_MODELS["design"]` 기본값 = deep과 동일 모델.
- `IRIS_LLM_DESIGN_PROVIDER = ollama | anthropic` (기본 ollama).
- anthropic 선택 시 `llm_cloud.generate_json()` 호출 — 반환 dict 형태 `{ok, data, ms, model, error}`를 `llm.generate_json`과 동일하게 맞춰 storyboard 코드는 provider 무지(無知).
- 클라우드 실패(키 없음·네트워크) 시 **자동으로 로컬 design → deep 순 fallback**, UI에 배지 표시.
- 비용 통제: 클라우드 호출은 **storyboard 1회만**. slidegen은 항상 로컬. (덱당 입력 ~4k·출력 ~2k 토큰 수준)

---

## 6. Stage ③ slidegen 상세

### 6.1 호출 단위와 입력

- 장당 LLM 1회. 입력 = `해당 패턴의 슬롯 정의 + message + section_refs 원문(합계 상한 4,000자)`.
- `temperature=0.2`, `num_predict=4096`, `format=json` (Ollama JSON 모드 강제 — qwen `<think>` 누출 차단).
- cover·closing·agenda는 **LLM 미사용**: meta와 DeckPlan에서 결정적으로 채움 (표지 품질 편차 제거).
- 병렬도 2~3 (Ollama 동시 요청 한계 고려, `concurrent.futures.ThreadPoolExecutor`).

### 6.2 패턴별 슬롯 검증기 (`validators.py`)

모든 슬라이드는 저장 전 검증을 통과해야 한다. 검증기는 순수 함수로 단위 테스트 대상.

공통 규칙:
```
V-C1  필수 슬롯 존재 (패턴별 정의)
V-C2  제목류(title/label) 길이 4~40자
V-C3  필러 제목 정규식 거부:
      (目标|原则|流程|活动|工作|항목|목표|원칙|단계)[一二三四五六七八九十0-9]$
      ^(Goal|Item|Step|Principle)\s*\d+$
V-C4  항목 수가 슬롯 정의 범위 내 (예: dimensions 4~8)
V-C5  detail/summary 문장형 최소 15자 (단어 나열 차단)
V-C6  color 값은 color_mode 허용 집합 내
```

패턴별 예시:
```
table:         columns 2~5, rows 3~10, 셀 최대 60자, 헤더 필수
process-flow:  steps 3~6, 각 step {label ≤10자, bullets 2~5}
stack:         layers 2~5, 각 layer {label, desc, emphasis?}
metrics-row:   value는 숫자·%·배수 패턴 매칭 필수 (원문 유래 검증은 린트에서)
```

### 6.3 재시도·fallback 정책

```
1차 생성 → 검증 실패 → 실패 사유를 프롬프트에 덧붙여 재생성 (최대 2회)
  예: "이전 응답의 문제: 제목이 '目标一' 같은 번호 필러였음. 원문 어구에서 제목을 뽑아라."
2회 실패 → deterministic fallback:
  - 섹션 원문을 규칙으로 직접 슬롯에 사상
    (헤딩→title, 리스트 앞 8개→items, 표→table 패턴으로 패턴 자체를 강등)
  - meta.fallback_used=True → 린트 리포트에 표시
결과: 덱 생성은 어떤 경우에도 완주한다.
```

### 6.4 수치 보존 장치

- slidegen 프롬프트에 "수치는 원문에 있는 것만, 원문 표기 그대로" 명시.
- 린트 L-N1(§8)에서 프로그램 검증: 슬라이드의 모든 `\d+(\.\d+)?%|\d+배|\d+시간|\d+일` 토큰이 참조 섹션 원문에 존재하는지 대조. 불일치 → warning + 해당 장 하이라이트.

---

## 7. 템플릿·디자인 시스템

### 7.1 신규 패턴 4종

| 패턴 | 용도 | 슬롯 | 시각 사양 |
|---|---|---|---|
| `table` | 정의서·비교표·주기표 | title, subtitle, headers[2~5], rows[3~10][cells], footer_note? | 헤더 행 네이비 배경 백색 글자, 줄무늬 zebra, 첫 열 bold. 클로드 덱 p.6·p.9 준거 |
| `process-flow` | PDCA·절차·순환 | title, subtitle, steps[3~6]{label, color, bullets[2~5]}, cycle_note? | 가로 박스 + 화살표(CSS triangle), semantic 모드에서만 단계별 색. 클로드 덱 p.7 준거 |
| `stack` | 계층 구조·아키텍처 | title, subtitle, top_band?, layers[2~5]{label, desc, right_note?}, bottom_band? | 상하 풀폭 밴드 + 중간 계층 행(좌 라벨 / 중 설명 / 우 주기). 클로드 덱 p.4 준거 |
| `section-divider` | 장 전환 (16장 이상 덱) | chapter_no, title, one_liner | 네이비 풀블리드 + 대형 번호. 긴 덱의 호흡용 |
| `closing` | 마무리 | quote?, contact? | cover 변형. 클로드 덱 p.14 준거 |

(section-divider와 closing 포함 총 13종이 되나, closing은 cover 템플릿 변형으로 구현해 템플릿 파일은 +4개)

### 7.2 색 토큰 (iris.css 정비)

```css
:root {
  --ink-900:#1e3a5f; --ink-700:#2c4f7c;          /* 네이비 기본 */
  --accent:#2f80c4;                                /* 포인트 (deck.accent) */
  --paper:#ffffff; --paper-dim:#f5f7fa;
  --sem-plan:#1e3a5f; --sem-do:#2f80c4;
  --sem-check:#5ba3d9; --sem-act:#27ae60;          /* semantic 모드 전용 */
  --neg:#c0392b; --pos:#27ae60;                    /* contrast 모드 전용 */
}
```
규칙: 템플릿은 color_mode에 따라 허용 변수만 참조. **base 모드에서 red/green 계열 사용 불가** — V2의 "빨강/초록 카드" 재발을 CSS 레벨에서 차단.

### 7.3 타이포·밀도 규칙

- 폰트 스택: `Pretendard, "Noto Sans KR", "Noto Sans SC", sans-serif` (중국어 덱 대응 — SSIM 사례).
- 표지 제목 자동 축소: 글자수 구간별 폰트 크기 (≤12자 64px / ≤20자 52px / ≤32자 42px / 초과 34px) — Jinja 필터 `fit_title`로 구현. `完整文/档` 깨짐 방지.
- 본문 영역 최소 채움률: 템플릿마다 항목 수 하한(V-C4)이 이를 담보. 항목 3개 이하가 배정되면 slidegen 단계에서 인접 슬라이드와 병합하도록 enforce()가 사전 차단.
- 헤더/푸터 통일: 상단 네이비 밴드(제목 + 우측 pageno/total), 하단 좌측 deck_title, 우측 Confidential 표기 1곳만 (현행 표지 중복 제거).

---

## 8. Stage ④ 덱 린트 (`lint.py`)

wiki 린트와 동일한 철학: 기계 판정 + 등급 + 게이트.

| 코드 | 검사 | 등급 |
|---|---|---|
| L-P1 | 패턴 종류 < 4 | warning |
| L-P2 | 단일 패턴 > 40% | **block** (enforce 버그 검출용 — 정상 흐름에선 발생 불가) |
| L-P3 | 동일 패턴 3연속 | warning |
| L-T1 | 필러 제목 검출 (V-C3 정규식, fallback 슬라이드 포함 재검) | **block** → 해당 장 재생성 |
| L-T2 | 제목 40자 초과·4자 미만 | warning |
| L-N1 | 수치 토큰 원문 대조 실패 | warning + 장 하이라이트 |
| L-D1 | 장당 텍스트 총량 < 80자 (빈약 슬라이드) | **block** → 재생성 |
| L-D2 | 장당 텍스트 총량 > 900자 (과밀) | warning |
| L-S1 | cover/agenda/closing 부재 | **block** |
| L-F1 | fallback_used 슬라이드 목록 | info |

- `quality_gate = block | warning | pass` — block 슬라이드는 **자동 재생성 1회** 후 재린트, 그래도 block이면 UI에 사유와 함께 표시하고 다운로드는 허용 (경고 배지). 생성을 막지 않는다.
- 리포트는 JSON으로 `Deck.meta`에 저장 → UI 렌더 + `exports/`에 덱과 함께 `deck_*.lint.json` 저장 (품질 추적 데이터 축적 → 이후 프롬프트 개선 근거).

---

## 9. UI 재설계 (`tabs/pptx.py`)

4단 위저드 (st.session_state로 단계 상태 유지):

```
[1 입력] ─ [2 스토리라인] ─ [3 생성] ─ [4 결과]
```

**1 입력** (현행 유지 + 정리)
- 소스 3종: 직접 입력 / 파일 업로드 / 디스크 md 선택 (archive·docs)
- 메타: 회사명·제목·부제·날짜 + 장수(auto/지정) + 엔진(V3 디자인 / V2 디자인(레거시) / Marp)
- 모델: storyboard용 provider 선택 (로컬 모델 드롭다운 / Claude API), slidegen용 로컬 모델 드롭다운

**2 스토리라인** — V3.0의 사람 개입 지점 (품질 레버리지 최대)
- DeckPlan을 `st.data_editor` 표로 표시: `no | pattern(드롭다운) | message(편집 가능) | 참조 섹션 | color_mode(드롭다운)`
- 행 추가/삭제/순서 변경 지원
- 미참조 섹션 경고 목록 표시 (enforce()의 d 항목)
- [이대로 생성] / [스토리라인 재생성] 버튼
- 여기서 확정된 DeckPlan은 `exports/deck_*.plan.json`으로 저장 → **재현 가능** (같은 plan으로 재생성)

**3 생성**
- 장당 진행바: `st.progress` + 장별 상태 아이콘 (생성중/통과/재시도/fallback)
- 병렬 생성이어도 완료 순 업데이트
- 생성 완료 즉시 린트 실행 → block 자동 재생성 경과 표시

**4 결과**
- 슬라이드 썸네일 그리드 (renderer의 장별 PNG 재활용)
- 린트 리포트 (등급 배지 + 항목별 표) / 장별 [이 장만 재생성] 버튼
- PDF·PPTX 다운로드 + exports 영구 저장 (현행 `_save_to_exports` 유지)

레거시 경로: 엔진 선택에서 V2·Marp 선택 시 기존 흐름 그대로 (한 릴리스 동안 병행 후 V2 제거).

---

## 10. LLM 계층 변경

### 10.1 `src/llm.py`
- `model_for()`에 role `design` 추가. `config.LLM_MODELS = {"deep":…, "fast":…, "embed":…, "design":…}` (기본값 deep 모델 복제).
- `generate_json`에 `format_json: bool = True` 인자 노출 (Ollama `format="json"` — slidegen 안정화).

### 10.2 `src/llm_cloud.py` (신규, ~80줄)
```python
def generate_json(prompt, *, model="claude-sonnet-5", timeout=120.0,
                  max_tokens=8192) -> dict:
    """Anthropic Messages API 호출. 반환 형태는 llm.generate_json과 동일:
    {ok, data, raw, ms, model, error}"""
```
- 의존성: `anthropic` 패키지 (requirements에 optional로, import 실패 시 provider 목록에서 자동 제외).
- 키: `ANTHROPIC_API_KEY` 환경변수. 미설정 시 UI에서 클라우드 옵션 비활성 + 안내.
- 호출처는 storyboard 한 곳뿐. slidegen에서 사용 금지 (비용 상한 원칙).

---

## 11. 구현 순서 (PR 단위)

| PR | 내용 | 규모 | 의존 |
|---|---|---|---|
| PR1 | `sections.py` + `storyboard.py`(plan/enforce) + schema 확장 + 단위 테스트 | 중 | — |
| PR2 | `slidegen.py` + `validators.py` + 결정적 fallback + 테스트 | 중 | PR1 |
| PR3 | 신규 템플릿 4종 + iris.css 토큰 정비 + `fit_title` 필터 + 기존 8종 색 모드 반영 | 중 | — (병행 가능) |
| PR4 | `lint.py` + 재생성 루프 + lint.json 저장 | 소 | PR2 |
| PR5 | `tabs/pptx.py` 4단 위저드 재작성 (레거시 병행) | 중 | PR1~4 |
| PR6 | `llm_cloud.py` + provider 분기 + config | 소 | PR1 |

권장 착수 순서: PR1 → PR2 → PR5(최소 UI) → PR3 → PR4 → PR6.
PR1+PR2+최소 UI만으로도 "20장 동일 패턴·필러 제목·빈 공간"의 대부분이 해소된다.

## 12. 테스트 계획

### 12.1 골든 입력 3종 (`tests/fixtures/deck/`)
1. `ssim.md` — SSIM 방법론 (중국어, 표·단계·SLA 수치 다수) ← 이번 실패 사례
2. `weekly.md` — 주간보고 (현행 `_SAMPLE_MD`, 짧은 입력)
3. `kpi.md` — 종합지표관리 원문 md (클로드 덱과 직접 비교용)

### 12.2 자동 검증 (LLM 호출 mock + 실호출 통합테스트 분리)
```
test_sections:    표 비분할, 3000자 분할, 헤딩 트리
test_enforce:     3연속·40% 위반 입력 → 교정 결과 검증
test_validators:  필러 제목 거부, 슬롯 범위, color_mode 집합
test_fallback:    LLM 2회 실패 mock → 덱 완주 + fallback_used 표식
test_lint:        각 규칙 양성·음성 케이스
통합(수동/야간):   골든 3종 실생성 → 패턴 종류 ≥4, 필러 0, block 0 어서션
```

### 12.3 수용 기준 (V3.0 출시 판정)
- `ssim.md` 재생성 결과: 패턴 5종 이상, compare-2col ≤ 30%, 필러 제목 0, 표 슬라이드 ≥ 2, 빈약 슬라이드(L-D1) 0.
- 생성 시간: 20장 기준 로컬 전용 ≤ 15분 (deep qwen3:8b, 병렬 2), storyboard 클라우드 시 ≤ 8분.

## 13. 리스크와 완화

| 리스크 | 완화 |
|---|---|
| 로컬 모델이 storyboard JSON도 불안정 | 소형 출력(≤8k) + format=json + enforce()가 구조 보정. 최후엔 규칙 기반 기본 plan(섹션→패턴 사상표) 생성 |
| 장당 호출로 총 시간 증가 | 병렬 2~3 + cover/agenda/closing LLM 미사용 + 재시도는 실패 장만. 체감상 V2 거대 JSON 1방(5~10분)과 유사하거나 빠름 |
| 사람 개입 단계가 번거로움 | [바로 생성] 단축 버튼 제공 (plan 검토 스킵). 단 기본 흐름은 검토 경유 |
| 템플릿 CSS 회귀 | 골든 3종의 장별 PNG를 스냅샷으로 보관, 육안 diff 절차를 릴리스 체크리스트에 포함 |
| Claude API 장애·키 부재 | 로컬 자동 fallback + UI 배지. 클라우드는 어디까지나 옵션 |

## 14. 부록 A — 패턴 12종 최종 슬롯 정의

```
cover:           company, title, subtitle, target, date_version          (LLM 미사용)
agenda:          title, items=[{ch, title, summary} 4~10]                (LLM 미사용, plan에서 유도)
section-divider: chapter_no, title, one_liner                            (LLM 미사용)
closing:         quote?, contact?                                        (LLM 미사용)
exec-summary:    title, subtitle, rows=[{label, statement} 3~6]          # WHY/WHAT/HOW형
metrics-row:     title, subtitle, metrics=[{value, label, note?} 3~6]
compare-2col:    title, subtitle, left_label, right_label,
                 left_items=[{title, detail} 3~6], right_items=[동일], footer_note?
card-grid-4:     title, subtitle, cards=[{title, subtitle, bullets? } 3~8], outro?
phase-roadmap:   title, subtitle, phases=[{label, title, period, tasks[2~6]} 3~6], footer_note?
dimension-5:     title, subtitle, dimensions=[{label, bullets[2~6]} 4~8], footer_note?
table:           title, subtitle, headers[2~5], rows[3~10], footer_note?
process-flow:    title, subtitle, steps=[{label, bullets[2~5]} 3~6], cycle_note?
stack:           title, subtitle, top_band?, layers=[{label, desc, right_note?} 2~5], bottom_band?
```
색은 슬롯에서 제거 — color_mode가 템플릿 레벨에서 결정 (모델이 색을 고르지 않는다).

## 14. 부록 B — slidegen 프롬프트 골격

```
당신은 슬라이드 1장을 채우는 작성기입니다. JSON만 출력.

## 이 슬라이드의 메시지 (부제로 사용됨)
{message}

## 채울 패턴과 슬롯
{pattern}: {slot_spec}

## 규칙
1. 아래 원문에 있는 내용만 사용. 새 사실·수치 창조 금지.
2. 제목류는 원문의 어구에서 추출 (번호 필러 "目标一/원칙1" 절대 금지).
3. detail은 완전한 문장 (15자 이상). 단어 나열 금지.
4. 수치는 원문 표기 그대로.
5. 원문 언어 유지.

## 원문 (참조 섹션 {section_ids})
{sections_md}

## 출력 (JSON만)
```
재시도 시: `## 이전 시도의 문제\n{validation_errors}` 블록을 규칙 아래 삽입.

---

## 부록 C — PPT 탭 UX 스펙 (확정 목업 기준 2026-07-03)

목업을 확정 스펙으로 고정. 4단계 위저드 = 입력 → 스토리라인 → 생성 → 결과.

### C.1 단계별 역할

| 단계 | 역할 | 사람 개입 |
|---|---|---|
| ① 입력 | 소스 확보 (3방식) + 메타 | 소스·메타 지정 |
| ② 스토리라인 | **LLM이 전체 흐름·페이지별 내용 자동 분류** | 표 검토·수정 (핵심 개입) |
| ③ 생성 | **디자인 선택** + 장당 슬라이드 생성 | 테마 선택 |
| ④ 결과 | 산출(PDF·PPTX) + 린트 | 다운로드·장별 재생성 |

### C.2 ① 입력 단계

- **메타**: 회사 `Semi-tech`(기본 고정) · 제목 `= md 파일명` · 모델(로컬 드롭다운) · 수량.
- **입력 방식 3종**:
  | 방식 | 내용 | 엔진 |
  |---|---|---|
  | 주제로 생성 | 간단한 주제 → LLM이 슬라이드용 md로 확장 | expander(storyboard 전) |
  | md 로딩 | 디스크·볼트 마크다운 선택 | 직접 |
  | 붙여넣기 | 많은 내용 직접 | 직접 |
- → 다음: 스토리라인 (LLM 자동 흐름·페이지 분류).

### C.3 ② 스토리라인 단계 (핵심 개입)

- LLM이 소스를 **슬라이드별 `{no·패턴·메시지·참조섹션·색}`으로 자동 분류** (DeckPlan §4.2).
- 표로 표시, **행 추가/삭제/순서변경·패턴/메시지 수정 가능** (st.data_editor).
- 패턴 뱃지 색 = color_mode. 하단 "패턴 6종·동일 40% 이하" 다양성 강제 표시.
- [이대로 생성] / [스토리라인 재생성]. 확정 plan은 `exports/*.plan.json` 저장(재현).

### C.4 ③ 생성 · ④ 결과

- 생성: 디자인(테마) 선택 → 장당 slidegen(§6) → 검증·재시도 → 린트.
- 결과: 썸네일 그리드 + 린트 리포트 + [PDF][PPTX] 다운로드 + 장별 [재생성].

### C.5 데이터 바인딩
```python
engine/output/
  expand_topic(topic, meta) -> md          # 주제→md (입력 ①)
  plan_storyboard(md, meta) -> DeckPlan     # LLM 자동 분류 (②)
  generate_slides(plan, theme) -> Deck      # 장당 생성 (③)
  render(deck) -> pdf/pptx                   # 결과 (④)
```
