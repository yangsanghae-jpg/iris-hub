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
*컨설팅급 PPT 25~30장 분량의 풍부한 슬라이드용 마크다운*으로 재구조화하세요.

## 출력 언어
반드시 모든 슬라이드를 {lang}로 작성한다. 추론 과정·설명·메타텍스트를 절대
출력하지 말고 마크다운 슬라이드 내용만 출력한다.

## 메타
회사명: {company}
보고서명: {title}
부제: {subtitle}
날짜: {date}

## ⚠️ 절대 규칙 (위반 금지)

1. **정보 손실 금지**: 원본의 *모든 섹션, 표, 리스트, 수치, 항목*을 *빠짐없이* 보존.
   - 원본에 7단계가 있으면 7단계 전부 박음
   - 원본에 27개 교부물이 있으면 27개 전부 박음
   - 원본에 SLA 4단계 (30분/1시간/2시간/1일)가 있으면 4개 시간 전부 박음
   - 표는 *그대로* 마크다운 표로 박음

2. **풍부함 의무**: 한 슬라이드에 *제목 + 본문 (리스트 5~10개 또는 표 또는 단락)*.
   - 한 문장만 박힌 슬라이드 금지
   - 단어 줄임 금지 ("WBS 制定" 같은 3-4단어 X, "制定WBS工作分解结构,定义详细任务" O)
   - 항목 내용은 *완전한 구절·문장형*

3. **슬라이드 분리자**: 슬라이드마다 `---` 한 줄로 구분. 25~30개 슬라이드 박음.
   - 너무 많은 정보가 박힌 섹션은 *2~3 슬라이��로 쪼갬*
   - 너무 적은 정보는 *가까운 섹션과 합침*

4. **시각 패턴 힌트** (LLM이 Stage 2에서 패턴 선택할 수 있게):
   - 비교/대조 → 표로 박음 (markdown table)
   - 단계 로드맵 → 번호 매긴 리스트 + 기간
   - 차원·관점 → 헤더 + 불릿 그룹
   - 지표 → "**값** 라벨" 형태로 강조
   - As-Is vs To-Be → 두 컬럼 표

5. **다국어 보존**: 입력이 중국어면 *중국어 그대로*, 영어면 영어 그대로.
   원본 용어 (IM100, CMMI, SSIM 등) *그대로* 박음.

6. **frontmatter 박지 마** (호출자가 박음). 다른 말 0, 마크다운만.

## 좋은 슬라이드 예시 (이 정도 풍부함)

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

## 출력 (Marp 마크다운만, 25~30 슬라이드, 다른 말 0)
/no_think
"""


def expand_for_slides(
    md_text: str,
    meta: dict,
    *,
    timeout: float = 600.0,
    model: str | None = None,
    max_input_chars: int = 24000,
    lang: str | None = None,
) -> ExpandedResult:
    """LLM이 사용자 마크다운을 풍부한 슬라이드용 마크다운으로 확장.

    인자:
      md_text: 사용자 원본 마크다운
      meta: 회사·제목 등 (프롬프트 박힘)
      timeout: 80b는 5~10분 가능 → 기본 10분
      model: 사용자가 UI에서 박은 모델 (None이면 deep)
      max_input_chars: 원본 입력 자르기 (기본 24k, 80b 컨텍스트 여유)
      lang: 출력 언어 지시 (예: "한국어"). None이면 "입력과 동일한 언어".

    반환: ExpandedResult
    """
    original_chars = len(md_text)
    if not md_text.strip():
        raise ExpansionError("입력 마크다운 비어 있음")

    truncated = md_text[:max_input_chars]
    if len(md_text) > max_input_chars:
        truncated += f"\n\n[... 이하 {len(md_text) - max_input_chars:,}자 생략 ...]"

    prompt = _PROMPT.format(
        lang=lang or meta.get("lang") or "입력과 동일한 언어",
        company=meta.get("company", ""),
        title=meta.get("title", ""),
        subtitle=meta.get("subtitle", ""),
        date=meta.get("date", ""),
        md_text=truncated,
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
