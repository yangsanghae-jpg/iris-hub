"""K1~K3 재처리 — raw 디스크 자료를 documents/chunks/FTS에 일괄 박기.

본 모듈은 iris-system raw_intake 내부 함수를 import해서 hub UI에서
*사용자 통제로* 호출한다. iris-system 코드는 안 건드림.

대상:
  - raw/ 루트의 .md/.txt
  - raw/_external/<source>/ 하위의 .md (외부응답 격납)

흐름 (각 파일):
  1. doc_id_for(path) — content-based sha1
  2. parse_frontmatter + split_chunks
  3. upsert_raw_doc — documents/chunks 박기
  4. classify.suggest_classification → UPDATE industry/area/level (덮어쓰기)
  5. 끝에 FTS rebuild_all 1회

정책:
  - "덮어쓰기" — 사용자 합의 (사람 SQL 시드도 덮어씀)
  - 본문 chunk 0개면 skip
  - 한 파일 실패해도 나머지 진행
"""
from __future__ import annotations

import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

IRIS_SYSTEM = Path("/Users/iris/Documents/0Dev/iris-system")
if str(IRIS_SYSTEM) not in sys.path:
    sys.path.insert(0, str(IRIS_SYSTEM))

RAW_DIR = IRIS_SYSTEM / "knowledge" / "raw"
DB_PATH = IRIS_SYSTEM / "knowledge" / "_index.db"
INCLUDE_SUFFIXES = {".md", ".txt"}


@dataclass
class ReprocessResult:
    scanned: int = 0
    upserted: int = 0
    skipped_empty: int = 0
    classified: int = 0
    errors: list[tuple[str, str]] = field(default_factory=list)
    fts_counts: dict | None = None

    @property
    def ok(self) -> bool:
        return not self.errors


def _walk_raw(scope: str = "all") -> Iterable[Path]:
    """raw 자료를 재귀로 훑음.

    scope:
      "all"      — raw/ 전체 (루트 + _external/ 하위)
      "external" — raw/_external/ 하위만
      "root"     — raw/ 루트만 (raw_intake.main과 동일 범위)
    """
    if not RAW_DIR.exists():
        return

    if scope == "external":
        ext = RAW_DIR / "_external"
        if ext.exists():
            yield from (p for p in ext.rglob("*")
                        if p.is_file() and p.suffix.lower() in INCLUDE_SUFFIXES)
    elif scope == "root":
        yield from (p for p in RAW_DIR.iterdir()
                    if p.is_file() and p.suffix.lower() in INCLUDE_SUFFIXES)
    else:  # all
        yield from (p for p in RAW_DIR.rglob("*")
                    if p.is_file() and p.suffix.lower() in INCLUDE_SUFFIXES)


def reprocess(scope: str = "all", *, only_null: bool = False) -> ReprocessResult:
    """K1~K3 일괄 재처리.

    scope: 'all' / 'external' / 'root'
    only_null: True면 documents에 분류가 NULL인 것만 갱신.
               False면 덮어쓰기 (기본 — 사용자 합의).
    """
    res = ReprocessResult()

    try:
        from apps.ingest.raw_intake import (
            doc_id_for, parse_frontmatter, split_chunks, upsert_raw_doc,
        )
        from apps.ingest.fts_sync import rebuild_all
    except Exception as e:
        res.errors.append(("import", f"{type(e).__name__}: {e}"))
        return res

    if not DB_PATH.exists():
        res.errors.append(("db", f"DB 없음: {DB_PATH}"))
        return res

    try:
        from src.classify import suggest_classification
    except Exception as e:
        res.errors.append(("classify", f"import 실패: {e}"))
        return res

    files = list(_walk_raw(scope))
    res.scanned = len(files)

    if not files:
        return res

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")

    try:
        for path in files:
            try:
                text = path.read_text(encoding="utf-8")
                meta, body = parse_frontmatter(text)
                title = meta.get("title") or path.stem
                chunks = split_chunks(body)
                if not chunks:
                    res.skipped_empty += 1
                    continue

                doc_id = doc_id_for(path)
                upsert_raw_doc(conn, doc_id, path, title, chunks)
                res.upserted += 1

                # classify 추천 → UPDATE
                clf = suggest_classification(title, body)
                ind, area, lvl = clf.get("industry"), clf.get("area"), clf.get("level")

                if only_null:
                    # 현 DB가 NULL인 컬럼만 채움
                    cur = conn.execute(
                        "SELECT industry, area, level FROM documents WHERE doc_id=?",
                        (doc_id,)
                    ).fetchone()
                    if cur:
                        ind = ind if cur[0] is None else cur[0]
                        area = area if cur[1] is None else cur[1]
                        lvl = lvl if cur[2] is None else cur[2]

                if any(v is not None for v in (ind, area, lvl)):
                    conn.execute(
                        "UPDATE documents SET industry=?, area=?, level=? "
                        "WHERE doc_id=?",
                        (ind, area, lvl, doc_id),
                    )
                    if any(v is not None for v in (ind, area, lvl)):
                        res.classified += 1

            except Exception as e:
                res.errors.append((path.name, f"{type(e).__name__}: {e}"))

        # FTS 동기 — 끝에 1회
        try:
            res.fts_counts = rebuild_all(conn)
        except Exception as e:
            res.errors.append(("fts_sync", f"{type(e).__name__}: {e}"))

        conn.commit()
    finally:
        conn.close()

    return res


__all__ = ["ReprocessResult", "reprocess", "RAW_DIR", "DB_PATH"]
