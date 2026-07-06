"""Tests for diagnosis-tool git resolution (진단툴 탭 경로 해석)."""
from pathlib import Path

import pytest

from src.diagnosis_git import normalize_remote, remote_matches_canonical, resolve_diagnosis_repo


def test_remote_matches_github():
    assert remote_matches_canonical("git@github.com:yangsanghae-jpg/diagnosis-tool.git")
    assert remote_matches_canonical("https://github.com/yangsanghae-jpg/diagnosis-tool")
    assert not remote_matches_canonical("https://github.com/other/repo")


def test_normalize_remote():
    assert normalize_remote("git@github.com:yangsanghae-jpg/diagnosis-tool.git") == (
        "github.com/yangsanghae-jpg/diagnosis-tool"
    )


def test_resolve_diagnosis_repo_from_0dev():
    repo = resolve_diagnosis_repo()
    if not (Path("/Users/iris/0Dev/diagnosis-tool") / ".git").exists():
        pytest.skip("diagnosis-tool git not present")
    assert repo is not None
    assert repo.root.name == "diagnosis-tool"
    assert len(repo.head) == 40
    assert repo.remote_ok
    assert remote_matches_canonical(repo.remote_url)
    assert hasattr(repo, "last_push_iso")
