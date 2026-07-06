"""DIAG-SOT dx JSON 파생 인덱스 (read-only, JSON에서 재생성).

정본 = git-tracked dx JSON. 이 모듈의 인메모리 구조는 조회·검증용이며 쓰기 대상이 아니다.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.diagnosis_git import DiagnosisRepo

_DX_REL = {
    "q_matrix": "scripts/data_poc/_p1b/dx_q_matrix.json",
    "q_framework": "scripts/data_poc/_p1b/dx_q_framework.json",
    "registry_framework": "scripts/data_poc/_p1b/dx_registry_framework.json",
    "sub_industry": "scripts/data_poc/_p1a/dx_sub_industry.json",
    "industry": "scripts/data_poc/_p1b/dx_industry.json",
}

_HUB_DATA = Path(__file__).resolve().parents[2] / "data" / "diag_sot"


def _read_json(path: Path) -> Any:
    if not path.is_file():
        return None
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _load_hub_json(name: str) -> dict[str, Any]:
    path = _HUB_DATA / name
    data = _read_json(path)
    return data if isinstance(data, dict) else {}


def pack_scope() -> dict[str, Any]:
    return _load_hub_json("pack_scope.json")


def pack_glossary() -> dict[str, dict[str, str]]:
    return _load_hub_json("pack_glossary.json")


def field_locks() -> dict[str, Any]:
    return _load_hub_json("field_locks.json")


def q_pack_runtime_map() -> dict[str, Any]:
    return _load_hub_json("q_pack_runtime_map.json")


def pack_mirror_entry(manifest_pack_id: str) -> dict[str, Any] | None:
    entry = (q_pack_runtime_map().get("packs") or {}).get(manifest_pack_id)
    return entry if isinstance(entry, dict) else None


def pack_mirror_dx_ids(manifest_pack_id: str) -> list[str]:
    entry = pack_mirror_entry(manifest_pack_id)
    if entry:
        mirrors = entry.get("mirrors") or []
        return [str(m["dx_pack_id"]) for m in mirrors if m.get("dx_pack_id")]
    scope = pack_scope()
    mapping = scope.get("manifest_to_dx_pack") or {}
    return [str(mapping.get(manifest_pack_id, manifest_pack_id))]


def pack_edit_primary_dx_id(manifest_pack_id: str) -> str:
    entry = pack_mirror_entry(manifest_pack_id)
    if entry:
        primary = entry.get("edit_primary_dx_pack_id")
        if primary:
            return str(primary)
        mirrors = entry.get("mirrors") or []
        if mirrors:
            return str(mirrors[0].get("dx_pack_id", manifest_pack_id))
    scope = pack_scope()
    mapping = scope.get("manifest_to_dx_pack") or {}
    return str(mapping.get(manifest_pack_id, manifest_pack_id))


def pack_mirror_runtime_rels(manifest_pack_id: str) -> list[dict[str, str]]:
    entry = pack_mirror_entry(manifest_pack_id)
    if not entry:
        return []
    out: list[dict[str, str]] = []
    for m in entry.get("mirrors") or []:
        dx_pid = m.get("dx_pack_id")
        rel = m.get("runtime_rel")
        if dx_pid and rel:
            out.append({"dx_pack_id": str(dx_pid), "runtime_rel": str(rel)})
    return out


def q3_field_glossary() -> dict[str, dict[str, str]]:
    return _load_hub_json("q3_field_glossary.json")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    return sha256_bytes(path.read_bytes())


def unescape_json_pointer(value: str) -> str:
    return value.replace("~1", "/").replace("~0", "~")


def escape_json_pointer(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def get_nested(obj: dict[str, Any], dotted: str) -> Any:
    cur: Any = obj
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def set_nested(obj: dict[str, Any], dotted: str, value: Any) -> None:
    parts = dotted.split(".")
    cur = obj
    for part in parts[:-1]:
        nxt = cur.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[part] = nxt
        cur = nxt
    cur[parts[-1]] = value


@dataclass
class DxIndex:
    """JSON에서 로드한 dx 파생 인덱스."""

    repo_root: Path
    q_matrix: list[dict[str, Any]] = field(default_factory=list)
    q_framework: list[dict[str, Any]] = field(default_factory=list)
    sub_codes: set[str] = field(default_factory=set)
    _conn: sqlite3.Connection | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        self._conn = sqlite3.connect(":memory:")
        self._conn.row_factory = sqlite3.Row
        self._build_sqlite()

    def _build_sqlite(self) -> None:
        assert self._conn is not None
        c = self._conn
        c.execute(
            """
            CREATE TABLE dx_q_matrix (
                rowid INTEGER PRIMARY KEY,
                q TEXT, sub_code TEXT, pack_id TEXT, field_path TEXT,
                source_json_pointer TEXT, source_index INTEGER, row_index INTEGER,
                value_json TEXT
            )
            """
        )
        for row in self.q_matrix:
            c.execute(
                """
                INSERT INTO dx_q_matrix
                (q, sub_code, pack_id, field_path, source_json_pointer, source_index, row_index, value_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row.get("q"),
                    row.get("sub_code"),
                    row.get("pack_id"),
                    row.get("field_path"),
                    row.get("source_json_pointer"),
                    row.get("source_index"),
                    row.get("row_index"),
                    json.dumps(row.get("value_json"), ensure_ascii=False),
                ),
            )
        c.commit()

    def matrix_rows(self, dx_pack_id: str) -> list[dict[str, Any]]:
        return [r for r in self.q_matrix if r.get("pack_id") == dx_pack_id]

    def matrix_row_count(self, dx_pack_id: str) -> int:
        return len(self.matrix_rows(dx_pack_id))

    def total_row_count(self) -> int:
        return len(self.q_matrix) + len(self.q_framework)

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None


