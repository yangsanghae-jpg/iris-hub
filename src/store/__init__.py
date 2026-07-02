"""src/store — 저장소 접근 계층 (DAL). STORE_SCHEMA_DESIGN (S1).

탭·엔진이 DB 에 닿는 유일한 관문. sqlite3 직접 열기 금지 — 여기를 통해서만.

    from src.store import db, vault, knowledge
    from src.store.models import DocRow, ChunkRow, ConceptRow
"""
from __future__ import annotations

from . import db, knowledge, vault
from .db import SCHEMA_VERSION, ensure_schema, get_conn

__all__ = [
    "db", "vault", "knowledge",
    "get_conn", "ensure_schema", "SCHEMA_VERSION",
]
