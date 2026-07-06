"""Tests for DIAG-SOT dx index and editor."""
from __future__ import annotations

import json
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
    assert dx_index.pack_edit_mode("q5_recommendation_by_subindustry") == "editable"
    assert dx_index.pack_edit_mode("q1_industry_product_taxonomy") == "pilot_wait"
    assert dx_index.pack_edit_mode("q5_axes") == "pilot_wait"
    assert dx_index.pack_edit_mode("ch2_systems_catalog") == "deferred"
    assert dx_index.pack_edit_mode("industry_master") == "spine"


def test_load_dx_index_regenerates(repo):
    ok, msg = dx_editor.prove_index_regenerates(repo)
    assert ok, msg


def test_rebuild_q3_byte_match(repo):
    idx, err = dx_index.load_dx_index(repo)
    assert idx is not None, err
    status, _ = dx_index.pack_mirror_sync_status_from_index(idx, "q3_scale_profile")
    idx.close()
    assert status == "synced"


def test_rebuild_q5_byte_match(repo):
    """ST3-a: 무편집 rebuild_q5 == server·client runtime byte-0 MATCH."""
    idx, err = dx_index.load_dx_index(repo)
    assert idx is not None, err
    status, detail = dx_index.pack_mirror_sync_status_from_index(idx, "q5_recommendation_by_subindustry")
    idx.close()
    assert status == "synced", detail


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
        status, detail = dx_index.pack_mirror_sync_status_from_index(idx, manifest)
        assert status == "synced", f"{manifest}: {detail}"
    idx.close()


def test_q5_mirror_synced_at_rest(repo):
    idx, err = dx_index.load_dx_index(repo)
    assert idx is not None, err
    status, detail = dx_index.pack_mirror_sync_status_from_index(idx, "q5_recommendation_by_subindustry")
    idx.close()
    assert status == "synced", detail


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


def test_q5_edit_both_mirrors(repo):
    """ST3-b: enum leaf 편집 → server·client 둘 다 갱신."""
    q5 = dx_editor.load_q5_recommendation(repo.root)
    row = next(r for r in q5 if r.get("sub_code") == "A01")
    orig = dx_index.get_nested(row.get("value_json") or {}, "q5_2.recommended_levels.C")
    new_val = "L3" if orig != "L3" else "L4"
    updated = dx_index.apply_q5_grid_edits(q5, {"A01|q5_2.recommended_levels.C": new_val})
    result = dx_editor.save_q5_and_rebuild(repo, updated, "q5_recommendation_by_subindustry")
    assert result.ok, result.message
    for rel in (
        "server/data/q5/recommendation_by_subindustry_v1.json",
        "client/data/q5/recommendation_by_subindustry_v1.json",
    ):
        payload = json.loads((repo.root / rel).read_text(encoding="utf-8"))
        rec = payload["recommendations"][0]
        assert dx_index.get_nested(rec, "q5_2.recommended_levels.C") == new_val
    # restore original
    restored = dx_index.apply_q5_grid_edits(updated, {"A01|q5_2.recommended_levels.C": orig})
    restore_result = dx_editor.save_q5_and_rebuild(repo, restored, "q5_recommendation_by_subindustry")
    assert restore_result.ok


def test_q5_locked_fields_not_editable():
    """ST3-c: priority_axes 등 whitelist 밖 필드는 편집 불가."""
    paths = dx_index.q_editable_field_paths("q5")
    assert "q5_1.priority_axes" not in paths
    assert "subindustry_code" not in paths
    assert not dx_index.is_field_editable("q5", "q5_1.priority_axes")


def test_validate_q5_rejects_invalid(repo):
    """ST3-d: 범위 밖 값 저장 거부."""
    idx, _ = dx_index.load_dx_index(repo)
    assert idx is not None
    sub_codes = idx.sub_codes
    q5 = dx_editor.load_q5_recommendation(repo.root)
    bad = dx_index.apply_q5_grid_edits(q5, {"A01|q5_2.recommended_levels.C": "L9"})
    issues = dx_editor.validate_q5_edits(bad, sub_codes)
    idx.close()
    assert any(i.level == "error" for i in issues)
    bad2 = dx_index.apply_q5_grid_edits(q5, {"A01|q5_1.default_axis_weight.C": "always"})
    issues2 = dx_editor.validate_q5_edits(bad2, sub_codes)
    assert any(i.level == "error" for i in issues2)


def test_flatten_q5_has_editable_fields(repo):
    idx, _ = dx_index.load_dx_index(repo)
    assert idx is not None
    rows = idx.q5_recommendation_rows()
    grid = dx_index.flatten_q5_grid_rows(rows[:3], sub_filter="A01")
    assert grid
    assert any(r["editable"] for r in grid)
    assert any(r["field_path"].startswith("q5_2.recommended_levels.") for r in grid)
    idx.close()


def test_pack_mirror_map_q5():
    entry = dx_index.pack_mirror_entry("q5_recommendation_by_subindustry")
    assert entry is not None
    rels = dx_index.pack_mirror_runtime_rels("q5_recommendation_by_subindustry")
    assert len(rels) == 2


def test_audit_allowed_write_targets_st3e():
    allowed = dx_editor.audit_allowed_write_targets()
    assert "scripts/data_poc/_p1a/dx_q5_recommendation.json" in allowed
    for rel in (
        "server/data/q5/recommendation_by_subindustry_v1.json",
        "client/data/q5/recommendation_by_subindustry_v1.json",
    ):
        assert rel in allowed


def test_q2_q4_regression_synced(repo):
    """ST3-g: Q2·Q3·Q4 무편집 synced 유지."""
    idx, err = dx_index.load_dx_index(repo)
    assert idx is not None, err
    for manifest in ("q2_routing_product_nature", "q3_scale_profile", "q4_automation_profile"):
        status, detail = dx_index.pack_mirror_sync_status_from_index(idx, manifest)
        assert status == "synced", f"{manifest}: {detail}"
    idx.close()


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
    q5_patterns = locks["dx_q5_recommendation"]["value_json_edit_patterns"]["q5"]
    assert "q5_2.recommended_levels.C" in q5_patterns
    assert "q5_1.priority_axes" not in q5_patterns


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
