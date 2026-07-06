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
    assert dx_index.pack_edit_mode("q2_routing_product_nature") == "editable"
    assert dx_index.pack_edit_mode("q4_automation_profile") == "editable"
    assert dx_index.pack_edit_mode("q1_industry_product_taxonomy") == "pilot_wait"
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
    for manifest in ("q2_routing_product_nature", "q3_scale_profile", "q4_automation_profile"):
        entry = dx_index.pack_mirror_entry(manifest)
        assert entry is not None, manifest
        rels = dx_index.pack_mirror_runtime_rels(manifest)
        assert len(rels) == 2, manifest


def test_q2_q4_mirror_synced_at_rest(repo):
    idx, err = dx_index.load_dx_index(repo)
    assert idx is not None, err
    for manifest in ("q2_routing_product_nature", "q4_automation_profile"):
        status, detail = dx_index.pack_mirror_sync_status(
            repo.root, idx.q_matrix, idx.q_framework, manifest
        )
        assert status == "synced", f"{manifest}: {detail}"
    idx.close()


def test_q2_edit_both_mirrors(repo):
    qm = dx_editor.load_q_matrix(repo.root)
    orig = dx_index.get_nested(
        next(
            r["value_json"]
            for r in qm
            if r.get("pack_id") == "q2_routing_product_nature_server" and r.get("sub_code") == "A01"
        ),
        "routing_profile.primary_route",
    )
    new_val = "R1" if orig != "R1" else "R2"
    updated = dx_index.apply_q3_grid_edits(
        qm, "q2_routing_product_nature", {"A01|routing_profile.primary_route": new_val}
    )
    for dx_pid in ("q2_routing_product_nature_server", "q2_routing_product_nature_client"):
        row = next(x for x in updated if x.get("pack_id") == dx_pid and x.get("sub_code") == "A01")
        assert (
            dx_index.get_nested(row.get("value_json") or {}, "routing_profile.primary_route") == new_val
        )


def test_q4_edit_both_mirrors(repo):
    qm = dx_editor.load_q_matrix(repo.root)
    row = next(
        r
        for r in qm
        if r.get("pack_id") == "q4_automation_profile_server" and r.get("sub_code") == "A01"
    )
    orig = dx_index.get_nested(row.get("value_json") or {}, "weights.planning")
    new_val = (orig - 1) if isinstance(orig, int) and orig > 1 else (orig + 1 if isinstance(orig, int) else 3)
    updated = dx_index.apply_q3_grid_edits(
        qm, "q4_automation_profile", {"A01|weights.planning": new_val}
    )
    for dx_pid in ("q4_automation_profile_server", "q4_automation_profile_client"):
        r = next(x for x in updated if x.get("pack_id") == dx_pid and x.get("sub_code") == "A01")
        assert dx_index.get_nested(r.get("value_json") or {}, "weights.planning") == new_val


def test_flatten_q2_has_editable_fields(repo):
    idx, _ = dx_index.load_dx_index(repo)
    assert idx is not None
    rows = idx.matrix_rows("q2_routing_product_nature_server")
    grid = dx_index.flatten_q_grid_rows(rows[:3], "q2_routing_product_nature", sub_filter="A01")
    assert grid
    assert any(r["editable"] for r in grid)
    idx.close()


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
    patterns = locks["dx_q_matrix"]["value_json_edit_patterns"]
    assert "q2" in patterns
    assert "q3" in patterns
    assert "q4" in patterns


def test_audit_allowed_write_targets_st2():
    allowed = dx_editor.audit_allowed_write_targets()
    assert "scripts/data_poc/_p1b/dx_q_matrix.json" in allowed
    for rel in (
        "server/data/step2/routing_product_nature_v3.json",
        "client/data/step2/routing_product_nature_v3.json",
        "server/data/step4/automation_profile_v3.json",
        "client/data/step4/automation_profile_v3.json",
    ):
        assert rel in allowed
