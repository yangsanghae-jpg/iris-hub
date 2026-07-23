"""deck expander 출력 계약·검증 단위 테스트 (네트워크 없음)."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from src.engine.output.deck import expander
from src.engine.output.deck.expander import (
    SLIDES_END,
    SLIDES_START,
    ExpansionValidationError,
    _count_slides,
    _extract_slides_block,
    _strip_think,
    _validate_expanded,
    expand_for_slides,
)


def _wrap(inner: str) -> str:
    return f"{SLIDES_START}\n{inner}\n{SLIDES_END}"


def test_extract_slides_block_ok():
    inner = "## 제목\n\n---\n\n## 본문"
    assert _extract_slides_block(_wrap(inner)) == inner


def test_extract_missing_markers():
    with pytest.raises(ExpansionValidationError):
        _extract_slides_block("## only markdown")


def test_extract_end_before_start():
    bad = f"{SLIDES_END}\n## x\n{SLIDES_START}"
    with pytest.raises(ExpansionValidationError):
        _extract_slides_block(bad)


def test_extract_duplicate_start():
    bad = f"{SLIDES_START}\na\n{SLIDES_START}\nb\n{SLIDES_END}"
    with pytest.raises(ExpansionValidationError):
        _extract_slides_block(bad)


def test_extract_duplicate_end():
    bad = f"{SLIDES_START}\na\n{SLIDES_END}\n{SLIDES_END}"
    with pytest.raises(ExpansionValidationError):
        _extract_slides_block(bad)


def test_extract_rejects_text_outside_markers():
    bad = f"Okay, the user is asking...\n{_wrap('## 제목')}"
    with pytest.raises(ExpansionValidationError):
        _extract_slides_block(bad)


def test_strip_think_removes_closed_and_open():
    s = _strip_think("<think>secret</think>\n## 제목")
    assert "secret" not in s
    assert s.startswith("## 제목")
    s2 = _strip_think("<think>unclosed secret\n## 제목")
    assert "secret" not in s2


def test_strip_think_preserves_clean_markdown():
    md = "## 메타\n\n본문입니다.\n\n---\n\n## 다음"
    assert _strip_think(md) == md


def test_validate_detects_leak_even_after_header():
    md = "## 메타\n\nOkay, the user is asking for slides.\n\n---\n\n## 다음"
    with pytest.raises(ExpansionValidationError):
        _validate_expanded(md, pages="5장", lang="한국어")


def test_validate_passes_clean_korean():
    slides = []
    for i in range(5):
        slides.append(f"## 슬라이드 {i + 1}\n\n- 항목 하나\n- 항목 둘")
    md = "\n\n---\n\n".join(slides)
    _validate_expanded(md, pages="5장", lang="한국어")


def test_validate_page_count_out_of_range():
    md = "## A\n\n---\n\n## B\n\n---\n\n## C"
    with pytest.raises(ExpansionValidationError):
        _validate_expanded(md, pages="5장", lang="한국어")


def test_count_slides_includes_cover():
    md = "# 표지\n\n---\n\n## 본문1\n\n---\n\n## 본문2"
    assert _count_slides(md) == 3


def test_expand_rejects_length_done_reason():
    def fake_gen(*args, **kwargs):
        return {
            "ok": True,
            "text": _wrap("## A\n\n---\n\n## B\n\n---\n\n## C\n\n---\n\n## D\n\n---\n\n## E"),
            "model": "qwen3:30b",
            "done_reason": "length",
            "thinking_present": True,
        }

    with patch("src.llm.generate_text", side_effect=fake_gen):
        with pytest.raises(ExpansionValidationError, match="길이 제한"):
            expand_for_slides(
                "# src", {"lang": "한국어"}, model="qwen3:30b",
                lang="한국어", pages="5장",
            )


def test_expand_success_path_no_thinking_in_result():
    body = "\n\n---\n\n".join(
        f"## 제목 {i}\n\n- 내용" for i in range(1, 6)
    )
    calls = {"n": 0}

    def fake_gen(*args, **kwargs):
        calls["n"] += 1
        assert kwargs.get("num_ctx") == expander.EXPAND_NUM_CTX
        assert kwargs.get("num_predict") == expander.EXPAND_NUM_PREDICT
        return {
            "ok": True,
            "text": _wrap(body),
            "model": "qwen3:30b",
            "done_reason": "stop",
            "thinking_present": True,
        }

    with patch("src.llm.generate_text", side_effect=fake_gen):
        result = expand_for_slides(
            "# 원본", {"lang": "한국어", "company": "X"},
            model="qwen3:30b", lang="한국어", pages=5,
        )
    assert calls["n"] == 1
    assert "Okay" not in result.md
    assert result.md.startswith("## 제목 1")
    assert _count_slides(result.md) == 5


def test_expand_retries_then_succeeds_on_marker_fix():
    body = "\n\n---\n\n".join(
        f"## 제목 {i}\n\n- 내용" for i in range(1, 6)
    )
    seq = [
        {
            "ok": True,
            "text": "no markers here ## 제목",
            "model": "qwen3:30b",
            "done_reason": "stop",
        },
        {
            "ok": True,
            "text": _wrap(body),
            "model": "qwen3:30b",
            "done_reason": "stop",
        },
    ]

    with patch("src.llm.generate_text", side_effect=seq):
        result = expand_for_slides(
            "# 원본", {"lang": "한국어"}, model="qwen3:30b",
            lang="한국어", pages="5장",
        )
    assert _count_slides(result.md) == 5


def test_expand_does_not_fallback_to_full_response():
    """마커 실패 시 전체 response를 결과로 쓰지 않는다."""
    leak = "Okay, the user is asking...\n## 메타\n\n---\n\n## 다음"
    with patch(
        "src.llm.generate_text",
        return_value={
            "ok": True,
            "text": leak,
            "model": "qwen3:30b",
            "done_reason": "stop",
        },
    ):
        with pytest.raises(ExpansionValidationError):
            expand_for_slides(
                "# 원본", {"lang": "한국어"}, model="qwen3:30b",
                lang="한국어", pages="2장",
            )
