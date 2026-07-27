"""V2.8.2 — Stage 1: LLM 자유 마크다운 확장기.

문제: V2.8.1.x까지의 디자인 엔진은 *단일-패스 슬롯 채우기*. LLM이 8개 패턴
박스에 정보를 끼워넣어야 해서 80b 모델 능력의 일부만 박힘. 결과 8장 빈약.

해결: 2단 파이프라인의 *1단*. LLM이 *JSON 강제 없이* 자유 마크다운으로 입력을
*풍부하게 재구조화*. 손실 없이 슬라이드 25~30장 분량으로 확장.

흐름:
  사용자 마크다운
    ↓ Stage 1: expand_for_slides() — 자유 마크다운, raw text 모드
  풍부한 구조화 마크다운 (~6~15k자)
    ↓ Stage 2: design_deck(pre_expanded=True) — JSON 슬롯 채우기
  Deck (25~30장)

호출 모델: 사용자가 UI에서 박은 모델 (deep 슬롯 또는 직접 선택).

출력 계약 (V2.8.3):
  <<<IRIS_SLIDES_START>>> ... <<<IRIS_SLIDES_END>>> 마커로 최종 답만 추출.
  thinking 원문은 generate_text가 버리고, 여기서도 사용자 오류에 넣지 않는다.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass

from src import llm

SLIDES_START = "<<<IRIS_SLIDES_START>>>"
SLIDES_END = "<<<IRIS_SLIDES_END>>>"

# 25~30장 Markdown + thinking 토큰을 수용. 모델 ctx를 초과하지 않도록 상한.
EXPAND_NUM_CTX = 32768
EXPAND_NUM_PREDICT = 16384
EXPAND_MAX_ATTEMPTS = 3


class ExpansionError(Exception):
    """확장 실패 — 메시지에 thinking/원문 응답을 넣지 말 것."""


class ExpansionValidationError(ExpansionError):
    """출력 계약 위반 (마커·누출·페이지수·잘림)."""


@dataclass
class ExpandedResult:
    md: str
    elapsed_ms: int
    model: str
    original_chars: int
    output_chars: int
    contract: dict | None = None


@dataclass
class RegeneratedContent:
    """재생성 패스(regenerate_chapters) 결과 — 형식 마커 없는 순수 챕터 콘텐츠."""
    md: str
    elapsed_ms: int
    model: str
    original_chars: int
    output_chars: int


_PROMPT = """당신은 컨설팅 회사의 PPT 작가입니다. 사용자가 박은 마크다운 보고서를
*컨설팅급 PPT 슬라이드용 마크다운*으로 재구조화하세요.

## ⚠️ 최우선 지시 — 사용자가 UI에서 직접 고른 값 (언어·챕터 수·모델)
아래 세 지시는 다른 모든 규칙·예시보다 우선한다. 특히 예시의 언어나 아래
'25~30장' 같은 표현이 이 지시와 충돌하면 *반드시 이 지시를 따른다*.

### 1) 출력 언어
{lang_directive}
추론 과정·설명·메타텍스트를 절대 출력하지 말고 마크다운 슬라이드 내용만 출력한다.

### 2) 챕터 구성 (이것은 "슬라이드 개수 맞추기"가 아니라 "재정리" 작업이다)
먼저 원문 전체를 정독한다. 그 다음 원문의 섹션 구분을 그대로 옮기지 말고,
**의미 단위로 재구성**해 아래 지시된 개수만큼의 챕터로 나눈다. 원문에 없던
내용을 지어내지 않되, 원문의 섹션 경계에 얽매이지 말고 주제가 같은 내용을
모아 하나의 챕터로 통합해도 된다(예: 서로 다른 부서에 흩어진 설비 관련
항목들을 "설비 관리"라는 하나의 챕터로 합치는 식).

**단, 입력이 이미 의미 단위로 잘 재구성된 챕터 형태(`## 제목`+`---`로 구분되고
내용이 이미 풍부한 경우)라면 재구성하지 말고 그 챕터 구성과 문장을 그대로
유지한다** — 이 경우 당신의 역할은 각 챕터에 형식(IRIS_BODY/PATTERN/ROLES)을
판단해 붙이는 것뿐이며, 본문 내용 자체를 다시 쓰지 않는다.
{count_directive}
목표 챕터 수: **{slide_target}**.

**원문의 어떤 섹션도 완전히 빠뜨리지 않는다** — 사소해 보이는 섹션이라도
반드시 어느 챕터에건 최소 한 줄 이상 반영되어야 한다. 다만 각 챕터 *안에서*
개별 항목을 얼마나 압축할지는 챕터별 IRIS_BODY 판단(아래 3b)에 따라
달라진다 — 이 압축 허용 여부는 챕터마다 다르다는 점을 명심할 것.

### 3) 모델
이 요청은 사용자가 고른 모델({model_name})로 처리된다. 모델 능력을 최대한 활용해
위 언어·챕터 구성 지시를 정확히 지켜라.

## 메타
회사명: {company}
보고서명: {title}
부제: {subtitle}
날짜: {date}

