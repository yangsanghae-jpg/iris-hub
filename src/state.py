"""meta_kv read/write — Phase 상태 진실원 (V2.5.3 §4.3 키 규약).

Keys:
  phase_{ver}_{id}_status     = done | in_progress | skipped
  phase_{ver}_{id}_started    = ISO8601
  phase_{ver}_{id}_done       = ISO8601
  phase_{ver}_{id}_skipped    = reason
  phase_{ver}_{id}_note       = freeform
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .config import IRIS_DB_PATH
from .phases import Phase


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _conn(db_path: Path | None = None) -> sqlite3.Connection:
    p = db_path or IRIS_DB_PATH
    c = sqlite3.connect(p)
    c.row_factory = sqlite3.Row
    return c


def get_kv(key: str, db_path: Path | None = None) -> str | None:
    c = _conn(db_path)
    try:
        row = c.execute("SELECT value FROM meta_kv WHERE key=?", (key,)).fetchone()
        return row["value"] if row else None
    finally:
        c.close()


def set_kv(key: str, value: str, db_path: Path | None = None) -> None:
    c = _conn(db_path)
    try:
        c.execute(
            "INSERT INTO meta_kv (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        c.commit()
    finally:
        c.close()


def del_kv(key: str, db_path: Path | None = None) -> None:
    c = _conn(db_path)
    try:
        c.execute("DELETE FROM meta_kv WHERE key=?", (key,))
        c.commit()
    finally:
        c.close()


def load_all_phase_status(db_path: Path | None = None) -> dict[str, dict[str, str]]:
    """Read all phase_* keys, group by prefix.
    Returns: {"phase_v25_0": {"status": "done", "done": "...", ...}}
    """
    c = _conn(db_path)
    try:
        rows = c.execute(
            "SELECT key, value FROM meta_kv WHERE key LIKE 'phase_%'"
        ).fetchall()
    finally:
        c.close()
    out: dict[str, dict[str, str]] = {}
    for r in rows:
        key, value = r["key"], r["value"]
        # key = phase_v25_0_status / phase_v26_1_done / ...
        parts = key.split("_")
        if len(parts) < 4:
            continue
        # rebuild prefix and field
        # prefix = phase_v25_0 (parts 0..-2 joined)
        field = parts[-1]
        prefix = "_".join(parts[:-1])
        out.setdefault(prefix, {})[field] = value
    return out


def status_by_key_for_phases(phases: list[Phase], db_path: Path | None = None) -> dict[str, str]:
    """For each Phase, return its current status (or '' if not set).
    Returns: {"V2.5/0": "done", "V2.6/1": "done", ...}
    """
    all_status = load_all_phase_status(db_path)
    out: dict[str, str] = {}
    for p in phases:
        block = all_status.get(p.meta_kv_prefix, {})
        out[p.key] = block.get("status", "")
    return out


# ─── High-level marking operations ─────────────────────────────────────────


def mark_done(phase: Phase, note: str | None = None, db_path: Path | None = None) -> None:
    pref = phase.meta_kv_prefix
    set_kv(f"{pref}_status", "done", db_path)
    set_kv(f"{pref}_done", now_iso(), db_path)
    if note:
        set_kv(f"{pref}_note", note, db_path)


def mark_start(phase: Phase, db_path: Path | None = None) -> None:
    pref = phase.meta_kv_prefix
    set_kv(f"{pref}_status", "in_progress", db_path)
    set_kv(f"{pref}_started", now_iso(), db_path)


def mark_skip(phase: Phase, reason: str, db_path: Path | None = None) -> None:
    pref = phase.meta_kv_prefix
    set_kv(f"{pref}_status", "skipped", db_path)
    set_kv(f"{pref}_skipped", reason, db_path)


def mark_unset(phase: Phase, db_path: Path | None = None) -> None:
    pref = phase.meta_kv_prefix
    for field in ("status", "started", "done", "skipped"):
        del_kv(f"{pref}_{field}", db_path)


def set_note(phase: Phase, note: str, db_path: Path | None = None) -> None:
    set_kv(f"{phase.meta_kv_prefix}_note", note, db_path)


def get_phase_block(phase: Phase, db_path: Path | None = None) -> dict[str, str]:
    """Return {status, started, done, skipped, note} for one phase (only set fields)."""
    all_status = load_all_phase_status(db_path)
    return all_status.get(phase.meta_kv_prefix, {})
