"""Ollama 설치 모델 목록 — UI 선택용."""
from __future__ import annotations

from src import llm
from src.config import IRIS_LLM_DEEP

_EMBED_HINTS = ("embed", "bge-", "nomic-embed", "mxbai-embed")


def list_installed_models(*, timeout: float = 3.0) -> list[str]:
    return llm.list_models(timeout=timeout)


def chat_capable_models(models: list[str] | None = None) -> list[str]:
    src = models if models is not None else list_installed_models()
    return [
        name for name in src
        if not any(h in name.lower() for h in _EMBED_HINTS)
    ]


def pick_default_chat_model(models: list[str] | None = None) -> str | None:
    chats = chat_capable_models(models)
    if not chats:
        return None
    if IRIS_LLM_DEEP in chats:
        return IRIS_LLM_DEEP
    norm = IRIS_LLM_DEEP if ":" in IRIS_LLM_DEEP else f"{IRIS_LLM_DEEP}:latest"
    for m in chats:
        if m == norm or m.split(":")[0] == IRIS_LLM_DEEP.split(":")[0]:
            return m
    return chats[0]


__all__ = ["chat_capable_models", "list_installed_models", "pick_default_chat_model"]