## 절대 규칙 (위반 금지)

1. {loss_rule}

2. **풍부함 의무**: 한 슬라이드에 *주장형 제목 + **핵심 메시지:** 한 문장 + 본문*.
   - cover 제외 모든 슬라이드에 `**핵심 메시지:**` 한 문장 필수
   - 한 문장만 박힌 슬라이드 금지
   - 단어 줄임 금지 (3-4단어 나열 X, *완전한 구절·문장형* O)
   - 항목 내용은 *완전한 구절·문장형*

3. **슬라이드 분리자**: 슬라이드마다 `---` 한 줄로 구분. 전체 {slide_target}으로 박음.
   표지(첫 슬라이드)를 포함해 센다.

3b. **형식 계약 마커 (필수, 기계 판독)**: 각 슬라이드 본문 *안*에 아래 주석 3종을
   **정확히 한 번씩** 넣는다. 자연어로 “카드형이 적절하다”고만 쓰면 인정하지 않는다.

   <!-- IRIS_BODY: <body-type> -->
   <!-- IRIS_PATTERN: <pattern-id> -->
   <!-- IRIS_ROLES: <role>,<role>,... -->

   ### 최상위 축 — IRIS_BODY (이 챕터의 내용을 *어떻게 쓸지*, 그리고
   *압축해도 되는지 아닌지*를 먼저 결정한다 — 이 판단은 챕터별로 다르다.

   허용 body-type (이 4종만): 요약형 | 도형형 | 표형 | 서술형

   **압축 허용 (개요·전체상 표현이 목적)**
   - **요약형**: 챕터 전체 내용을 핵심 불릿 3~8개로 압축한 개요. 세부 항목은
     통합·생략해도 된다. 문장 늘어놓기 금지, 짧은 구절로.
   - **도형형**: 병렬 항목·비교·절차·다차원 등을 시각 구조로 압축 표현.
     요약형과 마찬가지로 세부를 통합·구조화해도 된다.

   **압축 금지 (구체 내용을 원문 그대로 보존하는 것이 목적)**
   - **표형**: 구체적인 수치·데이터가 핵심인 내용(수치형). 항목을 요약하지
     말고 원문의 수치·행·열 대응을 *그대로* 표로 옮긴다. 표를 압축·생략하면
     안 된다.
   - **서술형**: 원문의 논리·배경·상세 설명을 문장으로 담는다. **이 챕터는
     압축 대상이 아니다** — 다른 챕터(요약형/도형형)에서 개요로 이미
     압축했더라도, 서술형 챕터에는 그 원문 내용을 *가능한 한 축약하지 않고*
     완전한 문장 단락(1~5개)으로 담는다. 불릿·표 금지.

   *모든 챕터를 한 형식으로 몰지 마라.* 개요가 필요한 챕터는 요약형/도형형,
   구체 수치를 보존해야 하는 챕터는 표형, 원문 상세를 보존해야 하는 챕터는
   서술형 — 내용 성격에 맞춰 4종을 고르게 섞는다.

   ### 하위 축 — IRIS_PATTERN (선택한 body-type 안에서 구체 레이아웃)
   허용 pattern-id (이 목록만):
   cover | narrative | summary | table | agenda | exec-summary | metrics-row |
   compare-2col | card-grid-4 | phase-roadmap | dimension-5

   ### body-type → pattern 매핑 (반드시 일치)
   - 요약형 → **summary**
   - 서술형 → **narrative**
   - 표형   → **table** (마크다운 표 유지, card-grid 금지)
   - 도형형 → agenda | exec-summary | metrics-row | compare-2col | card-grid-4 |
              phase-roadmap | dimension-5 중 내용에 맞는 하나
   - 표지(첫 장)는 body-type 면제 — pattern=cover, IRIS_BODY 생략 가능

   허용 role (해당되는 것만): context, items, relation, sequence, metrics,
   comparison, condition, exception, conclusion, source, output

3c. **수치 상한 및 분할**:
   - **표는 최대 6열.** 원본 표가 7열 이상이면 첫 열(키/구분 열)을 반복하고
     나머지 열을 나누어 2개 이상의 table 슬라이드로 만든다.
   - 항목 상한: card-grid-4 카드 ≤8, phase-roadmap 단계 ≤8,
     dimension-5 관점 ≤8, metrics-row 지표 ≤6, summary 불릿 ≤8, narrative 단락 ≤5.
     초과하면 여러 슬라이드로 나눈다.
   - 표가 너무 길면(행 8개 이상) 의미 단위로 여러 표 슬라이드로 나눠도 좋다.

   - 첫 슬라이드 pattern은 반드시 cover
   - cover는 첫 장에만
   - 도형형 안에서: 순서/절차→phase-roadmap, 두 축 대응→compare-2col/exec-summary,
     수치 핵심→metrics-row, 병렬 독립 항목(3~8)→card-grid-4, 다차원 분류→dimension-5
   - **병렬 독립 항목이 3개 이상이면 요약형 대신 도형형(card-grid-4)을 우선
     고려한다** — 모든 챕터를 요약형 나열로만 몰면 시각적으로 단조로운
     텍스트뿐인 덱이 된다. 요약형은 병렬 구조가 뚜렷하지 않은 개요에만 쓴다.
   - IRIS_ROLES에 condition/exception/conclusion/source가 있으면 그 문장을
     카드 항목으로 삭제하지 말고 슬라이드 하단(또는 상단 context)에 보존

