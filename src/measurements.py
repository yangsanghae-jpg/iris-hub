"""L4-K 시드 측정값 — _index.db 직접 쿼리 (V2.5.3 §4.4)."""
from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from .config import ALDA_BASELINE, IRIS_DB_PATH


@dataclass
class Measurements:
    db_exists: bool = False
    db_path: Path = IRIS_DB_PATH
    db_size: int = 0
    integrity: str = "?"
    schema_version: str = "?"

    documents_total: int = 0
    kind_dist: dict[str, int] = field(default_factory=dict)
    origin_dist: dict[str, int] = field(default_factory=dict)
    lane_dist: dict[str, int] = field(default_factory=dict)
    industry_dist: dict[str, int] = field(default_factory=dict)
    matrix_keyed: int = 0       # industry+area 둘 다 NOT NULL인 docs 수

    chunks_total: int = 0
    fts_total: int = 0
    aliases_total: int = 0

    last_ingest_raw: str = "-"
    last_ingest_ref: str = "-"

    @property
    def documents_gap(self) -> int:
        return self.documents_total - ALDA_BASELINE["documents"]

    @property
    def fts_gap(self) -> int:
        return self.fts_total - ALDA_BASELINE["documents_fts"]

    @property
    def entity_gap(self) -> int:
        return self.kind_dist.get("entity", 0) - ALDA_BASELINE["entity"]

    @property
    def concept_gap(self) -> int:
        return self.kind_dist.get("concept", 0) - ALDA_BASELINE["concept"]


def measure(db_path: Path | None = None) -> Measurements:
    p = db_path or IRIS_DB_PATH
    m = Measurements(db_path=p)
    # symlink target may be missing; check resolved
    try:
        resolved = p.resolve(strict=True)
        m.db_exists = resolved.is_file()
        if m.db_exists:
            m.db_size = resolved.stat().st_size
    except (FileNotFoundError, OSError):
        return m

    if not m.db_exists:
        return m

    c = sqlite3.connect(p)
    c.row_factory = sqlite3.Row
    try:
        m.integrity = (c.execute("PRAGMA integrity_check").fetchone() or ["?"])[0]

        row = c.execute("SELECT value FROM meta_kv WHERE key='schema_version'").fetchone()
        m.schema_version = row["value"] if row else "-"

        m.documents_total = c.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        m.chunks_total = c.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        m.fts_total = c.execute("SELECT COUNT(*) FROM documents_fts").fetchone()[0]

        try:
            m.aliases_total = c.execute("SELECT COUNT(*) FROM entity_aliases").fetchone()[0]
        except sqlite3.OperationalError:
            m.aliases_total = 0

        for col in ("kind", "origin", "lane"):
            try:
                rows = c.execute(
                    f"SELECT {col} as k, COUNT(*) as n FROM documents GROUP BY {col}"
                ).fetchall()
                dist = {(r["k"] or "(null)"): r["n"] for r in rows}
            except sqlite3.OperationalError:
                dist = {}
            if col == "kind":
                m.kind_dist = dist
            elif col == "origin":
                m.origin_dist = dist
            else:
                m.lane_dist = dist

        # K3 industry 분포 + matrix 키 부여된 doc 카운트
        try:
            rows = c.execute(
                "SELECT industry as k, COUNT(*) as n FROM documents GROUP BY industry"
            ).fetchall()
            m.industry_dist = {(r["k"] or "(null)"): r["n"] for r in rows}
            m.matrix_keyed = c.execute(
                "SELECT COUNT(*) FROM documents WHERE industry IS NOT NULL AND area IS NOT NULL"
            ).fetchone()[0]
        except sqlite3.OperationalError:
            pass

        for k, attr in (("last_ingest_raw_at", "last_ingest_raw"), ("last_ingest_reference_at", "last_ingest_ref")):
            row = c.execute("SELECT value FROM meta_kv WHERE key=?", (k,)).fetchone()
            if row:
                setattr(m, attr, row["value"])
    finally:
        c.close()
    return m
