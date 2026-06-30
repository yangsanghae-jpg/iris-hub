"""diagnosis-tool 마이그레이션 항목 — git 기반 자동 평가."""
from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from .config import DIAGNOSIS_TOOL_GITHUB
from .diagnosis_git import (
    DiagnosisRepo,
    git_diff_paths,
    git_show_file,
    git_tracked_paths,
    resolve_diagnosis_repo,
)
from .diagnosis_migration import MigrationItem, is_unblocked


@dataclass
class EvalResult:
    status: str  # pending | success | failure | verified | blocked
    detail: str
    evidence: list[str] = field(default_factory=list)


def evaluate_all(items: list[MigrationItem]) -> tuple[DiagnosisRepo | None, dict[str, EvalResult]]:
    repo = resolve_diagnosis_repo()
    if repo is None:
        empty = {
            it.key: EvalResult(
                "pending",
                f"로컬 clone 없음 — git clone {DIAGNOSIS_TOOL_GITHUB}.git",
                [],
            )
            for it in items
        }
        return None, empty

    tracked = git_tracked_paths(repo)
    results: dict[str, EvalResult] = {}
    status_by_key: dict[str, str] = {}

    ordered = sorted(items, key=lambda x: (_phase_num(x.phase), x.id))
    for it in ordered:
        if not is_unblocked(it, status_by_key):
            r = EvalResult("blocked", "선행 항목 미완료", [])
            results[it.key] = r
            status_by_key[it.key] = "blocked"
            continue
        r = _evaluate_item(it, repo, tracked)
        results[it.key] = r
        status_by_key[it.key] = r.status

    return repo, results


def _phase_num(phase: str) -> float:
    try:
        return float(phase)
    except ValueError:
        return 99.0


def _evaluate_item(item: MigrationItem, repo: DiagnosisRepo, tracked: set[str]) -> EvalResult:
    check: dict[str, Any] = item.check or {}
    if not check:
        return EvalResult("pending", "자동 검증 규칙 미정의", [])

    evidence: list[str] = []
    failures: list[str] = []
    pending: list[str] = []
    rel_paths: list[str] = []

    for p in check.get("absent", []):
        rel_paths.append(p)
        if p in tracked:
            failures.append(f"아직 git에 존재: {p}")
        else:
            evidence.append(f"absent OK: {p}")

    for p in check.get("tracked", []):
        rel_paths.append(p)
        full = repo.root / p
        if p in tracked:
            evidence.append(f"tracked: {p}")
        elif full.is_file() or full.is_dir():
            pending.append(f"작업 트리에 있으나 미커밋: {p}")
        else:
            pending.append(f"미생성: {p}")

    for group in check.get("equal", []):
        if not isinstance(group, list) or len(group) < 2:
            continue
        rel_paths.extend(group)
        hashes: dict[str, str | None] = {}
        for p in group:
            blob = git_show_file(repo, p)
            if blob is None:
                wt = repo.root / p
                if wt.is_file():
                    pending.append(f"equal 대상 미커밋: {p}")
                else:
                    pending.append(f"equal 대상 없음: {p}")
                hashes[p] = None
            else:
                hashes[p] = hashlib.md5(blob).hexdigest()
        vals = [h for h in hashes.values() if h]
        if len(vals) == len(group) and len(set(vals)) == 1:
            evidence.append(f"equal OK: {' = '.join(group)}")
        elif len(vals) >= 2 and len(set(vals)) > 1:
            failures.append(f"hash 불일치: {group}")

    script = check.get("script")
    if script:
        rel_paths.append(script)
        if script not in tracked and not (repo.root / script).is_file():
            pending.append(f"script 없음: {script}")
        else:
            ok, msg = _run_script(repo, script, check.get("script_args", []))
            if ok:
                evidence.append(f"script OK: {script}")
            else:
                failures.append(f"script FAIL: {msg}")

    for rule in check.get("grep", []):
        path = rule.get("path", "")
        needle = rule.get("contains", "")
        rel_paths.append(path)
        blob = git_show_file(repo, path)
        if blob is None:
            pending.append(f"grep 대상 미커밋: {path}")
        elif needle.encode() not in blob:
            pending.append(f"grep 미매칭: {path} ⊃ {needle!r}")
        else:
            evidence.append(f"grep OK: {path}")

    if failures:
        return EvalResult("failure", "; ".join(failures), evidence)

    if pending:
        return EvalResult("pending", "; ".join(pending), evidence)

    dirty = git_diff_paths(repo, list(dict.fromkeys(rel_paths)))
    if dirty:
        return EvalResult(
            "success",
            f"검증 통과 · 미커밋 변경 {len(dirty)}건",
            evidence + [f"dirty: {d}" for d in dirty[:5]],
        )
    return EvalResult("verified", "git HEAD 기준 검증·커밋 완료", evidence)


@lru_cache(maxsize=8)
def _run_script_cached(repo_root: str, head: str, script: str, args_json: str) -> tuple[bool, str]:
    cmd = ["bash", script]
    if args_json:
        cmd.extend(args_json.split("\0"))
    try:
        out = subprocess.run(
            cmd,
            cwd=Path(repo_root),
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        if out.returncode == 0:
            return True, "exit 0"
        tail = (out.stderr or out.stdout or "").strip()[-200:]
        return False, tail or f"exit {out.returncode}"
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, str(e)


def _run_script(repo: DiagnosisRepo, script: str, args: list[str]) -> tuple[bool, str]:
    args_json = "\0".join(args) if args else ""
    return _run_script_cached(str(repo.root), repo.head, script, args_json)
