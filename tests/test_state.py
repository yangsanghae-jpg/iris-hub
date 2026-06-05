"""Tests for state.py — meta_kv 키 규약."""
import sqlite3
from pathlib import Path

import pytest

from src.phases import load_phases
from src.state import (
    get_kv,
    set_kv,
    mark_done,
    mark_start,
    mark_skip,
    mark_unset,
    set_note,
    get_phase_block,
    status_by_key_for_phases,
)


@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    db = tmp_path / "test.db"
    c = sqlite3.connect(db)
    c.execute("CREATE TABLE meta_kv (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    c.commit()
    c.close()
    return db


def test_set_get(tmp_db):
    set_kv("foo", "bar", db_path=tmp_db)
    assert get_kv("foo", db_path=tmp_db) == "bar"
    set_kv("foo", "baz", db_path=tmp_db)  # upsert
    assert get_kv("foo", db_path=tmp_db) == "baz"


def test_mark_done(tmp_db):
    phases = load_phases()
    p1 = next(p for p in phases if p.key == "V2.6/1")
    mark_done(p1, note="hello", db_path=tmp_db)
    block = get_phase_block(p1, db_path=tmp_db)
    assert block["status"] == "done"
    assert block["note"] == "hello"
    assert block["done"].endswith("Z")


def test_mark_skip(tmp_db):
    phases = load_phases()
    p05 = next(p for p in phases if p.key == "V2.5/0.5")
    mark_skip(p05, reason="m2-venv", db_path=tmp_db)
    block = get_phase_block(p05, db_path=tmp_db)
    assert block["status"] == "skipped"
    assert block["skipped"] == "m2-venv"


def test_mark_unset(tmp_db):
    phases = load_phases()
    p1 = next(p for p in phases if p.key == "V2.6/1")
    mark_done(p1, db_path=tmp_db)
    assert get_phase_block(p1, db_path=tmp_db).get("status") == "done"
    mark_unset(p1, db_path=tmp_db)
    assert get_phase_block(p1, db_path=tmp_db) == {}


def test_status_by_key_for_phases(tmp_db):
    phases = load_phases()
    p1 = next(p for p in phases if p.key == "V2.6/1")
    p05 = next(p for p in phases if p.key == "V2.5/0.5")
    mark_done(p1, db_path=tmp_db)
    mark_skip(p05, "m2-venv", db_path=tmp_db)
    sk = status_by_key_for_phases(phases, db_path=tmp_db)
    assert sk["V2.6/1"] == "done"
    assert sk["V2.5/0.5"] == "skipped"
    assert sk["V2.6/5"] == ""  # not set


def test_skipped_key_with_dot_in_id(tmp_db):
    """V2.5/0.5 → meta_kv_prefix=phase_v25_0_5. last underscore split이 깨지는지 확인."""
    phases = load_phases()
    p05 = next(p for p in phases if p.key == "V2.5/0.5")
    assert p05.meta_kv_prefix == "phase_v25_0_5"
    mark_skip(p05, "m2-venv", db_path=tmp_db)
    block = get_phase_block(p05, db_path=tmp_db)
    assert block.get("status") == "skipped"
    assert block.get("skipped") == "m2-venv"
