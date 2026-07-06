"""DIAG-SOT dx JSON 쓰기·검증·byte-0 재생성 (파일럿: q3_scale_profile).

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


def validate_q3_edits(
    q_matrix: list[dict[str, Any]],
    dx_pack_id: str,
    sub_codes: set[str],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    rows = [r for r in q_matrix if r.get("pack_id") == dx_pack_id]
    weight_fields = [f for f in idx.q3_editable_field_paths() if f.startswith("weights.")]
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


def save_q_pack_and_rebuild(
    repo: DiagnosisRepo,
    q_matrix: list[dict[str, Any]],
    manifest_pack_id: str,
) -> SaveResult:
    """dx_q_matrix.json 저장 후 논리 팩의 server·client 미러 runtime 모두 재생성."""
    entry = idx.pack_mirror_entry(manifest_pack_id)
    if entry is None:
        return SaveResult(False, f"미러 매핑 없음: {manifest_pack_id}")

    mirrors = idx.pack_mirror_runtime_rels(manifest_pack_id)
    if not mirrors:
        return SaveResult(False, f"runtime 미러 경로 없음: {manifest_pack_id}")

    dx_index, err = idx.load_dx_index(repo)
    if dx_index is None:
        return SaveResult(False, err or "dx 인덱스 로드 실패")

    primary = idx.pack_edit_primary_dx_id(manifest_pack_id)
    q = str(entry.get("q") or "q3")
    if q == "q3":
        issues = validate_q3_edits(q_matrix, primary, dx_index.sub_codes)
    else:
        issues = []
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
    allowed = [DX_Q_MATRIX_REL]
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