4. **body-type·pattern·본문 구조 3자 일치** — IRIS_BODY, IRIS_PATTERN, 실제 본문이
   서로 맞아야 한다. 예: IRIS_BODY 서술형이면 pattern=narrative이고 본문은 문장 단락.

   - **서술형(narrative)** → 완전한 문장 단락 (context role). **압축 금지** —
     원문 상세를 축약하지 않고 담는다.
   - **요약형(summary)** → 짧은 불릿 3~8개. 압축 허용.
   - **표형(table)** → markdown 표 유지 (card-grid로 변환 금지). **압축 금지** —
     구체 수치·행을 요약해서 줄이지 않는다.
   - **도형형** → card-grid-4/phase-roadmap 등. 압축 허용(개요 표현). 공통 조건은
     roles에 condition 등으로 표시 후 카드 밖 문단으로 보존. 원문에 없는
     도입/결론을 꾸며내지 말 것.

5. **고유명사·코드 보존**: 표준 용어·코드·약어는 번역하지 말고 원문 표기 그대로.
   서술 문장·제목·설명은 위 '출력 언어' 지시를 따른다.

6. **frontmatter 박지 마** (호출자가 박음).

7. **출력 경계 (필수)**: 최종 답은 아래 마커로만 감싼다. 마커 밖 텍스트·추론·설명 금지.
   마커는 각각 정확히 한 번만 사용한다.
{SLIDES_START}
(슬라이드 마크다운만)
{SLIDES_END}

## 좋은 슬라이드 예시 (구조만 참고 — *실제 고객·전화·인증번호·프로젝트명 넣지 말 것*)

```markdown
<!-- IRIS_PATTERN: cover -->
<!-- IRIS_ROLES: context -->

# 보고서 제목
## 부제
> 날짜 · 버전

---

<!-- IRIS_BODY: 서술형 -->
<!-- IRIS_PATTERN: narrative -->
<!-- IRIS_ROLES: context -->

## 왜 지금 이 과제가 중요한가

**핵심 메시지:** 시장 변화가 기존 방식의 한계를 드러냈다.

최근 시장 환경은 기존 운영 방식의 구조적 한계를 드러내고 있다. 수요 변동성이
커지면서 단순 대응으로는 품질과 납기를 동시에 맞추기 어려워졌다.

따라서 본 과제는 근본 원인을 해소하는 체계적 접근을 목표로 한다.

---

<!-- IRIS_BODY: 도형형 -->
<!-- IRIS_PATTERN: phase-roadmap -->
<!-- IRIS_ROLES: sequence,items,output -->

## 실행 단계로 리스크를 줄인다

**핵심 메시지:** 4단계 절차로 범위·산출물을 고정한다.

1. 준비: 일정과 범위 확정
2. 분석: 현황 조사
3. 설계: 방안 확정
4. 이행: 적용과 점검

---

<!-- IRIS_BODY: 표형 -->
<!-- IRIS_PATTERN: table -->
<!-- IRIS_ROLES: relation,items -->

## 단계별 업무와 산출물

**핵심 메시지:** 행·열 대응으로 업무와 산출물을 함께 본다.

| 단계 | 코드 | 주요 업무 | 산출물 |
|---|---|---|---|
| 준비 | IM100 | 일정 수립 | WBS |
| 분석 | IM200 | 현황 조사 | 보고서 |

---

<!-- IRIS_BODY: 요약형 -->
<!-- IRIS_PATTERN: summary -->
<!-- IRIS_ROLES: items -->

## 핵심 요약

**핵심 메시지:** 세 가지만 기억하면 된다.

- 범위와 산출물을 4단계로 고정한다
- 행·열 대응 표로 업무를 한눈에 관리한다
- 공통 조건 아래 네 모듈을 독립 운영한다

---

<!-- IRIS_BODY: 도형형 -->
<!-- IRIS_PATTERN: card-grid-4 -->
<!-- IRIS_ROLES: context,items,condition -->

## 구성 요소를 병렬로 운영한다

**핵심 메시지:** 네 모듈이 공통 조건 아래에서 독립 동작한다.

공통 전제를 한 문장으로 적는다.

- 항목 A: 설명 A
- 항목 B: 설명 B
- 항목 C: 설명 C
- 항목 D: 설명 D

모든 항목에 공통인 조건·예외·결론이 있으면 아래에 문단으로 남긴다.
```

## 나쁜 예시 (절대 박지 마)

```markdown
## 단계 목록

- 준비
- 분석
- 설계
```

→ 빈약한 나열 + 형식 계약 마커 없음. 거부.

