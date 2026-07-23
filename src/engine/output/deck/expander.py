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
EXPAND_MAX_ATTEMPTS = 2


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

2. **풍부함 의무**: 한 슬라이드에 *제목 + 본문 (리스트 5~10개 또는 표 또는 단락)*.
   - 한 문장만 박힌 슬라이드 금지
   - 단어 줄임 금지 (3-4단어 나열 X, *완전한 구절·문장형* O)
   - 항목 내용은 *완전한 구절·문장형*

3. **슬라이드 분리자**: 슬라이드마다 `---` 한 줄로 구분. 전체 {slide_target}으로 박음.
   표지(첫 슬라이드)를 포함해 센다.

4. **시각 패턴 힌트** (LLM이 Stage 2에서 패턴 결정할 수 있게):
   - 비교/대조 → 표로 박음 (markdown table)
   - 단계 로드맵 → 번호 매긴 리스트 + 기간
   - 차원·관점 → 헤더 + 불릿 그룹
   - 지표 → "**값** 라벨" 형태로 강조
   - As-Is vs To-Be → 두 컬럼 표

5. **고유명사·코드 보존**: IM100, CMMI, SSIM, WBS, FAT 같은 표준 용어·코드·약어는
   번역하지 말고 원문 표기 그대로 박는다. 단 *서술 문장·제목·설명*은 위 '출력 언어'
   지시를 따른다 (즉 용어만 원문, 문장은 지정 언어).

6. **frontmatter 박지 마** (호출자가 박음).

7. **출력 경계 (필수)**: 최종 답은 아래 마커로만 감싼다. 마커 밖 텍스트·추론·설명 금지.
   마커는 각각 정확히 한 번만 사용한다.
{SLIDES_START}
(슬라이드 마크다운만)
{SLIDES_END}

## 좋은 슬라이드 예시 (구조·풍부함의 참고용 — *언어는 무시*하고 위 '출력 언어' 지시를 따를 것)

```markdown
<!-- _class: cover -->

# 赛美特SSIM项目实施方法论
## 标准化·可复制·高可靠的产品交付体系
> 2026年6月 · CMMI V3.0 5级认证企业

---

## SSIM七大实施阶段 (1/2)

| 阶段 | 编码 | 里程碑会议 | 核心任务 |
|------|------|------------|----------|
| 投入与准备 | IM100 (CMT) | 项目启动会 | 制定详细项目日程; 项目整体启动落地; WBS+SOW |
| 业务分析 | IM200 (ANA) | 分析结果报告会 | 现场现状调研; 业务现状深度分析 |
| 蓝图设计 | IM300 (DES) | 蓝图报告会 | 初步方案讲解; 详细方案讲解; 确认定稿业务蓝图 |
| 功能开发 | IM400 (IMP) | 无独立节点 | 功能详细设计; 各功能开发与自测; 模块联动测试 |

---

## 故障响应时效标准

四级故障分级与处理时效，确保业务连续性：

- **1级故障 (重大火灾)**: 系统整体宕机，核心业务功能完全失效 → 响应≤30分钟, 解决≤2小时到场
- **2级故障 (严重影响)**: 系统卡顿、运行不稳定，部分功能数据异常 → 响应≤1小时, 解决≤4小时闭环
- **3级故障 (轻微影响)**: 系统小幅误差，非核心模块异常 → 响应≤2小时, 解决≤24小时方案
- **4级故障 (咨询类)**: 功能咨询、配置调试、安装疑问 → 响应≤1工作日, 协商处理周期
```

## 나쁜 예시 (절대 박지 마)

```markdown
## SSIM七大阶段

- 投入与准备
- 业务分析
- 蓝图设计
```

→ 위는 *3단어 나열*. 빈약함. 풍부히 박지 않음.

## 사용자 입력 마크다운

{md_text}

## 출력
위 '출력 언어'·페이지 수 지시를 지킨 슬라이드 마크다운만
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


def _validate_expanded(md: str, *, pages: "str | int | None", lang: str | None) -> None:
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
        # 자동 모드: 25~30 권장. 너무 적으면 실패(잘림/계약 위반 신호).
        if count < 8:
            raise ExpansionValidationError(
                f"자동 모드 결과가 너무 짧습니다({count}장). 확장을 다시 실행하세요."
            )


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
) -> ExpandedResult:
    """LLM이 사용자 마크다운을 풍부한 슬라이드용 마크다운으로 확장.

    인자:
      md_text: 사용자 원본 마크다운
      meta: 회사·제목 등 (프롬프트 박힘)
      timeout: 80b는 5~10분 가능 → 기본 10분
      model: 사용자가 UI에서 박은 모델 (None이면 deep)
      max_input_chars: 원본 입력 자르기 (기본 24k, 80b 컨텍스트 여유)
      lang: 출력 언어 지시 (예: "한국어"). None이면 "입력과 동일한 언어".
      pages: 목표 페이지 수 (예: "5장"/"10장"/"자동 (LLM 판단)"/5). None이면 자동.
      num_ctx / num_predict: 생성 예산 (thinking 토큰 포함)

    반환: ExpandedResult. length 종료·마커 실패·누출은 ExpansionError.
    """
    original_chars = len(md_text)
    if not md_text.strip():
        raise ExpansionError("입력 마크다운 비어 있음")

    truncated = md_text[:max_input_chars]
    if len(md_text) > max_input_chars:
        truncated += f"\n\n[... 이하 {len(md_text) - max_input_chars:,}자 생략 ...]"

    effective_lang = lang or meta.get("lang")
    directives = _build_directives(effective_lang, pages)

    prompt = _PROMPT.format(
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
            _validate_expanded(out, pages=pages, lang=effective_lang)
        except ExpansionError as e:
            last_err = e
            continue

        elapsed_ms = int((time.time() - t0) * 1000)
        return ExpandedResult(
            md=out,
            elapsed_ms=elapsed_ms,
            model=used_model,
            original_chars=original_chars,
            output_chars=len(out),
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
