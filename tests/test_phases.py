"""Tests for phases.py — V2.5.3 §3.5 우회 룰 회귀."""
from src.phases import load_phases, is_unblocked, derive_display_status


def test_load_phases_count():
    phases = load_phases()
    assert len(phases) == 7
    keys = [p.key for p in phases]
    assert "V2.5/0" in keys
    assert "V2.6/5" in keys


def test_phase_meta_kv_prefix():
    phases = load_phases()
    by_key = {p.key: p for p in phases}
    assert by_key["V2.5/0"].meta_kv_prefix == "phase_v25_0"
    assert by_key["V2.5/0.5"].meta_kv_prefix == "phase_v25_0_5"
    assert by_key["V2.6/1"].meta_kv_prefix == "phase_v26_1"


def test_unblocked_basic():
    phases = load_phases()
    by_key = {p.key: p for p in phases}
    # V2.5/0 has no deps -> always unblocked
    assert is_unblocked(by_key["V2.5/0"], {})
    # V2.6/1 depends on V2.5/0.5 -> blocked initially
    assert not is_unblocked(by_key["V2.6/1"], {})


def test_skipped_unblocks():
    """V2.5.3 §3.5: skipped는 done과 동급."""
    phases = load_phases()
    by_key = {p.key: p for p in phases}
    # 0.5를 skipped로 처리하면 V2.6/1 진입 가능
    status = {"V2.5/0": "done", "V2.5/0.5": "skipped"}
    assert is_unblocked(by_key["V2.6/1"], status)
    assert is_unblocked(by_key["V2.6/2"], {**status, "V2.6/1": "done"})


def test_derive_display_status():
    phases = load_phases()
    by_key = {p.key: p for p in phases}
    # 명시 done
    assert derive_display_status(by_key["V2.5/0"], "done", {}) == "done"
    # in_progress
    assert derive_display_status(by_key["V2.5/0"], "in_progress", {}) == "in_progress"
    # skipped
    assert derive_display_status(by_key["V2.5/0.5"], "skipped", {}) == "skipped"
    # pending (의존 충족)
    assert derive_display_status(by_key["V2.5/0"], None, {}) == "pending"
    # blocked (의존 미충족)
    assert derive_display_status(by_key["V2.6/5"], None, {}) == "blocked"
