"""dx_* 리빌드 적용 — diagnosis_git 커밋 (DIAGNOSIS_PACK_MGMT_TAB_DESIGN §4.5)."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone

from src.diagnosis_git import git_commit_files, resolve_diagnosis_repo

from . import db, dx_export, dx_validate


@dataclass
class ApplyResult:
    ok: bool
    commit_sha: str | None = None
    files: list[str] | None = None
    error: str | None = None
    validation: dx_validate.ValidationResult | None = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def apply_rebuild(
    message: str = "pack rebuild: iris-hub dx_* export",
    *,
    allow_warnings: bool = True,
    conn: sqlite3.Connection | None = None,
) -> ApplyResult:
    validation = dx_validate.validate(conn)
    if not validation.ok:
        return ApplyResult(ok=False, error="검증 오류 — 적용 중단", validation=validation)
    if not allow_warnings and validation.warning_count > 0:
        return ApplyResult(ok=False, error="경고 존재 — allow_warnings=False", validation=validation)

    repo = resolve_diagnosis_repo()
    if repo is None:
        return ApplyResult(ok=False, error="diagnosis-tool clone 없음", validation=validation)

    export = dx_export.export_ch1(conn)
    if not export.files:
        return ApplyResult(ok=False, error="리빌드 파일 없음 — 먼저 임포트하세요", validation=validation)

    dx_export.write_files(repo.root, export.files)
    commit_sha = git_commit_files(repo, export.paths, message)
    if not commit_sha:
        return ApplyResult(
            ok=False,
            error="git commit 실패 (변경 없음 또는 git 오류)",
            files=export.paths,
            validation=validation,
        )

    own = conn is None
    conn = conn or db.get_conn()
    try:
        conn.execute(
            "INSERT INTO dx_apply_log(applied_at, commit_sha, message, files_json, validation_json) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                _now_iso(),
                commit_sha,
                message,
                json.dumps(export.paths, ensure_ascii=False),
                json.dumps(
                    {
                        "errors": len(validation.errors),
                        "warnings": len(validation.warnings),
                    },
                    ensure_ascii=False,
                ),
            ),
        )
        conn.commit()
    finally:
        if own:
            conn.close()

    return ApplyResult(
        ok=True,
        commit_sha=commit_sha,
        files=export.paths,
        validation=validation,
    )


def list_apply_log(limit: int = 10, conn: sqlite3.Connection | None = None) -> list[sqlite3.Row]:
    own = conn is None
    conn = conn or db.get_conn()
    try:
        return conn.execute(
            "SELECT * FROM dx_apply_log ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    finally:
        if own:
            conn.close()
