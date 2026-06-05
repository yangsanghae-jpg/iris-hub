"""Phase definitions loader (data/phase_deps.yaml) + dependency graph."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import yaml

from .config import DEPS_YAML


@dataclass
class Phase:
    version: str            # "V2.5" / "V2.6"
    id: str                 # "0", "0.5", "1", "2", ...
    title: str
    est_days: float
    depends: list[str]      # ["V2.5/0", ...]

    @property
    def key(self) -> str:
        """e.g. 'V2.5/0' or 'V2.6/1'"""
        return f"{self.version}/{self.id}"

    @property
    def meta_kv_prefix(self) -> str:
        """e.g. 'phase_v25_0' / 'phase_v26_1'"""
        v = self.version.lower().replace(".", "").replace("v", "v")  # V2.5 -> v25
        pid = self.id.replace(".", "_")
        return f"phase_{v}_{pid}"


def load_phases(path=None) -> list[Phase]:
    p = path or DEPS_YAML
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    deps_map: dict[str, list[str]] = data.get("deps", {})
    phases = []
    for row in data["phases"]:
        key = f"{row['version']}/{row['id']}"
        phases.append(
            Phase(
                version=row["version"],
                id=str(row["id"]),
                title=row["title"],
                est_days=float(row["est_days"]),
                depends=list(deps_map.get(key, [])),
            )
        )
    return phases


def is_unblocked(phase: Phase, status_by_key: dict[str, str]) -> bool:
    """V2.5.3 §4.7: skipped는 done과 동급."""
    for dep_key in phase.depends:
        dep_status = status_by_key.get(dep_key)
        if dep_status not in ("done", "skipped"):
            return False
    return True


def derive_display_status(phase: Phase, db_status: str | None, status_by_key: dict[str, str]) -> str:
    """V2.5.3 §3.2 5종: done / in_progress / skipped / pending / blocked"""
    if db_status in ("done", "in_progress", "skipped"):
        return db_status
    return "pending" if is_unblocked(phase, status_by_key) else "blocked"
