"""K5 reference-lane ingester.

Registers /diagnosis-tool/server/data/ files into iris-system/knowledge/_index.db
without copying. Per V2.3: documents = metadata + path pointer, chunks = flattened
JSON body for FTS5 search, lane='reference' for read-only canonical external data.

Run: python3 apps/ingest/reference_diagnosis.py  (from iris-system/)
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

# 머신 인식 (2026-07-02) — ~/Documents 미참조. M5:/0Dev, M2:/Documents/1Dev.
import socket as _socket
_DEV_BASE = (Path("/Users/iris/0Dev") if _socket.gethostname().startswith("irisM5")
             else Path("/Users/iris/Documents/1Dev"))
SOURCE_ROOT = _DEV_BASE / "diagnosis-tool" / "server" / "data"
IRIS_ROOT = Path("/Users/iris/iris-system")  # 홈(머신 독립)
DB_PATH = IRIS_ROOT / "knowledge" / "_index.db"
SCHEMA_PATH = IRIS_ROOT / "apps" / "ingest" / "schema.sql"

LANE = "reference"
TRUST = "verified"
SKIP_DIRS = {"_archive", "cache", "tools", "team_governance", "__pycache__", "snapshots"}
SKIP_SUFFIXES = {".py", ".sh", ".db", ".db-wal", ".db-shm", ".sqlite"}

INDUSTRY_LETTERS = set("ABCDEFGH")
FILE_INDUSTRY_RE = re.compile(r"(?:^|[/_])([A-H])_[a-z]", re.IGNORECASE)
STACK_INDUSTRY_RE = re.compile(r"stack_([a-h])_", re.IGNORECASE)
IND_PACK_RE = re.compile(r"IND_([A-H])_", re.IGNORECASE)
MGMT_FILE_RE = re.compile(r"industry_([A-H])_", re.IGNORECASE)
MGMT_SPLIT_RE = re.compile(r"^(\d+)_(.+)\.json$")


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def init_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema)
    return conn


def flatten_json(obj, prefix: str = "", out: list[str] | None = None) -> list[str]:
    """Flatten JSON to text lines for FTS body."""
    if out is None:
        out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            nk = f"{prefix}.{k}" if prefix else k
            if isinstance(v, (dict, list)):
                flatten_json(v, nk, out)
            elif v is not None:
                out.append(f"{nk}: {v}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            nk = f"{prefix}[{i}]"
            if isinstance(item, (dict, list)):
                flatten_json(item, nk, out)
            elif item is not None:
                out.append(f"{nk}: {item}")
    elif obj is not None:
        out.append(f"{prefix}: {obj}")
    return out


def upsert_doc(conn, doc_id, path, industry, area, level, title, body):
    # V2.6 Phase 2.1/2.2: K1/K3 게이트 — secure lane 진입 차단
    # (LANE='reference' 모듈 상수라 정상 호출엔 영향 없음. 의도적 secure는 secure_intake.py 사용)
    from src.ingest.secure_gate import assert_not_secure
    assert_not_secure(LANE, "K1", doc_id=doc_id)

    conn.execute(
        """INSERT INTO documents
           (doc_id, path, lane, trust, industry, area, level, title, fetched_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(doc_id) DO UPDATE SET
             path=excluded.path, industry=excluded.industry,
             area=excluded.area, level=excluded.level,
             title=excluded.title, fetched_at=excluded.fetched_at""",
        (doc_id, str(path), LANE, TRUST, industry, area, level, title, now_iso()),
    )
    conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
    if body:
        conn.execute(
            "INSERT INTO chunks (chunk_id, doc_id, ord, text) VALUES (?, ?, 0, ?)",
            (f"{doc_id}#0", doc_id, body),
        )


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  ! parse error {path.name}: {e}", file=sys.stderr)
        return None


# ─── Extractors ───────────────────────────────────────────────────────────────


def extract_industry_master(conn, path: Path) -> int:
    """Root industry_master.json → explode 8 industries."""
    d = load_json(path)
    if not d or "industries" not in d:
        return 0
    n = 0
    for code, body in d["industries"].items():
        if code not in INDUSTRY_LETTERS:
            continue
        title = body.get("name_ko") or body.get("industry_en") or f"Industry {code}"
        text = "\n".join(flatten_json(body))
        upsert_doc(
            conn,
            f"ref:industry_master:{code}",
            path,
            code,
            "rule_meta",
            "default",
            title,
            text,
        )
        n += 1
    return n


def extract_industry_profile_text(conn, path: Path) -> int:
    d = load_json(path)
    if not d or "industries" not in d:
        return 0
    n = 0
    for code, body in d["industries"].items():
        if code not in INDUSTRY_LETTERS:
            continue
        title = body.get("industry_name_ko") or body.get("industry_definition_ko", "")[:60] or f"Industry {code}"
        text = "\n".join(flatten_json(body))
        upsert_doc(
            conn,
            f"ref:exec_narrative:{code}",
            path,
            code,
            "exec_narrative",
            "default",
            title,
            text,
        )
        n += 1
    return n


def extract_step3_scale(conn, path: Path) -> int:
    d = load_json(path)
    if not d or "industries" not in d:
        return 0
    n = 0
    for code, body in d["industries"].items():
        if code not in INDUSTRY_LETTERS:
            continue
        # Try to find S/M/L sub-keys; otherwise register as default.
        per_level = None
        for k in ("scale_levels", "levels", "scale"):
            if isinstance(body.get(k), dict):
                per_level = body[k]
                break
        if per_level and any(lv in per_level for lv in ("S", "M", "L")):
            for level, lv_body in per_level.items():
                if level not in ("S", "M", "L"):
                    continue
                text = "\n".join(flatten_json(lv_body))
                upsert_doc(
                    conn,
                    f"ref:step3_scale:{code}:{level}",
                    path,
                    code,
                    "step3_scale",
                    level,
                    f"{code} scale {level}",
                    text,
                )
                n += 1
        else:
            text = "\n".join(flatten_json(body))
            upsert_doc(
                conn,
                f"ref:step3_scale:{code}",
                path,
                code,
                "step3_scale",
                "default",
                f"{code} scale",
                text,
            )
            n += 1
    return n


def extract_per_industry_file(conn, path: Path, area: str, level: str = "default") -> int:
    """For files named with industry letter at start or after IND_/stack_/industry_."""
    name = path.name
    code = None
    for rx in (FILE_INDUSTRY_RE, IND_PACK_RE, STACK_INDUSTRY_RE, MGMT_FILE_RE):
        m = rx.search(name)
        if m:
            code = m.group(1).upper()
            break
    if code is None or code not in INDUSTRY_LETTERS:
        return 0
    d = load_json(path)
    if d is None:
        return 0
    title = (
        d.get("industry_name_ko")
        or d.get("industry_label_ko")
        or d.get("stack_id")
        or d.get("industry_name")
        or name
    )
    text = "\n".join(flatten_json(d))
    upsert_doc(
        conn,
        f"ref:{area}:{code}:{level}",
        path,
        code,
        area,
        level,
        title,
        text,
    )
    return 1


def extract_mgmt_split(conn, dir_path: Path) -> int:
    """ch1_mgmt_model/industries/industry_B_semiconductor/ → 5 sub-files."""
    m = MGMT_FILE_RE.search(dir_path.name)
    if not m:
        return 0
    code = m.group(1).upper()
    n = 0
    for f in sorted(dir_path.iterdir()):
        if not f.name.endswith(".json"):
            continue
        ms = MGMT_SPLIT_RE.match(f.name)
        level = ms.group(2) if ms else f.stem
        # map filename to clean level name
        level = level.replace("profiles_", "")
        d = load_json(f)
        if d is None:
            continue
        title = f"{code} mgmt {level}"
        text = "\n".join(flatten_json(d))
        upsert_doc(
            conn,
            f"ref:ch1_mgmt_model:{code}:{level}",
            f,
            code,
            "ch1_mgmt_model",
            level,
            title,
            text,
        )
        n += 1
    return n


def extract_card2_industry_map(conn, path: Path, area: str) -> int:
    """ch2/card2/{subindustry_bridge,quality_level_mapping}_v1_7.json — industries → sub-keys."""
    d = load_json(path)
    if not d:
        return 0
    n = 0
    industries = d.get("industries") or d.get("levels") or {}
    if not isinstance(industries, dict):
        return 0
    for code, body in industries.items():
        if code in INDUSTRY_LETTERS and isinstance(body, dict):
            # per industry → expand sub-keys as level
            sub = body.get("sub_industries") or body.get("mapping") or {}
            if isinstance(sub, dict) and sub:
                for sub_code, sub_body in sub.items():
                    text = "\n".join(flatten_json(sub_body))
                    upsert_doc(
                        conn,
                        f"ref:{area}:{code}:{sub_code}",
                        path,
                        code,
                        area,
                        sub_code,
                        f"{code}/{sub_code}",
                        text,
                    )
                    n += 1
            else:
                text = "\n".join(flatten_json(body))
                upsert_doc(
                    conn,
                    f"ref:{area}:{code}",
                    path,
                    code,
                    area,
                    "default",
                    f"{code} {area}",
                    text,
                )
                n += 1
        elif isinstance(body, dict):
            # non-industry top-level key (e.g. 'L0', 'L1' in quality_level_mapping)
            text = "\n".join(flatten_json(body))
            upsert_doc(
                conn,
                f"ref:{area}:_:{code}",
                path,
                None,
                area,
                code,
                f"{area} {code}",
                text,
            )
            n += 1
    return n


def extract_catalog(conn, path: Path, catalog_kind: str, key_field: str = "code") -> int:
    """Group 2 — register each catalog entry as a row."""
    d = load_json(path)
    if not d:
        return 0
    if isinstance(d, list):
        entries = d
    else:
        entries = d.get("entries") or d.get("systems") or d.get("items") or d
    if isinstance(d, dict) and isinstance(entries, dict) and entries is d:
        # whole-dict catalog with no obvious wrapper; treat each top-level k=v as entry
        entries = [{"code": k, "value": v} for k, v in d.items() if not k.startswith("_")]
    if isinstance(entries, dict):
        entries = list(entries.values())
    if not isinstance(entries, list):
        # register whole file as a single 'default' row under the catalog kind
        text = "\n".join(flatten_json(d))
        upsert_doc(
            conn,
            f"ref:catalog:{catalog_kind}",
            path,
            None,
            f"catalog:{catalog_kind}",
            "default",
            path.stem,
            text,
        )
        return 1
    n = 0
    for ent in entries:
        if not isinstance(ent, dict):
            continue
        key = (
            ent.get(key_field)
            or ent.get("code")
            or ent.get("id")
            or ent.get("system_code")
            or ent.get("name")
        )
        if not key:
            continue
        title = ent.get("name_ko") or ent.get("name") or ent.get("display") or str(key)
        text = "\n".join(flatten_json(ent))
        upsert_doc(
            conn,
            f"ref:catalog:{catalog_kind}:{key}",
            path,
            None,
            f"catalog:{catalog_kind}",
            str(key),
            str(title),
            text,
        )
        n += 1
    return n


def extract_generic_file(conn, path: Path, area: str) -> int:
    """Fallback: register file as a single doc with industry=None."""
    d = load_json(path)
    if d is None:
        return 0
    title = path.stem
    text = "\n".join(flatten_json(d))
    upsert_doc(
        conn,
        f"ref:{area}:{path.stem}",
        path,
        None,
        area,
        "default",
        title,
        text,
    )
    return 1


# ─── Dispatcher ───────────────────────────────────────────────────────────────


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    if parts & SKIP_DIRS:
        return True
    if path.suffix in SKIP_SUFFIXES:
        return True
    if path.name.startswith("."):
        return True
    return False


def dispatch(conn) -> dict[str, int]:
    counts: dict[str, int] = {}

    def bump(label: str, n: int):
        if n:
            counts[label] = counts.get(label, 0) + n

    # Root canonical files
    bump("rule_meta", extract_industry_master(conn, SOURCE_ROOT / "industry_master.json"))
    bump("exec_narrative", extract_industry_profile_text(conn, SOURCE_ROOT / "industry_profile_text.json"))
    bump(
        "catalog:system",
        extract_catalog(conn, SOURCE_ROOT / "system_catalog.json", "system", "system_code"),
    )
    bump(
        "catalog:scale",
        extract_catalog(conn, SOURCE_ROOT / "scale_master.json", "scale", "code"),
    )

    # step3
    step3 = SOURCE_ROOT / "step3" / "industry_scale_model_v1.json"
    if step3.exists():
        bump("step3_scale", extract_step3_scale(conn, step3))

    # ch1_industries/
    for f in sorted((SOURCE_ROOT / "ch1_industries").glob("*.json")):
        bump("ch1_industry_def", extract_per_industry_file(conn, f, "ch1_industry_def"))

    # ch1/industry_packs/
    pack_dir = SOURCE_ROOT / "ch1" / "industry_packs"
    if pack_dir.exists():
        for f in sorted(pack_dir.glob("*.json")):
            bump("ch1_pack", extract_per_industry_file(conn, f, "ch1_pack"))

    # ch1_mgmt_model/industries/
    mgmt_dir = SOURCE_ROOT / "ch1_mgmt_model" / "industries"
    if mgmt_dir.exists():
        for item in sorted(mgmt_dir.iterdir()):
            if item.is_dir():
                bump("ch1_mgmt_model", extract_mgmt_split(conn, item))
            elif item.suffix == ".json":
                bump("ch1_mgmt_model", extract_per_industry_file(conn, item, "ch1_mgmt_model"))

    # ch2/catalog/stack_library/
    stack_dir = SOURCE_ROOT / "ch2" / "catalog" / "stack_library"
    if stack_dir.exists():
        for f in sorted(stack_dir.glob("*.json")):
            bump("ch2_stack", extract_per_industry_file(conn, f, "ch2_stack"))

    # ch2/card2/
    card2_dir = SOURCE_ROOT / "ch2" / "card2"
    if card2_dir.exists():
        for f in sorted(card2_dir.glob("*.json")):
            bump("ch2_card2_bridge", extract_card2_industry_map(conn, f, "ch2_card2_bridge"))

    # ch2/catalog/*.json (cross-industry catalogs, excluding stack_library which we did)
    ch2cat = SOURCE_ROOT / "ch2" / "catalog"
    if ch2cat.exists():
        for f in sorted(ch2cat.glob("*.json")):
            kind = f"ch2_{f.stem}"
            bump(f"catalog:{kind}", extract_catalog(conn, f, kind))

    # ch1/catalog/
    for f in sorted((SOURCE_ROOT / "ch1" / "catalog").glob("*.json")):
        kind = f"ch1_{f.stem}"
        bump(f"catalog:{kind}", extract_catalog(conn, f, kind))

    # ch1/catalogs/
    for f in sorted((SOURCE_ROOT / "ch1" / "catalogs").glob("*.json")):
        kind = f"codes:{f.stem}"
        bump(f"catalog:{kind}", extract_catalog(conn, f, kind))

    # ch1/routing_packs/
    rp_dir = SOURCE_ROOT / "ch1" / "routing_packs"
    if rp_dir.exists():
        for f in sorted(rp_dir.glob("*.json")):
            bump("catalog:routing", extract_generic_file(conn, f, "catalog:routing"))

    # ch1/ch1_code_alias.json
    alias = SOURCE_ROOT / "ch1" / "ch1_code_alias.json"
    if alias.exists():
        bump("catalog:ch1_alias", extract_catalog(conn, alias, "ch1_alias"))

    # ch1_mgmt_model/management_common_schema.json
    mgmt_schema = SOURCE_ROOT / "ch1_mgmt_model" / "management_common_schema.json"
    if mgmt_schema.exists():
        bump("ch1_mgmt_schema", extract_generic_file(conn, mgmt_schema, "ch1_mgmt_schema"))

    # roi/
    roi = SOURCE_ROOT / "roi" / "roi_logic_catalog_v1.json"
    if roi.exists():
        bump("catalog:roi", extract_generic_file(conn, roi, "catalog:roi"))

    return counts


def rebuild_fts(conn):
    """V2.5.3 §15: dual-tokenizer 동기 (documents_fts + documents_fts_trigram)."""
    try:
        from .fts_sync import rebuild_all
    except ImportError:
        from src.ingest.fts_sync import rebuild_all
    return rebuild_all(conn)


def main():
    if not SOURCE_ROOT.exists():
        print(f"source not found: {SOURCE_ROOT}", file=sys.stderr)
        return 1
    print(f"source: {SOURCE_ROOT}")
    print(f"target: {DB_PATH}")
    conn = init_db()
    try:
        # Idempotent: clear reference lane before re-ingest.
        conn.execute("DELETE FROM documents WHERE lane = ?", (LANE,))
        counts = dispatch(conn)
        rebuild_fts(conn)
        conn.execute(
            "INSERT OR REPLACE INTO meta_kv (key, value) VALUES (?, ?)",
            ("last_ingest_reference_at", now_iso()),
        )
        conn.execute(
            "INSERT OR REPLACE INTO meta_kv (key, value) VALUES (?, ?)",
            ("source_root_reference", str(SOURCE_ROOT)),
        )
        conn.commit()
    finally:
        conn.close()

    total = sum(counts.values())
    print(f"\n{total} documents ingested into lane='{LANE}'")
    for label in sorted(counts):
        print(f"  {label:40s} {counts[label]:4d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
