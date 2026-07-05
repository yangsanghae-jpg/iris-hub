"""Ch1 compose 미리보기 — diagnosis-tool 엔진 호출 (DIAGNOSIS_PACK_MGMT_TAB_DESIGN §4.4)."""
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.diagnosis_git import resolve_diagnosis_repo


@dataclass
class PreviewResult:
    ok: bool
    blocks: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    raw: str | None = None


_PREVIEW_SCRIPT = '''
import json
import sys
from pathlib import Path

repo = Path(sys.argv[1])
industry = sys.argv[2]
sub = sys.argv[3]
routing = sys.argv[4]
lang = sys.argv[5] if len(sys.argv) > 5 else "zh"

sys.path.insert(0, str(repo / "server"))
try:
    from assemble.ch1_mgmt.engine import compose_ch1_four_blocks
except Exception as exc:
    print(json.dumps({"ok": False, "error": f"import failed: {exc}"}))
    sys.exit(1)

# 엔진 실제 시그니처: compose_ch1_four_blocks(ctx, step3, knowledge, lang).
# 팩/라우팅은 엔진이 데이터 디렉토리에서 직접 로드하므로 step3/knowledge 는 비워도 된다.
ctx = {"industry_code": industry}
if sub and sub not in ("", "-", "—"):
    ctx["sub_industry"] = sub
if routing and routing not in ("", "-", "—"):
    ctx["routing_type"] = routing

try:
    result = compose_ch1_four_blocks(ctx, {}, {}, lang=lang)
    if result is None:
        print(json.dumps({"ok": False, "error": f"compose None (산업 팩 로드 실패: {industry})"}))
    else:
        print(json.dumps({"ok": True, "blocks": result}, ensure_ascii=False))
except Exception as exc:
    print(json.dumps({"ok": False, "error": str(exc)}))
'''


def preview_ch1_compose(
    industry_code: str,
    sub_industry_code: str,
    routing_code: str,
    *,
    lang: str = "zh",
    repo_root: Path | None = None,
) -> PreviewResult:
    repo = resolve_diagnosis_repo()
    root = repo_root or (repo.root if repo else None)
    if root is None:
        return PreviewResult(ok=False, error="diagnosis-tool clone 없음")

    engine = root / "server" / "assemble" / "ch1_mgmt" / "engine.py"
    if not engine.exists():
        return PreviewResult(
            ok=False,
            error=f"엔진 없음: {engine.relative_to(root)}",
        )

    proc = subprocess.run(
        [
            sys.executable, "-c", _PREVIEW_SCRIPT,
            str(root), industry_code, sub_industry_code or "", routing_code or "", lang,
        ],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=root,
    )
    raw = (proc.stdout or proc.stderr or "").strip()
    if not raw:
        return PreviewResult(ok=False, error="compose 출력 없음", raw=raw)

    try:
        payload = json.loads(raw.splitlines()[-1])
    except json.JSONDecodeError:
        return PreviewResult(ok=False, error="compose JSON 파싱 실패", raw=raw)

    if payload.get("error"):
        return PreviewResult(ok=False, error=str(payload["error"]), raw=raw)
    if not payload.get("ok"):
        return PreviewResult(ok=False, error=payload.get("error") or "compose 실패", raw=raw)
    return PreviewResult(ok=True, blocks=payload.get("blocks") or {}, raw=raw)
