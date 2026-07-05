"""dx_* → 진단툴 JSON 리빌드 (DIAGNOSIS_PACK_MGMT_TAB_DESIGN §4.5)."""
from __future__ import annotations

import copy
import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import db, dx

BLOCKS = dx.BLOCKS

# 블록 → 원본 파일에서 쓰는 키 후보(우선순위). overlay 시 원본 키 이름 보존.
_ORIG_BLOCK_KEYS = {
    "mvp": ("mvp_functions", "mvp"),
    "modules": ("core_modules", "modules"),
    "direction": ("smart_directions", "direction", "directions"),
    "kpi": ("kpi_keywords", "kpi"),
}
_BLOCK_TO_BOOST = {"mvp": "mvp_boost", "modules": "module_boost",
                   "direction": "direction_boost", "kpi": "kpi_boost"}


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


# ── overlay(원본 위에 관리 필드만 덮어쓰기) 헬퍼 ─────────────────────────────
def _profile_pairs(conn: sqlite3.Connection, profile_id: int, block: str) -> list[tuple[str, float | None]]:
    rows = conn.execute(
        "SELECT code, weight FROM dx_profile_item WHERE profile_id=? AND block=? ORDER BY ord, code",
        (profile_id, block),
    ).fetchall()
    return [(r["code"], r["weight"]) for r in rows]


def _find_block_key(profile: dict[str, Any], block: str) -> str:
    for k in _ORIG_BLOCK_KEYS.get(block, (block,)):
        if k in profile:
            return k
    return _ORIG_BLOCK_KEYS.get(block, (block,))[0]


def _reshape_block(original_value: Any, pairs: list[tuple[str, float | None]]) -> Any:
    """DB (code,weight) 리스트를 원본 블록과 같은 형태로 재구성 → 무변경 시 diff 0."""
    if isinstance(original_value, list):
        if original_value and isinstance(original_value[0], dict):
            wkey = "base_weight" if any(
                isinstance(x, dict) and "base_weight" in x for x in original_value
            ) else "weight"
            out = []
            for c, w in pairs:
                d: dict[str, Any] = {"code": c}
                if w is not None:
                    d[wkey] = w
                out.append(d)
            return out
        return [c for c, _ in pairs]  # list[str]
    if isinstance(original_value, dict):
        return {c: (w if w is not None else 1.0) for c, w in pairs}
    # 원본에 없던 블록
    if any(w is not None for _, w in pairs):
        return [({"code": c, "weight": w} if w is not None else {"code": c}) for c, w in pairs]
    return [c for c, _ in pairs]


def _patch_profile_blocks(conn: sqlite3.Connection, profile_id: int, target: dict[str, Any]) -> None:
    for block in BLOCKS:
        pairs = _profile_pairs(conn, profile_id, block)
        if not pairs:
            continue  # DB에 없으면 원본 보존(비우지 않음)
        key = _find_block_key(target, block)
        target[key] = _reshape_block(target.get(key), pairs)


def _set_if(d: dict[str, Any], key: str, value: Any) -> None:
    if value is not None and value != "":
        d[key] = value


def _overlay_industry_pack(conn: sqlite3.Connection, industry_code: str, original: dict[str, Any]) -> dict[str, Any]:
    pack = copy.deepcopy(original)
    labels = _labels_for(conn, "industry", industry_code)
    _set_if(pack, "industry_label_ko", labels.get("ko"))
    _set_if(pack, "industry_label_zh", labels.get("zh"))

    ind = conn.execute("SELECT * FROM dx_industry WHERE code=?", (industry_code,)).fetchone()
    if ind:
        keys = ind.keys()
        _set_if(pack, "industry_message_theme", ind["message_theme"])
        axes = json.loads(ind["priority_axes_json"] or "[]")
        if axes:
            pack["priority_axes"] = axes
        chars = json.loads((ind["characteristics_json"] if "characteristics_json" in keys else None) or "[]")
        if chars:
            pack["characteristics"] = chars

    default = conn.execute(
        "SELECT * FROM dx_profile WHERE industry_code=? AND scope='default'", (industry_code,)
    ).fetchone()
    if default and isinstance(pack.get("default_profile"), dict):
        dp = pack["default_profile"]
        _set_if(dp, "routing", default["routing_code"])
        _set_if(dp, "flow_style", default["flow_style"])
        _set_if(dp, "control_unit", default["control_unit"])
        _patch_profile_blocks(conn, default["id"], dp)

    subp = pack.get("sub_profiles")
    if isinstance(subp, dict):
        for canon, body in subp.items():
            if not isinstance(body, dict):
                continue
            prof = conn.execute(
                "SELECT * FROM dx_profile WHERE industry_code=? AND scope=?", (industry_code, canon)
            ).fetchone()
            if prof:
                _set_if(body, "primary_routing", prof["routing_code"])
                _patch_profile_blocks(conn, prof["id"], body)

    # 하위산업 분류 라벨 patch (구조 보존)
    subs = pack.get("sub_industries")
    if isinstance(subs, list):
        for item in subs:
            if isinstance(item, dict) and item.get("code"):
                sl = _labels_for(conn, "sub_industry", item["code"])
                _set_if(item, "label_ko", sl.get("ko"))
                _set_if(item, "label_zh", sl.get("zh"))
    return pack


