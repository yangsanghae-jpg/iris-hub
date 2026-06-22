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
    # 입력 길이 기반 슬라이드 수 가이드 (1k당 ~1장, 최소 8, 최대 16)
    target_min = max(8, min(16, len(md_text) // 1500))
    target_max = min(20, target_min + 4)
    return f"""당신은 IRIS 슬라이드 디자이너입니다. 사용자가 박은 마크다운 *전체 내용*을
*컨설팅급 PPT 슬라이드 사양*으로 변환합니다. JSON으로만 답하세요.

## 메타
회사명: {meta.get('company', '')}
보고서명: {meta.get('title', '')}
부제: {meta.get('subtitle', '')}
날짜: {meta.get('date', '')}

## 사용 가능 슬라이드 패턴 (이 8종만 사용)
{patterns_doc}

## ⚠️ 절대 규칙 (위반 금지)
1. **슬라이드 개수**: 반드시 {target_min}~{target_max}장. 입력 마크다운의 *모든 섹션을 빠짐없이* 슬라이드로 전개.
2. cover 1장 + agenda 1장 + 본문 {target_min - 2}~{target_max - 2}장 (각 섹션·소절 1~2장씩)
3. 마크다운의 ## / ### 헤더 1개당 *최소 1장*의 본문 슬라이드 박을 것
4. *반드시* 위 8 패턴 ID 중에서만 선택
5. 각 슬라이드는 *필수 슬롯*을 모두 채울 것 (생략 금지, 빈 문자열도 금지)
6. 색상 일관: 진단·문제 'red', 해결·혁신 'green', 중립 'blue', 강조 'orange', 분기 'purple'

## 슬라이드 전개 전략
- cover: 1장
- agenda: 1장 (전체 목차)
- exec-summary: 1장 (As-Is vs To-Be 또는 현황 vs 혁신)
- 본문 섹션마다 적절한 패턴 선택:
  · 비교/대조 → compare-2col
  · 4구역·4단계 → card-grid-4
  · 시간·단계 로드맵 → phase-roadmap
  · 5관점·5차원 → dimension-5
  · 지표 4개 → metrics-row

## 사용자 입력 마크다운
{md_text[:16000]}

## 출력 (JSON만, 다른 말 절대 금지, 슬라이드 {target_min}장 이상)
{{
  "slides": [
    {{"pattern": "cover", "data": {{"company": "...", "title": "...", "subtitle": "...", "target": "...", "date_version": "..."}}}},
    {{"pattern": "agenda", "data": {{"title": "...", "subtitle": "...", "items": [...]}}}},
    ...
  ]
}}
"""


def design_deck(md_text: str, meta: dict, *, timeout: float = 300.0) -> Deck:
    """LLM이 마크다운을 받아 슬라이드 사양 출력."""
    prompt = _build_prompt(md_text, meta)
    # V2.7.6.2 — 큰 입력은 응답도 큼. num_ctx 확장 + num_predict 충분히
    resp = llm.generate_json(
        prompt, role="deep", timeout=timeout,
        num_ctx=16384, num_predict=8192,
    )
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