def load_dx_index(repo: DiagnosisRepo) -> tuple[DxIndex | None, str | None]:
    root = repo.root
    q_matrix_path = root / _DX_REL["q_matrix"]
    if not q_matrix_path.is_file():
        return None, f"dx JSON 미배치: `{_DX_REL['q_matrix']}` 없음"

    q_matrix = _read_json(q_matrix_path)
    q_framework = _read_json(root / _DX_REL["q_framework"])
    sub_industry = _read_json(root / _DX_REL["sub_industry"])

    if not isinstance(q_matrix, list):
        return None, "dx_q_matrix.json 파싱 실패"

    sub_codes: set[str] = set()
    if isinstance(sub_industry, list):
        sub_codes = {str(r.get("code")) for r in sub_industry if r.get("code")}

    idx = DxIndex(
        repo_root=root,
        q_matrix=q_matrix,
        q_framework=q_framework if isinstance(q_framework, list) else [],
        sub_codes=sub_codes,
    )
    return idx, None


def resolve_dx_pack_id(manifest_pack_id: str) -> str:
    return pack_edit_primary_dx_id(manifest_pack_id)


def pack_edit_mode(manifest_pack_id: str) -> str:
    """editable | pilot_wait | deferred | spine | readonly"""
    scope = pack_scope()
    if manifest_pack_id in scope.get("spine_packs", []):
        return "spine"
    if manifest_pack_id in scope.get("deferred_content_packs", []):
        return "deferred"
    if manifest_pack_id in scope.get("q_packs", []):
        if manifest_pack_id in scope.get("pilot_packs", []):
            return "editable"
        return "pilot_wait"
    return "readonly"


def pack_display(manifest_pack_id: str) -> tuple[str, str]:
    gloss = pack_glossary().get(manifest_pack_id) or {}
    title = gloss.get("title_ko") or manifest_pack_id
    desc = gloss.get("desc_ko") or ""
    return title, desc


def chapter_group(pack: dict[str, Any]) -> str:
    chapters = pack.get("consumer_chapters") or []
    if not chapters:
        return "기타"
    ch = chapters[0]
    if ch.startswith("Q"):
        return "Q 수치팩"
    if ch.startswith("Ch"):
        return "A 콘텐츠팩"
    return "기타"


def rebuild_q_pack_payload(q_matrix: list[dict[str, Any]], q_framework: list[dict[str, Any]], dx_pack_id: str) -> dict[str, Any]:
    """p1b rebuild_q_pack와 동일 알고리즘."""
    framework = [row for row in q_framework if row.get("pack_id") == dx_pack_id]
    matrix = [row for row in q_matrix if row.get("pack_id") == dx_pack_id]
    events: list[tuple[int, str, Any]] = []
    for row in framework:
        ptr = str(row.get("source_json_pointer") or "").strip("/")
        key = unescape_json_pointer(ptr)
        events.append((int(row.get("source_index", 0)), key, row.get("value_json")))
    if matrix:
        source_index = int(matrix[0].get("source_index", 0))
        profiles = {
            row["sub_code"]: row["value_json"]
            for row in sorted(matrix, key=lambda item: int(item.get("row_index", 0)))
        }
        events.append((source_index, "subindustry_profiles", profiles))
    payload: dict[str, Any] = {}
    for _, key, value in sorted(events, key=lambda item: item[0]):
        payload[key] = value
    return payload


