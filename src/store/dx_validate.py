"""dx_* 검증 게이트 (DIAGNOSIS_PACK_MGMT_TAB_DESIGN §4.3)."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field

from . import db, dx

INDUSTRY_CODES = dx.INDUSTRY_CODES


@dataclass
class ValidationIssue:
    level: str  # error | warning
    code: str
    message: str


@dataclass
class ValidationResult:
    ok: bool
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)


def validate(conn: sqlite3.Connection | None = None) -> ValidationResult:
    own = conn is None
    conn = conn or db.get_conn()
    result = ValidationResult(ok=True)
    try:
        _check_industry_completeness(conn, result)
        _check_code_references(conn, result)
        _check_routing_references(conn, result)
        _check_bridge_completeness(conn, result)
        _check_coverage(conn, result)
    finally:
        if own:
            conn.close()
    result.ok = result.error_count == 0
    return result


def _check_industry_completeness(conn: sqlite3.Connection, result: ValidationResult) -> None:
    present = {
        r["code"] for r in conn.execute("SELECT code FROM dx_industry").fetchall()
    }
    missing = [c for c in INDUSTRY_CODES if c not in present]
    for code in missing:
        result.warnings.append(ValidationIssue(
            "warning", "industry_gap",
            f"산업 {code} IND 팩 없음 (A~I 완결성)",
        ))


def _check_code_references(conn: sqlite3.Connection, result: ValidationResult) -> None:
    active = {
        (r["kind"], r["code"])
        for r in conn.execute("SELECT kind, code FROM dx_code WHERE status='active'").fetchall()
    }
    rows = conn.execute(
        "SELECT pi.block, pi.code, p.industry_code, p.scope "
        "FROM dx_profile_item pi JOIN dx_profile p ON p.id=pi.profile_id"
    ).fetchall()
    for row in rows:
        kind = row["block"]
        if (kind, row["code"]) not in active:
            result.errors.append(ValidationIssue(
                "error", "code_ref",
                f"프로필 코드 미등록: {row['industry_code']}/{row['scope']} "
                f"{row['block']}:{row['code']}",
            ))


def _check_routing_references(conn: sqlite3.Connection, result: ValidationResult) -> None:
    routing_codes = {
        r["routing_code"]
        for r in conn.execute("SELECT routing_code FROM dx_routing_pack").fetchall()
    }
    profiles = conn.execute(
        "SELECT industry_code, scope, routing_code FROM dx_profile WHERE routing_code IS NOT NULL"
    ).fetchall()
    for row in profiles:
        rc = row["routing_code"]
        if rc and rc not in routing_codes:
            result.errors.append(ValidationIssue(
                "error", "routing_ref",
                f"라우팅 미등록: {row['industry_code']}/{row['scope']} → {rc}",
            ))


def _check_bridge_completeness(conn: sqlite3.Connection, result: ValidationResult) -> None:
    subs = conn.execute("SELECT id, canon_code FROM dx_sub_industry").fetchall()
    for sub in subs:
        bridges = dx.list_sub_bridges(conn, sub["id"])
        if "ch1name" not in bridges:
            result.warnings.append(ValidationIssue(
                "warning", "bridge_ch1",
                f"ch1name 브릿지 없음: {sub['canon_code']}",
            ))


def _check_coverage(conn: sqlite3.Connection, result: ValidationResult) -> None:
    metric_count = conn.execute("SELECT COUNT(*) AS n FROM dx_question_metric").fetchone()["n"]
    if metric_count == 0:
        return
    gaps = dx.coverage_gaps(conn)
    for gap in gaps[:20]:
        result.warnings.append(ValidationIssue(
            "warning", "coverage_gap",
            f"수치 누락: {gap['industry_code']}/{gap['canon_code']} {gap['question']}",
        ))
    if len(gaps) > 20:
        result.warnings.append(ValidationIssue(
            "warning", "coverage_gap",
            f"… 외 {len(gaps) - 20}건 커버리지 누락",
        ))
