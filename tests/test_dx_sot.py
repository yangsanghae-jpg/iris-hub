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
    status, _ = dx_index.pack_mirror_sync_status(
        repo.root, idx.q_matrix, idx.q_framework, "q3_scale_profile"
    )
    idx.close()
    assert status == "synced"


def test_q3_mirror_both_runtimes_exist(repo):
    for rel in (
        "server/data/step3/scale_profile_v3.json",
        "client/data/step3/scale_profile_v3.json",
    ):
        assert (repo.root / rel).is_file()


def test_apply_q3_edits_both_dx_mirrors(repo):
    qm = dx_editor.load_q_matrix(repo.root)
    row = next(
        r
        for r in qm
        if r.get("pack_id") == "q3_scale_profile_server" and r.get("sub_code") == "A01"
    )
    orig = dx_index.get_nested(row.get("value_json") or {}, "weights.site_scope")
    new_val = (orig - 1) if isinstance(orig, int) and orig > 0 else (orig + 1 if isinstance(orig, int) else 1)
    updated = dx_index.apply_q3_grid_edits(qm, "q3_scale_profile", {"A01|weights.site_scope": new_val})
    for dx_pid in ("q3_scale_profile_server", "q3_scale_profile_client"):
        r = next(x for x in updated if x.get("pack_id") == dx_pid and x.get("sub_code") == "A01")
        assert dx_index.get_nested(r.get("value_json") or {}, "weights.site_scope") == new_val


def test_pack_mirror_map_loaded():
    entry = dx_index.pack_mirror_entry("q3_scale_profile")
    assert entry is not None
    rels = dx_index.pack_mirror_runtime_rels("q3_scale_profile")
    assert len(rels) == 2


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
