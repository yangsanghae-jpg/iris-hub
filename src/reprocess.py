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

from src.config import IRIS_DB_PATH, IRIS_RAW_PATH

# V2.6.3.3: iris-knowledge로 경로 단일화. legacy IRIS_SYSTEM 참조 제거.
RAW_DIR = IRIS_RAW_PATH
DB_PATH = IRIS_DB_PATH
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


def reprocess(scope: str = "all", *, only_null: bool = False,
              use_k2: bool = True) -> ReprocessResult:
    """K1~K3 일괄 재처리.

    scope: 'all' / 'external' / 'root'
    only_null: True면 documents에 분류가 NULL인 것만 갱신.
               False면 덮어쓰기 (기본 — 사용자 합의).
    use_k2: True면 LLM K2 분석 (느림, 자료당 5~30초).
            False면 규칙 매칭만 (빠름).
    """
    res = ReprocessResult()

    try:
        from src.ingest.raw_intake import (
            doc_id_for, parse_frontmatter, split_chunks, upsert_raw_doc,
        )
        from src.ingest.fts_sync import rebuild_all
    except Exception as e:
        res.errors.append(("import", f"{type(e).__name__}: {e}"))
        return res

    if not DB_PATH.exists():
        res.errors.append(("db", f"DB 없음: {DB_PATH}"))
        return res

    # 분류기 — K2 우선, 실패 시 규칙
    if use_k2:
        try:
            from src import k2 as k2mod
            from src import document_meta
        except Exception as e:
            res.errors.append(("k2", f"K2 모듈 import 실패, 규칙 사용: {e}"))
            use_k2 = False

    if not use_k2:
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
    # writer 락 충돌 시 5초 대기 (자체 연결 안에서도 안전망)
    conn.execute("PRAGMA busy_timeout=5000")

    # K2 schema는 reprocess의 conn 위에서 보장 — 별도 연결 안 만듦
    if use_k2:
        try:
            document_meta.ensure_schema(conn=conn)
            conn.commit()
        except Exception as e:
            res.errors.append(("document_meta_schema", f"{type(e).__name__}: {e}"))
            use_k2 = False

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

                # 분류 — K2 또는 규칙
                if use_k2:
                    k2_result = k2mod.analyze(title, body, timeout=60.0)
                    ind, area, lvl = k2_result.industry, k2_result.area, k2_result.level
                    # document_meta 박기 — *같은 conn에 합류*하여 락 충돌 회피
                    try:
                        document_meta.upsert(
                            doc_id,
                            summary=k2_result.summary,
                            topics=k2_result.topics,
                            entities=k2_result.entities,
                            concepts=k2_result.concepts,
                            classifier_version=k2_result.classifier_version,
                            confidence=k2_result.confidence,
                            reason=k2_result.reason,
                            k2_ms=k2_result.elapsed_ms,
                            fallback_used=k2_result.fallback_used,
                            automation_levels=k2_result.automation_levels,
                            system_domains=k2_result.system_domains,
                            mgmt_categories=k2_result.mgmt_categories,
                            blurb_industry=k2_result.blurb_industry,
                            blurb_system=k2_result.blurb_system,
                            blurb_mgmt=k2_result.blurb_mgmt,
                            conn=conn,
                        )
                    except Exception as e:
                        res.errors.append((path.name, f"document_meta: {e}"))
                else:
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

                # 자료 1건이 끝날 때마다 commit — 락 holding time 최소화 +
                # 처리 중 죽어도 누적이 살아남음
                conn.commit()

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
