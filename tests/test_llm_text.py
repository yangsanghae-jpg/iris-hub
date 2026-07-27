"""generate_text / thinking_mode_for_model 단위 테스트 (네트워크 없음)."""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from src import llm


def test_thinking_mode_qwen3_thinking():
    assert llm.thinking_mode_for_model("qwen3:30b") is True
    assert llm.thinking_mode_for_model("qwen3:8b") is True


def test_thinking_mode_qwen3_next_instruct():
    assert llm.thinking_mode_for_model("qwen3-next:80b-a3b-instruct-q4_K_M") is False


def test_thinking_mode_gpt_oss_levels():
    assert llm.thinking_mode_for_model("gpt-oss:20b") == "low"
    # boolean 금지 — 문자열만
    assert isinstance(llm.thinking_mode_for_model("gpt-oss:20b"), str)


def test_thinking_mode_non_reasoning():
    assert llm.thinking_mode_for_model("gemma4:e4b") is False
    assert llm.thinking_mode_for_model("qwen3.5:4b") is False
    assert llm.thinking_mode_for_model("unknown-model-xyz") is False


def test_resolve_available_model_prefers_installed_config():
    installed = ["qwen3:8b", "bge-m3:latest", "gemma4:e4b"]
    assert llm.resolve_available_model("qwen3:8b", installed=installed) == "qwen3:8b"


def test_resolve_available_model_fallback_skips_embed():
    installed = ["bge-m3:latest", "nomic-embed-text:latest", "qwen3:30b", "gemma4:e4b"]
    assert llm.resolve_available_model("qwen3:8b", installed=installed) == "qwen3:30b"


def test_resolve_available_model_none_when_only_embed():
    installed = ["bge-m3:latest", "nomic-embed-text:latest"]
    assert llm.resolve_available_model("qwen3:8b", installed=installed) is None


class _FakeResp:
    def __init__(self, payload: dict):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _patch_urlopen(payload: dict):
    return patch("urllib.request.urlopen", return_value=_FakeResp(payload))


def test_generate_text_keeps_response_drops_thinking_body():
    payload = {
        "response": "# Clean answer",
        "thinking": "private reasoning that must never leak",
        "done": True,
        "done_reason": "stop",
        "prompt_eval_count": 100,
        "eval_count": 200,
        "total_duration": 1_500_000_000,
    }
    with _patch_urlopen(payload):
        out = llm.generate_text("hi", model="qwen3:30b")
    assert out["ok"] is True
    assert out["text"] == "# Clean answer"
    assert out["thinking_present"] is True
    assert "thinking" not in out
    assert "private reasoning" not in json.dumps(out)
    assert out["done_reason"] == "stop"
    assert out["prompt_eval_count"] == 100
    assert out["eval_count"] == 200
    assert out["done"] is True


def test_generate_text_empty_response_fails():
    payload = {
        "response": "",
        "thinking": "only thinking",
        "done": True,
        "done_reason": "stop",
        "total_duration": 0,
    }
    with _patch_urlopen(payload):
        out = llm.generate_text("hi", model="qwen3:30b")
    assert out["ok"] is False
    assert "only thinking" not in json.dumps(out)
    assert out["thinking_present"] is True


def test_generate_text_sends_think_true_for_qwen3():
    captured = {}

    def fake_urlopen(req, timeout=None):
        captured["body"] = json.loads(req.data.decode("utf-8"))
        return _FakeResp({
            "response": "ok",
            "done": True,
            "done_reason": "stop",
            "total_duration": 0,
        })

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        llm.generate_text("p", model="qwen3:30b", num_ctx=32768, num_predict=16384)
    assert captured["body"]["think"] is True
    assert captured["body"]["options"]["num_ctx"] == 32768
    assert captured["body"]["options"]["num_predict"] == 16384


def test_generate_text_sends_think_low_for_gpt_oss():
    captured = {}

    def fake_urlopen(req, timeout=None):
        captured["body"] = json.loads(req.data.decode("utf-8"))
        return _FakeResp({
            "response": "ok",
            "done": True,
            "done_reason": "stop",
            "total_duration": 0,
        })

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        llm.generate_text("p", model="gpt-oss:20b")
    assert captured["body"]["think"] == "low"


def test_generate_json_still_forces_think_false():
    captured = {}

    def fake_urlopen(req, timeout=None):
        captured["body"] = json.loads(req.data.decode("utf-8"))
        return _FakeResp({
            "response": '{"a": 1}',
            "done": True,
            "total_duration": 0,
        })

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        out = llm.generate_json("p", model="qwen3:30b", num_ctx=4096)
    assert out["ok"] is True
    assert out["data"] == {"a": 1}
    assert captured["body"]["think"] is False
    assert captured["body"]["format"] == "json"


def test_generate_json_uses_low_string_for_gpt_oss():
    """회귀 방지: generate_json이 gpt-oss에 think:False(boolean)를 보내면
    Ollama가 thinking을 못 끄고 추론 전문을 response에 그대로 쏟아내
    JSON 파싱이 항상 실패하는 버그가 있었다(design_deck 전체 실패로 관측됨).
    gpt-oss는 반드시 문자열 레벨("low")을 받아야 한다."""
    captured = {}

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["body"] = json.loads(req.data.decode("utf-8"))
        return _FakeResp({
            "message": {"content": '{"a": 1}'},
            "done": True,
            "total_duration": 0,
        })

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        out = llm.generate_json("p", model="gpt-oss:20b", num_ctx=4096)
    assert out["ok"] is True
    assert out["data"] == {"a": 1}
    assert captured["body"]["think"] == "low"
    assert captured["body"]["think"] is not False


def test_generate_json_routes_gpt_oss_through_chat_endpoint():
    """회귀 방지: gpt-oss + /api/generate(raw completion) + format:json은
    think 값과 무관하게 실측상 항상 빈 응답(eval_count 미미, done_reason=stop)
    으로 멈춘다(harmony 챗 템플릿 미적용 추정). /api/chat으로 우회해야 한다."""
    captured = {}

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["body"] = json.loads(req.data.decode("utf-8"))
        return _FakeResp({
            "message": {"content": '{"a": 1}'},
            "done": True,
            "total_duration": 0,
        })

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        llm.generate_json("p", model="gpt-oss:20b", num_ctx=4096)
    assert captured["url"].endswith("/api/chat")
    assert "messages" in captured["body"]
    assert captured["body"]["messages"] == [{"role": "user", "content": "p"}]
    assert "prompt" not in captured["body"]
