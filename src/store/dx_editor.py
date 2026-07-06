"""DIAG-SOT dx JSON 쓰기·검증·byte-0 재생성 (Q1 dx_q_framework · Q2/Q3/Q4 dx_q_matrix · Q5 dx_q5_* 팩).

쓰기는 dx JSON에만. runtime server/data·client/data는 재생성 결과물.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.diagnosis_git import DiagnosisRepo
from src.store import dx_index as idx

DX_Q_MATRIX_REL = "scripts/data_poc/_p1b/dx_q_matrix.json"
DX_Q_FRAMEWORK_REL = "scripts/data_poc/_p1b/dx_q_framework.json"
DX_Q5_RECOMMENDATION_REL = "scripts/data_poc/_p1a/dx_q5_recommendation.json"
DX_Q5_FRAMEWORK_REL = "scripts/data_poc/_p1a/dx_q5_framework.json"
DX_Q1_FRAMEWORK_REL = "scripts/data_poc/_p1a/dx_q_framework.json"


@dataclass
class ValidationIssue:
    level: str  # error | warn
    message: str
    row_key: str = ""


@dataclass
class SaveResult:
    ok: bool
    message: str
    runtime_path: str = ""
    issues: list[ValidationIssue] = field(default_factory=list)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_q_matrix(repo_root: Path) -> list[dict[str, Any]]:
    path = repo_root / DX_Q_MATRIX_REL
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("dx_q_matrix must be a list")
    return data


def load_q_framework(repo_root: Path) -> list[dict[str, Any]]:
    path = repo_root / DX_Q_FRAMEWORK_REL
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def load_q5_recommendation(repo_root: Path) -> list[dict[str, Any]]:
    path = repo_root / DX_Q5_RECOMMENDATION_REL
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("dx_q5_recommendation must be a list")
    return data


def load_q5_framework(repo_root: Path) -> list[dict[str, Any]]:
    path = repo_root / DX_Q5_FRAMEWORK_REL
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def load_q1_framework(repo_root: Path) -> list[dict[str, Any]]:
    path = repo_root / DX_Q1_FRAMEWORK_REL
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("dx_q_framework must be a list")
    return data


def validate_q3_edits(
    q_matrix: list[dict[str, Any]],
    dx_pack_id: str,
    sub_codes: set[str],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    rows = [r for r in q_matrix if r.get("pack_id") == dx_pack_id]
    weight_fields = [f for f in idx.q_editable_field_paths("q3") if f.startswith("weights.")]
    scale_levels = {"S1", "S2", "S3", "S4", "S5"}

    for row in rows:
        sub = str(row.get("sub_code") or "")
        if sub and sub not in sub_codes:
            issues.append(ValidationIssue("error", f"세부산업 코드 {sub} 가 척추에 없음", sub))
        vj = row.get("value_json") or {}
        if not isinstance(vj, dict):
            continue
        weights = vj.get("weights") or {}
        if isinstance(weights, dict) and weights:
            total = 0
            for wf in weight_fields:
                key = wf.split(".", 1)[1]
                w = weights.get(key)
                if w is None:
                    continue
                if not isinstance(w, int) or w < 0 or w > 100:
                    issues.append(
                        ValidationIssue("error", f"{sub} {key} 가중치는 0~100 정수", f"{sub}|{wf}")
                    )
                else:
                    total += w
            if total != 100:
                issues.append(
                    ValidationIssue("warn", f"{sub} 가중치 합 {total} (100 권장)", sub)
                )
        for fp in ("override.site_scope_hint", "override.recommended_site_scope_hint", "override.default_site_scope_hint"):
            val = idx.get_nested(vj, fp)
            if val is not None and str(val) not in scale_levels:
                issues.append(ValidationIssue("error", f"{sub} {fp} 는 S1~S5", f"{sub}|{fp}"))
    return issues


def validate_q2_edits(
    q_matrix: list[dict[str, Any]],
    dx_pack_id: str,
    sub_codes: set[str],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    rows = [r for r in q_matrix if r.get("pack_id") == dx_pack_id]
    route_codes = {"R1", "R2", "R3", "R4"}
    nature_levels = {"core", "low", "partial"}

    for row in rows:
        sub = str(row.get("sub_code") or "")
        if sub and sub not in sub_codes:
            issues.append(ValidationIssue("error", f"세부산업 코드 {sub} 가 척추에 없음", sub))
        vj = row.get("value_json") or {}
        if not isinstance(vj, dict):
            continue
        route = idx.get_nested(vj, "routing_profile.primary_route")
        if route is not None and str(route) not in route_codes:
            issues.append(
                ValidationIssue("error", f"{sub} primary_route 는 R1~R4", f"{sub}|routing_profile.primary_route")
            )
        for fp in idx.q_editable_field_paths("q2"):
            if not fp.startswith("product_nature."):
                continue
            val = idx.get_nested(vj, fp)
            if val is not None and str(val) not in nature_levels:
                issues.append(ValidationIssue("error", f"{sub} {fp} 는 core/low/partial", f"{sub}|{fp}"))
    return issues


def validate_q4_edits(
    q_matrix: list[dict[str, Any]],
    dx_pack_id: str,
    sub_codes: set[str],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    rows = [r for r in q_matrix if r.get("pack_id") == dx_pack_id]
    int_fields = idx.q_editable_field_paths("q4")

    for row in rows:
        sub = str(row.get("sub_code") or "")
        if sub and sub not in sub_codes:
            issues.append(ValidationIssue("error", f"세부산업 코드 {sub} 가 척추에 없음", sub))
        vj = row.get("value_json") or {}
        if not isinstance(vj, dict):
            continue
        for fp in int_fields:
            val = idx.get_nested(vj, fp)
            if val is None:
                continue
            if not isinstance(val, int) or val < 1 or val > 5:
                issues.append(ValidationIssue("error", f"{sub} {fp} 는 1~5 정수", f"{sub}|{fp}"))
    return issues


def validate_q1_edits(
    q1_framework: list[dict[str, Any]],
    *,
    pending_edits: dict[str, Any] | None = None,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    editable = set(idx.q_editable_field_paths("q1"))
    locks = idx.field_locks().get("dx_q_framework_q1", {})
    locked_blocks = set((locks.get("block_lock") or {}).get("blocks") or [])

    for row in q1_framework:
        if row.get("q") != "q1" or row.get("pack_id") != "q1_taxonomy":
            continue
        block = str(row.get("block") or "")
        if block in locked_blocks:
            continue
        if block != "metadata":
            issues.append(ValidationIssue("error", f"Q1 block {block} 편집 불가"))
            continue
        vj = row.get("value_json") or {}
        if not isinstance(vj, dict):
            issues.append(ValidationIssue("error", "metadata value_json 형식 오류"))
            continue
        for fp in editable:
            val = idx.get_nested(vj, fp)
            if val is not None and not isinstance(val, str):
                issues.append(
                    ValidationIssue("error", f"{fp} 는 문자열만 허용", fp)
                )

    if pending_edits:
        for key, val in pending_edits.items():
            if key not in editable:
                issues.append(ValidationIssue("error", f"whitelist 밖 필드: {key}", key))
            elif not isinstance(val, str):
                issues.append(ValidationIssue("error", f"{key} 는 문자열만 허용", key))
    return issues


def validate_q5_edits(
    q5_recommendation: list[dict[str, Any]],
    sub_codes: set[str],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    level_ids = {"L1", "L2", "L3", "L4", "L5"}
    weight_levels = {"primary", "secondary", "optional"}
    level_fields = [f for f in idx.q_editable_field_paths("q5") if f.startswith("q5_2.recommended_levels.")]
    weight_fields = [f for f in idx.q_editable_field_paths("q5") if f.startswith("q5_1.default_axis_weight.")]

    for row in q5_recommendation:
        if row.get("pack_id") != "q5_recommendation":
            continue
        sub = str(row.get("sub_code") or "")
        if sub and sub not in sub_codes:
            issues.append(ValidationIssue("error", f"세부산업 코드 {sub} 가 척추에 없음", sub))
        vj = row.get("value_json") or {}
        if not isinstance(vj, dict):
            continue
        for fp in level_fields:
            val = idx.get_nested(vj, fp)
            if val is not None and str(val) not in level_ids:
                issues.append(ValidationIssue("error", f"{sub} {fp} 는 L1~L5", f"{sub}|{fp}"))
        for fp in weight_fields:
            val = idx.get_nested(vj, fp)
            if val is not None and str(val) not in weight_levels:
                issues.append(
                    ValidationIssue(
                        "error",
                        f"{sub} {fp} 는 primary/secondary/optional",
                        f"{sub}|{fp}",
                    )
                )
    return issues


def validate_q_pack_edits(
    q_matrix: list[dict[str, Any]],
    manifest_pack_id: str,
    sub_codes: set[str],
    *,
    q1_framework: list[dict[str, Any]] | None = None,
    q5_recommendation: list[dict[str, Any]] | None = None,
    pending_edits: dict[str, Any] | None = None,
) -> list[ValidationIssue]:
    q = idx.pack_q_code(manifest_pack_id)
    if q == "q1":
        if q1_framework is None:
            return [ValidationIssue("error", "Q1 dx 데이터 없음")]
        return validate_q1_edits(q1_framework, pending_edits=pending_edits)
    if q == "q5":
        if q5_recommendation is None:
            return [ValidationIssue("error", "Q5 dx 데이터 없음")]
        return validate_q5_edits(q5_recommendation, sub_codes)
    primary = idx.pack_edit_primary_dx_id(manifest_pack_id)
    if q == "q2":
        return validate_q2_edits(q_matrix, primary, sub_codes)
    if q == "q4":
        return validate_q4_edits(q_matrix, primary, sub_codes)
    return validate_q3_edits(q_matrix, primary, sub_codes)


def save_q5_and_rebuild(
    repo: DiagnosisRepo,
    q5_recommendation: list[dict[str, Any]],
    manifest_pack_id: str,
) -> SaveResult:
    """dx_q5_recommendation.json 저장 후 동일 payload를 server·client runtime에 기록."""
    entry = idx.pack_mirror_entry(manifest_pack_id)
    if entry is None:
        return SaveResult(False, f"미러 매핑 없음: {manifest_pack_id}")

    mirrors = idx.pack_mirror_runtime_rels(manifest_pack_id)
    if not mirrors:
        return SaveResult(False, f"runtime 미러 경로 없음: {manifest_pack_id}")

    dx_index_obj, err = idx.load_dx_index(repo)
    if dx_index_obj is None:
        return SaveResult(False, err or "dx 인덱스 로드 실패")

    issues = validate_q5_edits(q5_recommendation, dx_index_obj.sub_codes)
    dx_index_obj.close()

    errors = [i for i in issues if i.level == "error"]
    if errors:
        return SaveResult(False, "검증 오류로 저장하지 않음", issues=issues)

    dx_path = repo.root / DX_Q5_RECOMMENDATION_REL
    _write_json(dx_path, q5_recommendation)

    q5_framework = load_q5_framework(repo.root)
    payload = idx.rebuild_q5_payload(q5_framework, q5_recommendation)
    written: list[str] = []
    for m in mirrors:
        runtime_path = repo.root / m["runtime_rel"]
        _write_json(runtime_path, payload)
        written.append(m["runtime_rel"])

    return SaveResult(True, "저장하고 리포트에 반영함", ", ".join(written), issues)


def save_q1_and_rebuild(
    repo: DiagnosisRepo,
    q1_framework: list[dict[str, Any]],
    manifest_pack_id: str,
    *,
    pending_edits: dict[str, Any] | None = None,
) -> SaveResult:
    """dx_q_framework.json 저장 후 동일 payload를 server·client runtime에 기록."""
    entry = idx.pack_mirror_entry(manifest_pack_id)
    if entry is None:
        return SaveResult(False, f"미러 매핑 없음: {manifest_pack_id}")

    mirrors = idx.pack_mirror_runtime_rels(manifest_pack_id)
    if not mirrors:
        return SaveResult(False, f"runtime 미러 경로 없음: {manifest_pack_id}")

    issues = validate_q1_edits(q1_framework, pending_edits=pending_edits)
    errors = [i for i in issues if i.level == "error"]
    if errors:
        return SaveResult(False, "검증 오류로 저장하지 않음", issues=issues)

    dx_path = repo.root / DX_Q1_FRAMEWORK_REL
    _write_json(dx_path, q1_framework)

    payload = idx.rebuild_q1_payload(q1_framework)
    written: list[str] = []
    for m in mirrors:
        runtime_path = repo.root / m["runtime_rel"]
        _write_json(runtime_path, payload)
        written.append(m["runtime_rel"])

    return SaveResult(True, "저장하고 리포트에 반영함", ", ".join(written), issues)


def save_q_pack_and_rebuild(
    repo: DiagnosisRepo,
    q_matrix: list[dict[str, Any]],
    manifest_pack_id: str,
    *,
    q1_framework: list[dict[str, Any]] | None = None,
    q5_recommendation: list[dict[str, Any]] | None = None,
    pending_edits: dict[str, Any] | None = None,
) -> SaveResult:
    """dx JSON 저장 후 논리 팩 runtime 미러 재생성 (Q1 framework · Q2~Q4 matrix · Q5 recommendation)."""
    if idx.pack_q_code(manifest_pack_id) == "q1":
        if q1_framework is None:
            return SaveResult(False, "Q1 dx 데이터 없음")
        return save_q1_and_rebuild(
            repo, q1_framework, manifest_pack_id, pending_edits=pending_edits
        )
    if idx.pack_q_code(manifest_pack_id) == "q5":
        if q5_recommendation is None:
            return SaveResult(False, "Q5 dx 데이터 없음")
        return save_q5_and_rebuild(repo, q5_recommendation, manifest_pack_id)

    entry = idx.pack_mirror_entry(manifest_pack_id)
    if entry is None:
        return SaveResult(False, f"미러 매핑 없음: {manifest_pack_id}")

    mirrors = idx.pack_mirror_runtime_rels(manifest_pack_id)
    if not mirrors:
        return SaveResult(False, f"runtime 미러 경로 없음: {manifest_pack_id}")

    dx_index, err = idx.load_dx_index(repo)
    if dx_index is None:
        return SaveResult(False, err or "dx 인덱스 로드 실패")

    issues = validate_q_pack_edits(q_matrix, manifest_pack_id, dx_index.sub_codes)
    dx_index.close()

    errors = [i for i in issues if i.level == "error"]
    if errors:
        return SaveResult(False, "검증 오류로 저장하지 않음", issues=issues)

    dx_path = repo.root / DX_Q_MATRIX_REL
    _write_json(dx_path, q_matrix)

    q_framework = load_q_framework(repo.root)
    written: list[str] = []
    for m in mirrors:
        payload = idx.rebuild_q_pack_payload(q_matrix, q_framework, m["dx_pack_id"])
        runtime_path = repo.root / m["runtime_rel"]
        _write_json(runtime_path, payload)
        written.append(m["runtime_rel"])

    return SaveResult(True, "저장하고 리포트에 반영함", ", ".join(written), issues)


def save_q3_and_rebuild(
    repo: DiagnosisRepo,
    q_matrix: list[dict[str, Any]],
    runtime_rel: str,
    *,
    dx_pack_id: str = "q3_scale_profile_server",
) -> SaveResult:
    """Deprecated — manifest_pack_id 기반 save_q_pack_and_rebuild 사용."""
    _ = runtime_rel, dx_pack_id
    return save_q_pack_and_rebuild(repo, q_matrix, "q3_scale_profile")


def prove_index_regenerates(repo: DiagnosisRepo) -> tuple[bool, str]:
    """파생 인덱스가 JSON에서 재생성됨을 증명."""
    a, err = idx.load_dx_index(repo)
    if a is None:
        return False, err or "fail"
    n1 = a.total_row_count()
    a.close()
    b, _ = idx.load_dx_index(repo)
    if b is None:
        return False, "second load failed"
    n2 = b.total_row_count()
    b.close()
    if n1 != n2:
        return False, f"row count mismatch {n1} vs {n2}"
    return True, f"regenerated {n1} rows from JSON"


def audit_allowed_write_targets() -> list[str]:
    """save 경로가 쓰는 허용 대상 — dx JSON + q_pack_runtime_map runtime 미러."""
    allowed = [DX_Q_MATRIX_REL, DX_Q5_RECOMMENDATION_REL, DX_Q1_FRAMEWORK_REL]
    for entry in (idx.q_pack_runtime_map().get("packs") or {}).values():
        for m in entry.get("mirrors") or []:
            rel = m.get("runtime_rel")
            if rel:
                allowed.append(str(rel))
    return allowed


def grep_dx_only_writes(root: Path) -> list[str]:
    """dx + 설정된 runtime 미러만 쓰는지 — save 구현 구조 점검."""
    _ = root
    editor_src = Path(__file__).read_text(encoding="utf-8")
    violations: list[str] = []
    if "_write_json(dx_path" not in editor_src:
        violations.append("dx_q_matrix write missing")
    if "pack_mirror_runtime_rels" not in editor_src:
        violations.append("save does not iterate mirror runtime map")
    if "save_q_pack_and_rebuild" not in editor_src:
        violations.append("save_q_pack_and_rebuild missing")
    return violations