def runtime_sync_status(
    repo_root: Path,
    runtime_rel: str,
    q_matrix: list[dict[str, Any]],
    q_framework: list[dict[str, Any]],
    dx_pack_id: str,
) -> tuple[str, str | None]:
    """Returns (status, detail) — synced | pending."""
    runtime_path = repo_root / runtime_rel
    if not runtime_path.is_file():
        return "pending", "리포트 파일 없음"

    rebuilt = rebuild_q_pack_payload(q_matrix, q_framework, dx_pack_id)
    rebuilt_bytes = (json.dumps(rebuilt, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    actual_bytes = runtime_path.read_bytes()
    if rebuilt_bytes == actual_bytes:
        return "synced", None
    return "pending", "진실원과 리포트 내용이 다름"


def pack_mirror_sync_status(
    repo_root: Path,
    q_matrix: list[dict[str, Any]],
    q_framework: list[dict[str, Any]],
    manifest_pack_id: str,
) -> tuple[str, str | None]:
    """server·client 등 모든 미러 runtime이 byte-0 일치일 때만 synced."""
    mirrors = pack_mirror_runtime_rels(manifest_pack_id)
    if not mirrors:
        dx_pid = pack_edit_primary_dx_id(manifest_pack_id)
        rel = f"server/data/step3/scale_profile_v3.json"
        return runtime_sync_status(repo_root, rel, q_matrix, q_framework, dx_pid)

    pending_details: list[str] = []
    for m in mirrors:
        status, detail = runtime_sync_status(
            repo_root, m["runtime_rel"], q_matrix, q_framework, m["dx_pack_id"]
        )
        if status != "synced":
            label = m["runtime_rel"].split("/")[0]
            pending_details.append(detail or f"{label} 미러 불일치")
    if pending_details:
        return "pending", "; ".join(pending_details)
    return "synced", None


def q3_editable_field_paths() -> list[str]:
    locks = field_locks()
    patterns = (
        locks.get("dx_q_matrix", {})
        .get("value_json_edit_patterns", {})
        .get("q3", [])
    )
    return list(patterns)


def is_field_editable(q: str, field_path: str) -> bool:
    locks = field_locks()
    patterns = (
        locks.get("dx_q_matrix", {})
        .get("value_json_edit_patterns", {})
        .get(q, [])
    )
    return field_path in patterns


def flatten_q3_grid_rows(
    matrix_rows: list[dict[str, Any]],
    *,
    sub_filter: str = "",
) -> list[dict[str, Any]]:
    """편집 그리드용 평탄 행."""
    glossary = q3_field_glossary()
    field_paths = q3_editable_field_paths()
    out: list[dict[str, Any]] = []
    for row in sorted(matrix_rows, key=lambda r: str(r.get("sub_code", ""))):
        sub = str(row.get("sub_code") or "")
        if sub_filter and sub != sub_filter:
            continue
        value_json = row.get("value_json") or {}
        if not isinstance(value_json, dict):
            continue
        label_ko = ""
        sub_label = value_json.get("subindustry_label") or {}
        if isinstance(sub_label, dict):
            label_ko = str(sub_label.get("ko") or "")
        for fp in field_paths:
            val = get_nested(value_json, fp)
            if val is None:
                continue
            meta = glossary.get(fp) or {}
            editable = is_field_editable("q3", fp)
            out.append(
                {
                    "_row_key": f"{sub}|{fp}",
                    "sub_code": sub,
                    "sub_label_ko": label_ko,
                    "field_path": fp,
                    "meaning": meta.get("label_ko") or fp,
                    "hint": meta.get("hint_ko") or "",
                    "value": val,
                    "reflects": meta.get("reflects_ko") or "—",
                    "editable": editable,
                }
            )
    return out


def apply_q3_grid_edits(
    q_matrix: list[dict[str, Any]],
    manifest_pack_id: str,
    edits: dict[str, Any],
) -> list[dict[str, Any]]:
    """edits: {_row_key: new_value} → server·client 미러 dx 행 모두 갱신."""
    updated = [dict(r) for r in q_matrix]
    for dx_pid in pack_mirror_dx_ids(manifest_pack_id):
        updated = _apply_q3_grid_edits_for_pack(updated, dx_pid, edits)
    return updated


def _apply_q3_grid_edits_for_pack(
    q_matrix: list[dict[str, Any]],
    dx_pack_id: str,
    edits: dict[str, Any],
) -> list[dict[str, Any]]:
    updated = [dict(r) for r in q_matrix]
    key_to_idx = {
        f"{r.get('sub_code')}|{fp}": (i, fp)
        for i, r in enumerate(updated)
        if r.get("pack_id") == dx_pack_id
        for fp in q3_editable_field_paths()
    }
    for row_key, new_val in edits.items():
        loc = key_to_idx.get(row_key)
        if not loc:
            continue
        idx, fp = loc
        row = updated[idx]
        vj = dict(row.get("value_json") or {})
        set_nested(vj, fp, new_val)
        row["value_json"] = vj
        updated[idx] = row
    return updated
