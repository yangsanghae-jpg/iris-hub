"""③ 지식저장소 DAL (S1) — STORE_SCHEMA_DESIGN §3.3.

개념·별칭·링크·관계. 정규화(별칭→canonical)의 관문. 탭은 이 함수들만 부른다.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from .models import (
    ConceptPage,
    ConceptRow,
    DocRow,
    Graph,
    GraphEdge,
    GraphNode,
)
from .vault import _conn  # 동일한 연결 컨텍스트 재사용


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _row_to_concept(r: sqlite3.Row) -> ConceptRow:
    return ConceptRow(
        concept_id=r["concept_id"], canonical=r["canonical"],
        definition=r["definition"], trust=r["trust"], degree=r["degree"],
        created_at=r["created_at"], updated_at=r["updated_at"],
    )


# ─── 정규화 ────────────────────────────────────────────────────────────────
def resolve_concept(raw: str, conn: sqlite3.Connection | None = None) -> str | None:
    """별칭/표시명 → canonical concept_id. 못 찾으면 None (미매칭 추적)."""
    key = (raw or "").strip()
    if not key:
        return None
    with _conn(conn) as c:
        # 1) concept_id 직접 일치
        r = c.execute("SELECT concept_id FROM concepts WHERE concept_id=?", (key,)).fetchone()
        if r:
            return r["concept_id"]
        # 2) 별칭 일치 (대소문자 무시)
        r = c.execute(
            "SELECT concept_id FROM concept_aliases WHERE alias=? COLLATE NOCASE",
            (key,),
        ).fetchone()
        if r:
            return r["concept_id"]
        # 3) canonical 표시명 일치
        r = c.execute(
            "SELECT concept_id FROM concepts WHERE canonical=? COLLATE NOCASE", (key,)
        ).fetchone()
        return r["concept_id"] if r else None


# ─── 쓰기 ──────────────────────────────────────────────────────────────────
def upsert_concept(c: ConceptRow, conn: sqlite3.Connection | None = None) -> None:
    now = _now()
    with _conn(conn) as cx:
        cx.execute(
            """INSERT INTO concepts
                 (concept_id, canonical, definition, trust, degree, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?)
               ON CONFLICT(concept_id) DO UPDATE SET
                 canonical=excluded.canonical,
                 definition=COALESCE(excluded.definition, concepts.definition),
                 trust=excluded.trust,
                 updated_at=excluded.updated_at""",
            (c.concept_id, c.canonical, c.definition, c.trust, c.degree,
             c.created_at or now, now),
        )


def add_alias(
    concept_id: str, alias: str, lang: str | None = None,
    conn: sqlite3.Connection | None = None,
) -> None:
    with _conn(conn) as c:
        c.execute(
            "INSERT OR IGNORE INTO concept_aliases(concept_id, alias, lang) VALUES (?,?,?)",
            (concept_id, alias, lang),
        )


def link_concept_doc(
    concept_id: str, doc_id: str, weight: float = 1.0,
    conn: sqlite3.Connection | None = None,
) -> None:
    with _conn(conn) as c:
        c.execute(
            """INSERT INTO concept_docs(concept_id, doc_id, weight) VALUES (?,?,?)
               ON CONFLICT(concept_id, doc_id) DO UPDATE SET weight=excluded.weight""",
            (concept_id, doc_id, weight),
        )


def add_relation(
    src_id: str, dst_id: str, kind: str = "cooccur", weight: int = 1,
    conn: sqlite3.Connection | None = None,
) -> None:
    with _conn(conn) as c:
        c.execute(
            """INSERT INTO concept_relations(src_id, dst_id, kind, weight) VALUES (?,?,?,?)
               ON CONFLICT(src_id, dst_id, kind) DO UPDATE SET weight=excluded.weight""",
            (src_id, dst_id, kind, weight),
        )


def recompute_degree(conn: sqlite3.Connection | None = None) -> None:
    """concept_docs 집계 → concepts.degree 캐시 재계산 (active 문서만, S4 §5)."""
    with _conn(conn) as c:
        c.execute(
            """UPDATE concepts SET degree = (
                 SELECT COUNT(*) FROM concept_docs cd
                   JOIN documents d ON d.doc_id = cd.doc_id AND d.status = 'active'
                  WHERE cd.concept_id = concepts.concept_id
               )"""
        )


def recompute_cooccurrence(
    min_docs: int = 3, conn: sqlite3.Connection | None = None
) -> int:
    """같은 active 문서 min_docs건 이상에서 공출현한 개념쌍 → concept_relations(cooccur). Returns 쌍 수."""
    with _conn(conn) as c:
        rows = c.execute(
            """SELECT a.concept_id AS src, b.concept_id AS dst, COUNT(*) AS n
                 FROM concept_docs a
                 JOIN concept_docs b
                   ON a.doc_id = b.doc_id AND a.concept_id < b.concept_id
                 JOIN documents d ON d.doc_id = a.doc_id AND d.status = 'active'
                GROUP BY a.concept_id, b.concept_id
               HAVING n >= ?""",
            (min_docs,),
        ).fetchall()
        for r in rows:
            c.execute(
                """INSERT INTO concept_relations(src_id, dst_id, kind, weight)
                   VALUES (?,?,'cooccur',?)
                   ON CONFLICT(src_id, dst_id, kind) DO UPDATE SET weight=excluded.weight""",
                (r["src"], r["dst"], r["n"]),
            )
    return len(rows)


# ─── 후보 큐 (미매칭 개념, S4 §4) ─────────────────────────────────────────
def add_candidate(
    raw_norm: str, sample: str, doc_id: str | None = None,
    conn: sqlite3.Connection | None = None,
) -> None:
    """정규화 실패 개념을 후보로 누적 (doc_count++). 사람 승인 대기."""
    now = _now()
    with _conn(conn) as c:
        c.execute(
            """INSERT INTO concept_candidates(raw_norm, sample, doc_count, first_seen, last_seen)
               VALUES (?,?,1,?,?)
               ON CONFLICT(raw_norm) DO UPDATE SET
                 doc_count = concept_candidates.doc_count + 1,
                 last_seen = excluded.last_seen,
                 sample    = COALESCE(concept_candidates.sample, excluded.sample)""",
            (raw_norm, sample, now, now),
        )


def list_candidates(
    n: int = 50, conn: sqlite3.Connection | None = None
) -> list[dict]:
    """개념 후보 (데이터 탭) — doc_count 순."""
    with _conn(conn) as c:
        rows = c.execute(
            "SELECT raw_norm, sample, doc_count, first_seen, last_seen "
            "FROM concept_candidates ORDER BY doc_count DESC, last_seen DESC LIMIT ?",
            (n,),
        ).fetchall()
    return [dict(r) for r in rows]


def dismiss_candidate(raw_norm: str, conn: sqlite3.Connection | None = None) -> None:
    """후보 기각 (사람 판단)."""
    with _conn(conn) as c:
        c.execute("DELETE FROM concept_candidates WHERE raw_norm=?", (raw_norm,))


# ─── 읽기 ──────────────────────────────────────────────────────────────────
def top_concepts(
    n: int = 50, conn: sqlite3.Connection | None = None
) -> list[ConceptRow]:
    """degree 순 (위키 인덱스·그래프)."""
    with _conn(conn) as c:
        rows = c.execute(
            "SELECT * FROM concepts ORDER BY degree DESC, canonical ASC LIMIT ?", (n,)
        ).fetchall()
    return [_row_to_concept(r) for r in rows]


def concept_page(
    concept_id: str, conn: sqlite3.Connection | None = None
) -> ConceptPage | None:
    """정의 + 근거문서(active) + 관련개념 (위키 탭)."""
    with _conn(conn) as c:
        cr = c.execute("SELECT * FROM concepts WHERE concept_id=?", (concept_id,)).fetchone()
        if cr is None:
            return None
        aliases = [
            r["alias"] for r in c.execute(
                "SELECT alias FROM concept_aliases WHERE concept_id=? ORDER BY alias",
                (concept_id,),
            ).fetchall()
        ]
        doc_rows = c.execute(
            """SELECT d.doc_id, d.channel, d.source, d.original_path, d.title,
                      d.trust, d.status, d.industry, d.area, d.level, d.ingested_at
                 FROM concept_docs cd
                 JOIN documents d ON d.doc_id = cd.doc_id
                WHERE cd.concept_id=? AND d.status='active'
                ORDER BY cd.weight DESC""",
            (concept_id,),
        ).fetchall()
        related_rows = c.execute(
            """SELECT c2.* FROM concept_relations r
                 JOIN concepts c2 ON c2.concept_id = r.dst_id
                WHERE r.src_id=?
                ORDER BY r.weight DESC LIMIT 20""",
            (concept_id,),
        ).fetchall()
    return ConceptPage(
        concept=_row_to_concept(cr),
        aliases=aliases,
        docs=[DocRow(**{k: r[k] for k in r.keys()}) for r in doc_rows],
        related=[_row_to_concept(r) for r in related_rows],
    )


def concept_graph(
    center: str | None = None, hops: int = 2, limit: int = 200,
    conn: sqlite3.Connection | None = None,
) -> Graph:
    """개념 그래프 (그래프 탭). center 없으면 degree 상위 서브그래프."""
    with _conn(conn) as c:
        if center is None:
            node_ids = [
                r["concept_id"] for r in c.execute(
                    "SELECT concept_id FROM concepts ORDER BY degree DESC LIMIT ?", (limit,)
                ).fetchall()
            ]
        else:
            node_ids = {center}
            frontier = {center}
            for _ in range(max(hops, 0)):
                if not frontier:
                    break
                placeholders = ",".join("?" * len(frontier))
                rows = c.execute(
                    f"""SELECT src_id, dst_id FROM concept_relations
                         WHERE src_id IN ({placeholders}) OR dst_id IN ({placeholders})""",
                    (*frontier, *frontier),
                ).fetchall()
                nxt = set()
                for r in rows:
                    for cid in (r["src_id"], r["dst_id"]):
                        if cid not in node_ids:
                            nxt.add(cid)
                node_ids |= nxt
                frontier = nxt
            node_ids = list(node_ids)[:limit]

        if not node_ids:
            return Graph()
        placeholders = ",".join("?" * len(node_ids))
        nodes = [
            GraphNode(r["concept_id"], r["canonical"], r["degree"], r["trust"])
            for r in c.execute(
                f"SELECT concept_id, canonical, degree, trust FROM concepts "
                f"WHERE concept_id IN ({placeholders})",
                tuple(node_ids),
            ).fetchall()
        ]
        edges = [
            GraphEdge(r["src_id"], r["dst_id"], r["kind"], r["weight"])
            for r in c.execute(
                f"""SELECT src_id, dst_id, kind, weight FROM concept_relations
                     WHERE src_id IN ({placeholders}) AND dst_id IN ({placeholders})""",
                (*node_ids, *node_ids),
            ).fetchall()
        ]
    return Graph(nodes=nodes, edges=edges)
