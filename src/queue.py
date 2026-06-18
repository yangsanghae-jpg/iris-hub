"""V2.6.3.7 처리 큐 — 대기/처리중/완료 카운트 + 묶음·개별·선택 처리.

큐의 정의 (옵션 A — 가상 큐, 별도 테이블 없음):
  - 대기열 = 1-inbox/intake + _external/ 하위 파일 중 *K2 미분석* 또는 *DB에 없는 doc*
  - 처리중 = document_meta.processing_started_at IS NOT NULL
  - 완료 = document_meta 행 있음 AND processing_started_at IS NULL

락 정책:
  - 처리 직전 set_processing(doc_id) → processing_started_at=now
  - 성공/실패 후 clear_processing(doc_id) → processing_started_at=NULL
  - 좀비 락 (처리 시작 후 N분 경과): 자동 무시 (다음 묶음에서 재시도)
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from src.config import IRIS_DB_PATH, IRIS_RAW_PATH
from src.reprocess import _walk_raw, INCLUDE_SUFFIXES  # noqa: F401


@dataclass
class QueueSnapshot:
    """현재 큐 상태."""
    waiting: int = 0          # 대기열 — 디스크에 있지만 K2 미분석
    in_progress: int = 0      # 처리중 — 락 박혀 있음
    done: int = 0             # 완료 — document_meta 행 있음 (K2 분석됨)
    archived: int = 0         # 영구보존 — 3-archive 카피 완료
    waiting_files: list[Path] = field(default_factory=list)  # 대기 파일 목록 (uperbund N)


@dataclass
class ProcessResult:
    """묶음 처리 1회 결과."""
    requested: int = 0        # 처리 요청 건수
    succeeded: int = 0
    failed: int = 0
    skipped: int = 0          # 이미 처리중이거나 처리 완료된 것
    errors: list[tuple[str, str]] = field(default_factory=list)


# ─── 큐 상태 측정 ─────────────────────────────────────────────────────
def _doc_id_for_path(path: Path) -> str:
    """raw_intake와 같은 규칙으로 doc_id 추출."""
    from src.ingest.raw_intake import doc_id_for
    return doc_id_for(path)


def measure_queue(db_path: Path = IRIS_DB_PATH, *, max_list: int = 50) -> QueueSnapshot:
    """디스크 + DB를 교차해서 대기/처리중/완료 카운트."""
    s = QueueSnapshot()

    # 디스크 파일 목록
    files = list(_walk_raw("all"))

    if not db_path.exists():
        # DB 부재 → 모두 대기
        s.waiting = len(files)
        s.waiting_files = files[:max_list]
        return s

    conn = sqlite3.connect(db_path)
    try:
        # 처리중·완료 카운트
        s.in_progress = conn.execute(
            "SELECT COUNT(*) FROM document_meta "
            "WHERE processing_started_at IS NOT NULL"
        ).fetchone()[0]
        s.done = conn.execute(
            "SELECT COUNT(*) FROM document_meta "
            "WHERE processing_started_at IS NULL"
        ).fetchone()[0]

        # 디스크 파일 중 K2 미분석 = 대기
        done_ids = {
            r[0] for r in conn.execute(
                "SELECT doc_id FROM document_meta"
            ).fetchall()
        }

        for p in files:
            try:
                did = _doc_id_for_path(p)
            except Exception:
                # doc_id 산출 실패는 일단 대기로
                if len(s.waiting_files) < max_list:
                    s.waiting_files.append(p)
                s.waiting += 1
                continue
            if did in done_ids:
                continue
            s.waiting += 1
            if len(s.waiting_files) < max_list:
                s.waiting_files.append(p)
    finally:
        conn.close()

    # 3-archive 카운트 (영구보존)
    from src.config import IRIS_KNOWLEDGE_ARCHIVE
    if IRIS_KNOWLEDGE_ARCHIVE.exists():
        for date_dir in IRIS_KNOWLEDGE_ARCHIVE.iterdir():
            if not date_dir.is_dir():
                continue
            s.archived += sum(1 for p in date_dir.iterdir() if p.is_dir())

    return s


# ─── 락 (처리중 표식) ─────────────────────────────────────────────────
def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def set_processing(doc_id: str, *, db_path: Path = IRIS_DB_PATH) -> bool:
    """처리 시작 표식. 이미 처리중이면 False (중복 방지)."""
    if not db_path.exists():
        return False
    conn = sqlite3.connect(db_path)
    try:
        # document_meta 행 없으면 placeholder로 만들어 락 박음
        row = conn.execute(
            "SELECT processing_started_at FROM document_meta WHERE doc_id=?",
            (doc_id,),
        ).fetchone()
        if row and row[0]:
            return False  # 이미 처리중
        if row:
            conn.execute(
                "UPDATE document_meta SET processing_started_at=? WHERE doc_id=?",
                (_now_iso(), doc_id),
            )
        else:
            conn.execute(
                "INSERT INTO document_meta (doc_id, processing_started_at) VALUES (?, ?)",
                (doc_id, _now_iso()),
            )
        conn.commit()
        return True
    finally:
        conn.close()


def clear_processing(doc_id: str, *, db_path: Path = IRIS_DB_PATH) -> None:
    """처리 종료 — 락 해제."""
    if not db_path.exists():
        return
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "UPDATE document_meta SET processing_started_at=NULL WHERE doc_id=?",
            (doc_id,),
        )
        conn.commit()
    finally:
        conn.close()


def clear_stale_locks(stale_minutes: int = 30, *, db_path: Path = IRIS_DB_PATH) -> int:
    """N분 이상 처리중인 좀비 락 해제. 반환=정리된 건수."""
    if not db_path.exists():
        return 0
    cutoff = datetime.now(timezone.utc).timestamp() - stale_minutes * 60
    cutoff_iso = datetime.fromtimestamp(cutoff, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            "UPDATE document_meta SET processing_started_at=NULL "
            "WHERE processing_started_at IS NOT NULL AND processing_started_at < ?",
            (cutoff_iso,),
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


# ─── 묶음 처리 (batch fetch + 처리) ───────────────────────────────────
def fetch_waiting(n: int = 5, *, db_path: Path = IRIS_DB_PATH) -> list[Path]:
    """대기열 위에서 N건 fetch (디스크 파일 객체)."""
    snap = measure_queue(db_path=db_path, max_list=max(n, 5))
    return snap.waiting_files[:n]


def process_batch(paths: list[Path], *, use_k2: bool = True,
                  db_path: Path = IRIS_DB_PATH) -> ProcessResult:
    """주어진 파일들을 1건씩 재처리. 각 파일에 락 박고 → reprocess 단일파일 흐름 → 락 해제.

    인자:
      paths: 처리할 파일 목록 (이미 fetch된 것)
      use_k2: K2 LLM 분석 여부
    """
    res = ProcessResult()
    res.requested = len(paths)

    if not paths:
        return res

    # 좀비 락 먼저 정리
    clear_stale_locks(stale_minutes=30, db_path=db_path)

    from src.ingest.raw_intake import (
        doc_id_for, parse_frontmatter, split_chunks, upsert_raw_doc,
    )
    from src.ingest.fts_sync import rebuild_all

    if use_k2:
        from src import k2 as k2mod
        from src import document_meta as dm
    else:
        from src.classify import suggest_classification

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")

    if use_k2:
        dm.ensure_schema(conn=conn)
        conn.commit()

    try:
        for path in paths:
            try:
                doc_id = doc_id_for(path)
            except Exception as e:
                res.errors.append((path.name, f"doc_id: {e}"))
                res.failed += 1
                continue

            # 락 시도 — 이미 처리중이면 skip
            if not set_processing(doc_id, db_path=db_path):
                res.skipped += 1
                continue

            try:
                text = path.read_text(encoding="utf-8")
                meta, body = parse_frontmatter(text)
                title = meta.get("title") or path.stem
                chunks = split_chunks(body)
                if not chunks:
                    res.skipped += 1
                    clear_processing(doc_id, db_path=db_path)
                    continue

                upsert_raw_doc(conn, doc_id, path, title, chunks)

                if use_k2:
                    k2_result = k2mod.analyze(title, body, timeout=60.0)
                    dm.upsert(
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
                    if k2_result.industry or k2_result.area or k2_result.level:
                        conn.execute(
                            "UPDATE documents SET industry=?, area=?, level=? "
                            "WHERE doc_id=?",
                            (k2_result.industry, k2_result.area, k2_result.level, doc_id),
                        )
                else:
                    sg = suggest_classification(title, body)
                    conn.execute(
                        "UPDATE documents SET industry=?, area=?, level=? WHERE doc_id=?",
                        (sg.industry, sg.area, sg.level, doc_id),
                    )
                conn.commit()
                clear_processing(doc_id, db_path=db_path)
                res.succeeded += 1
            except Exception as e:
                res.errors.append((path.name, f"{type(e).__name__}: {e}"))
                res.failed += 1
                clear_processing(doc_id, db_path=db_path)
    finally:
        conn.close()

    # FTS 1회 재구축
    if res.succeeded > 0:
        try:
            rebuild_all(db_path)
        except Exception as e:
            res.errors.append(("fts_rebuild", f"{type(e).__name__}: {e}"))

    return res


__all__ = [
    "QueueSnapshot", "ProcessResult",
    "measure_queue", "fetch_waiting", "process_batch",
    "set_processing", "clear_processing", "clear_stale_locks",
]
