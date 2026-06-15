"""Ollama API 래퍼 — qwen3:8b JSON 호출 (K2 분석용).

설계:
  - 외부 의존성 0 (urllib만)
  - 타임아웃 강제
  - format=json 지원 (qwen3:8b 검증됨)
  - 실패 시 명확한 에러 (raise X, dict로 반환)
"""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from typing import Any

OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen3:8b"
DEFAULT_TIMEOUT = 60.0  # K2 분석은 5-30초 기대, 60초 헤드룸


def generate_json(prompt: str, *,
                  model: str = DEFAULT_MODEL,
                  timeout: float = DEFAULT_TIMEOUT,
                  temperature: float = 0.1) -> dict[str, Any]:
    """Ollama /api/generate 호출, JSON 모드 강제.

    반환:
        성공: {"ok": True, "data": <parsed JSON>, "ms": <elapsed>, "raw": <text>}
        실패: {"ok": False, "error": <str>, "ms": <elapsed>}
    """
    body = json.dumps({
        "model": model,
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
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        return {"ok": False, "error": f"Ollama 연결 실패: {e}", "ms": 0}
    except json.JSONDecodeError as e:
        return {"ok": False, "error": f"Ollama 응답 파싱 실패: {e}", "ms": 0}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}", "ms": 0}

    ms = payload.get("total_duration", 0) // 1_000_000
    raw = payload.get("response", "")

    # qwen3:8b의 format=json 응답을 파싱
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return {
            "ok": False,
            "error": f"JSON 파싱 실패: {e}. raw={raw[:200]}",
            "ms": ms,
            "raw": raw,
        }

    return {"ok": True, "data": data, "ms": ms, "raw": raw}


def health() -> dict[str, Any]:
    """Ollama 가용성 + 모델 존재 확인. K2 호출 전 sanity."""
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=3) as resp:
            tags = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"ok": False, "error": f"Ollama down: {e}"}

    names = [m.get("name") for m in tags.get("models", [])]
    return {
        "ok": DEFAULT_MODEL in names,
        "model": DEFAULT_MODEL,
        "available_models": names,
        "error": None if DEFAULT_MODEL in names else f"{DEFAULT_MODEL} 미설치",
    }


__all__ = ["generate_json", "health", "DEFAULT_MODEL"]
