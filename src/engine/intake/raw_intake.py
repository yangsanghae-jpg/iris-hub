"""K1 raw-lane ingester for unstructured markdown/text drops.

Ingests files from iris-system/knowledge/raw/ into _index.db:
  - documents row per file (lane='bronze', kind='source', origin='human')
  - chunks split by paragraph boundary, ~800 chars target
  - schema V2.6 (kind/origin columns from migration 001)

LLM-less by design (V2.5.1 §10 plan, K2 cleansing handles LLM work later).

Run: ~/iris-local/venv/iris-system/bin/python apps/ingest/raw_intake.py  (from iris-system/)
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from .origin_rules import IngestSource, origin_for
except ImportError:
    # 스크립트 직접 실행 시
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from src.engine.intake.origin_rules import IngestSource, origin_for

# 경로 config 단일화 (2026-07-02) — ~/Documents 미참조, hub 볼트와 일치.
from src.config import IRIS_DB_PATH as DB_PATH, IRIS_RAW_PATH as RAW_DIR
IRIS_ROOT = Path("/Users/iris/iris-system")  # 스키마 등 참조용(홈, 머신 독립)

LANE = "bronze"
KIND = "source"
ORIGIN = origin_for(IngestSource.USER_DROP)  # → 'human'  (V2.6 Phase 3.1)
TRUST = "verified"

INCLUDE_SUFFIXES = {".md", ".txt"}
CHUNK_TARGET = 800
CHUNK_MAX = 1200

SLUG_NONALNUM = re.compile(r"[^a-z0-9가-힣]+")


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slugify(name: str) -> str:
    base = name.lower()
    base = SLUG_NONALNUM.sub("-", base).strip("-")
    if not base:
        base = hashlib.sha1(name.encode("utf-8")).hexdigest()[:12]
    return base[:80]


def doc_id_for(path: Path) -> str:
    """V2.5.3 §18: 내용 기반 결정적 doc_id.

    이전 (5500c86 이전): `raw:{slugify(stem)}:{sha1(path)[:8]}` — 파일명·경로 의존.
        M2/M5 양쪽이 같은 raw 파일에 *다른 doc_id*를 생성하는 사고 (V2.5.3 §18).

    현재: `raw:{sha1(content)[:12]}` — 내용 기반.
        - 같은 파일 = 어디서든 같은 doc_id (M2/M5 보장)
        - 파일명 변경 시 doc_id 안정
        - 내용 변경 시 새 doc_id (의도된 동작)
        - 가독성은 documents.title 이 담당
    """
    content_hash = hashlib.sha1(path.read_bytes()).hexdigest()[:12]
    return f"raw:{content_hash}"


def split_chunks(text: str) -> list[str]:
    """Split by blank-line paragraphs, then accumulate to ~CHUNK_TARGET chars."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    buf = ""
    for p in paragraphs:
        if len(p) > CHUNK_MAX:
            if buf:
                chunks.append(buf)
                buf = ""
            for i in range(0, len(p), CHUNK_MAX):
                chunks.append(p[i : i + CHUNK_MAX])
            continue
        if buf and len(buf) + len(p) + 2 > CHUNK_TARGET:
            chunks.append(buf)
            buf = p
        else:
            buf = f"{buf}\n\n{p}" if buf else p
    if buf:
        chunks.append(buf)
    return chunks


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Minimal YAML frontmatter parser (key: value lines only)."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    meta: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip().strip("\"'")
    return meta, text[end + 5 :]


def upsert_raw_doc(conn: sqlite3.Connection, doc_id: str, path: Path, title: str, chunks: list[str]) -> None:
    # V2.6 Phase 2.1: K1 게이트 — secure lane 진입 차단
    from src.engine.secure.secure_gate import assert_not_secure
    assert_not_secure(LANE, "K1", doc_id=doc_id)

    conn.execute(
        """INSERT INTO documents
             (doc_id, path, lane, trust, kind, origin, title, fetched_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(doc_id) DO UPDATE SET
             path=excluded.path,
             lane=excluded.lane,
             trust=excluded.trust,
             kind=excluded.kind,
             origin=excluded.origin,
             title=excluded.title,
             fetched_at=excluded.fetched_at""",
        (doc_id, str(path), LANE, TRUST, KIND, ORIGIN, title, now_iso()),
    )
    conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
    for i, chunk in enumerate(chunks):
        conn.execute(
            "INSERT INTO chunks (chunk_id, doc_id, ord, text) VALUES (?, ?, ?, ?)",
            (f"{doc_id}#{i}", doc_id, i, chunk),
        )


def main() -> int:
    if not DB_PATH.exists():
        print(f"[FATAL] DB not found: {DB_PATH}", file=sys.stderr)
        return 2
    if not RAW_DIR.exists():
        print(f"[FATAL] raw dir not found: {RAW_DIR}", file=sys.stderr)
        return 2

    files = sorted(p for p in RAW_DIR.iterdir() if p.is_file() and p.suffix.lower() in INCLUDE_SUFFIXES)
    if not files:
        print(f"[WARN] no raw files in {RAW_DIR}")
        return 0

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")

    total_chunks = 0
    for path in files:
        text = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)
        title = meta.get("title") or path.stem
        chunks = split_chunks(body)
        if not chunks:
            print(f"  - skip empty: {path.name}")
            continue
        did = doc_id_for(path)
        upsert_raw_doc(conn, did, path, title, chunks)
        total_chunks += len(chunks)
        print(f"  [OK] {path.name}  doc_id={did}  chunks={len(chunks)}")

    conn.execute(
        "INSERT INTO meta_kv (key, value) VALUES ('last_ingest_raw_at', ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (now_iso(),),
    )
    # V2.5.3 §15: FTS dual-tokenizer 동기 (raw 신규 ingest 후 자동)
    try:
        from .fts_sync import rebuild_all
    except ImportError:
        from src.engine.intake.fts_sync import rebuild_all
    counts = rebuild_all(conn)
    conn.commit()
    conn.close()
    print(f"[DONE] {len(files)} files, {total_chunks} chunks, FTS: {counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
