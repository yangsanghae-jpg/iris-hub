"""진단툴 JSON → dx_* 임포터 (DIAGNOSIS_PACK_MGMT_TAB_DESIGN §4.1)."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.diagnosis_git import DiagnosisRepo, resolve_diagnosis_repo

from . import db, dx

IND_PACK_RE = re.compile(r"^IND_([A-I])\.json$", re.IGNORECASE)
BLOCKS = dx.BLOCKS


@dataclass
class ImportResult:
    source_root: Path
    branch: str | None = None
    commit: str | None = None
    industries: int = 0
    sub_industries: int = 0
    routing_packs: int = 0
    codes: int = 0
    bridges: int = 0
    question_metrics: int = 0
    warnings: list[str] = field(default_factory=list)


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_entries(body: Any, key_field: str = "code") -> list[dict[str, Any]]:
    if body is None:
        return []
    if isinstance(body, list):
        return [x for x in body if isinstance(x, dict)]
    if isinstance(body, dict):
        if "codes" in body and isinstance(body["codes"], list):
            return [x for x in body["codes"] if isinstance(x, dict)]
        if "entries" in body and isinstance(body["entries"], list):
            return [x for x in body["entries"] if isinstance(x, dict)]
        if key_field in body and isinstance(body[key_field], str):
            return [body]
        # dict keyed by code
        out = []
        for k, v in body.items():
            if isinstance(v, dict):
                entry = dict(v)
                entry.setdefault(key_field, k)
                out.append(entry)
        return out
    return []


def _profile_block_items(block_data: Any) -> list[tuple[str, float | None]]:
    items: list[tuple[str, float | None]] = []
    if isinstance(block_data, list):
        for item in block_data:
            if isinstance(item, str):
                items.append((item, None))
            elif isinstance(item, dict):
                code = item.get("code") or item.get("system_code") or item.get("mvp_code")
                if code:
                    w = item.get("weight")
                    items.append((str(code), float(w) if w is not None else None))
    elif isinstance(block_data, dict):
        for code, val in block_data.items():
            if isinstance(val, (int, float)):
                items.append((str(code), float(val)))
            elif isinstance(val, dict):
                w = val.get("weight")
                items.append((str(code), float(w) if w is not None else None))
            else:
                items.append((str(code), None))
    return items


def _import_profile_blocks(
    conn,
    profile_id: int,
    source: dict[str, Any],
) -> None:
    for block in BLOCKS:
        block_data = source.get(block) or source.get(f"{block}_codes") or source.get(f"{block}_items")
        if block_data is None:
            continue
        items = _profile_block_items(block_data)
        dx.set_profile_items(
            conn, profile_id, block,
            [(code, weight, i) for i, (code, weight) in enumerate(items)],
        )


def _import_industry_pack(conn, path: Path, result: ImportResult) -> None:
    body = _load_json(path)
    if not isinstance(body, dict):
        result.warnings.append(f"skip invalid pack: {path.name}")
        return

    m = IND_PACK_RE.match(path.name)
    industry_code = (body.get("industry_code") or (m.group(1).upper() if m else None) or "").strip()
    if not industry_code:
        result.warnings.append(f"skip pack without industry_code: {path.name}")
        return

    priority_axes = body.get("priority_axes") or body.get("priority_axis") or []
    if isinstance(priority_axes, str):
        priority_axes = [priority_axes]

    dx.upsert_industry(
        conn,
        industry_code,
        message_theme=body.get("message_theme"),
        priority_axes=list(priority_axes),
        ord=INDUSTRY_ORD.get(industry_code),
    )
    result.industries += 1

    for lang_key, lang in (("industry_label_ko", "ko"), ("industry_label_zh", "zh")):
        if body.get(lang_key):
            dx.upsert_label(conn, "industry", industry_code, lang, body[lang_key])

    default_src = body.get("default_profile") or body
    profile_id = dx.upsert_profile(
        conn,
        industry_code,
        "default",
        routing_code=default_src.get("routing_code") or body.get("routing_code"),
        flow_style=default_src.get("flow_style") or body.get("flow_style"),
        control_unit=default_src.get("control_unit") or body.get("control_unit"),
    )
    _import_profile_blocks(conn, profile_id, default_src)

    subs = body.get("sub_industries") or body.get("sub_industry") or {}
    sub_entries: list[tuple[str, dict]] = []
    if isinstance(subs, dict):
        sub_entries = [(k, v if isinstance(v, dict) else {}) for k, v in subs.items()]
    elif isinstance(subs, list):
        for item in subs:
            if isinstance(item, dict):
                code = item.get("code") or item.get("sub_industry_code")
                if code:
                    sub_entries.append((str(code), item))

    for ord_i, (sub_code, sub_body) in enumerate(sub_entries):
        sub_id = dx.upsert_sub_industry(conn, industry_code, sub_code, ord=ord_i)
        result.sub_industries += 1
        dx.add_bridge(conn, sub_id, "ch1name", sub_code)

        for lang_key, lang in (("label_ko", "ko"), ("label_zh", "zh")):
            label = sub_body.get(lang_key) or sub_body.get(f"sub_{lang_key}")
            if label:
                dx.upsert_label(conn, "sub_industry", sub_code, lang, label)

        sub_profile_id = dx.upsert_profile(
            conn,
            industry_code,
            sub_code,
            routing_code=sub_body.get("routing_code") or default_src.get("routing_code"),
            flow_style=sub_body.get("flow_style"),
            control_unit=sub_body.get("control_unit"),
        )
        _import_profile_blocks(conn, sub_profile_id, sub_body)


def _catalog_kind_from_filename(name: str) -> str:
    stem = Path(name).stem
    for suffix in ("_codes", "_catalog"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
    return stem.replace("ch1_", "")


def _import_catalog_file(conn, path: Path, result: ImportResult) -> None:
    body = _load_json(path)
    kind = _catalog_kind_from_filename(path.name)
    entries = _iter_entries(body)
    for entry in entries:
        code = entry.get("code") or entry.get("system_code") or entry.get("mvp_code")
        if not code:
            continue
        status = entry.get("status") or "active"
        dx.upsert_code(conn, kind, str(code), status)
        result.codes += 1
        label_key = f"code:{kind}:{code}"
        for lang_key, lang in (
            ("label_ko", "ko"), ("label_zh", "zh"), ("label_en", "en"),
        ):
            if entry.get(lang_key):
                dx.upsert_label(conn, "code", f"{kind}:{code}", lang, entry[lang_key])
        explain = entry.get("context_explain_ko") or entry.get("context_explain")
        if explain:
            dx.upsert_label(conn, "code", f"{kind}:{code}", "ko", entry.get("label_ko"), explain)


def _import_routing_pack(conn, path: Path, result: ImportResult) -> None:
    body = _load_json(path)
    if not isinstance(body, dict):
        return
    routing_code = body.get("routing_code") or path.stem
    priority_axes = body.get("priority_axes") or body.get("axes") or []
    if isinstance(priority_axes, str):
        priority_axes = [priority_axes]

    dx.upsert_routing_pack(
        conn,
        routing_code,
        flow_style=body.get("flow_style"),
        control_unit=body.get("control_unit"),
        priority_axes=list(priority_axes) if isinstance(priority_axes, list) else [],
        routing_theme=body.get("routing_theme"),
    )
    for lang_key, lang in (("routing_label_ko", "ko"), ("routing_label_zh", "zh")):
        if body.get(lang_key):
            dx.upsert_label(conn, "routing", routing_code, lang, body[lang_key])
    if body.get("description"):
        dx.upsert_label(conn, "routing", routing_code, "ko", body.get("routing_label_ko"), body["description"])

    effects: list[tuple[str, str, str, float | None]] = []
    overlay = body.get("overlay") or body.get("overlays")
    if isinstance(overlay, dict):
        block = overlay.get("block") or "mvp"
        code = overlay.get("code")
        if code:
            boost = overlay.get("boost")
            effects.append(("overlay", block, str(code), float(boost) if boost is not None else None))
    elif isinstance(overlay, list):
        for ov in overlay:
            if isinstance(ov, dict) and ov.get("code"):
                effects.append((
                    "overlay",
                    ov.get("block") or "mvp",
                    str(ov["code"]),
                    float(ov["boost"]) if ov.get("boost") is not None else None,
                ))

    adjustments = body.get("adjustments") or body.get("adjustment") or []
    if isinstance(adjustments, dict):
        adjustments = [adjustments]
    for adj in adjustments or []:
        if not isinstance(adj, dict):
            continue
        code = adj.get("code")
        if not code:
            continue
        w = adj.get("weight")
        effects.append((
            "adjustment",
            adj.get("block") or "mvp",
            str(code),
            float(w) if w is not None else None,
        ))

    dx.set_routing_effects(conn, routing_code, effects)
    result.routing_packs += 1


def _import_aliases(conn, path: Path, kind: str, result: ImportResult) -> None:
    body = _load_json(path)
    if not isinstance(body, dict):
        return
    mapping = body.get("aliases") or body.get("mapping") or body
    if not isinstance(mapping, dict):
        return
    for alias, canon in mapping.items():
        if isinstance(canon, list):
            canon = canon[0] if canon else alias
        dx.upsert_code_alias(conn, kind, str(alias), str(canon))


def _import_sub_bridge_catalog(conn, data_root: Path, result: ImportResult) -> None:
    path = data_root / "ch1" / "catalogs" / "sub_industry_codes.json"
    body = _load_json(path)
    entries = _iter_entries(body, "sub_industry_code")
    for entry in entries:
        ext = entry.get("sub_industry_code") or entry.get("code")
        canon = entry.get("canon_code") or entry.get("ch1_name") or entry.get("name_code")
        if not ext:
            continue
        sub_id = dx.sub_id_by_canon(conn, str(canon)) if canon else None
        if sub_id is None and canon:
            # orphan SUB entry
            result.warnings.append(f"SUB bridge orphan: {ext} → {canon}")
            continue
        if sub_id is None:
            continue
        dx.add_bridge(conn, sub_id, "SUB", str(ext))
        result.bridges += 1


def _flatten_metrics(obj: Any, prefix: str = "") -> list[tuple[str, float]]:
    out: list[tuple[str, float]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                out.append((key, float(v)))
            elif isinstance(v, dict):
                out.extend(_flatten_metrics(v, key))
    return out


def _import_step_profiles(
    conn,
    path: Path,
    question: str,
    scheme: str,
    profiles_key: str,
    result: ImportResult,
) -> None:
    body = _load_json(path)
    if not isinstance(body, dict):
        return
    profiles = body.get(profiles_key) or body.get("subindustry_profiles") or {}
    if not isinstance(profiles, dict):
        return
    for ext_code, profile in profiles.items():
        sub_id = dx.resolve_sub_id(conn, str(ext_code), scheme)
        if sub_id is None:
            continue
        dx.add_bridge(conn, sub_id, scheme, str(ext_code))
        result.bridges += 1
        metrics = _flatten_metrics(profile if isinstance(profile, dict) else {})
        for metric_key, value in metrics[:50]:
            dx.upsert_question_metric(conn, sub_id, question, metric_key, value)
            result.question_metrics += 1


def _import_q5_management(conn, data_root: Path, result: ImportResult) -> None:
    path = data_root / "step5_2" / "management_analysis_v3.json"
    body = _load_json(path)
    if not isinstance(body, dict):
        return
    overrides = body.get("subindustry_overrides") or body.get("overrides") or {}
    if not isinstance(overrides, dict):
        return
    for ext_code, profile in overrides.items():
        sub_id = dx.resolve_sub_id(conn, str(ext_code), "step5name")
        if sub_id is None:
            continue
        dx.add_bridge(conn, sub_id, "step5name", str(ext_code))
        metrics = _flatten_metrics(profile if isinstance(profile, dict) else {})
        for metric_key, value in metrics[:50]:
            dx.upsert_question_metric(conn, sub_id, "Q5_MGMT", metric_key, value)
            result.question_metrics += 1


INDUSTRY_ORD = {code: i for i, code in enumerate(dx.INDUSTRY_CODES)}


def import_from_path(
    data_root: Path,
    *,
    branch: str | None = None,
    commit: str | None = None,
    note: str | None = None,
) -> ImportResult:
    """server/data 경로에서 dx_* 재적재 (멱등)."""
    data_root = data_root.resolve()
    result = ImportResult(source_root=data_root, branch=branch, commit=commit)

    conn = db.get_conn()
    try:
        db.ensure_schema(conn)
        conn.execute("BEGIN")
        dx.clear_all(conn)

        pack_dir = data_root / "ch1" / "industry_packs"
        if pack_dir.is_dir():
            for path in sorted(pack_dir.glob("IND_*.json")):
                _import_industry_pack(conn, path, result)

        rp_dir = data_root / "ch1" / "routing_packs"
        if rp_dir.is_dir():
            for path in sorted(rp_dir.glob("*.json")):
                _import_routing_pack(conn, path, result)

        for catalog_dir in (
            data_root / "ch1" / "catalogs",
            data_root / "ch1" / "catalog",
        ):
            if catalog_dir.is_dir():
                for path in sorted(catalog_dir.glob("*.json")):
                    _import_catalog_file(conn, path, result)

        alias = data_root / "ch1" / "ch1_code_alias.json"
        if alias.exists():
            _import_aliases(conn, alias, "ch1", result)
        sub_alias = data_root / "ch1" / "sub_industry_aliases.json"
        if sub_alias.exists():
            _import_aliases(conn, sub_alias, "sub_industry", result)

        _import_sub_bridge_catalog(conn, data_root, result)

        step2 = data_root / "step2" / "routing_product_nature_v3.json"
        if step2.exists():
            _import_step_profiles(conn, step2, "Q2", "A01", "subindustry_profiles", result)
        step3 = data_root / "step3" / "scale_profile_v3.json"
        if step3.exists():
            _import_step_profiles(conn, step3, "Q3", "A01", "subindustry_profiles", result)
        step4 = data_root / "step4" / "automation_profile_v3.json"
        if step4.exists():
            _import_step_profiles(conn, step4, "Q4", "A01", "subindustry_profiles", result)
        q5 = data_root / "q5" / "recommendation_by_subindustry_v1.json"
        if q5.exists():
            _import_step_profiles(conn, q5, "Q5_REC", "A01", "subindustry_profiles", result)

        _import_q5_management(conn, data_root, result)

        dx.record_import(
            conn=conn,
            source_branch=branch,
            source_commit=commit,
            note=note or f"import from {data_root}",
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return result


def import_from_repo(repo: DiagnosisRepo | None = None) -> ImportResult:
    repo = repo or resolve_diagnosis_repo()
    if repo is None:
        raise FileNotFoundError(
            "diagnosis-tool clone 없음 — DIAGNOSIS_TOOL_GIT 환경변수 또는 0Dev/diagnosis-tool clone 필요"
        )
    data_root = repo.root / "server" / "data"
    if not data_root.is_dir():
        raise FileNotFoundError(f"data root 없음: {data_root}")
    return import_from_path(
        data_root,
        branch=repo.branch,
        commit=repo.head,
        note="auto import from diagnosis-tool clone",
    )


def resolve_data_root() -> Path | None:
    repo = resolve_diagnosis_repo()
    if repo is None:
        return None
    root = repo.root / "server" / "data"
    return root if root.is_dir() else None
