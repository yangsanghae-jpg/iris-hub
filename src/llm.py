"""Ollama API 래퍼 — role-based 모델 분기 (V2.5.4 부록).

3슬롯:
  deep  — K2 본문 분석 (qwen3:8b / qwen3.6:35b-a3b)
  fast  — 분류 추천·UI 즉응 (qwen3.5:4b / gemma4:e4b)
  embed — 임베딩 (bge-m3, 양쪽 동일)

설계:
  - 외부 의존성 0 (urllib만)
  - 모델은 config.LLM_MODELS에서 role로 lookup
  - 호출자는 model 이름이 아니라 role을 지정 (deep/fast)
  - 타임아웃 강제 + 명확한 실패 dict
"""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from typing import Any

from .config import LLM_MODELS, OLLAMA_URL

DEFAULT_TIMEOUT = 60.0  # deep K2 분석 5-30초 기대, 60초 헤드룸
FAST_TIMEOUT = 15.0     # fast는 1-5초 기대


def model_for(role: str) -> str:
    """role → 실제 모델명. 'deep'|'fast'|'embed'."""
    try:
        return LLM_MODELS[role]
    except KeyError:
        raise ValueError(f"unknown LLM role: {role!r} (allowed: deep|fast|embed)")


def generate_json(prompt: str, *,
                  role: str = "deep",
                  model: str | None = None,
                  timeout: float | None = None,
                  temperature: float = 0.1) -> dict[str, Any]:
    """Ollama /api/generate 호출, JSON 모드 강제.

    role 또는 model 중 하나를 지정. role이 우선이며 model이 명시되면 override.

    반환:
        성공: {"ok": True, "data": <parsed JSON>, "ms": <elapsed>, "raw": <text>, "model": <name>}
        실패: {"ok": False, "error": <str>, "ms": <elapsed>, "model": <name>}
    """
    resolved_model = model or model_for(role)
    resolved_timeout = timeout if timeout is not None else (
        FAST_TIMEOUT if role == "fast" else DEFAULT_TIMEOUT
    )

    body = json.dumps({
        "model": resolved_model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": temperature},
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=resolved_timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        return {"ok": False, "error": f"Ollama 연결 실패: {e}", "ms": 0, "model": resolved_model}
    except json.JSONDecodeError as e:
        return {"ok": False, "error": f"Ollama 응답 파싱 실패: {e}", "ms": 0, "model": resolved_model}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}", "ms": 0, "model": resolved_model}

    ms = payload.get("total_duration", 0) // 1_000_000
    raw = payload.get("response", "")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return {
            "ok": False,
            "error": f"JSON 파싱 실패: {e}. raw={raw[:200]}",
            "ms": ms,
            "raw": raw,
            "model": resolved_model,
        }

    return {"ok": True, "data": data, "ms": ms, "raw": raw, "model": resolved_model}


def generate_text(prompt: str, *,
                  role: str = "deep",
                  model: str | None = None,
                  timeout: float | None = None,
                  temperature: float = 0.3) -> dict[str, Any]:
    """V2.7.5.2 — Ollama raw text 모드. JSON 강제 없음.

    PPT 재구조화처럼 *마크다운 그대로* 받아야 할 때 사용.

    반환:
        성공: {"ok": True, "text": <str>, "ms": <elapsed>, "model": <name>}
        실패: {"ok": False, "error": <str>, "ms": 0, "model": <name>}
    """
    resolved_model = model or model_for(role)
    resolved_timeout = timeout if timeout is not None else (
        FAST_TIMEOUT if role == "fast" else DEFAULT_TIMEOUT
    )

    body = json.dumps({
        "model": resolved_model,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "options": {"temperature": temperature},
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=resolved_timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        return {"ok": False, "error": f"Ollama 연결 실패: {e}", "ms": 0, "model": resolved_model}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}", "ms": 0, "model": resolved_model}

    ms = payload.get("total_duration", 0) // 1_000_000
    text = payload.get("response", "")
    return {"ok": True, "text": text, "ms": ms, "model": resolved_model}


def embed(text: str, *, model: str | None = None,
          timeout: float = 10.0) -> dict[str, Any]:
    """Ollama /api/embeddings 호출.

    반환:
        성공: {"ok": True, "embedding": [...], "dim": int, "model": <name>}
        실패: {"ok": False, "error": <str>, "model": <name>}
    """
    resolved_model = model or model_for("embed")
    body = json.dumps({"model": resolved_model, "prompt": text}).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/embeddings",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}", "model": resolved_model}

    vec = payload.get("embedding") or []
    if not vec:
        return {"ok": False, "error": f"empty embedding. raw={str(payload)[:200]}",
                "model": resolved_model}
    return {"ok": True, "embedding": vec, "dim": len(vec), "model": resolved_model}


def health(role: str = "deep") -> dict[str, Any]:
    """Ollama 가용성 + 해당 role 모델 존재 확인.

    `ollama list`는 태그 누락 시 ':latest'를 자동 부여하므로,
    비교 시에도 태그 없는 이름은 ':latest'로 정규화해 매칭.
    """
    target = model_for(role)
    target_norm = target if ":" in target else f"{target}:latest"
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=3) as resp:
            tags = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"ok": False, "error": f"Ollama down: {e}", "role": role, "model": target}

    names = [m.get("name") for m in tags.get("models", [])]
    found = target in names or target_norm in names
    return {
        "ok": found,
        "role": role,
        "model": target,
        "available_models": names,
        "error": None if found else f"{target} 미설치",
    }


def health_all() -> dict[str, dict[str, Any]]:
    """3슬롯 동시 점검 — UI 사이드바·진단용."""
    return {role: health(role) for role in ("deep", "fast", "embed")}


__all__ = ["generate_json", "embed", "health", "health_all", "model_for"]
