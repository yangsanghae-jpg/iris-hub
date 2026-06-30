"""diagnosis-tool 마이그레이션 항목 로더 (data/diagnosis_migration.yaml)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .config import DIAGNOSIS_MIGRATION_YAML

STATUSES = ("pending", "success", "failure", "verified")

STATUS_LABEL = {
    "pending": "대기",
    "success": "성공",
    "failure": "실패",
    "verified": "확인",
}

STATUS_ICON = {
    "pending": "⬜",
    "success": "✅",
    "failure": "❌",
    "verified": "🔵",
}


@dataclass
class MigrationItem:
    phase: str
    id: str
    title: str
    gate: str
    depends: list[str]
    check: dict[str, Any] | None = None

    @property
    def key(self) -> str:
        return f"{self.phase}/{self.id}"

    @property
    def meta_kv_prefix(self) -> str:
        pid = self.phase.replace(".", "_")
        iid = self.id.replace(".", "_")
        return f"dt_migrate_{pid}_{iid}"


def load_migration_items(path: Path | None = None) -> list[MigrationItem]:
    p = path or DIAGNOSIS_MIGRATION_YAML
    data: dict[str, Any] = yaml.safe_load(p.read_text(encoding="utf-8"))
    deps_map: dict[str, list[str]] = data.get("deps", {})
    items: list[MigrationItem] = []
    for row in data["items"]:
        key = f"{row['phase']}/{row['id']}"
        items.append(
            MigrationItem(
                phase=str(row["phase"]),
                id=str(row["id"]),
                title=row["title"],
                gate=row.get("gate", ""),
                depends=list(deps_map.get(key, [])),
                check=row.get("check"),
            )
        )
    return items


def load_migration_meta(path: Path | None = None) -> dict[str, str]:
    p = path or DIAGNOSIS_MIGRATION_YAML
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    return {
        "version": data.get("version", ""),
        "project": data.get("project", ""),
        "github": data.get("github", ""),
        "doc_ref": data.get("doc_ref", ""),
    }


def is_unblocked(item: MigrationItem, status_by_key: dict[str, str]) -> bool:
    """verified·success는 선행 완료로 인정."""
    ok = {"success", "verified"}
    for dep in item.depends:
        st = status_by_key.get(dep)
        if st not in ok:
            return False
    return True
