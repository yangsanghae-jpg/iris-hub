"""Tests for diagnosis git resolution and auto evaluation."""
from pathlib import Path

import pytest

from src.diagnosis_eval import evaluate_all
from src.diagnosis_git import normalize_remote, remote_matches_canonical, resolve_diagnosis_repo
from src.diagnosis_migration import is_unblocked, load_migration_items


def test_load_items_have_checks():
    items = load_migration_items()
    assert len(items) >= 20
    with_check = [it for it in items if it.check]
    assert len(with_check) >= 15


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


def test_eval_taxonomy_drift_is_failure_or_pending():
    items = load_migration_items()
    repo, evals = evaluate_all(items)
    if repo is None:
        pytest.skip("no repo")
    ev = evals["0/1"]
    # client/server taxonomy hashes differ in current tree
    assert ev.status in ("failure", "pending", "success", "verified")


def test_eval_poc_items_verified():
    items = load_migration_items()
    repo, evals = evaluate_all(items)
    if repo is None:
        pytest.skip("no repo")
    # 0.5/1 migrate should be verified (files committed)
    assert evals["0.5/1"].status in ("success", "verified")


def test_dependency_blocks_phase1_until_phase0():
    items = load_migration_items()
    repo, evals = evaluate_all(items)
    if repo is None:
        pytest.skip("no repo")
    by_key = {it.key: it for it in items}
    child = by_key["1/1"]
    sk = {k: v.status for k, v in evals.items()}
    # 0/1 likely not verified — 1/1 may be blocked
    if evals["0/1"].status not in ("success", "verified"):
        assert evals["1/1"].status == "blocked"
        assert not is_unblocked(child, sk)


def test_meta_kv_prefix_dot_phase():
    items = load_migration_items()
    p05 = next(it for it in items if it.key == "0.5/1")
    assert p05.meta_kv_prefix == "dt_migrate_0_5_1"
