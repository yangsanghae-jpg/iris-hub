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

from .config import LLM_MODELS, OLLAMA_URL, IRIS_LLM_DEEP

DEFAULT_TIMEOUT = 60.0  # deep K2 분석 5-30초 기대, 60초 헤드룸
FAST_TIMEOUT = 15.0     # fast는 1-5초 기대

# deep 슬롯 미설치 시 fallback 우선순위 (embedding 제외).
# 설정값(IRIS_LLM_DEEP)이 설치돼 있으면 그걸 쓰고, 없을 때만 이 목록을 순회한다.
_DEEP_FALLBACK_PRIORITY = (
    "qwen3:30b",
    "qwen3-next:80b-a3b-instruct-q4_K_M",
    "gpt-oss:20b",
    "qwen3.5:4b",
    "gemma4:e4b",
    "gemma4:latest",
)

_EMBED_NAME_MARKERS = ("bge-m3", "nomic-embed", "embed")


def model_for(role: str) -> str:
    """role → 실제 모델명. 'deep'|'fast'|'embed'."""
    try:
        return LLM_MODELS[role]
    except KeyError:
        raise ValueError(f"unknown LLM role: {role!r} (allowed: deep|fast|embed)")


def thinking_mode_for_model(model: str) -> bool | str | None:
    """모델별 Ollama `think` 파라미터 정책.

    반환:
      - True/False: boolean think 지원 모델
      - "low"|"medium"|"high": gpt-oss 계열 전용 (boolean 금지)
      - None: 요청에 think 키를 생략

    규칙 (이름 substring 기준, 대소문자 무시):
      1. gpt-oss* → "low"  (boolean 절대 사용 금지)
      2. *instruct* / gemma* / qwen3.5* → False (비추론·instruct)
      3. qwen3* (위 제외) / deepseek-r1* → True  (thinking 분리 모델)
      4. 그 외 unknown → False (안전한 기본)
    """
    name = (model or "").lower()
    if not name:
        return False
    if "gpt-oss" in name:
        return "low"
    if "instruct" in name or "gemma" in name or "qwen3.5" in name:
        return False
    if "qwen3" in name or "deepseek-r1" in name:
        return True
    return False


def _is_embed_model(name: str) -> bool:
    n = name.lower()
    return any(k in n for k in _EMBED_NAME_MARKERS)


def resolve_available_model(
    preferred: str | None = None,
    *,
    installed: list[str] | None = None,
) -> str | None:
    """preferred가 설치돼 있으면 그대로, 아니면 정책 우선순위로 fallback.

    embedding 모델은 제외. 생성 모델이 하나도 없으면 None.
    """
    names = installed if installed is not None else list_models()
    if not names:
        return None

    def _norm(n: str) -> str:
        return n if ":" in n else f"{n}:latest"

    name_set = set(names)
    name_set_norm = {_norm(n) for n in names}

    def _present(candidate: str) -> str | None:
        if candidate in name_set:
            return candidate
        cn = _norm(candidate)
        if cn in name_set_norm:
            # 원본 목록에서 매칭되는 실제 이름 반환
            for n in names:
                if _norm(n) == cn:
                    return n
        # 태그 없는 preferred ↔ 태그 있는 설치본
        base = candidate.split(":", 1)[0]
        for n in names:
            if n == base or n.startswith(base + ":"):
                return n
        return None

    pref = preferred or IRIS_LLM_DEEP
    hit = _present(pref)
    if hit and not _is_embed_model(hit):
        return hit

    for cand in _DEEP_FALLBACK_PRIORITY:
        hit = _present(cand)
        if hit and not _is_embed_model(hit):
            return hit

    for n in names:
        if not _is_embed_model(n):
            return n
    return None


def _build_generate_options(
    *,
    temperature: float,
    num_ctx: int | None,
    num_predict: int | None,
) -> dict[str, Any]:
    options: dict[str, Any] = {"temperature": temperature}
    if num_ctx is not None:
        options["num_ctx"] = num_ctx
    if num_predict is not None:
        options["num_predict"] = num_predict
    return options


