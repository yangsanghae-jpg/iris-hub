"""Claude(Anthropic) API 래퍼 — src.llm과 동일한 반환 스키마.

배경:
  PPT 탭 ②확장/③설계 단계에서 로컬 Ollama 모델(gemma4:e4b 등)을 실사용
  테스트했더니 사고과정(<think>) 누출, 언어 지시 무시 등으로 품질이 사용
  불가 수준이었다. 로컬 모델 재평가는 나중으로 미루고, 이 두 단계만
  Claude API로 임시 전환한다 (K2 분석·분류·임베딩 등 다른 모든 기능은
  여전히 src.llm/Ollama를 그대로 쓴다 — 이 파일은 그 전역 교체가 아니다).

설계:
  - src.llm.generate_text/generate_json과 동일한 인자 이름·반환 dict 키를
    맞춰서, expander.py/designer.py의 호출부를 거의 그대로 재사용한다.
  - 외부 의존성 0 (urllib만) — src.llm의 zero-dep 원칙을 그대로 따른다.
  - role 인자는 받되 무시한다 (Claude는 role 기반 모델 분기가 없음 —
    호출자가 model을 명시적으로 넘긴다).
"""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from typing import Any

from .config import ANTHROPIC_API_KEY, ANTHROPIC_MODELS, IRIS_PPTX_MODEL

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"
DEFAULT_TIMEOUT = 120.0
DEFAULT_MAX_TOKENS = 8192


def _call(prompt: str, *, model: str, timeout: float, temperature: float,
          max_tokens: int) -> dict[str, Any]:
    if not ANTHROPIC_API_KEY:
        return {"ok": False, "error": "ANTHROPIC_API_KEY 미설정 — 서비스 환경변수를 확인하세요.",
                "ms": 0, "model": model}

    body = json.dumps({
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": API_VERSION,
        },
        method="POST",
    )

    import time
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:300]
        return {"ok": False, "error": f"Claude API {e.code}: {detail}", "ms": 0, "model": model}
    except urllib.error.URLError as e:
        return {"ok": False, "error": f"Claude API 연결 실패: {e}", "ms": 0, "model": model}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}", "ms": 0, "model": model}
    ms = int((time.monotonic() - t0) * 1000)

    blocks = payload.get("content") or []
    text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
    if not text:
        err = payload.get("error", {}).get("message") if isinstance(payload.get("error"), dict) else None
        return {"ok": False, "error": err or "Claude 응답에 텍스트 블록 없음", "ms": ms, "model": model}
    return {"ok": True, "text": text, "ms": ms, "model": model}


def generate_text(prompt: str, *,
                   role: str = "deep",
                   model: str | None = None,
                   timeout: float | None = None,
                   temperature: float = 0.3,
                   max_tokens: int = DEFAULT_MAX_TOKENS) -> dict[str, Any]:
    """src.llm.generate_text와 동일한 반환 스키마: {"ok","text","ms","model"}."""
    resolved_model = model or IRIS_PPTX_MODEL
    resolved_timeout = timeout if timeout is not None else DEFAULT_TIMEOUT
    return _call(prompt, model=resolved_model, timeout=resolved_timeout,
                 temperature=temperature, max_tokens=max_tokens)


def generate_json(prompt: str, *,
                   role: str = "deep",
                   model: str | None = None,
                   timeout: float | None = None,
                   temperature: float = 0.1,
                   num_ctx: int | None = None,
                   num_predict: int | None = None) -> dict[str, Any]:
    """src.llm.generate_json과 동일한 반환 스키마: {"ok","data","raw","ms","model"}.

    Claude에는 Ollama의 format:json 강제 옵션이 없으므로, 호출자(프롬프트)가
    JSON만 출력하도록 지시해야 한다 (designer.py 프롬프트가 이미 그렇게 함).
    """
    resolved_model = model or IRIS_PPTX_MODEL
    resolved_timeout = timeout if timeout is not None else DEFAULT_TIMEOUT
    # Claude 표준 메시지 API는 max_tokens 상한이 있음 (베타 확장 없이) —
    # designer.py가 Ollama 관례로 큰 num_predict(32768)를 넘겨도 안전하게 클램프.
    max_tokens = min(num_predict, 8192) if num_predict else DEFAULT_MAX_TOKENS

    result = _call(prompt, model=resolved_model, timeout=resolved_timeout,
                   temperature=temperature, max_tokens=max_tokens)
    if not result["ok"]:
        return result

    raw = result["text"]
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
        if cleaned.rstrip().endswith("```"):
            cleaned = cleaned.rstrip()[:-3]
        cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        return {
            "ok": False,
            "error": f"JSON 파싱 실패: {e}. raw={raw[:200]}",
            "ms": result["ms"],
            "raw": raw,
            "model": resolved_model,
        }
    return {"ok": True, "data": data, "ms": result["ms"], "raw": raw, "model": resolved_model}


def health() -> dict[str, Any]:
    """API 키 존재 여부만 확인 (실제 호출은 하지 않음 — 과금 방지)."""
    if not ANTHROPIC_API_KEY:
        return {"ok": False, "error": "ANTHROPIC_API_KEY 미설정", "model": IRIS_PPTX_MODEL}
    return {"ok": True, "model": IRIS_PPTX_MODEL, "available_models": ANTHROPIC_MODELS}


__all__ = ["generate_text", "generate_json", "health"]
