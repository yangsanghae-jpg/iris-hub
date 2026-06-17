"""IRIS L4-K schema migration runner.

V2.5.1 Phase 1 — meta_kv.schema_version 기반 idempotent up/down 마이그레이션.

용법:
    python -m apps.ingest.migrate status
    python -m apps.ingest.migrate up           # 모든 미적용 up 마이그레이션 실행
    python -m apps.ingest.migrate up --to 001  # 특정 버전까지만
    python -m apps.ingest.migrate down --to 000  # 특정 버전까지 롤백
    python -m apps.ingest.migrate up --dry-run  # SQL만 출력, 실행 안 함

DB 경로는 KNOWLEDGE_BASE_PATH 환경변수 또는 --db 인자로 지정.
기본: <PROJECT_ROOT>/knowledge/_index.db
"""
from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent.parent
MIGRATIONS_DIR = APP_DIR / "migrations"

DEFAULT_KNOWLEDGE_PATH = PROJECT_ROOT / "knowledge"
KNOWLEDGE_PATH = Path(os.environ.get("KNOWLEDGE_BASE_PATH", DEFAULT_KNOWLEDGE_PATH))
DEFAULT_DB_PATH = KNOWLEDGE_PATH / "_index.db"

VERSION_RE = re.compile(r"^(\d{3})_(.+?)(_down)?\.sql$")


def discover_migrations() -> dict[str, dict[str, Path]]:
    """{'001': {'up': Path, 'down': Path}, ...}"""
    out: dict[str, dict[str, Path]] = {}
    for p in sorted(MIGRATIONS_DIR.glob("*.sql")):
        m = VERSION_RE.match(p.name)
        if not m:
            continue
        version, _slug, is_down = m.groups()
        out.setdefault(version, {})[("down" if is_down else "up")] = p
    return out


def current_version(conn: sqlite3.Connection) -> str:
    """meta_kv.schema_version 읽기. 없으면 '000'."""
    try:
        row = conn.execute(
            "SELECT value FROM meta_kv WHERE key = 'schema_version'"
        ).fetchone()
    except sqlite3.OperationalError:
        return "000"
    return row[0] if row else "000"


def apply_sql(conn: sqlite3.Connection, sql_path: Path, dry_run: bool) -> None:
    sql = sql_path.read_text(encoding="utf-8")
    print(f"--- {sql_path.name} ---")
    if dry_run:
        print(sql)
        return
    conn.executescript(sql)
    print(f"[OK] {sql_path.name}")


def cmd_status(db_path: Path) -> int:
    if not db_path.exists():
        print(f"[WARN] DB not found: {db_path}", file=sys.stderr)
        return 1
    migrations = discover_migrations()
    with sqlite3.connect(db_path) as conn:
        cur = current_version(conn)
    print(f"DB path        : {db_path}")
    print(f"Current version: {cur}")
    print(f"Available:")
    for ver in sorted(migrations.keys()):
        marker = "*" if ver <= cur else " "
        up_name = migrations[ver].get("up", Path("?")).name
        down_name = migrations[ver].get("down", Path("(no down)")).name
        print(f"  {marker} {ver}  up={up_name}  down={down_name}")
    return 0


def cmd_up(db_path: Path, to: str | None, dry_run: bool) -> int:
    migrations = discover_migrations()
    versions = sorted(migrations.keys())
    if not versions:
        print("[WARN] No migrations found", file=sys.stderr)
        return 1
    target = to or versions[-1]
    if target not in migrations:
        print(f"[ERROR] Unknown version: {target}", file=sys.stderr)
        return 2

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        cur = current_version(conn)
        pending = [v for v in versions if cur < v <= target]
        if not pending:
            print(f"[OK] Already at version {cur} (target {target}, nothing to do)")
            return 0
        print(f"Current: {cur}  →  Target: {target}")
        print(f"Pending: {', '.join(pending)}")
        if dry_run:
            print("[DRY RUN] No changes will be applied")
        for ver in pending:
            up = migrations[ver].get("up")
            if up is None:
                print(f"[ERROR] No up file for {ver}", file=sys.stderr)
                return 3
            apply_sql(conn, up, dry_run)
        if not dry_run:
            final = current_version(conn)
            print(f"[DONE] DB at version {final}")
    return 0


def cmd_down(db_path: Path, to: str, dry_run: bool) -> int:
    if not to:
        print("[ERROR] --to required for down", file=sys.stderr)
        return 2
    migrations = discover_migrations()
    versions = sorted(migrations.keys())

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        cur = current_version(conn)
        if cur <= to:
            print(f"[OK] Already at or below {to} (current={cur})")
            return 0
        # cur 부터 거꾸로 to까지의 down 실행
        rollback = [v for v in reversed(versions) if to < v <= cur]
        print(f"Current: {cur}  →  Rollback to: {to}")
        print(f"Will run down for: {', '.join(rollback)}")
        if dry_run:
            print("[DRY RUN] No changes will be applied")
        for ver in rollback:
            down = migrations[ver].get("down")
            if down is None:
                print(f"[ERROR] No down file for {ver}", file=sys.stderr)
                return 3
            apply_sql(conn, down, dry_run)
        if not dry_run:
            final = current_version(conn)
            print(f"[DONE] DB at version {final}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(prog="migrate")
    p.add_argument("command", choices=["status", "up", "down"])
    p.add_argument("--to", help="대상 버전 (예: 001)")
    p.add_argument("--db", help=f"DB 경로 (기본: {DEFAULT_DB_PATH})")
    p.add_argument("--dry-run", action="store_true", help="실행하지 않고 SQL만 출력")
    args = p.parse_args()

    db_path = Path(args.db) if args.db else DEFAULT_DB_PATH

    if args.command == "status":
        return cmd_status(db_path)
    if args.command == "up":
        return cmd_up(db_path, args.to, args.dry_run)
    if args.command == "down":
        return cmd_down(db_path, args.to or "", args.dry_run)
    return 1


if __name__ == "__main__":
    sys.exit(main())
