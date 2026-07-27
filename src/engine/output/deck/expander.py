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


_PROMPT = """당신은 컨설팅 회사의 PPT 작가입니다. 사용자가 박은 마크다운 보고서를
*컨설팅급 PPT 슬라이드용 마크다운*으로 재구조화하세요.

## ⚠️ 최우선 지시 — 사용자가 UI에서 직접 고른 값 (언어·페이지 수·모델)
아래 세 지시는 다른 모든 규칙·예시보다 우선한다. 특히 예시의 언어나 아래
'25~30장' 같은 표현이 이 지시와 충돌하면 *반드시 이 지시를 따른다*.

### 1) 출력 언어
{lang_directive}
추론 과정·설명·메타텍스트를 절대 출력하지 말고 마크다운 슬라이드 내용만 출력한다.

### 2) 페이지 수
{count_directive}
목표 분량: **{slide_target}**.

### 3) 모델
이 요청은 사용자가 고른 모델({model_name})로 처리된다. 모델 능력을 최대한 활용해
위 언어·페이지 수 지시를 정확히 지켜라.

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

   ### 최상위 축 — IRIS_BODY (이 페이지의 내용을 *어떻게 쓸지* 먼저 결정)
   허용 body-type (이 4종만): 요약형 | 서술형 | 표형 | 도형형
   - **요약형**: 핵심을 짧은 불릿 3~8개로 압축. 문장 늘어놓기 금지.
   - **서술형**: 근거·배경·논리를 완전한 문장 단락(1~5개)으로 서술. 불릿·표 금지.
   - **표형**: 행·열 대응이 핵심. 마크다운 표를 그대로 유지.
   - **도형형**: 병렬 항목·비교·절차·수치·다차원 등 시각 구조로 표현.
   *모든 슬라이드를 한 형식으로 몰지 마라.* 내용 성격에 맞춰 4종을 고르게 섞는다.

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

   - 첫 슬라이드 pattern은 반드시 cover
   - cover는 첫 장에만
   - 도형형 안에서: 순서/절차→phase-roadmap, 두 축 대응→compare-2col/exec-summary,
     수치 핵심→metrics-row, 병렬 독립 항목(3~8)→card-grid-4, 다차원 분류→dimension-5
   - IRIS_ROLES에 condition/exception/conclusion/source가 있으면 그 문장을
     카드 항목으로 삭제하지 말고 슬라이드 하단(또는 상단 context)에 보존

4. **body-type·pattern·본문 구조 3자 일치** — IRIS_BODY, IRIS_PATTERN, 실제 본문이
   서로 맞아야 한다. 예: IRIS_BODY 서술형이면 pattern=narrative이고 본문은 문장 단락.

   - **서술형(narrative)** → 완전한 문장 단락 (context role)
   - **요약형(summary)** → 짧은 불릿 3~8개
   - **표형(table)** → markdown 표 유지 (card-grid로 변환 금지)
   - **도형형** → card-grid-4/phase-roadmap 등. 공통 조건은 roles에 condition 등으로
     표시 후 카드 밖 문단으로 보존. 원문에 없는 도입/결론을 꾸며내지 말 것.

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

## 사용자 입력 마크다운

{md_text}

## 출력
위 '출력 언어'·페이지 수·형식 계약 지시를 지킨 슬라이드 마크다운만
{SLIDES_START} … {SLIDES_END} 사이에 넣는다. 다른 말 0.
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
        slide_target = f"정확히 {n}장 (±1장까지만 허용, 표지 포함)"
        count_directive = (
            f"반드시 **정확히 {n}장**의 슬라이드로 재구성한다(표지 포함, ±1장까지만 허용). "
            f"원본이 {n}장보다 많은 내용을 담고 있으면 *핵심만 남기고 요약·압축·통합*해 "
            f"{n}장에 맞춘다. 장수를 늘리려고 내용을 억지로 쪼개지 말 것."
        )
        loss_rule = (
            "**핵심 우선·요약 허용**: 지정된 장수에 맞추기 위해 덜 중요한 세부는 "
            "통합·요약한다. 단 수치·고유명사·핵심 표는 왜곡하거나 지어내지 않는다."
        )
    else:
        slide_target = "25~30장"
        count_directive = (
            "정보 손실 없이 25~30장 분량으로 *풍부하게 확장*한다. "
            "너무 많은 정보가 박힌 섹션은 2~3장으로 쪼개고, 너무 적은 섹션은 합친다."
        )
        loss_rule = (
            "**정보 손실 금지**: 원본의 *모든 섹션·표·리스트·수치·항목*을 "
            "*빠짐없이* 보존한다. 표는 *그대로* 마크다운 표로 박는다."
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


def _postprocess_response(raw: str) -> str:
    """response → strip think → 마커 추출 → fence/frontmatter."""
    out = _strip_think(raw)
    out = _extract_slides_block(out)
    out = _strip_frontmatter(out)
    out = _strip_code_fence(out)
    return out.strip()


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
    "expand_for_slides",
    "SLIDES_START",
    "SLIDES_END",
    "_extract_slides_block",
    "_strip_think",
    "_count_slides",
    "_validate_expanded",
    "_resolve_pages",
]
