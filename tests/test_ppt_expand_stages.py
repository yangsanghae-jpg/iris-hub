"""v31 expand API — 1차 regen / 2차 classify 분리 계약."""
from __future__ import annotations

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.engine.output.deck import expander
from v31 import server

client = TestClient(server.app)


def _fake_regen(**kwargs):
    return expander.RegeneratedContent(
        md="# regenerated\n\n---\n\n## Ch1\nbody",
        elapsed_ms=1200,
        model="mock-model",
        original_chars=10,
        output_chars=40,
    )


def _fake_expand(**kwargs):
    return expander.ExpandedResult(
        md="# classified\n\n<!-- IRIS_PATTERN: narrative -->\nbody",
        elapsed_ms=800,
        model="mock-model",
        original_chars=40,
        output_chars=55,
        contract={"ok": True},
    )


def test_expand_regen_endpoint(monkeypatch):
    monkeypatch.setattr(expander, "regenerate_chapters", lambda *a, **k: _fake_regen())
    resp = client.post("/api/expand/regen", json={"md_text": "# src", "lang": "한국어"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["stage"] == "regen"
    assert "regenerated" in data["md"]
    assert data["elapsed"] == 1.2


def test_expand_classify_endpoint(monkeypatch):
    monkeypatch.setattr(expander, "expand_for_slides", lambda *a, **k: _fake_expand())
    resp = client.post("/api/expand/classify", json={"md_text": "# regenerated", "lang": "한국어"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["stage"] == "classify"
    assert "classified" in data["md"]
    assert data["contract"]["ok"] is True


def test_expand_combined_still_works(monkeypatch):
    monkeypatch.setattr(expander, "regenerate_chapters", lambda *a, **k: _fake_regen())
    monkeypatch.setattr(expander, "expand_for_slides", lambda *a, **k: _fake_expand())
    resp = client.post("/api/expand", json={"md_text": "# src", "lang": "한국어"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert "classified" in data["md"]
    assert data["elapsed"] == 2.0
    assert "regen_md" in data
