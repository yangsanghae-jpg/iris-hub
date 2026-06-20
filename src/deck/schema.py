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


__all__ = ["Slide", "Deck", "PatternId", "PATTERN_TEMPLATES"]
