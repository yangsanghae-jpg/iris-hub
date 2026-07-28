"""designer.rewrite_slides — 형식 변경·밀도 교정 단위 테스트."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from src.engine.output.deck import designer
from src.engine.output.deck.schema import Deck, Slide


def _deck():
    return Deck(
        title="t", subtitle="s", company_name="c", date="d",
        slides=[
            Slide(pattern="cover", data={"title": "표지", "company": "c"}),
            Slide(
                pattern="summary",
                data={
                    "title": "전략",
                    "key_message": "핵심",
                    "points": ["a", "b", "c"],
                },
            ),
        ],
    )


def test_coerce_rewrite_payload_flat_slots():
    out = designer._coerce_rewrite_payload(
        {"title": "t", "points": ["a", "b", "c"], "key_message": "k"},
        "summary",
    )
    assert out["pattern"] == "summary"
    assert out["data"]["title"] == "t"


def test_coerce_rewrite_payload_nested_data():
    out = designer._coerce_rewrite_payload(
        {"data": {"title": "t", "paragraphs": ["p1"]}},
        "narrative",
    )
    assert out["pattern"] == "narrative"
    assert "paragraphs" in out["data"]


def test_coerce_rewrite_payload_slides_wrapper():
    out = designer._coerce_rewrite_payload(
        {
            "slides": [
                {
                    "pattern": "narrative",
                    "data": {"title": "t", "paragraphs": ["p1"]},
                }
            ]
        },
        "narrative",
    )
    assert out["pattern"] == "narrative"
    assert out["data"]["paragraphs"] == ["p1"]


def test_rewrite_slides_accepts_flat_llm_slots():
    """LLM이 pattern 래핑 없이 슬롯만 줘도 coerce 후 성공."""
    flat = {
        "title": "전략",
        "key_message": "핵심",
        "points": ["짧은1", "짧은2", "짧은3"],
    }
    with patch.object(designer, "_call_design_llm", return_value=flat):
        out = designer.rewrite_slides(
            _deck(), [1],
            md_text="## 전략\n\n긴 본문",
            meta={},
            density_action="condense",
        )
    assert out.slides[1].pattern == "summary"
    assert out.slides[1].data["points"] == ["짧은1", "짧은2", "짧은3"]


def test_rewrite_slides_changes_pattern_to_table():
    fake = {
        "pattern": "table",
        "data": {
            "title": "전략",
            "columns": [{"key": "k", "label": "항목"}, {"key": "v", "label": "값"}],
            "rows": [{"k": "a", "v": "1"}, {"k": "b", "v": "2"}],
        },
    }
    with patch.object(designer, "_call_design_llm", return_value=fake):
        out = designer.rewrite_slides(
            _deck(), [1],
            md_text="## 전략\n\n내용",
            meta={},
            body_type="표형",
        )
    assert out.slides[1].pattern == "table"
    assert out.slides[0].pattern == "cover"


def test_rewrite_slides_rejects_cover():
    with pytest.raises(designer.DesignError, match="표지"):
        designer.rewrite_slides(
            _deck(), [0],
            md_text="x",
            meta={},
            body_type="서술형",
        )


def test_rewrite_slides_shape_pattern():
    fake = {
        "pattern": "card-grid-4",
        "data": {
            "title": "전략",
            "section_title": "항목",
            "cards": [
                {"title": "A", "subtitle": "1", "color": "blue"},
                {"title": "B", "subtitle": "2", "color": "green"},
                {"title": "C", "subtitle": "3", "color": "orange"},
            ],
        },
    }
    with patch.object(designer, "_call_design_llm", return_value=fake) as mock:
        out = designer.rewrite_slides(
            _deck(), [1],
            md_text="## 전략",
            meta={},
            body_type="도형형",
            new_pattern="card-grid-4",
            rework_mode="format",
        )
    assert out.slides[1].pattern == "card-grid-4"
    prompt = mock.call_args[0][0]
    assert "형식 변환" in prompt
    assert "card-grid-4" in prompt


def test_rewrite_slides_density_keeps_pattern():
    flat = {
        "title": "전략",
        "key_message": "핵심",
        "points": ["a", "b", "c", "d"],
    }
    with patch.object(designer, "_call_design_llm", return_value=flat) as mock:
        out = designer.rewrite_slides(
            _deck(), [1],
            md_text="## 전략",
            meta={},
            density_action="expand",
            rework_mode="density",
        )
    assert out.slides[1].pattern == "summary"
    prompt = mock.call_args[0][0]
    assert "내용 추가" in prompt
    assert "형식 변환" not in prompt


def test_rewrite_slides_issues_keeps_pattern():
    flat = {
        "title": "전략",
        "key_message": "핵심",
        "points": ["a", "b", "c"],
    }
    with patch.object(designer, "_call_design_llm", return_value=flat) as mock:
        out = designer.rewrite_slides(
            _deck(), [1],
            md_text="## 전략",
            meta={},
            rework_mode="issues",
            issue_types=["language"],
            other_note="번역체 제거",
        )
    assert out.slides[1].pattern == "summary"
    prompt = mock.call_args[0][0]
    assert "문제 교정" in prompt
    assert "번역체 제거" in prompt
