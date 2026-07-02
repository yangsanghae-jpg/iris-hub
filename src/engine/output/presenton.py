"""V2.8.0 — Presenton bridge.

Presenton (https://github.com/presenton/presenton)을 별도 Docker로 띄우고
iris-hub가 HTTP 호출로 PPT 생성.

흐름:
  1. Docker Presenton (기본 http://localhost:5001 — macOS AirPlay :5000 회피)
  2. iris-hub 🦅 탭에서 프롬프트 입력
  3. POST /api/v1/ppt/presentation/generate (JSON, cookie 세션)
  4. 결과를 IRIS_HUB_WORK_DIR/presenton/ 에 저장 (M5: ~/0Dev/work/iris-hub/…)

설정:
  PRESENTON_URL, PRESENTON_AUTH_USERNAME/PASSWORD
  PRESENTON_OLLAMA_MODEL — Docker 컨테이너용 (UI에서 선택, 컨테이너 재기동 필요)
"""
from __future__ import annotations

import http.cookiejar
import json
import os
import shutil
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

from src.config import hub_work_subdir

PRESENTON_URL = os.environ.get("PRESENTON_URL", "http://localhost:5001")
PRESENTON_WORK_DIR = hub_work_subdir("presenton")


class PresentonError(Exception):
    pass


@dataclass
class PresentonResult:
    out_path: Path
    presentation_id: str
    edit_path: str
    elapsed_ms: int
    size_bytes: int


def _build_opener() -> urllib.request.OpenerDirector:
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def _auth_status(opener: urllib.request.OpenerDirector) -> dict:
    req = urllib.request.Request(f"{PRESENTON_URL}/api/v1/auth/status")
    with opener.open(req, timeout=5) as r:
        return json.loads(r.read().decode("utf-8"))


def _auth_setup(opener: urllib.request.OpenerDirector) -> None:
    user = os.environ.get("PRESENTON_AUTH_USERNAME", "iris")
    pw = os.environ.get("PRESENTON_AUTH_PASSWORD", "iris-hub-local")
    body = json.dumps({"username": user, "password": pw}).encode("utf-8")
    req = urllib.request.Request(
        f"{PRESENTON_URL}/api/v1/auth/setup",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with opener.open(req, timeout=10):
        pass


def _auth_login(opener: urllib.request.OpenerDirector) -> None:
    user = os.environ.get("PRESENTON_AUTH_USERNAME", "iris")
    pw = os.environ.get("PRESENTON_AUTH_PASSWORD", "iris-hub-local")
    body = json.dumps({"username": user, "password": pw}).encode("utf-8")
    req = urllib.request.Request(
        f"{PRESENTON_URL}/api/v1/auth/login",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with opener.open(req, timeout=10):
        pass


def _ensure_authenticated(opener: urllib.request.OpenerDirector) -> None:
    status = _auth_status(opener)
    if not status.get("configured"):
        _auth_setup(opener)
    if not status.get("authenticated"):
        _auth_login(opener)


def is_alive(*, timeout: float = 1.0) -> bool:
    try:
        req = urllib.request.Request(f"{PRESENTON_URL}/")
        with urllib.request.urlopen(req, timeout=timeout):
            return True
    except Exception:
        return False


def docker_run_hint(*, ollama_model: str, port: int = 5001) -> str:
    """Presenton Docker 한 줄 명령 (선택 모델 반영)."""
    return (
        f"docker rm -f presenton 2>/dev/null; docker run -d --name presenton "
        f"--platform linux/amd64 -p {port}:80 \\\n"
        f"  -e LLM=ollama \\\n"
        f"  -e OLLAMA_MODEL={ollama_model} \\\n"
        f"  -e OLLAMA_URL=http://host.docker.internal:11434 \\\n"
        f"  -e DISABLE_IMAGE_GENERATION=true \\\n"
        f"  -e CAN_CHANGE_KEYS=false \\\n"
        f"  -v presenton-data:/app_data \\\n"
        f"  ghcr.io/presenton/presenton:latest"
    )


def save_to_work_dir(src: Path, *, prefix: str = "presenton") -> Path:
    """작업 폴더로 복사 — Desktop 사용 안 함."""
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    dest = PRESENTON_WORK_DIR / f"{prefix}_{stamp}{src.suffix}"
    shutil.copy2(src, dest)
    return dest


def generate(
    prompt: str,
    *,
    n_slides: int = 8,
    language: str = "Korean",
    theme: str = "general",
    export_as: str = "pptx",
    timeout: float = 600.0,
    save_to_work: bool = True,
) -> PresentonResult:
    """Presenton API 호출 → PPT/PDF 생성."""
    if not is_alive():
        raise PresentonError(
            f"Presenton 미가동 ({PRESENTON_URL}).\n"
            "Docker 안내는 🦅 Presenton 탭 참고."
        )

    opener = _build_opener()
    try:
        _ensure_authenticated(opener)
    except Exception as e:
        raise PresentonError(f"인증 실패: {e}")

    payload = {
        "content": prompt,
        "n_slides": n_slides,
        "language": language,
        "template": theme,
        "export_as": export_as,
        "include_title_slide": True,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{PRESENTON_URL}/api/v1/ppt/presentation/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    t0 = time.time()
    try:
        with opener.open(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        msg = e.read().decode("utf-8", errors="ignore")[:500]
        raise PresentonError(f"API 에러 (HTTP {e.code}): {msg}")
    except Exception as e:
        raise PresentonError(f"호출 실패: {type(e).__name__}: {e}")
    elapsed_ms = int((time.time() - t0) * 1000)

    presentation_id = str(data.get("presentation_id", ""))
    file_path = data.get("path", "")
    edit_path = data.get("edit_path", "")
    if not file_path:
        raise PresentonError(f"API 응답에 path 없음: {data}")

    download_url = urljoin(PRESENTON_URL, file_path) if file_path.startswith("/") else file_path
    tmp = PRESENTON_WORK_DIR / f"_tmp_{int(time.time())}.{export_as}"
    try:
        with opener.open(download_url, timeout=120) as r:
            tmp.write_bytes(r.read())
    except Exception as e:
        raise PresentonError(f"파일 다운로드 실패 ({download_url}): {e}")

    out_path = save_to_work_dir(tmp, prefix="presenton") if save_to_work else tmp
    if save_to_work and tmp.exists():
        tmp.unlink(missing_ok=True)

    return PresentonResult(
        out_path=out_path,
        presentation_id=presentation_id,
        edit_path=urljoin(PRESENTON_URL, edit_path) if edit_path else "",
        elapsed_ms=elapsed_ms,
        size_bytes=out_path.stat().st_size,
    )


__all__ = [
    "PRESENTON_URL",
    "PRESENTON_WORK_DIR",
    "PresentonError",
    "PresentonResult",
    "docker_run_hint",
    "generate",
    "is_alive",
    "save_to_work_dir",
]
