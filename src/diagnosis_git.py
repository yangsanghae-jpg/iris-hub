"""diagnosis-tool Git 저장소 해석 — GitHub 정본 URL + 로컬 clone."""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .config import DEV_ROOT, DIAGNOSIS_TOOL_GITHUB


@dataclass(frozen=True)
class DiagnosisRepo:
    root: Path
    branch: str
    head: str
    head_short: str
    remote_url: str
    canonical_url: str
    remote_ok: bool
    dirty: bool
    last_commit_iso: str
    last_push_iso: str
    unpushed_commits: int


def _git(args: list[str], cwd: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if out.returncode != 0:
            return None
        return out.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return None


def normalize_remote(url: str) -> str:
    """git@github.com:user/repo.git → github.com/user/repo"""
    u = url.strip().rstrip("/")
    if u.endswith(".git"):
        u = u[:-4]
    if u.startswith("git@"):
        u = u.replace(":", "/", 1).replace("git@", "", 1)
    for prefix in ("https://", "http://", "ssh://"):
        if u.startswith(prefix):
            u = u[len(prefix):]
    return u.lower()


def remote_matches_canonical(remote_url: str, canonical: str = DIAGNOSIS_TOOL_GITHUB) -> bool:
    if not remote_url:
        return False
    return normalize_remote(remote_url) == normalize_remote(canonical)


def _default_clone_paths() -> list[Path]:
    """M5/M2 표준 clone 위치 — iris-local에서 실행해도 0Dev/1Dev 탐색."""
    # DEV_ROOT가 hostname 기반(M5:/0Dev, M2:/Documents/1Dev)이라 이것만으로 양 머신 커버.
    return [(DEV_ROOT / "diagnosis-tool").resolve()]


def _candidate_roots() -> list[Path]:
    roots: list[Path] = []
    env = os.getenv("DIAGNOSIS_TOOL_GIT", "").strip()
    if env:
        roots.append(Path(env).expanduser().resolve())
    for p in _default_clone_paths():
        if p not in roots:
            roots.append(p)
    return roots


def format_git_date(iso: str) -> str:
    """ISO8601 → YYYY-MM-DD (표시용)."""
    return iso[:10] if iso and len(iso) >= 10 else "—"


def _repo_from_path(root: Path) -> DiagnosisRepo | None:
    head = _git(["rev-parse", "HEAD"], root)
    if not head:
        return None
    branch = _git(["branch", "--show-current"], root) or "(detached)"
    remote = _git(["remote", "get-url", "origin"], root) or ""
    dirty = _git(["status", "--porcelain"], root) not in ("", None)
    last = _git(["log", "-1", "--format=%cI"], root) or ""

    last_push = ""
    unpushed = 0
    if branch and branch != "(detached)":
        upstream = f"origin/{branch}"
        if _git(["rev-parse", upstream], root):
            last_push = _git(["log", "-1", "--format=%cI", upstream], root) or ""
            ahead = _git(["rev-list", "--count", f"{upstream}..HEAD"], root)
            if ahead and ahead.isdigit():
                unpushed = int(ahead)

    return DiagnosisRepo(
        root=root,
        branch=branch,
        head=head,
        head_short=head[:7],
        remote_url=remote,
        canonical_url=DIAGNOSIS_TOOL_GITHUB,
        remote_ok=remote_matches_canonical(remote),
        dirty=dirty,
        last_commit_iso=last,
        last_push_iso=last_push,
        unpushed_commits=unpushed,
    )


def resolve_diagnosis_repo() -> DiagnosisRepo | None:
    """GitHub 정본(origin 일치) clone 우선. 없으면 일치하는 로컬 git repo 탐색."""
    found: list[DiagnosisRepo] = []
    for cand in _candidate_roots():
        if not cand.is_dir():
            continue
        top = _git(["rev-parse", "--show-toplevel"], cand)
        if not top:
            continue
        repo = _repo_from_path(Path(top).resolve())
        if repo:
            found.append(repo)

    if not found:
        return None
    # origin이 정본 GitHub와 일치하는 clone 우선
    for r in found:
        if r.remote_ok:
            return r
    return found[0]


def git_tracked_paths(repo: DiagnosisRepo) -> set[str]:
    out = _git(["ls-files"], repo.root)
    if not out:
        return set()
    return set(out.splitlines())


def git_diff_paths(repo: DiagnosisRepo, rel_paths: list[str]) -> list[str]:
    if not rel_paths:
        return []
    out = _git(["diff", "--name-only", "HEAD", "--", *rel_paths], repo.root)
    if not out:
        return []
    return [p for p in out.splitlines() if p.strip()]


def git_show_file(repo: DiagnosisRepo, rel_path: str) -> bytes | None:
    out = subprocess.run(
        ["git", "show", f"HEAD:{rel_path}"],
        cwd=repo.root,
        capture_output=True,
        timeout=15,
        check=False,
    )
    if out.returncode != 0:
        return None
    return out.stdout