def _order_like(codes: list[str], original: list[str]) -> list[str]:
    """codes(집합)를 original 순서에 맞춰 정렬 — 무변경 시 순서 diff 방지. 신규는 뒤에 추가."""
    cset = set(codes)
    seen: set[str] = set()
    out: list[str] = []
    for c in original:
        if c in cset and c not in seen:
            out.append(c)
            seen.add(c)
    for c in codes:
        if c not in seen:
            out.append(c)
            seen.add(c)
    return out


def _overlay_routing_pack(conn: sqlite3.Connection, routing_code: str, original: dict[str, Any]) -> dict[str, Any]:
    pack = copy.deepcopy(original)
    labels = _labels_for(conn, "routing", routing_code)
    _set_if(pack, "routing_label_ko", labels.get("ko"))
    _set_if(pack, "routing_label_zh", labels.get("zh"))
    ov_codes: dict[str, list[str]] = {b: [] for b in BLOCKS}
    for e in dx.list_routing_effects(conn, routing_code):
        if e["kind"] == "overlay":
            ov_codes.setdefault(e["block"], []).append(e["code"])
    if isinstance(pack.get("overlay"), dict):
        for block, boost_key in _BLOCK_TO_BOOST.items():
            if boost_key in pack["overlay"]:
                orig_list = pack["overlay"][boost_key]
                orig_list = orig_list if isinstance(orig_list, list) else []
                pack["overlay"][boost_key] = _order_like(ov_codes.get(block, []), orig_list)
    return pack


def _overlay_catalog(conn: sqlite3.Connection, kind: str, original: Any) -> Any:
    """언어/설명은 원본 보존, DB가 관리하는 status 만 patch."""
    pack = copy.deepcopy(original)
    db_status = {
        r["code"]: r["status"]
        for r in conn.execute("SELECT code, status FROM dx_code WHERE kind=?", (kind,)).fetchall()
    }
    if isinstance(pack, list):
        entries = pack
    elif isinstance(pack, dict):
        entries = pack.get("codes") or pack.get("entries") or []
    else:
        entries = []
    if isinstance(entries, list):
        for e in entries:
            if isinstance(e, dict) and e.get("code") in db_status and "status" in e:
                e["status"] = db_status[e["code"]]
    return pack


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


def _load_original(base_root: Path | None, rel: str) -> Any | None:
    if base_root is None:
        return None
    p = base_root / rel
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def export_ch1(
    conn: sqlite3.Connection | None = None,
    *,
    base_root: Path | None = None,
) -> ExportResult:
    """Ch1 IND_*/RT_*/catalogs JSON 리빌드.

    base_root 지정 시 **overlay 모드**: 원본 파일 위에 DB 관리 필드만 덮어쓰고,
    내용이 실제로 바뀐 파일만 내보낸다(부수 필드·키·포맷 보존 → diff 최소화).
    base_root=None 이면 DB에서 처음부터 재구성(from-scratch).
    """
    own = conn is None
    conn = conn or db.get_conn()
    result = ExportResult()

    def _emit(rel: str, built: Any) -> None:
        if not built:
            return
        if base_root is not None:
            original = _load_original(base_root, rel)
            if original is not None and built == original:
                return  # 변경 없음 → 스킵(diff 0)
        result.files[rel] = json.dumps(built, ensure_ascii=False, indent=2) + "\n"
        result.paths.append(rel)

    try:
        for ind in dx.list_industries(conn):
            code = ind["code"]
            slug = ind["slug"] if ("slug" in ind.keys() and ind["slug"]) else f"IND_{code}"
            rel = f"server/data/ch1/industry_packs/{slug}.json"
            original = _load_original(base_root, rel)
            if original is not None:
                built = _overlay_industry_pack(conn, code, original)
            else:
                built = _build_industry_pack(conn, code)
            _emit(rel, built)

        for rp in dx.list_routing_packs(conn):
            routing_code = rp["routing_code"]
            rel = f"server/data/ch1/routing_packs/{routing_code}.json"
            original = _load_original(base_root, rel)
            if original is not None:
                built = _overlay_routing_pack(conn, routing_code, original)
            else:
                built = _build_routing_pack(conn, routing_code)
            _emit(rel, built)

        kinds = conn.execute("SELECT DISTINCT kind FROM dx_code ORDER BY kind").fetchall()
        for row in kinds:
            kind = row["kind"]
            rel = f"server/data/ch1/catalogs/{kind}_codes.json"
            original = _load_original(base_root, rel)
            if original is not None:
                built = _overlay_catalog(conn, kind, original)
            else:
                built = _build_catalog(conn, kind)
                if not built.get("codes"):
                    built = None
            _emit(rel, built)
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
