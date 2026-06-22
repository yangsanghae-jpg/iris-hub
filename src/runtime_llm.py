"""런타임 LLM 모델 선택 — Streamlit session + env (V2.8.0)."""
from __future__ import annotations

from src.config import IRIS_LLM_DEEP, IRIS_LLM_FAST, IRIS_LLM_EMBED


def _session_get(key: str) -> str | None:
    try:
        import streamlit as st
        val = st.session_state.get(key)
        if val:
            return str(val)
    except Exception:
        pass
    return None


def effective_deep_model() -> str:
    return _session_get("iris_llm_deep") or IRIS_LLM_DEEP


def effective_fast_model() -> str:
    return _session_get("iris_llm_fast") or IRIS_LLM_FAST


def effective_embed_model() -> str:
    return _session_get("iris_llm_embed") or IRIS_LLM_EMBED


def effective_presenton_ollama_model() -> str:
    return _session_get("presenton_ollama_model") or effective_deep_model()


__all__ = [
    "effective_deep_model",
    "effective_embed_model",
    "effective_fast_model",
    "effective_presenton_ollama_model",
]