```markdown
<!-- IRIS_BODY: 표형 -->
<!-- IRIS_PATTERN: table -->

## 연도별 실적

| 구분 | 수치 |
|---|---|
| 요약 | 대체로 증가 추세 |
```

→ **표형인데 원본 수치를 "대체로 증가 추세"로 요약해버림. 거부.** 표형은
압축 금지 — 원문에 있는 연도별 실제 수치를 행마다 그대로 담아야 한다.

```markdown
<!-- IRIS_BODY: 서술형 -->
<!-- IRIS_PATTERN: narrative -->

## 배경

**핵심 메시지:** 여러 요인이 복합적으로 작용했다.

여러 요인이 복합적으로 작용해 현재 상황에 이르렀다.
```

→ **서술형인데 원문의 구체적 배경·근거를 한 문장으로 뭉개버림. 거부.**
서술형은 압축 금지 — 원문에 있던 배경·논리·인과관계를 축약하지 않고
완전한 문장 단락으로 담아야 한다.

## 사용자 입력 마크다운

{md_text}

## 출력
위 '출력 언어'·챕터 구성·형식 계약 지시를 지킨 슬라이드 마크다운만
{SLIDES_START} … {SLIDES_END} 사이에 넣는다. 다른 말 0.
"""


# ─── 재생성(regenerate) 패스 — 형식 마커 없이 순수 콘텐츠만 ────────────────
#
# 왜 별도 패스인가: 기존 단일 패스는 "내용을 풍부하게 쓰기"와 "형식 마커
# 정확히 붙이기"를 한 번에 요구해 콘텐츠 품질이 떨어졌다(같은 모델인데
# 형식 제약이 없으면 훨씬 풍부한 결과가 나오는 것을 실측으로 확인함).
# 이 패스는 오직 "원문을 읽고 챕터로만 재구성"하는 것이 유일한 임무이며,
# IRIS_BODY/PATTERN/ROLES 판단은 하지 않는다. 그 결과를 기존 _PROMPT(위)의
# 입력으로 넘기면, 그쪽은 이미 풍부한 콘텐츠에 형식만 판단해 붙이면 된다.

_REGEN_PROMPT = """당신은 숙련된 컨설턴트입니다. 아래 원문 전체를 정독하고,
전문적이고 통찰력 있는 보고서로 재작성하세요. **지금은 형식 규칙이나 슬라이드
패턴을 신경 쓰지 않습니다** — 오직 내용을 잘 쓰는 데만 집중합니다.

### 1) 출력 언어
{lang_directive}
추론 과정·설명·메타텍스트를 절대 출력하지 말고 재작성한 본문만 출력한다.

### 2) 챕터 구성
원문의 섹션 순서·경계를 그대로 베끼지 말고 **의미 단위로 재구성**해
{slide_target}로 나눈다. 같은 주제에 해당하는 내용이 원문에서 서로 다른
곳에 흩어져 있어도 하나의 챕터로 통합한다. **원문의 어떤 내용도 완전히
빠뜨리지 않는다** — 사소해 보이는 내용도 반드시 어느 챕터에건 반영한다.
원문에 중복된 섹션이 있으면(예: 같은 내용이 이름만 바뀌어 두 번 나옴)
하나로 합친다. 챕터 수를 늘리려고 내용을 억지로 쪼개지 말 것.

### 3) 풍부함 — 가장 중요한 지시
각 챕터를 최대한 상세하고 전문적으로 쓴다:
- 원문에 있는 수치·고유명사·조건·예외·인과관계를 삭제하거나 뭉개지 않는다.
- 단순 나열이 아니라, 왜 중요한지·서로 어떻게 연결되는지 맥락을 붙인다.
- 추상적 표현("체계를 구축한다")보다 원문에 있는 구체적 사례를 그대로 인용한다.
- 원문에 없는 사실을 지어내지 않는다.

## 메타
회사명: {company}
보고서명: {title}
부제: {subtitle}

## 절대 규칙
1. **챕터 분리자**: 챕터마다 `---` 한 줄로 구분. 표지(도입부, 제목/부제)도
   첫 챕터로 포함해 센다.
2. **형식 마커 금지**: `<!-- IRIS_BODY -->` 등 형식 계약 주석을 넣지 않는다.
   지금은 순수한 서술형 재작성만 한다.
3. **고유명사·코드 보존**: 표준 용어·코드·약어는 번역하지 말고 원문 표기 그대로.
4. **frontmatter 박지 마** (호출자가 박음).
5. **출력 경계 (필수)**: 최종 답은 아래 마커로만 감싼다. 마커 밖 텍스트 금지.
{SLIDES_START}
(챕터 마크다운만)
{SLIDES_END}

## 원문

{md_text}

