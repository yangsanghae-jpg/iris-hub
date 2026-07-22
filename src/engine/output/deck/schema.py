"""V2.7.6 — 슬라이드 JSON 스키마."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

PatternId = Literal[
    "cover", "agenda", "exec-summary", "metrics-row",
    "compare-2col", "card-grid-4", "phase-roadmap", "dimension-5",
]

PATTERN_TEMPLATES = {
    "cover": "cover.html.j2",
    "agenda": "agenda.html.j2",
    "exec-summary": "exec-summary.html.j2",
    "metrics-row": "metrics-row.html.j2",
    "compare-2col": "compare-2col.html.j2",
    "card-grid-4": "card-grid-4.html.j2",
    "phase-roadmap": "phase-roadmap.html.j2",
    "dimension-5": "dimension-5.html.j2",
}


@dataclass
class Slide:
    pattern: PatternId
    data: dict[str, Any]


@dataclass
class Deck:
    title: str
    subtitle: str
    company_name: str
    date: str
    slides: list[Slide] = field(default_factory=list)


def detect_deck_lang(deck: Deck) -> str:
    """덱 콘텐츠 언어 감지("ko"/"zh"/"en") — pptx/PDF 렌더러가 공유.

    한글 음절이 하나라도 있으면 ko (한자가 섞여도 한글이 압도적으로 함께
    나타나므로 ko 우선 판정), 없고 한자(CJK)만 있으면 zh, 그 외 en.
    """
    text = deck.title + deck.company_name + " ".join(
        str(v) for sl in deck.slides for v in sl.data.values() if isinstance(v, str)
    )[:2000]
    if any("가" <= ch <= "힣" for ch in text):
        return "ko"
    if any("一" <= ch <= "鿿" for ch in text):
        return "zh"
    return "en"


__all__ = ["Slide", "Deck", "PatternId", "PATTERN_TEMPLATES", "detect_deck_lang"]
