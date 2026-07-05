"""dx_* → 진단툴 JSON 리빌드 (DIAGNOSIS_PACK_MGMT_TAB_DESIGN §4.5)."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import db, dx

BLOCKS = dx.BLOCKS


@dataclass
class ExportResult:
    files: dict[str, str] = field(default_factory=dict)
    paths: list[str] = field(default_factory=list)


def _labels_for(
    conn: sqlite3.Connection,
    entity_kind: str,
    entity_key: str,
) -> dict[str, str]:
    rows = conn.execute(
        "SELECT lang, label FROM dx_label WHERE entity_kind=? AND entity_key=?",
        (entity_kind, entity_key),
    ).fetchall()
    return {r["lang"]: r["label"] for r in rows if r["label"]}


def _profile_items_as_list(
    conn: sqlite3.Connection,
    profile_id: int,
    block: str,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT code, weight FROM dx_profile_item "
        "WHERE profile_id=? AND block=? ORDER BY ord, code",
        (profile_id, block),
    ).fetchall()
    out = []
    for row in rows:
        item: dict[str, Any] = {"code": row["code"]}
        if row["weight"] is not None:
            item["weight"] = row["weight"]
        out.append(item)
    return out


def _build_industry_pack(conn: sqlite3.Connection, industry_code: str) -> dict[str, Any]:
    ind = conn.execute(
        "SELECT * FROM dx_industry WHERE code=?", (industry_code,)
    ).fetchone()
    if not ind:
        return {}

    keys = ind.keys()
    labels = _labels_for(conn, "industry", industry_code)
    pack: dict[str, Any] = {
        "industry_code": f"IND_{industry_code}",
        "industry_label_ko": labels.get("ko"),
        "industry_label_zh": labels.get("zh"),
        "industry_message_theme": ind["message_theme"],
        "priority_axes": json.loads(ind["priority_axes_json"] or "[]"),
        "characteristics": json.loads(
            (ind["characteristics_json"] if "characteristics_json" in keys else None) or "[]"
        ),
    }

    default = conn.execute(
        "SELECT * FROM dx_profile WHERE industry_code=? AND scope='default'",
        (industry_code,),
    ).fetchone()
    if default:
        default_body: dict[str, Any] = {}
        if default["routing_code"]:
            default_body["routing"] = default["routing_code"]
        if default["flow_style"]:
            default_body["flow_style"] = default["flow_style"]
        if default["control_unit"]:
            default_body["control_unit"] = default["control_unit"]
        for block in BLOCKS:
            items = _profile_items_as_list(conn, default["id"], block)
            if items:
                default_body[block] = items
        pack["default_profile"] = default_body

    # 엔진은 분류(sub_industries)와 가중치(sub_profiles)를 별도 키로 읽는다.
    sub_taxonomy: list[dict[str, Any]] = []
    sub_profiles: dict[str, Any] = {}
    for sub in dx.list_sub_industries(conn, industry_code):
        canon = sub["canon_code"]
        sub_labels = _labels_for(conn, "sub_industry", canon)
        sub_taxonomy.append({
            "code": canon,
            "label_ko": sub_labels.get("ko"),
            "label_zh": sub_labels.get("zh"),
        })
        profile = conn.execute(
            "SELECT * FROM dx_profile WHERE industry_code=? AND scope=?",
            (industry_code, canon),
        ).fetchone()
        if profile:
            pbody: dict[str, Any] = {}
            if profile["routing_code"]:
                pbody["primary_routing"] = profile["routing_code"]
            if profile["flow_style"]:
                pbody["flow_style"] = profile["flow_style"]
            if profile["control_unit"]:
                pbody["control_unit"] = profile["control_unit"]
            for block in BLOCKS:
                items = _profile_items_as_list(conn, profile["id"], block)
                if items:
                    pbody[block] = items
            if pbody:
                sub_profiles[canon] = pbody

    if sub_taxonomy:
        pack["sub_industries"] = sub_taxonomy
    if sub_profiles:
        pack["sub_profiles"] = sub_profiles
    return pack


def _build_routing_pack(conn: sqlite3.Connection, routing_code: str) -> dict[str, Any]:
    row = conn.execute(
        "SELECT * FROM dx_routing_pack WHERE routing_code=?", (routing_code,)
    ).fetchone()
    if not row:
        return {}
    labels = _labels_for(conn, "routing", routing_code)
    body: dict[str, Any] = {
        "routing_code": routing_code,
        "routing_label_ko": labels.get("ko"),
        "routing_label_zh": labels.get("zh"),
        "flow_style": row["flow_style"],
        "control_unit": row["control_unit"],
        "priority_axes": json.loads(row["priority_axes_json"] or "[]"),
        "routing_theme": row["routing_theme"],
    }
    effects = dx.list_routing_effects(conn, routing_code)
    overlays = []
    adjustments = []
    for eff in effects:
        item = {"block": eff["block"], "code": eff["code"]}
        if eff["kind"] == "overlay":
            if eff["value"] is not None:
                item["boost"] = eff["value"]
            overlays.append(item)
        else:
            if eff["value"] is not None:
                item["weight"] = eff["value"]
            adjustments.append(item)
    if len(overlays) == 1:
        body["overlay"] = overlays[0]
    elif overlays:
        body["overlays"] = overlays
    if adjustments:
        body["adjustments"] = adjustments
    return body


def _build_catalog(conn: sqlite3.Connection, kind: str) -> dict[str, Any]:
    rows = conn.execute(
        "SELECT code, status FROM dx_code WHERE kind=? ORDER BY code", (kind,)
    ).fetchall()
    entries = []
    for row in rows:
        labels = _labels_for(conn, "code", f"{kind}:{row['code']}")
        entry: dict[str, Any] = {
            "code": row["code"],
            "status": row["status"],
            "label_ko": labels.get("ko"),
            "label_zh": labels.get("zh"),
            "label_en": labels.get("en"),
        }
        explain_row = conn.execute(
            "SELECT explain FROM dx_label WHERE entity_kind='code' "
            "AND entity_key=? AND lang='ko'",
            (f"{kind}:{row['code']}",),
        ).fetchone()
        if explain_row and explain_row["explain"]:
            entry["context_explain_ko"] = explain_row["explain"]
        entries.append(entry)
    return {"codes": entries}


def export_ch1(conn: sqlite3.Connection | None = None) -> ExportResult:
    """Ch1 IND_*/RT_*/catalogs JSON 재생성."""
    own = conn is None
    conn = conn or db.get_conn()
    result = ExportResult()
    try:
        for ind in dx.list_industries(conn):
            code = ind["code"]
            pack = _build_industry_pack(conn, code)
            if pack:
                slug = ind["slug"] if ("slug" in ind.keys() and ind["slug"]) else f"IND_{code}"
                rel = f"server/data/ch1/industry_packs/{slug}.json"
                text = json.dumps(pack, ensure_ascii=False, indent=2) + "\n"
                result.files[rel] = text
                result.paths.append(rel)

        for rp in dx.list_routing_packs(conn):
            routing_code = rp["routing_code"]
            pack = _build_routing_pack(conn, routing_code)
            if pack:
                rel = f"server/data/ch1/routing_packs/{routing_code}.json"
                text = json.dumps(pack, ensure_ascii=False, indent=2) + "\n"
                result.files[rel] = text
                result.paths.append(rel)

        kinds = conn.execute(
            "SELECT DISTINCT kind FROM dx_code ORDER BY kind"
        ).fetchall()
        for row in kinds:
            kind = row["kind"]
            catalog = _build_catalog(conn, kind)
            if catalog["codes"]:
                rel = f"server/data/ch1/catalogs/{kind}_codes.json"
                text = json.dumps(catalog, ensure_ascii=False, indent=2) + "\n"
                result.files[rel] = text
                result.paths.append(rel)
    finally:
        if own:
            conn.close()
    return result


def write_files(repo_root: Path, files: dict[str, str]) -> list[Path]:
    written: list[Path] = []
    for rel, content in files.items():
        path = repo_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written