## 출력
위 지시를 지킨 챕터 마크다운만 {SLIDES_START} … {SLIDES_END} 사이에 넣는다.
다른 말 0.
"""


def _resolve_pages(pages: "str | int | None") -> tuple[str, int | None]:
    """UI '페이지 수' 선택값 → (mode, n).

    - "자동 (LLM 판단)" / None / 숫자 없음 → ("auto", None)
    - "5장" / "10장" / 5 → ("fixed", 5)
    """
    if pages is None:
        return ("auto", None)
    if isinstance(pages, int):
        return ("fixed", pages) if pages > 0 else ("auto", None)
    s = str(pages)
    if "자동" in s:
        return ("auto", None)
    m = re.search(r"\d+", s)
    return ("fixed", int(m.group())) if m else ("auto", None)


def _build_directives(lang: str | None, pages: "str | int | None") -> dict:
    """언어·페이지 수 조합을 프롬프트용 명시 지시문으로 변환.

    이 함수가 룰엔진의 핵심: UI 선택(언어·페이지 수)이 프롬프트 안에서
    *모순 없는 단일 명령*이 되도록 조립한다.
    """
    lang_final = (lang or "").strip()
    if lang_final and lang_final != "입력과 동일한 언어":
        lang_directive = (
            f"출력의 **모든 제목·문장·표·불릿을 반드시 {lang_final}로 작성**한다. "
            f"원본이 다른 언어(중국어·영어 등)라도 {lang_final}로 **번역**해서 쓴다. "
            f"{lang_final} 이외의 언어로 된 서술 문장을 출력하지 말 것 "
            f"(고유명사·표준 용어·코드는 예외 — 규칙 5 참조)."
        )
    else:
        lang_directive = (
            "원본과 *동일한 언어* 그대로 작성한다. 번역하지 말 것."
        )

    mode, n = _resolve_pages(pages)
    if mode == "fixed":
        slide_target = f"정확히 {n}개 챕터 (±1까지만 허용, 표지 포함)"
        count_directive = (
            f"원문 전체를 정독한 뒤, 의미 단위로 재구성해 **정확히 {n}개 챕터**로 "
            f"나눈다(표지 포함, ±1까지만 허용). 이것은 슬라이드 개수를 억지로 맞추는 "
            f"작업이 아니라 *재정리* 작업이다 — 원문 섹션 순서·경계를 그대로 베끼지 "
            f"말고, 같은 주제의 내용을 모아 하나의 챕터로 통합해도 된다. "
            f"챕터 수를 늘리려고 내용을 억지로 쪼개지 말 것."
        )
        loss_rule = (
            "**챕터 배분 시 전량 반영, 챕터 내부 압축은 body-type별로 차등**: "
            "원문의 어떤 섹션도 완전히 빠뜨리지 말고 반드시 어느 챕터에건 반영한다. "
            "단, 요약형/도형형 챕터는 세부를 통합·압축해 개요로 표현해도 된다. "
            "표형·서술형 챕터는 압축 대상이 아니다 — 표형은 구체 수치를 표로 그대로, "
            "서술형은 원문의 논리·상세를 축약 없이 문장으로 담는다. "
            "수치·고유명사·핵심 표는 어떤 챕터에서도 왜곡하거나 지어내지 않는다."
        )
    else:
        slide_target = "25~30개 챕터"
        count_directive = (
            "원문 전체를 정독한 뒤, 정보 손실 없이 25~30개 챕터로 *의미 단위로 "
            "재구성*한다(슬라이드 개수 채우기가 아니라 재정리 작업). "
            "너무 많은 정보가 박힌 주제는 2~3개 챕터로 쪼개고, 서로 관련된 작은 "
            "섹션들은 하나의 챕터로 합친다."
        )
        loss_rule = (
            "**정보 손실 금지, 챕터 내부 압축은 body-type별로 차등**: 원본의 "
            "*모든 섹션·표·리스트·수치·항목*을 *빠짐없이* 어느 챕터에건 반영한다. "
            "요약형/도형형 챕터는 개요로 압축해도 되지만, 표형은 표를 *그대로* "
            "마크다운 표로 담고, 서술형은 원문 상세를 축약 없이 문장으로 담는다."
        )

    return {
        "lang_directive": lang_directive,
        "count_directive": count_directive,
        "slide_target": slide_target,
        "loss_rule": loss_rule,
    }


def _count_slides(md: str) -> int:
    """`---`로 구분된 슬라이드 수 (표지 포함). 빈 섹션은 제외."""
    parts = re.split(r"(?m)^---\s*$", md.strip())
    return sum(1 for p in parts if p.strip())


def _extract_slides_block(text: str) -> str:
    """START/END 마커 사이만 반환. 없거나 중복·순서 오류면 검증 실패.

    전체 response로 조용히 fallback하지 않는다.
    """
    starts = [m.start() for m in re.finditer(re.escape(SLIDES_START), text)]
    ends = [m.start() for m in re.finditer(re.escape(SLIDES_END), text)]
    if len(starts) != 1 or len(ends) != 1:
        raise ExpansionValidationError(
            "출력 경계 마커가 없거나 중복입니다. 확장을 다시 실행하세요."
        )
    if starts[0] >= ends[0]:
        raise ExpansionValidationError(
            "출력 경계 마커 순서가 잘못되었습니다. 확장을 다시 실행하세요."
        )
    before = text[:starts[0]].strip()
    after = text[ends[0] + len(SLIDES_END):].strip()
    if before or after:
        raise ExpansionValidationError(
            "출력 경계 마커 밖에 허용되지 않은 텍스트가 있습니다."
        )
    inner = text[starts[0] + len(SLIDES_START):ends[0]]
    return inner.strip()


def _strip_think(text: str) -> str:
    """명시적 <think>...</think>만 제거. 자연어 사고과정 휴리스틱 삭제 없음."""
    s = re.sub(r"<think>.*?(</think>|$)", "", text, flags=re.DOTALL | re.IGNORECASE)
    return s.strip()


def _strip_frontmatter(md: str) -> str:
    """앞쪽 `---\\n...\\n---\\n` 블록 제거. 단 슬라이드 구분자 `---/---`는 건드리지 마."""
    md = md.lstrip()
    if not md.startswith("---"):
        return md
    lines = md.split("\n")
    if not (lines and lines[0].strip() == "---"):
        return md
    if len(lines) > 1 and lines[1].strip() == "---":
        return md
    for i in range(1, min(len(lines), 20)):
        if lines[i].strip() == "---":
            return "\n".join(lines[i + 1:]).lstrip()
    return md


def _strip_code_fence(md: str) -> str:
    """LLM이 ```markdown ... ``` 로 감싸 응답한 경우 fence 제거."""
    s = md.strip()
    if s.startswith("```"):
        first_nl = s.find("\n")
        if first_nl > 0:
            s = s[first_nl + 1:]
        if s.endswith("```"):
            s = s[:-3].rstrip()
    return s


# 사고과정 누출 탐지 — 탐지 시 삭제하지 않고 검증 실패/재시도.
_LEAK_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"okay,\s*the\s+user",
        r"the\s+user\s+is\s+asking",
        r"let\s+me\s+(make|check|think|count|ensure|verify|see)",
        r"\bwait,",
        r"let'?s\s+count",
        r"\bi\s+need\s+to\b",
        r"\bi\s+should\b",
        r"<think>",
    )
]


def _has_reasoning_leak(md: str) -> bool:
    for pat in _LEAK_PATTERNS:
        if pat.search(md):
            return True
    return False


def _looks_like_english_reasoning(md: str, lang: str | None) -> bool:
    """한국어 요청인데 본문이 사실상 영어 추론문인 최소 탐지.

    고유명사·코드는 허용. 완벽 언어 판별이 아니라 명백한 실패만 잡는다.
    """
    if not lang or "한국" not in lang:
        return False
    sample = md[:2000]
    hangul = len(re.findall(r"[가-힣]", sample))
    latin_words = len(re.findall(r"\b[A-Za-z]{3,}\b", sample))
    if hangul < 20 and latin_words > 40:
        return True
    return False


def _validate_expanded(
    md: str,
    *,
    pages: "str | int | None",
    lang: str | None,
    contract_mode: str = "optional",
) -> None:
    from src.engine.output.deck.pattern_contract import (
        PatternContractError,
        has_pattern_contracts,
        validate_expansion_contracts,
    )

    if not md.strip():
        raise ExpansionValidationError("확장 결과가 비어 있습니다.")
    if SLIDES_START in md or SLIDES_END in md:
        raise ExpansionValidationError("결과에 경계 마커가 남아 있습니다.")
    if not re.search(r"(?m)^#{1,6}\s", md):
        raise ExpansionValidationError("Markdown 헤더가 없습니다.")
    if not re.search(r"(?m)^---\s*$", md):
        raise ExpansionValidationError("슬라이드 경계(---)가 없습니다.")
    if _has_reasoning_leak(md):
        raise ExpansionValidationError(
            "결과에 허용되지 않은 메타/추론 문구가 포함되어 있습니다."
        )
    if _looks_like_english_reasoning(md, lang):
        raise ExpansionValidationError(
            "요청 언어와 결과 언어가 일치하지 않습니다. 확장을 다시 실행하세요."
        )

    mode, n = _resolve_pages(pages)
    count = _count_slides(md)
    if mode == "fixed" and n is not None:
        if not (n - 1 <= count <= n + 1):
            raise ExpansionValidationError(
                f"페이지 수 불일치: 요청 {n}장(±1), 결과 {count}장."
            )
    elif mode == "auto":
        if count < 8:
            raise ExpansionValidationError(
                f"자동 모드 결과가 너무 짧습니다({count}장). 확장을 다시 실행하세요."
            )

    try:
        if contract_mode == "required":
            validate_expansion_contracts(
                md, require_roles=True, check_richness=True, require_body=True,
            )
        elif has_pattern_contracts(md):
            validate_expansion_contracts(
                md, require_roles=False, check_richness=False, require_body=False,
            )
    except PatternContractError as e:
        raise ExpansionValidationError(str(e)) from e


def _validate_regen(md: str, *, pages: "str | int | None", lang: str | None) -> None:
    """재생성 패스 결과 검증 — 형식 계약(IRIS_BODY 등)은 아직 없어야 한다."""
    if not md.strip():
        raise ExpansionValidationError("재생성 결과가 비어 있습니다.")
    if SLIDES_START in md or SLIDES_END in md:
        raise ExpansionValidationError("결과에 경계 마커가 남아 있습니다.")
    if not re.search(r"(?m)^#{1,6}\s", md):
        raise ExpansionValidationError("Markdown 헤더가 없습니다.")
    if not re.search(r"(?m)^---\s*$", md):
        raise ExpansionValidationError("챕터 경계(---)가 없습니다.")
    if re.search(r"<!--\s*IRIS_(BODY|PATTERN|ROLES)\s*:", md, re.IGNORECASE):
        raise ExpansionValidationError(
            "재생성 단계에서 형식 계약 마커가 출력되었습니다(이 단계는 순수 "
            "콘텐츠만 작성해야 합니다). 다시 시도하세요."
        )
    if _has_reasoning_leak(md):
        raise ExpansionValidationError(
            "결과에 허용되지 않은 메타/추론 문구가 포함되어 있습니다."
        )
    if _looks_like_english_reasoning(md, lang):
        raise ExpansionValidationError(
            "요청 언어와 결과 언어가 일치하지 않습니다. 재생성을 다시 실행하세요."
        )

    mode, n = _resolve_pages(pages)
    count = _count_slides(md)
    if mode == "fixed" and n is not None:
        if not (n - 1 <= count <= n + 1):
            raise ExpansionValidationError(
                f"챕터 수 불일치: 요청 {n}개(±1), 결과 {count}개."
            )
    elif mode == "auto":
        if count < 8:
            raise ExpansionValidationError(
                f"자동 모드 결과가 너무 짧습니다({count}개). 재생성을 다시 실행하세요."
            )


def _postprocess_response(raw: str) -> str:
    """response → strip think → 마커 추출 → fence/frontmatter."""
    out = _strip_think(raw)
    out = _extract_slides_block(out)
    out = _strip_frontmatter(out)
    out = _strip_code_fence(out)
    return out.strip()


def regenerate_chapters(
    md_text: str,
    meta: dict,
    *,
    timeout: float = 600.0,
    model: str | None = None,
    max_input_chars: int = 24000,
    lang: str | None = None,
    pages: "str | int | None" = None,
    num_ctx: int = EXPAND_NUM_CTX,
    num_predict: int = EXPAND_NUM_PREDICT,
) -> RegeneratedContent:
    """Stage 0 — 원문을 읽고 챕터로만 재구성(형식 마커 없음, 압축 없음).

    이 결과를 expand_for_slides()의 입력으로 넘기면, 그쪽은 이미 풍부한
    콘텐츠에 형식(IRIS_BODY/PATTERN/ROLES)만 판단해 붙이면 된다 — 콘텐츠
    합성과 형식 분류가 같은 호출 안에서 서로의 여력을 깎아먹지 않도록
    두 단계로 분리한 것이 이 함수의 존재 이유다.
    """
    original_chars = len(md_text)
    if not md_text.strip():
        raise ExpansionError("입력 마크다운 비어 있음")

    truncated = md_text[:max_input_chars]
    if len(md_text) > max_input_chars:
        truncated += f"\n\n[... 이하 {len(md_text) - max_input_chars:,}자 생략 ...]"

    effective_lang = lang or meta.get("lang")
    directives = _build_directives(effective_lang, pages)

    base_prompt = _REGEN_PROMPT.format(
        company=meta.get("company", ""),
        title=meta.get("title", ""),
        subtitle=meta.get("subtitle", ""),
        md_text=truncated,
        SLIDES_START=SLIDES_START,
        SLIDES_END=SLIDES_END,
        lang_directive=directives["lang_directive"],
        slide_target=directives["slide_target"],
    )

    last_err: Exception | None = None
    t0 = time.time()
    used_model = model or ""
    prompt = base_prompt

    for attempt in range(EXPAND_MAX_ATTEMPTS):
        resp = llm.generate_text(
            prompt,
            role="deep",
            model=model,
            timeout=timeout,
            temperature=0.6,  # 낮은 temperature는 압축·형식 준수엔 유리하지만
                              # 이 단계의 목표(풍부한 종합)엔 불리하다.
            num_ctx=num_ctx,
            num_predict=num_predict,
        )
        used_model = resp.get("model", model or "") or used_model

        if not resp.get("ok"):
            last_err = ExpansionError(f"LLM 실패: {resp.get('error', 'unknown')}")
            continue

        done_reason = (resp.get("done_reason") or "").lower()
        if done_reason == "length":
            last_err = ExpansionValidationError(
                "출력 길이 제한으로 재생성이 완료되지 않았습니다. "
                "챕터 수를 줄이거나 다시 시도하세요."
            )
            continue

        try:
            out = _postprocess_response(resp.get("text", ""))
            _validate_regen(out, pages=pages, lang=effective_lang)
        except ExpansionError as e:
            last_err = e
            prompt = (
                base_prompt
                + "\n\n## 이전 출력 검증 실패 — 수정 후 다시 출력하세요\n"
                + str(e)
                + "\n형식 마커는 넣지 말고, 챕터 구분(---)과 언어·챕터 수 "
                + "지시만 정확히 지켜 순수 콘텐츠로 다시 작성하세요.\n"
            )
            continue

        elapsed_ms = int((time.time() - t0) * 1000)
        return RegeneratedContent(
            md=out,
            elapsed_ms=elapsed_ms,
            model=used_model,
            original_chars=original_chars,
            output_chars=len(out),
        )

    elapsed_ms = int((time.time() - t0) * 1000)
    if last_err is not None:
        raise last_err
    raise ExpansionError("재생성 실패")


def expand_for_slides(
    md_text: str,
    meta: dict,
    *,
    timeout: float = 600.0,
    model: str | None = None,
    max_input_chars: int = 24000,
    lang: str | None = None,
    pages: "str | int | None" = None,
    num_ctx: int = EXPAND_NUM_CTX,
    num_predict: int = EXPAND_NUM_PREDICT,
    contract_mode: str = "optional",
) -> ExpandedResult:
    """LLM이 사용자 마크다운을 풍부한 슬라이드용 마크다운으로 확장."""
    original_chars = len(md_text)
    if not md_text.strip():
        raise ExpansionError("입력 마크다운 비어 있음")

    truncated = md_text[:max_input_chars]
    if len(md_text) > max_input_chars:
        truncated += f"\n\n[... 이하 {len(md_text) - max_input_chars:,}자 생략 ...]"

    effective_lang = lang or meta.get("lang")
    directives = _build_directives(effective_lang, pages)

    base_prompt = _PROMPT.format(
        company=meta.get("company", ""),
        title=meta.get("title", ""),
        subtitle=meta.get("subtitle", ""),
        date=meta.get("date", ""),
        model_name=model or "deep",
        md_text=truncated,
        SLIDES_START=SLIDES_START,
        SLIDES_END=SLIDES_END,
        **directives,
    )

    last_err: Exception | None = None
    t0 = time.time()
    used_model = model or ""
    prompt = base_prompt

    for attempt in range(EXPAND_MAX_ATTEMPTS):
        resp = llm.generate_text(
            prompt,
            role="deep",
            model=model,
            timeout=timeout,
            temperature=0.3,
            num_ctx=num_ctx,
            num_predict=num_predict,
        )
        used_model = resp.get("model", model or "") or used_model

        if not resp.get("ok"):
            last_err = ExpansionError(
                f"LLM 실패: {resp.get('error', 'unknown')}"
            )
            continue

        done_reason = (resp.get("done_reason") or "").lower()
        if done_reason == "length":
            last_err = ExpansionValidationError(
                "출력 길이 제한으로 확장이 완료되지 않았습니다. "
                "페이지 수를 줄이거나 다시 시도하세요."
            )
            continue

        try:
            out = _postprocess_response(resp.get("text", ""))
            _validate_expanded(
                out, pages=pages, lang=effective_lang, contract_mode=contract_mode,
            )
        except ExpansionError as e:
            last_err = e
            # 재시도 시 실패 이유만 추가 (특정 문서 텍스트 하드코딩 금지)
            prompt = (
                base_prompt
                + "\n\n## 이전 출력 검증 실패 — 수정 후 전체 계약을 다시 출력하세요\n"
                + str(e)
                + "\n선언된 형식을 수정하고 IRIS_BODY/IRIS_PATTERN/IRIS_ROLES 계약을 완성하세요.\n"
                + "cover 제외 모든 슬라이드에 IRIS_BODY(요약형/서술형/표형/도형형)와 "
                + "`**핵심 메시지:**` 한 문장을 넣으세요.\n"
                + "body-type→pattern 일치: 요약형=summary, 서술형=narrative, 표형=table, "
                + "도형형=card-grid-4/phase-roadmap 등.\n"
                + "표형·서술형 챕터는 압축 금지(원문 수치·상세를 그대로 보존), "
                + "요약형·도형형만 개요로 압축 가능합니다.\n"
            )
            continue

        elapsed_ms = int((time.time() - t0) * 1000)
        from src.engine.output.deck.pattern_contract import (
            contracts_to_api,
            has_pattern_contracts,
            parse_pattern_contracts,
        )
        contract_dict = None
        if contract_mode == "required" or has_pattern_contracts(out):
            contract_dict = contracts_to_api(parse_pattern_contracts(out))
        return ExpandedResult(
            md=out,
            elapsed_ms=elapsed_ms,
            model=used_model,
            original_chars=original_chars,
            output_chars=len(out),
            contract=contract_dict,
        )

    elapsed_ms = int((time.time() - t0) * 1000)
    if last_err is not None:
        raise last_err
    raise ExpansionError("확장 실패")


__all__ = [
    "ExpansionError",
    "ExpansionValidationError",
    "ExpandedResult",
    "RegeneratedContent",
    "expand_for_slides",
    "regenerate_chapters",
    "SLIDES_START",
    "SLIDES_END",
    "_extract_slides_block",
    "_strip_think",
    "_count_slides",
    "_validate_expanded",
    "_validate_regen",
    "_resolve_pages",
]
