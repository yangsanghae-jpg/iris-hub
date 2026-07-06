"""Tests for DIAG-SOT dx index and editor."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.diagnosis_git import resolve_diagnosis_repo
from src.store import dx_editor, dx_index


@pytest.fixture
def repo():
    r = resolve_diagnosis_repo()
    if r is None or not (r.root / "scripts/data_poc/_p1b/dx_q_matrix.json").is_file():
        pytest.skip("diagnosis-tool dx JSON not present")
    return r


def test_pack_edit_mode_q3_editable():
    assert dx_index.pack_edit_mode("q3_scale_profile") == "editable"
    assert dx_index.pack_edit_mode("q2_routing_product_nature") == "pilot_wait"
    assert dx_index.pack_edit_mode("ch2_systems_catalog") == "deferred"
    assert dx_index.pack_edit_mode("industry_master") == "spine"


def test_load_dx_index_regenerates(repo):
    ok, msg = dx_editor.prove_index_regenerates(repo)
    assert ok, msg


def test_rebuild_q3_byte_match(repo):
    idx, err = dx_index.load_dx_index(repo)
    assert idx is not None, err
    dx_pid = "q3_scale_profile_server"
    runtime_rel = "server/data/step3/scale_profile_v3.json"
    status, _ = dx_index.runtime_sync_status(
        repo.root, runtime_rel, idx.q_matrix, idx.q_framework, dx_pid
    )
    idx.close()
    assert status == "synced"


def test_flatten_q3_has_editable_fields(repo):
    idx, _ = dx_index.load_dx_index(repo)
    assert idx is not None
    rows = idx.matrix_rows("q3_scale_profile_server")
    grid = dx_index.flatten_q3_grid_rows(rows[:3], sub_filter="A01")
    assert grid
    assert any(r["editable"] for r in grid)
    idx.close()


def test_validate_q3_weights(repo):
    idx, _ = dx_index.load_dx_index(repo)
    assert idx is not None
    issues = dx_editor.validate_q3_edits(
        idx.q_matrix, "q3_scale_profile_server", idx.sub_codes
    )
    errors = [i for i in issues if i.level == "error"]
    idx.close()
    assert not errors


def test_field_locks_loaded():
    locks = dx_index.field_locks()
    assert "dx_q_matrix" in locks
    assert "q3" in locks["dx_q_matrix"]["value_json_edit_patterns"]
