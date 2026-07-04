"""진단툴 팩 SoT DAL — dx_* 테이블 접근 (DIAGNOSIS_PACK_MGMT_TAB_DESIGN §3)."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from . import db

BLOCKS = ("mvp", "modules", "direction", "kpi")
QUESTIONS = ("Q2", "Q3", "Q4", "Q5_REC", "Q5_MGMT")
INDUSTRY_CODES = list("ABCDEFGHI")


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def clear_all(conn: sqlite3.Connection) -> None:
    """dx_* 전체 초기화 (재임포트용)."""
    tables = (
        "dx_apply_log", "dx_text", "dx_label", "dx_scoring_param",
        "dx_question_metric", "dx_code_alias", "dx_code",
        "dx_routing_effect", "dx_routing_pack",
        "dx_profile_item", "dx_profile",
        "dx_sub_bridge", "dx_sub_industry", "dx_industry", "dx_import",
    )
    for name in tables:
        conn.execute(f"DELETE FROM {name}")


@dataclass(frozen=True)
class ImportMeta:
    id: int
    source_branch: str | None
    source_commit: str | None
    imported_at: str
    note: str | None


def latest_import(conn: sqlite3.Connection | None = None) -> ImportMeta | None:
    own = conn is None
    conn = conn or db.get_conn()
    try:
        row = conn.execute(
            "SELECT id, source_branch, source_commit, imported_at, note "
            "FROM dx_import ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if not row:
            return None
        return ImportMeta(**dict(row))
    finally:
        if own:
            conn.close()


def record_import(
    *,
    source_branch: str | None,
    source_commit: str | None,
    note: str | None = None,
    conn: sqlite3.Connection | None = None,
) -> int:
    own = conn is None
    conn = conn or db.get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO dx_import(source_branch, source_commit, imported_at, note) "
            "VALUES (?, ?, ?, ?)",
            (source_branch, source_commit, _now_iso(), note),
        )
        return int(cur.lastrowid)
    finally:
        if own:
            conn.close()


def upsert_industry(
    conn: sqlite3.Connection,
    code: str,
    *,
    message_theme: str | None = None,
    priority_axes: list[str] | None = None,
    ord: int | None = None,
) -> None:
    conn.execute(
        "INSERT INTO dx_industry(code, message_theme, priority_axes_json, ord) "
        "VALUES (?, ?, ?, ?) "
        "ON CONFLICT(code) DO UPDATE SET "
        "message_theme=excluded.message_theme, "
        "priority_axes_json=excluded.priority_axes_json, ord=excluded.ord",
        (code, message_theme, json.dumps(priority_axes or [], ensure_ascii=False), ord),
    )


def upsert_sub_industry(
    conn: sqlite3.Connection,
    industry_code: str,
    canon_code: str,
    *,
    ord: int | None = None,
) -> int:
    conn.execute(
        "INSERT INTO dx_sub_industry(industry_code, canon_code, ord) "
        "VALUES (?, ?, ?) "
        "ON CONFLICT(canon_code) DO UPDATE SET industry_code=excluded.industry_code, ord=excluded.ord",
        (industry_code, canon_code, ord),
    )
    row = conn.execute(
        "SELECT id FROM dx_sub_industry WHERE canon_code=?", (canon_code,)
    ).fetchone()
    return int(row["id"])


def add_bridge(
    conn: sqlite3.Connection,
    sub_id: int,
    scheme: str,
    external_code: str,
) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO dx_sub_bridge(sub_id, scheme, external_code) VALUES (?, ?, ?)",
        (sub_id, scheme, external_code),
    )


def upsert_label(
    conn: sqlite3.Connection,
    entity_kind: str,
    entity_key: str,
    lang: str,
    label: str | None,
    explain: str | None = None,
) -> None:
    conn.execute(
        "INSERT INTO dx_label(entity_kind, entity_key, lang, label, explain) "
        "VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(entity_kind, entity_key, lang) DO UPDATE SET "
        "label=excluded.label, explain=excluded.explain",
        (entity_kind, entity_key, lang, label, explain),
    )


def upsert_code(
    conn: sqlite3.Connection,
    kind: str,
    code: str,
    status: str = "active",
) -> None:
    conn.execute(
        "INSERT INTO dx_code(kind, code, status) VALUES (?, ?, ?) "
        "ON CONFLICT(kind, code) DO UPDATE SET status=excluded.status",
        (kind, code, status),
    )


def upsert_code_alias(
    conn: sqlite3.Connection,
    kind: str,
    alias_code: str,
    canon_code: str,
) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO dx_code_alias(kind, alias_code, canon_code) "
        "VALUES (?, ?, ?)",
        (kind, alias_code, canon_code),
    )


def upsert_profile(
    conn: sqlite3.Connection,
    industry_code: str,
    scope: str,
    *,
    routing_code: str | None = None,
    flow_style: str | None = None,
    control_unit: str | None = None,
) -> int:
    conn.execute(
        "INSERT INTO dx_profile(industry_code, scope, routing_code, flow_style, control_unit) "
        "VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(industry_code, scope) DO UPDATE SET "
        "routing_code=excluded.routing_code, flow_style=excluded.flow_style, "
        "control_unit=excluded.control_unit",
        (industry_code, scope, routing_code, flow_style, control_unit),
    )
    row = conn.execute(
        "SELECT id FROM dx_profile WHERE industry_code=? AND scope=?",
        (industry_code, scope),
    ).fetchone()
    return int(row["id"])


def set_profile_items(
    conn: sqlite3.Connection,
    profile_id: int,
    block: str,
    items: list[tuple[str, float | None, int]],
) -> None:
    conn.execute(
        "DELETE FROM dx_profile_item WHERE profile_id=? AND block=?",
        (profile_id, block),
    )
    for ord_i, (code, weight, _) in enumerate(items):
        conn.execute(
            "INSERT INTO dx_profile_item(profile_id, block, code, weight, ord) "
            "VALUES (?, ?, ?, ?, ?)",
            (profile_id, block, code, weight, ord_i),
        )


def upsert_routing_pack(
    conn: sqlite3.Connection,
    routing_code: str,
    *,
    flow_style: str | None = None,
    control_unit: str | None = None,
    priority_axes: list[str] | None = None,
    routing_theme: str | None = None,
) -> None:
    conn.execute(
        "INSERT INTO dx_routing_pack(routing_code, flow_style, control_unit, "
        "priority_axes_json, routing_theme) VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(routing_code) DO UPDATE SET "
        "flow_style=excluded.flow_style, control_unit=excluded.control_unit, "
        "priority_axes_json=excluded.priority_axes_json, routing_theme=excluded.routing_theme",
        (
            routing_code,
            flow_style,
            control_unit,
            json.dumps(priority_axes or [], ensure_ascii=False),
            routing_theme,
        ),
    )


def set_routing_effects(
    conn: sqlite3.Connection,
    routing_code: str,
    effects: list[tuple[str, str, str, float | None]],
) -> None:
    conn.execute("DELETE FROM dx_routing_effect WHERE routing_code=?", (routing_code,))
    for kind, block, code, value in effects:
        conn.execute(
            "INSERT INTO dx_routing_effect(routing_code, kind, block, code, value) "
            "VALUES (?, ?, ?, ?, ?)",
            (routing_code, kind, block, code, value),
        )


def upsert_question_metric(
    conn: sqlite3.Connection,
    sub_id: int,
    question: str,
    metric_key: str,
    value: float | None,
    notes: str | None = None,
) -> None:
    conn.execute(
        "INSERT INTO dx_question_metric(sub_id, question, metric_key, value, notes) "
        "VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(sub_id, question, metric_key) DO UPDATE SET "
        "value=excluded.value, notes=excluded.notes",
        (sub_id, question, metric_key, value, notes),
    )


def sub_id_by_canon(conn: sqlite3.Connection, canon_code: str) -> int | None:
    row = conn.execute(
        "SELECT id FROM dx_sub_industry WHERE canon_code=?", (canon_code,)
    ).fetchone()
    return int(row["id"]) if row else None


def sub_id_by_bridge(conn: sqlite3.Connection, scheme: str, external_code: str) -> int | None:
    row = conn.execute(
        "SELECT sub_id FROM dx_sub_bridge WHERE scheme=? AND external_code=? LIMIT 1",
        (scheme, external_code),
    ).fetchone()
    return int(row["sub_id"]) if row else None


def resolve_sub_id(conn: sqlite3.Connection, external_code: str, scheme: str | None = None) -> int | None:
    """브릿지·정본·별칭 순으로 하위산업 id 해석."""
    if scheme:
        sub_id = sub_id_by_bridge(conn, scheme, external_code)
        if sub_id is not None:
            return sub_id
    sub_id = sub_id_by_canon(conn, external_code)
    if sub_id is not None:
        return sub_id
    alias = conn.execute(
        "SELECT canon_code FROM dx_code_alias WHERE kind='sub_industry' AND alias_code=?",
        (external_code,),
    ).fetchone()
    if alias:
        return sub_id_by_canon(conn, alias["canon_code"])
    return None


def list_industries(conn: sqlite3.Connection | None = None) -> list[sqlite3.Row]:
    own = conn is None
    conn = conn or db.get_conn()
    try:
        return conn.execute(
            "SELECT * FROM dx_industry ORDER BY ord, code"
        ).fetchall()
    finally:
        if own:
            conn.close()


def list_sub_industries(
    conn: sqlite3.Connection | None = None,
    industry_code: str | None = None,
) -> list[sqlite3.Row]:
    own = conn is None
    conn = conn or db.get_conn()
    try:
        if industry_code:
            return conn.execute(
                "SELECT s.*, "
                "(SELECT label FROM dx_label WHERE entity_kind='sub_industry' "
                " AND entity_key=s.canon_code AND lang='ko') AS label_ko "
                "FROM dx_sub_industry s WHERE industry_code=? ORDER BY ord, canon_code",
                (industry_code,),
            ).fetchall()
        return conn.execute(
            "SELECT s.*, "
            "(SELECT label FROM dx_label WHERE entity_kind='sub_industry' "
            " AND entity_key=s.canon_code AND lang='ko') AS label_ko "
            "FROM dx_sub_industry s ORDER BY industry_code, ord, canon_code"
        ).fetchall()
    finally:
        if own:
            conn.close()


def list_sub_bridges(conn: sqlite3.Connection, sub_id: int) -> dict[str, list[str]]:
    rows = conn.execute(
        "SELECT scheme, external_code FROM dx_sub_bridge WHERE sub_id=? ORDER BY scheme",
        (sub_id,),
    ).fetchall()
    out: dict[str, list[str]] = {}
    for row in rows:
        out.setdefault(row["scheme"], []).append(row["external_code"])
    return out


def list_codes(conn: sqlite3.Connection, kind: str | None = None) -> list[sqlite3.Row]:
    if kind:
        return conn.execute(
            "SELECT c.*, "
            "(SELECT label FROM dx_label WHERE entity_kind='code' "
            " AND entity_key=c.kind||':'||c.code AND lang='ko') AS label_ko "
            "FROM dx_code c WHERE kind=? ORDER BY code",
            (kind,),
        ).fetchall()
    return conn.execute(
        "SELECT c.*, "
        "(SELECT label FROM dx_label WHERE entity_kind='code' "
        " AND entity_key=c.kind||':'||c.code AND lang='ko') AS label_ko "
        "FROM dx_code c ORDER BY kind, code"
    ).fetchall()


def list_profiles(
    conn: sqlite3.Connection,
    industry_code: str,
) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM dx_profile WHERE industry_code=? ORDER BY scope",
        (industry_code,),
    ).fetchall()


def list_profile_items(conn: sqlite3.Connection, profile_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM dx_profile_item WHERE profile_id=? ORDER BY block, ord, code",
        (profile_id,),
    ).fetchall()


def list_routing_packs(conn: sqlite3.Connection | None = None) -> list[sqlite3.Row]:
    own = conn is None
    conn = conn or db.get_conn()
    try:
        return conn.execute(
            "SELECT * FROM dx_routing_pack ORDER BY routing_code"
        ).fetchall()
    finally:
        if own:
            conn.close()


def list_routing_effects(conn: sqlite3.Connection, routing_code: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM dx_routing_effect WHERE routing_code=? ORDER BY kind, block, code",
        (routing_code,),
    ).fetchall()


def coverage_matrix(conn: sqlite3.Connection | None = None) -> list[dict[str, Any]]:
    """산업×질문 커버리지 집계."""
    own = conn is None
    conn = conn or db.get_conn()
    try:
        rows = conn.execute(
            """
            SELECT industry_code, question,
                   SUM(has_metric) AS filled,
                   COUNT(*) AS total
            FROM v_dx_coverage
            GROUP BY industry_code, question
            ORDER BY industry_code, question
            """
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        if own:
            conn.close()


def coverage_gaps(conn: sqlite3.Connection | None = None) -> list[sqlite3.Row]:
    own = conn is None
    conn = conn or db.get_conn()
    try:
        return conn.execute(
            "SELECT * FROM v_dx_coverage WHERE has_metric=0 ORDER BY industry_code, question, canon_code"
        ).fetchall()
    finally:
        if own:
            conn.close()


def count_rows(conn: sqlite3.Connection | None = None) -> dict[str, int]:
    own = conn is None
    conn = conn or db.get_conn()
    try:
        counts = {}
        for table in (
            "dx_industry", "dx_sub_industry", "dx_sub_bridge", "dx_profile",
            "dx_profile_item", "dx_routing_pack", "dx_code", "dx_question_metric",
        ):
            row = conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()
            counts[table] = int(row["n"])
        return counts
    finally:
        if own:
            conn.close()


def save_grid_rows(
    conn: sqlite3.Connection,
    table: str,
    rows: list[dict[str, Any]],
    *,
    key_cols: list[str],
) -> None:
    """범용 그리드 저장 — 지원 테이블만."""
    allowed = {
        "dx_sub_industry": ("id", ["industry_code", "canon_code", "ord"]),
        "dx_code": (None, ["kind", "code", "status"]),
        "dx_profile_item": (None, ["profile_id", "block", "code", "weight", "ord"]),
    }
    if table not in allowed:
        raise ValueError(f"unsupported grid table: {table}")
    id_col, cols = allowed[table]
    for row in rows:
        if id_col and not row.get(id_col):
            placeholders = ", ".join("?" * len(cols))
            conn.execute(
                f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})",
                [row.get(c) for c in cols],
            )
        elif table == "dx_sub_industry" and row.get("id"):
            conn.execute(
                "UPDATE dx_sub_industry SET industry_code=?, canon_code=?, ord=? WHERE id=?",
                (row["industry_code"], row["canon_code"], row.get("ord"), row["id"]),
            )
        elif table == "dx_code":
            upsert_code(conn, row["kind"], row["code"], row.get("status") or "active")
        elif table == "dx_profile_item":
            conn.execute(
                "INSERT INTO dx_profile_item(profile_id, block, code, weight, ord) "
                "VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT(profile_id, block, code) DO UPDATE SET "
                "weight=excluded.weight, ord=excluded.ord",
                (
                    row["profile_id"], row["block"], row["code"],
                    row.get("weight"), row.get("ord"),
                ),
            )
