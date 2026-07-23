"""V2.8.2 — Stage 1: LLM 자유 마크다운 확장기.

문제: V2.8.1.x까지의 디자인 엔진은 *단일-패스 슬롯 채우기*. LLM이 8개 패턴
박스에 정보를 끼워넣어야 해서 80b 모델 능력의 일부만 박힘. 결과 8장 빈약.

해결: 2단 파이프라인의 *1단*. LLM이 *JSON 강제 없이* 자유 마크다운으로 입력을
*풍부하게 재구조화*. 손실 없이 슬라이드 25~30장 분량으로 확장.

흐름:
  사��자 마크다운
    ↓ Stage 1: expand_for_slides() — 자유 마크다운, raw text 모드
  풍부한 구조화 마크다운 (~6~15k자)
    ↓ Stage 2: design_deck(pre_expanded=True) — JSON 슬롯 채우기
  Deck (25~30장)

호출 모델: 사용자가 UI에서 박은 모델 (deep 슬롯 또는 직접 선택).
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from src import llm


class ExpansionError(Exception):
    pass


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

4. **시각 패턴 힌트** (LLM이 Stage 2에서 패턴 선택할 수 있게):
   - 비교/대조 → 표로 박음 (markdown table)
   - 단계 로드맵 → 번호 매긴 리스트 + 기간
   - 차원·관점 → 헤더 + 불릿 그룹
   - 지표 → "**값** 라벨" 형태로 강조
   - As-Is vs To-Be → 두 컬럼 표

5. **고유명사·코드 보존**: IM100, CMMI, SSIM, WBS, FAT 같은 표준 용어·코드·약어는
   번역하지 말고 원문 표기 그대로 박는다. 단 *서술 문장·제목·설명*은 위 '출력 언어'
   지시를 따른다 (즉 용어만 원문, 문장은 지정 언어).

6. **frontmatter 박지 마** (호출자가 박음). 다른 말 0, 마크다운만.

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

## 출력 (Marp 마크다운만, {slide_target}, 위 '출력 언어' 지시 준수, 다른 말 0)
/no_think
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
    import re
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


def expand_for_slides(
    md_text: str,
    meta: dict,
    *,
    timeout: float = 600.0,
    model: str | None = None,
    max_input_chars: int = 24000,
    lang: str | None = None,
    pages: "str | int | None" = None,
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

    UI에서 고른 (언어·페이지 수·모델) 조합은 _build_directives()에서 모순 없는
    단일 지시문으로 조립되어 프롬프트 최상단에 박힌다.

    반환: ExpandedResult
    """
    original_chars = len(md_text)
    if not md_text.strip():
        raise ExpansionError("입력 마크다운 비어 있음")

    truncated = md_text[:max_input_chars]
    if len(md_text) > max_input_chars:
        truncated += f"\n\n[... 이하 {len(md_text) - max_input_chars:,}자 생략 ...]"

    directives = _build_directives(lang or meta.get("lang"), pages)

    prompt = _PROMPT.format(
        company=meta.get("company", ""),
        title=meta.get("title", ""),
        subtitle=meta.get("subtitle", ""),
        date=meta.get("date", ""),
        model_name=model or "deep",
        md_text=truncated,
        **directives,
    )

    t0 = time.time()
    resp = llm.generate_text(
        prompt, role="deep", model=model,
        timeout=timeout, temperature=0.3,
    )
    elapsed_ms = int((time.time() - t0) * 1000)

    if not resp.get("ok"):
        raise ExpansionError(f"LLM 실패: {resp.get('error', 'unknown')}")

    out = resp.get("text", "")
    out = _strip_think(out)
    out = _strip_frontmatter(out)
    out = _strip_code_fence(out)

    if not out.strip():
        raise ExpansionError("LLM 응답 비어 있음 (think 토큰에 박혔거나 모델 문제)")

    return ExpandedResult(
        md=out,
        elapsed_ms=elapsed_ms,
        model=resp.get("model", model or ""),
        original_chars=original_chars,
        output_chars=len(out),
    )


def _strip_think(text: str) -> str:
    """추론 모델의 <think>...</think> 블록 및 그 이전 산문 프리앰블 제거.

    관측된 실제 증상: `/no_think` 지시에도 일부 모델이 "Wait, that's 30
    slides. Need to check if all content is covered..." 같은 영어 사고과정을
    마크다운 앞에 그대로 흘려보냄. 명시적 <think> 태그가 있으면 태그째 제거하고,
    없더라도 첫 마크다운 헤더/구분자(`#`, `##`, `---`) 이전에 산문이 섞여 있으면
    그 앞부분을 잘라낸다.
    """
    import re

    s = text
    # 1) 명시적 <think>...</think> 블록 제거 (닫는 태그 없이 끝나는 경우도 처리)
    s = re.sub(r"<think>.*?(</think>|$)", "", s, flags=re.DOTALL | re.IGNORECASE)
    s = s.strip()

    # 2) 첫 마크다운 헤더/구분자 이전의 산문 프리앰블 제거.
    #    이미 마크다운 헤더로 시작하면 손대지 않음.
    if s and not re.match(r"^(#{1,6}\s|---)", s):
        m = re.search(r"^(#{1,6}\s|---)", s, flags=re.MULTILINE)
        if m and m.start() > 0:
            s = s[m.start():]

    return s.strip()


def _strip_frontmatter(md: str) -> str:
    """앞쪽 `---\\n...\\n---\\n` 블록 제거. 단 슬라이드 구분자 `---/---`는 건드리지 마."""
    md = md.lstrip()
    if not md.startswith("---"):
        return md
    lines = md.split("\n")
    if not (lines and lines[0].strip() == "---"):
        return md
    # 다음 줄이 바로 `---`면 슬라이드 구분자 — 건드리지 마
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


__all__ = ["ExpansionError", "ExpandedResult", "expand_for_slides"]
