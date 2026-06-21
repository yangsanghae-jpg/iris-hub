"""V2.8.0 — Presenton bridge.

Presenton (https://github.com/presenton/presenton)을 별도 Docker로 띄우고
iris-hub가 HTTP 호출로 PPT 생성.

흐름:
  1. 사용자가 brew docker로 Presenton 컨테이너 띄움 (http://localhost:5000)
  2. iris-hub의 🦅 Presenton 탭에서 마크다운/프롬프트 입력
  3. iris-hub가 POST http://localhost:5000/api/v1/ppt/generate/presentation 호출
  4. 응답의 path를 다운로드 → 사용자에게 제공

설정:
  - 환경변수 PRESENTON_URL (기본 http://localhost:5000)
  - 환경변수 PRESENTON_AUTH_USERNAME / PRESENTON_AUTH_PASSWORD (옵션)
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

import urllib.request
import urllib.error
import json
import tempfile


PRESENTON_URL = os.environ.get("PRESENTON_URL", "http://localhost:5000")


class PresentonError(Exception):
    pass


@dataclass
class PresentonResult:
    out_path: Path
    presentation_id: str
    edit_path: str
    elapsed_ms: int
    size_bytes: int


def is_alive(*, timeout: float = 1.0) -> bool:
    """Presenton 가동 여부 체크."""
    try:
        req = urllib.request.Request(f"{PRESENTON_URL}/")
        with urllib.request.urlopen(req, timeout=timeout):
            return True
    except Exception:
        return False


def _login_if_needed() -> str | None:
    """AUTH 설정시 토큰 발급."""
    user = os.environ.get("PRESENTON_AUTH_USERNAME")
    pw = os.environ.get("PRESENTON_AUTH_PASSWORD")
    if not (user and pw):
        return None
    body = json.dumps({"username": user, "password": pw}).encode("utf-8")
    req = urllib.request.Request(
        f"{PRESENTON_URL}/api/v1/auth/login",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode("utf-8"))
            return data.get("access_token")
    except Exception as e:
        raise PresentonError(f"인증 실패: {e}")


def generate(
    prompt: str,
    *,
    n_slides: int = 8,
    language: str = "Korean",
    theme: str = "royal_blue",
    export_as: str = "pptx",
    timeout: float = 600.0,
) -> PresentonResult:
    """Presenton API 호출 → PPT/PDF 생성.

    Args:
      prompt: 마크다운 또는 자연어 (Presenton이 LLM으로 처리)
      n_slides: 슬라이드 수 (보통 5~15)
      language: "Korean" / "English" / ...
      theme: royal_blue / cream / light_red / faint_yellow ... (Presenton 내장)
      export_as: "pptx" 또는 "pdf"

    raise PresentonError: 연결 실패, API 에러, 다운로드 실패.
    """
    if not is_alive():
        raise PresentonError(
            f"Presenton 미가동 ({PRESENTON_URL}). "
            "Docker로 띄우기:\n"
            "  docker run -d --name presenton -p 5000:80 \\\n"
            "    -e LLM=ollama -e OLLAMA_MODEL=qwen3:8b \\\n"
            "    -e OLLAMA_URL=http://host.docker.internal:11434 \\\n"
            "    ghcr.io/presenton/presenton:latest"
        )

    token = _login_if_needed()

    # multipart/form-data 직접 박음
    boundary = "----iris-hub-boundary-x7y9z"
    parts: list[bytes] = []
    fields = {
        "prompt": prompt,
        "n_slides": str(n_slides),
        "language": language,
        "theme": theme,
        "export_as": export_as,
    }
    for k, v in fields.items():
        parts.append(f"--{boundary}\r\n".encode("utf-8"))
        parts.append(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode("utf-8"))
        parts.append(v.encode("utf-8"))
        parts.append(b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    body = b"".join(parts)

    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(
        f"{PRESENTON_URL}/api/v1/ppt/generate/presentation",
        data=body,
        headers=headers,
        method="POST",
    )

    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            payload = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        msg = e.read().decode("utf-8", errors="ignore")[:500]
        raise PresentonError(f"API 에러 (HTTP {e.code}): {msg}")
    except Exception as e:
        raise PresentonError(f"호출 실패: {type(e).__name__}: {e}")
    elapsed_ms = int((time.time() - t0) * 1000)

    presentation_id = payload.get("presentation_id", "")
    file_path = payload.get("path", "")
    edit_path = payload.get("edit_path", "")
    if not file_path:
        raise PresentonError(f"API 응답에 path 없음: {payload}")

    # 결과 파일 다운로드 (Presenton 정적 경로)
    if file_path.startswith("/"):
        download_url = urljoin(PRESENTON_URL, file_path)
    else:
        download_url = file_path

    out_path = Path(tempfile.mkdtemp(prefix="iris_presenton_")) / f"deck.{export_as}"
    try:
        req2 = urllib.request.Request(download_url)
        if token:
            req2.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req2, timeout=60) as r:
            data = r.read()
        out_path.write_bytes(data)
    except Exception as e:
        raise PresentonError(f"파일 다운로드 실패 ({download_url}): {e}")

    return PresentonResult(
        out_path=out_path,
        presentation_id=presentation_id,
        edit_path=urljoin(PRESENTON_URL, edit_path) if edit_path else "",
        elapsed_ms=elapsed_ms,
        size_bytes=out_path.stat().st_size,
    )


__all__ = ["PRESENTON_URL", "PresentonError", "PresentonResult", "generate", "is_alive"]
