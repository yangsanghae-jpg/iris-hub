"""연결 관리 · 스키마 관문 (S1) — STORE_SCHEMA_DESIGN §3.1.

핵심 규칙: 탭·엔진은 sqlite3 를 직접 열지 않는다. 이 모듈의 get_conn() 을 통해서만.
- 경로: config.IRIS_VAULT_DB (심볼릭 → .nosync/index.db)
- PRAGMA: WAL · foreign_keys · busy_timeout 강제
- 스키마: schema.sql 멱등 적용 + SCHEMA_VERSION 확인
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from src import config

SCHEMA_VERSION = 2
_SCHEMA_SQL = Path(__file__).with_name("schema.sql")
_DX_MIGRATION_SQL = Path(__file__).with_name("dx_schema.sql")


def _ensure_db_location() -> Path:
    """볼트/.nosync 디렉터리 + index.db 심볼릭 보장. 실파일은 .nosync 에 둔다."""
    config.IRIS_VAULT_NOSYNC.mkdir(parents=True, exist_ok=True)
    link = config.IRIS_VAULT_DB
    real = config.IRIS_VAULT_NOSYNC / "index.db"
    # 심볼릭도 실파일도 없으면: .nosync 실파일을 가리키는 심볼릭 생성(댕글링 허용 — 열면 생성됨).
    if not link.is_symlink() and not link.exists():
        link.symlink_to(Path(".nosync") / "index.db")
    return link if link.is_symlink() or link.exists() else real


def get_conn() -> sqlite3.Connection:
    """단일 연결 팩토리. WAL, busy_timeout, foreign_keys 강제. row_factory=Row."""
    path = _ensure_db_location()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def _current_version(conn: sqlite3.Connection) -> int | None:
    try:
        row = conn.execute(
            "SELECT value FROM meta_kv WHERE key='schema_version'"
        ).fetchone()
    except sqlite3.OperationalError:
        return None  # meta_kv 부재 → 미초기화
    return int(row["value"]) if row else None


def _migrate_to_v2(conn: sqlite3.Connection) -> None:
    """v1 → v2: dx_* 스키마 추가."""
    conn.executescript(_DX_MIGRATION_SQL.read_text(encoding="utf-8"))
    conn.execute(
        "INSERT OR REPLACE INTO meta_kv(key, value) VALUES('schema_version', ?)",
        ("2",),
    )


def ensure_schema(conn: sqlite3.Connection | None = None) -> int:
    """schema.sql 적용 + SCHEMA_VERSION 기록. 없으면 생성(빈 볼트). 멱등.

    Returns 적용된 SCHEMA_VERSION.
    """
    own = conn is None
    conn = conn or get_conn()
    try:
        have = _current_version(conn)
        if have is None:
            conn.executescript(_SCHEMA_SQL.read_text(encoding="utf-8"))
            conn.execute(
                "INSERT OR REPLACE INTO meta_kv(key, value) VALUES('schema_version', ?)",
                (str(SCHEMA_VERSION),),
            )
        elif have == 1 and SCHEMA_VERSION >= 2:
            _migrate_to_v2(conn)
        elif have != SCHEMA_VERSION:
            raise RuntimeError(
                f"schema_version 불일치: DB={have}, code={SCHEMA_VERSION}. "
                "재출발 정책 — 볼트를 재초기화하거나 코드 버전을 맞추라."
            )
        conn.commit()
        return SCHEMA_VERSION
    finally:
        if own:
            conn.close()
