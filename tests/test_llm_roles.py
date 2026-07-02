"""LLM role 슬롯 회귀 (V2.5.4 부록).

Ollama 미가동에도 통과하도록 네트워크 호출 없는 단위만 검증.
"""
import os

import pytest


def _reload_modules():
    """env 변경 후 config + llm 재로드."""
    import importlib
    from src import config, llm
    importlib.reload(config)
    importlib.reload(llm)
    return config, llm


def test_default_models_match_m2_baseline(monkeypatch):
    """env 미설정 시 M2 기본값."""
    for k in ("IRIS_LLM_DEEP", "IRIS_LLM_FAST", "IRIS_LLM_EMBED", "IRIS_OLLAMA_URL"):
        monkeypatch.delenv(k, raising=False)
    config, llm = _reload_modules()
    assert config.IRIS_LLM_DEEP  == "qwen3:8b"
    assert config.IRIS_LLM_FAST  == "qwen3.5:4b"
    assert config.IRIS_LLM_EMBED == "bge-m3"
    assert config.OLLAMA_URL.startswith("http")
    assert llm.model_for("deep")  == "qwen3:8b"
    assert llm.model_for("fast")  == "qwen3.5:4b"
    assert llm.model_for("embed") == "bge-m3"


def test_env_override_for_m5(monkeypatch):
    """M5처럼 env override → llm.model_for가 새 모델 반환."""
    monkeypatch.setenv("IRIS_LLM_DEEP",  "qwen3.6:35b-a3b")
    monkeypatch.setenv("IRIS_LLM_FAST",  "gemma4:e4b")
    monkeypatch.setenv("IRIS_LLM_EMBED", "bge-m3")
    config, llm = _reload_modules()
    assert config.IRIS_LLM_DEEP == "qwen3.6:35b-a3b"
    assert llm.model_for("deep") == "qwen3.6:35b-a3b"
    assert llm.model_for("fast") == "gemma4:e4b"


def test_unknown_role_raises(monkeypatch):
    monkeypatch.delenv("IRIS_LLM_DEEP", raising=False)
    _, llm = _reload_modules()
    with pytest.raises(ValueError):
        llm.model_for("chat")


def test_k2_version_embeds_deep_model(monkeypatch):
    """K2_VERSION 문자열에 deep 모델명이 박혀야 추적 가능."""
    monkeypatch.setenv("IRIS_LLM_DEEP", "qwen3.6:35b-a3b")
    import importlib
    from src import config
    from src.engine.process import k2
    importlib.reload(config)
    importlib.reload(k2)
    assert "qwen3.6:35b-a3b" in k2.K2_VERSION
    assert k2.K2_VERSION.startswith("k2-")


def test_k2result_default_classifier_version_dynamic(monkeypatch):
    """K2Result()의 기본 classifier_version이 현재 deep 모델 반영."""
    monkeypatch.setenv("IRIS_LLM_DEEP", "qwen3:8b")
    import importlib
    from src import config
    from src.engine.process import k2
    importlib.reload(config)
    importlib.reload(k2)
    r = k2.K2Result()
    assert "qwen3:8b" in r.classifier_version
