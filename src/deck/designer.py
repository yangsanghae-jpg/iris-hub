"""V2.7.6 — LLM 슬라이드 설계기."""
from __future__ import annotations

from src import llm
from src.deck.schema import Deck, PATTERN_TEMPLATES, Slide


class DesignError(Exception):
    pass


PATTERN_SLOTS = {
    "cover": "company, title, subtitle, target, date_version",
    "agenda": "title, subtitle, items=[{ch, title, summary}, ...]",
    "exec-summary": "title, subtitle, left_label, right_label, left_items=[{title, detail}*5], right_items=[{title, detail}*5]",
    "metrics-row": "title, subtitle, metrics=[{value, label, color in [blue,orange,red,green]}*4]",
    "compare-2col": "title, subtitle, left_label, right_label, left_items=[str], right_items=[str], footer_note?",
    "card-grid-4": "title, subtitle, intro?={label, lines}, section_title, cards=[{title, subtitle, color}*4], outro?={label, bullets}",
    "phase-roadmap": "title, subtitle, phases=[{label, title, period, color, tasks=[str]}*4], footer_note?",
    "dimension-5": "title, subtitle, dimensions=[{label, color, bullets=[str]*3}*5], footer_note?",
}


def _build_prompt(md_text: str, meta: dict) -> str:
    patterns_doc = "\n".join(f"- {pid}: {slots}" for pid, slots in PATTERN_SLOTS.items())
    return f"""당신은 IRIS 슬라이드 디자이너입니다. 사용자가 박은 마크다운 내용을
*컨설팅급 PPT 슬라이드 사양*으로 변환합니다. JSON으로만 답하세요.

## 메타
회사명: {meta.get('company', '')}
보고서명: {meta.get('title', '')}
날짜: {meta.get('date', '')}

## 사용 가능 슬라이드 패턴 (이 8종만 사용)
{patterns_doc}

## 규칙
1. *반드시* 위 8 패턴 ID 중에서만 선택
2. 각 슬라이드는 *필수 슬롯*을 모두 채울 것
3. 첫 슬라이드는 보통 cover, 두 번째는 agenda 또는 exec-summary
4. 슬라이드 개수는 6~12장 권장
5. 색상은 진단·문제는 'red', 해결·혁신은 'green', 중립은 'blue', 강조는 'orange', 분기는 'purple' 으로 일관

## 사용자 입력 마크다운
{md_text[:4000]}

## 출력 (JSON만, 다른 말 절대 금지)
{{
  "slides": [
    {{"pattern": "cover", "data": {{...}}}},
    ...
  ]
}}
"""


def design_deck(md_text: str, meta: dict, *, timeout: float = 180.0) -> Deck:
    """LLM이 마크다운을 받아 슬라이드 사양 출력."""
    prompt = _build_prompt(md_text, meta)
    resp = llm.generate_json(prompt, role="deep", timeout=timeout)
    if not resp.get("ok"):
        raise DesignError(f"LLM 실패: {resp.get('error', 'unknown')}")

    data = resp.get("data", {})
    raw_slides = data.get("slides", [])

    slides: list[Slide] = []
    for sl in raw_slides:
        pid = sl.get("pattern")
        if pid not in PATTERN_TEMPLATES:
            continue
        sl_data = sl.get("data", {})
        if not isinstance(sl_data, dict):
            continue
        slides.append(Slide(pattern=pid, data=sl_data))

    if not slides:
        raise DesignError("LLM 응답에서 유효한 슬라이드 0개")

    return Deck(
        title=meta.get("title", "보고서"),
        subtitle=meta.get("subtitle", ""),
        company_name=meta.get("company", ""),
        date=meta.get("date", "2026.06"),
        slides=slides,
    )


__all__ = ["DesignError", "design_deck", "PATTERN_SLOTS"]
