"""DIAG-SOT MANIFEST / LINEAGE read-only loader (P5).

탭은 이 모듈만 통해 P4-core 산출물을 읽는다. SoT 직접 쓰기 금지.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

from src.diagnosis_git import resolve_diagnosis_repo

MANIFEST_REL = "scripts/data_poc/DIAG_SOT_MANIFEST.json"
LINEAGE_REL = "scripts/data_poc/DIAG_SOT_LINEAGE.json"
INVENTORY_REL = "docs/diag-sot/reports/P4_INVENTORY.json"


def diagnosis_tool_root() -> Path | None:
    repo = resolve_diagnosis_repo()
    return repo.root if repo else None


def _mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


@st.cache_data(show_spinner=False)
def _load_json_cached(path_str: str, mtime: float) -> dict[str, Any] | None:
    _ = mtime  # cache bust key
    return _read_json(Path(path_str))


def load_manifest() -> tuple[dict[str, Any] | None, str | None]:
    """Return (manifest, error_reason). error_reason is set when data is None."""
    root = diagnosis_tool_root()
    if root is None:
        return None, "diagnosis-tool clone을 찾을 수 없습니다."
    path = root / MANIFEST_REL
    if not path.is_file():
        return None, f"P4-core 미배치: `{MANIFEST_REL}` 없음"
    data = _load_json_cached(str(path), _mtime(path))
    if data is None:
        return None, f"`{MANIFEST_REL}` JSON 파싱 실패"
    return data, None


def load_lineage() -> tuple[dict[str, Any] | None, str | None]:
    root = diagnosis_tool_root()
    if root is None:
        return None, "diagnosis-tool clone을 찾을 수 없습니다."
    path = root / LINEAGE_REL
    if not path.is_file():
        return None, f"P4-core 미배치: `{LINEAGE_REL}` 없음"
    data = _load_json_cached(str(path), _mtime(path))
    if data is None:
        return None, f"`{LINEAGE_REL}` JSON 파싱 실패"
    return data, None


def load_inventory() -> tuple[dict[str, Any] | None, str | None]:
    """Lazy — 드릴다운 시에만 호출."""
    root = diagnosis_tool_root()
    if root is None:
        return None, "diagnosis-tool clone을 찾을 수 없습니다."
    path = root / INVENTORY_REL
    if not path.is_file():
        return None, f"`{INVENTORY_REL}` 없음"
    data = _load_json_cached(str(path), _mtime(path))
    if data is None:
        return None, f"`{INVENTORY_REL}` JSON 파싱 실패"
    return data, None


def pack_lineage_index(lineage: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = lineage.get("pack_level_lineage") or []
    return {row["pack_id"]: row for row in rows if isinstance(row, dict) and row.get("pack_id")}


def normalize_path_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [str(v) for v in value if v]
    return []


def related_issues(pack: dict[str, Any], lineage: dict[str, Any]) -> list[dict[str, Any]]:
    """issue_rollup에서 팩 연관 issue 필터 (pack_id·dx 경로 fragment)."""
    direct = pack.get("issues") or []
    if direct:
        return list(direct)

    pack_id = pack.get("pack_id") or ""
    dx_paths = normalize_path_list(pack.get("dx_artifacts"))
    fragments = {pack_id, *dx_paths}
    for p in dx_paths:
        fragments.add(Path(p).stem)

    matched: list[dict[str, Any]] = []
    rollup = (lineage.get("issue_rollup") or {}).get("issues") or []
    for issue in rollup:
        if not isinstance(issue, dict):
            continue
        blob = " ".join(
            str(issue.get(k, ""))
            for k in ("issue_id", "description", "source", "issue_kind")
        )
        if any(frag and frag in blob for frag in fragments):
            matched.append(issue)
    return matched


def status_sort_key(pack: dict[str, Any]) -> tuple[int, str]:
    order = {
        "legacy_duplicate_unreferenced": 0,
        "unclassified_candidate": 1,
        "residual_live": 2,
        "dx_covered_partial": 3,
        "tool_fixture": 4,
        "dx_covered_byte0": 5,
    }
    status = pack.get("coverage_status") or ""
    return (order.get(status, 99), pack.get("pack_id") or "")