def generate_json(prompt: str, *,
                  role: str = "deep",
                  model: str | None = None,
                  timeout: float | None = None,
                  temperature: float = 0.1,
                  num_ctx: int | None = None,
                  num_predict: int | None = None) -> dict[str, Any]:
    """Ollama /api/generate 호출, JSON 모드 강제.

    role 또는 model 중 하나를 지정. role이 우선이며 model이 명시되면 override.

    V2.7.6.2 — num_ctx / num_predict 옵션 추가:
      - num_ctx: 컨텍스트 윈도우 (Ollama 기본 2048 — 큰 입력은 잘림)
      - num_predict: 출력 토큰 한도 (Ollama 기본 128 — 큰 JSON 잘림)

    V2.8.1.3 — think: False 박음:
      - Qwen3 / Qwen3.6 / Gemma4 / DeepSeek-R1 등 *추론 모델*은 기본 thinking ON
      - thinking 켜진 채 format:json 호출하면 JSON이 *thinking 블록*에 박히고
        response가 비어서 `raw=""` 회귀 (M5 진단)
      - generate_text()엔 V2.7.5.2 사이클에 박혔으나 generate_json()은 누락
      - non-thinking 모델(예: gemma4:e4b native JSON)엔 무해

    반환:
        성공: {"ok": True, "data": <parsed JSON>, "ms": <elapsed>, "raw": <text>, "model": <name>}
        실패: {"ok": False, "error": <str>, "ms": <elapsed>, "model": <name>}
    """
    resolved_model = model or model_for(role)
    resolved_timeout = timeout if timeout is not None else (
        FAST_TIMEOUT if role == "fast" else DEFAULT_TIMEOUT
    )

    options = _build_generate_options(
        temperature=temperature, num_ctx=num_ctx, num_predict=num_predict,
    )

    body = json.dumps({
        "model": resolved_model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "think": False,
        "options": options,
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
                  temperature: float = 0.3,
                  think: bool | str | None = None,
                  num_ctx: int | None = None,
                  num_predict: int | None = None) -> dict[str, Any]:
    """Ollama raw text 모드. JSON 강제 없음.

    PPT 재구조화처럼 *마크다운 그대로* 받아야 할 때 사용.

    think:
      - None → thinking_mode_for_model(model) 정책 적용
      - bool / "low"|"medium"|"high" → 그대로 요청에 포함
      - 정책이 None이면 think 키 자체를 생략

    반환 (성공):
      ok, text(=response만), thinking_present(bool), model, ms,
      done, done_reason, prompt_eval_count, eval_count
      ※ thinking 원문은 절대 반환하지 않음
    """
    resolved_model = model or model_for(role)
    resolved_timeout = timeout if timeout is not None else (
        FAST_TIMEOUT if role == "fast" else DEFAULT_TIMEOUT
    )
    think_mode = thinking_mode_for_model(resolved_model) if think is None else think

    options = _build_generate_options(
        temperature=temperature, num_ctx=num_ctx, num_predict=num_predict,
    )

    req_body: dict[str, Any] = {
        "model": resolved_model,
        "prompt": prompt,
        "stream": False,
        "options": options,
    }
    if think_mode is not None:
        req_body["think"] = think_mode

    body = json.dumps(req_body).encode("utf-8")

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
    text = payload.get("response") or ""
    thinking_raw = payload.get("thinking")
    thinking_present = bool(thinking_raw and str(thinking_raw).strip())
    # thinking 원문은 여기서 버리고 존재 여부만 메타로 남긴다.
    del thinking_raw

    done = payload.get("done")
    done_reason = payload.get("done_reason")
    prompt_eval_count = payload.get("prompt_eval_count")
    eval_count = payload.get("eval_count")

    if not str(text).strip():
        return {
            "ok": False,
            "error": "빈 response (thinking만 있거나 모델이 최종 답을 비움)",
            "ms": ms,
            "model": resolved_model,
            "thinking_present": thinking_present,
            "done": done,
            "done_reason": done_reason,
            "prompt_eval_count": prompt_eval_count,
            "eval_count": eval_count,
        }

    return {
        "ok": True,
        "text": text,
        "thinking_present": thinking_present,
        "ms": ms,
        "model": resolved_model,
        "done": done,
        "done_reason": done_reason,
        "prompt_eval_count": prompt_eval_count,
        "eval_count": eval_count,
    }


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
    if not found and role == "deep":
        fb = resolve_available_model(target, installed=names)
        if fb:
            return {
                "ok": True,
                "role": role,
                "model": fb,
                "configured": target,
                "fallback": True,
                "available_models": names,
                "error": None,
            }
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


def list_models(*, timeout: float = 3.0) -> list[str]:
    """V2.7.6.3 — Ollama에 설치된 모델 이름 목록.

    반환: 모델명 list (예: ['qwen3:8b', 'qwen3.5:4b', 'bge-m3:latest']).
    Ollama가 죽었거나 모델 0개면 빈 리스트.

    embed 전용 모델(bge-m3, nomic-*)은 *PPT 생성용*으론 의미 없지만,
    필터링은 호출자가 결정 (UI에서 추천만).
    """
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=timeout) as resp:
            tags = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return []
    names = [m.get("name") for m in tags.get("models", []) if m.get("name")]
    return sorted(names)


__all__ = [
    "generate_json", "generate_text", "embed", "health", "health_all",
    "list_models", "model_for", "thinking_mode_for_model", "resolve_available_model",
]
