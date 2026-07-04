"""dx_* 임포트·검증·익스포트 테스트."""
from pathlib import Path

import pytest

from src.store import db, dx, dx_export, dx_import, dx_validate

FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "diagnosis_tool" / "server" / "data"


def test_dx_schema_tables(vault_root):
    conn = db.get_conn()
    try:
        names = {
            r["name"] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table','view')"
            ).fetchall()
        }
    finally:
        conn.close()
    assert "dx_industry" in names
    assert "v_dx_coverage" in names
    assert db.SCHEMA_VERSION == 2


def test_import_from_fixture(vault_root):
    result = dx_import.import_from_path(FIXTURE_ROOT, branch="test", commit="abc123")
    assert result.industries == 2
    assert result.sub_industries == 3
    assert result.routing_packs == 2
    assert result.codes >= 4
    assert result.question_metrics > 0

    counts = dx.count_rows()
    assert counts["dx_industry"] == 2
    assert counts["dx_sub_industry"] == 3


def test_coverage_detects_q5_mgmt_gap(vault_root):
    dx_import.import_from_path(FIXTURE_ROOT)
    gaps = dx.coverage_gaps()
    questions = {g["question"] for g in gaps}
    # medical_imaging has no step5 override in fixture
    assert any(g["canon_code"] == "medical_imaging_equipment" for g in gaps)


def test_validate_passes_after_import(vault_root):
    dx_import.import_from_path(FIXTURE_ROOT)
    result = dx_validate.validate()
    assert result.ok
    assert result.error_count == 0


def test_export_roundtrip_structure(vault_root):
    dx_import.import_from_path(FIXTURE_ROOT)
    export = dx_export.export_ch1()
    assert "server/data/ch1/industry_packs/IND_A.json" in export.files
    assert "server/data/ch1/routing_packs/RT_PROJECT.json" in export.files
    assert "MVP_PROGRESS_MON" in export.files["server/data/ch1/industry_packs/IND_A.json"]


def test_schema_migration_v1_to_v2(vault_root, monkeypatch):
    """기존 v1 DB에 dx_* 마이그레이션이 적용되는지."""
    conn = db.get_conn()
    try:
        conn.execute("DELETE FROM meta_kv")
        conn.execute("INSERT INTO meta_kv(key, value) VALUES('schema_version', '1')")
        conn.commit()
    finally:
        conn.close()
    db.ensure_schema()
    conn = db.get_conn()
    try:
        v = conn.execute(
            "SELECT value FROM meta_kv WHERE key='schema_version'"
        ).fetchone()["value"]
        has_dx = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='dx_industry'"
        ).fetchone()
    finally:
        conn.close()
    assert int(v) == 2
    assert has_dx is not None
