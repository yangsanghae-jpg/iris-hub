"""④ 데이터볼트 DAL (S1) — STORE_SCHEMA_DESIGN §3.2.

문서·청크·검색·메타·큐레이션. 탭·엔진은 이 함수들만 부른다. SQL 은 여기 안에만.
연결은 호출자가 넘기거나(트랜잭션 묶음), 생략 시 함수가 자체 연결한다.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from src import config

from .db import get_conn
from .models import ChunkRow, DBStats, DistStats, DocHit, DocRow, QueueStats


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def _conn(conn: sqlite3.Connection | None):
    """넘겨받은 연결은 그대로, 없으면 열고 commit/close 까지 책임."""
    if conn is not None:
        yield conn
        return
    c = get_conn()
    try:
        yield c
        c.commit()
    finally:
        c.close()


# ─── 쓰기 (엔진 intake/process 가 호출) ────────────────────────────────────
def upsert_document(doc: DocRow, conn: sqlite3.Connection | None = None) -> None:
    with _conn(conn) as c:
        c.execute(
            """INSERT INTO documents
                 (doc_id, channel, source, original_path, title, trust, status,
                  industry, area, level, ingested_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(doc_id) DO UPDATE SET
                 channel=excluded.channel, source=excluded.source,
                 original_path=excluded.original_path, title=excluded.title,
                 trust=excluded.trust, status=excluded.status,
                 industry=excluded.industry, area=excluded.area, level=excluded.level""",
            (doc.doc_id, doc.channel, doc.source, doc.original_path, doc.title,
             doc.trust, doc.status, doc.industry, doc.area, doc.level,
             doc.ingested_at or _now()),
        )


def insert_chunks(
    doc_id: str, chunks: list[ChunkRow], conn: sqlite3.Connection | None = None
) -> None:
    """청크 삽입 + 두 FTS 인덱스 동기(rowid=chunks.rowid 정렬)."""
    with _conn(conn) as c:
        for ch in chunks:
            cur = c.execute(
                "INSERT INTO chunks(chunk_id, doc_id, ord, text, page_ref) VALUES (?,?,?,?,?)",
                (ch.chunk_id, doc_id, ch.ord, ch.text, ch.page_ref),
            )
            rid = cur.lastrowid
            # unicode61(외부콘텐츠) + trigram(독립) 둘 다 같은 rowid 로 수동 동기.
            c.execute("INSERT INTO documents_fts(rowid, text) VALUES (?, ?)", (rid, ch.text))
            c.execute("INSERT INTO documents_fts_trigram(rowid, text) VALUES (?, ?)", (rid, ch.text))


def upsert_meta(doc_id: str, conn: sqlite3.Connection | None = None, **k2_fields) -> None:
    """document_meta 부분 갱신(넘긴 필드만). 행 없으면 생성."""
    allowed = {
        "summary", "topics_json", "entities_json", "concepts_json",
        "extract_at", "classify_at", "summarize_at", "k2_done_at",
        "classifier_version", "confidence", "fallback_used",
        "processing_started_at", "fail_count", "last_error",
    }
    fields = {k: v for k, v in k2_fields.items() if k in allowed}
    with _conn(conn) as c:
        c.execute("INSERT OR IGNORE INTO document_meta(doc_id) VALUES (?)", (doc_id,))
        if fields:
            sets = ", ".join(f"{k}=?" for k in fields)
            c.execute(
                f"UPDATE document_meta SET {sets} WHERE doc_id=?",
                (*fields.values(), doc_id),
            )


def set_status(
    doc_id: str, status: str, reason: str = "", conn: sqlite3.Connection | None = None
) -> None:
    """큐레이션 게이트. status ∈ {active, quarantine, rejected}."""
    if status not in ("active", "quarantine", "rejected"):
        raise ValueError(f"잘못된 status: {status}")
    with _conn(conn) as c:
        c.execute("UPDATE documents SET status=? WHERE doc_id=?", (status, doc_id))
        if reason:
            c.execute("INSERT OR IGNORE INTO document_meta(doc_id) VALUES (?)", (doc_id,))
            c.execute(
                "UPDATE document_meta SET last_error=? WHERE doc_id=?",
                (f"[{status}] {reason}", doc_id),
            )


# ─── 읽기 (탭·엔진이 호출) ─────────────────────────────────────────────────
def _fts_match(raw: str) -> str:
    """사용자 질의를 FTS5 안전 구문(구절 매치)으로. 특수문자 이스케이프."""
    return '"' + raw.replace('"', '""') + '"'


def _row_to_dochit(row: sqlite3.Row) -> DocHit:
    return DocHit(
        doc_id=row["doc_id"], title=row["title"], snippet=row["snippet"],
        score=float(row["score"]), channel=row["channel"],
    )


def search_fts(
    query: str, limit: int = 20, conn: sqlite3.Connection | None = None
) -> list[DocHit]:
    """전문검색. unicode61 우선, 결과 없으면 trigram 폴백(dual tokenizer)."""
    match = _fts_match(query)
    with _conn(conn) as c:
        for table in ("documents_fts", "documents_fts_trigram"):
            # bm25/snippet 은 FTS 행 문맥에서만 호출 가능(집계 문맥 불가). GROUP BY 를 SQL 에
            # 쓰면 서브쿼리 평탄화로 집계 문맥이 되어 실패 → 청크 단위로 뽑아 Python 중복제거.
            sql = f"""
              SELECT d.doc_id AS doc_id, d.title AS title, d.channel AS channel,
                     snippet({table}, 0, '[', ']', '…', 10) AS snippet,
                     bm25({table}) AS score
                FROM {table} f
                JOIN chunks c2   ON c2.rowid = f.rowid
                JOIN documents d ON d.doc_id = c2.doc_id
               WHERE {table} MATCH ? AND d.status = 'active'
               ORDER BY score ASC
            """
            try:
                rows = c.execute(sql, (match,)).fetchall()
            except sqlite3.OperationalError:
                rows = []
            if rows:
                seen: dict[str, DocHit] = {}
                for r in rows:                       # score ASC → 첫 등장이 문서별 최선
                    if r["doc_id"] not in seen:
                        seen[r["doc_id"]] = _row_to_dochit(r)
                    if len(seen) >= limit:
                        break
                return list(seen.values())
    return []


def queue_snapshot(conn: sqlite3.Connection | None = None) -> QueueStats:
    """대기/처리중/완료 (흐름·데이터 탭)."""
    with _conn(conn) as c:
        total = c.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        done = c.execute(
            "SELECT COUNT(*) FROM document_meta WHERE k2_done_at IS NOT NULL"
        ).fetchone()[0]
        processing = c.execute(
            "SELECT COUNT(*) FROM document_meta "
            "WHERE processing_started_at IS NOT NULL AND k2_done_at IS NULL"
        ).fetchone()[0]
        failed = c.execute(
            "SELECT COUNT(*) FROM document_meta WHERE fail_count > 0"
        ).fetchone()[0]
    return QueueStats(
        total=total, done=done, processing=processing, failed=failed,
        pending=max(total - done - processing, 0),
    )


def doc_distribution(conn: sqlite3.Connection | None = None) -> DistStats:
    """산업·채널·상태 분포 (데이터 탭)."""
    def _counts(c, col):
        return {
            (r[0] or "(none)"): r[1]
            for r in c.execute(
                f"SELECT {col}, COUNT(*) FROM documents GROUP BY {col}"
            ).fetchall()
        }

    with _conn(conn) as c:
        return DistStats(
            by_channel=_counts(c, "channel"),
            by_industry=_counts(c, "industry"),
            by_status=_counts(c, "status"),
        )


def db_stats(conn: sqlite3.Connection | None = None) -> DBStats:
    """볼트 규모·K2 단계 진척 (데이터·흐름 탭). 빈 볼트면 0."""
    s = DBStats()
    try:
        real = config.IRIS_VAULT_DB.resolve(strict=True)
        s.db_exists = real.is_file()
        s.db_size_mb = round(real.stat().st_size / (1024 * 1024), 1)
    except (FileNotFoundError, OSError):
        return s
    with _conn(conn) as c:
        s.integrity = (c.execute("PRAGMA integrity_check").fetchone() or ["?"])[0]
        row = c.execute("SELECT value FROM meta_kv WHERE key='schema_version'").fetchone()
        s.schema_version = row[0] if row else "-"
        one = lambda q: c.execute(q).fetchone()[0]
        s.documents = one("SELECT COUNT(*) FROM documents")
        s.chunks = one("SELECT COUNT(*) FROM chunks")
        s.fts = one("SELECT COUNT(*) FROM documents_fts")
        s.classified = one("SELECT COUNT(*) FROM documents WHERE industry IS NOT NULL AND area IS NOT NULL")
        s.extract_done = one("SELECT COUNT(*) FROM document_meta WHERE extract_at IS NOT NULL")
        s.classify_done = one("SELECT COUNT(*) FROM document_meta WHERE classify_at IS NOT NULL")
        s.summarize_done = one("SELECT COUNT(*) FROM document_meta WHERE summarize_at IS NOT NULL")
        s.k2_done = one("SELECT COUNT(*) FROM document_meta WHERE k2_done_at IS NOT NULL")
        s.concepts = one("SELECT COUNT(*) FROM concepts")
        s.aliases = one("SELECT COUNT(*) FROM concept_aliases")
    return s


def list_documents(
    limit: int = 100, status: str = "active", conn: sqlite3.Connection | None = None
) -> list[DocRow]:
    """문서 목록 (위키·데이터 탭). 최신 ingest 순."""
    with _conn(conn) as c:
        rows = c.execute(
            "SELECT doc_id, channel, source, original_path, title, trust, status, "
            "industry, area, level, ingested_at FROM documents "
            "WHERE status=? ORDER BY ingested_at DESC LIMIT ?",
            (status, limit),
        ).fetchall()
    return [DocRow(**{k: r[k] for k in r.keys()}) for r in rows]


def get_document(doc_id: str, conn: sqlite3.Connection | None = None) -> DocRow | None:
    with _conn(conn) as c:
        r = c.execute(
            "SELECT doc_id, channel, source, original_path, title, trust, status, "
            "industry, area, level, ingested_at FROM documents WHERE doc_id=?",
            (doc_id,),
        ).fetchone()
    if r is None:
        return None
    return DocRow(**{k: r[k] for k in r.keys()})
