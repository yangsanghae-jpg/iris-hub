"""V2.7.5.2 — LLM 마크다운 재구조화 (Marp 입력 품질 보강).

문제: 사용자 마크다운이 *문서형* (`# 1. 목적`, `---`, `### 역할` 등)일 때 Marp가
그대로 변환하면 슬라이드당 한 문장만 박힌 60+장 짜리 빈약한 PPT가 나옴.

해결: Marp 호출 *전*에 LLM이 마크다운을 *프레젠테이션용*으로 재구조화:
  1. 의미적 단락 그룹핑
  2. 같은 주제는 한 슬라이드에 묶음
  3. 빈 슬라이드 제거
  4. 표·리스트로 압축
  5. `---` 슬라이드 분리자 적정 빈도로 박음
  6. cover/lead/card 클래스 적절히 적용

호출:
  M2: qwen3:8b (deep 슬롯)
  M5: qwen3:30b 또는 qwen3-next:80b (deep 슬롯, env IRIS_LLM_DEEP)

본문이 너무 길면 (>8000자) 앞부분만 사용 + 안내. 청크 분할은 V2.7.5.3에서.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass

from src import llm
from src.config import IRIS_LLM_DEEP


class RestructureError(Exception):
    pass


@dataclass
class RestructureResult:
    md: str
    slides_count: int
    elapsed_ms: int
    model: str
    original_chars: int
    output_chars: int


_PROMPT = """당신은 IRIS 프레젠테이션 디자이너입니다. 사용자가 박은 마크다운을
*컨설팅급 프레젠테이션*으로 재구조화해 Marp 마크다운으로 출력하세요.

## 규칙 (반드시 지킴)
1. **슬라이드 분리자는 `---` 한 줄만** — 빈도는 *내용 단위*로 (보통 5~12장)
2. **빈 슬라이드 금지** — 헤더만 있는 슬라이드 박지 마
3. **밀도 확보** — 한 슬라이드에 *제목 + 리스트(3~7개) 또는 표 또는 인용*
4. **의미적 그룹핑** — 같은 주제는 *한 슬라이드*에. 분산된 항목을 *통합*
5. **표 활용** — 비교·항목 나열은 마크다운 표 (가독성↑)
6. **첫 슬라이드는 표지** — `<!-- _class: cover -->` 박음
7. **소제목 슬라이드는 lead 클래스** — `<!-- _class: lead -->`로 큰 키워드 슬라이드
8. **frontmatter 박지 마** (호출자가 박음)
9. **다른 말 절대 금지** — 마크다운만 출력

## 좋은 슬라이드 예시

```markdown
<!-- _class: cover -->

# 회사명 / 프로젝트
## 부제 — 날짜

---

## 처리 흐름 (요약)

| 단계 | 입력 | 출력 |
|---|---|---|
| ① extract | 본문 | 키워드 |
| ② classify | 키워드 | 5축 분류 |
| ③ summarize | 분류 | 요약 + blurb |

> 각 단계 timestamp로 진척 추적

---

## 다음 단계

- V2.7.5 PPT 자동화 (현재)
- V2.7.6 OpenClaw 통합
- V2.8.x Presenton 통합

---

<!-- _class: lead -->

# 결론
## 마크다운만으로 충분
```

## 나쁜 예시 (절대 박지 마)

```markdown
# 1. 목적

---

본 문서는 다음을 정의한다.

---

# 2. 배경

---

LLM Wiki는 지식을 보유한다.

Claude는 추론을 수행한다.

---
```

→ 위는 슬라이드당 한 문장. 빈약함. 한 슬라이드로 합쳐서 박아야 함.

## 사용자 입력 마크다운

{md_text}

## 출력 (Marp 마크다운만, 다른 말 절대 금지)
/no_think
"""


def restructure_markdown(
    md_text: str,
    *,
    timeout: float = 300.0,
    max_input_chars: int = 8000,
) -> RestructureResult:
    """LLM이 마크다운을 Marp 프레젠테이션용으로 재구조화."""
    original_chars = len(md_text)
    if not md_text.strip():
        raise RestructureError("입력 마크다운 비어 있음")

    truncated = md_text[:max_input_chars]
    if len(md_text) > max_input_chars:
        truncated += f"\n\n[... 이하 {len(md_text) - max_input_chars:,}자 생략 ...]"

    prompt = _PROMPT.format(md_text=truncated)

    t0 = time.time()
    resp = llm.generate_text(prompt, role="deep", timeout=timeout, temperature=0.3)
    elapsed_ms = int((time.time() - t0) * 1000)

    if not resp.get("ok"):
        raise RestructureError(f"LLM 실패: {resp.get('error', 'unknown')}")

    out = resp.get("text", "")
    out = _strip_frontmatter(out)
    out = _strip_code_fence(out)

    slides_count = len(re.findall(r"^---\s*$", out, re.MULTILINE)) + 1

    return RestructureResult(
        md=out,
        slides_count=slides_count,
        elapsed_ms=elapsed_ms,
        model=resp.get("model", IRIS_LLM_DEEP),
        original_chars=original_chars,
        output_chars=len(out),
    )


def _strip_frontmatter(md: str) -> str:
    """앞쪽 `---\\n...\\n---\\n` 블록 제거. 단 *진짜 frontmatter*만 (3줄 이상)."""
    md = md.lstrip()
    if not md.startswith("---"):
        return md
    lines = md.split("\n")
    if not (lines and lines[0].strip() == "---"):
        return md
    # frontmatter는 보통 `key: value` 형태가 박힘. 첫 N줄 안에 두 번째 `---` 찾기.
    # 단 다음 줄이 바로 `---`면 그건 slide 구분자 — 건드리지 마.
    if len(lines) > 1 and lines[1].strip() == "---":
        return md  # `--- / ---` 패턴은 frontmatter가 아님
    for i in range(1, min(len(lines), 20)):
        if lines[i].strip() == "---":
            # i+1줄부터 본문
            return "\n".join(lines[i + 1 :]).lstrip()
    return md


def _strip_code_fence(md: str) -> str:
    """LLM이 ```markdown ... ``` 로 감싸 응답한 경우 fence 제거."""
    s = md.strip()
    if s.startswith("```"):
        # 첫 줄 (```markdown 또는 ```) 제거
        first_nl = s.find("\n")
        if first_nl > 0:
            s = s[first_nl + 1 :]
        if s.endswith("```"):
            s = s[:-3].rstrip()
    return s


__all__ = ["RestructureError", "RestructureResult", "restructure_markdown"]
