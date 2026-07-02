"""V2.6.3.7 처리 큐 — 대기/처리중/완료 카운트 + 묶음·개별·선택 처리.

V2.6.3.8 — 큐 정의를 DB 기반으로 전환.
  - 대기열 = documents.kind='source' 행 중 K2 분석 안 됨
            (document_meta 없거나 classifier_version IS NULL)
  - 처리중 = document_meta.processing_started_at IS NOT NULL
  - 완료   = document_meta.classifier_version IS NOT NULL AND 락 없음
  - 영구보존 = 3-archive 카운트 (별개)

이유: 입력 탭이 디스크 카피 없이 DB에만 박을 수 있어(폴더 로딩 No-Copy),
디스크 기준 대기열은 *놓치는 자료*가 생긴다. DB 기준이 진실.

락 정책 (좀비 안전망):
  - 처리 직전 set_processing(doc_id) → processing_started_at=now
  - 성공/실패 후 clear_processing(doc_id) → processing_started_at=NULL
  - 30분 이상 처리중인 좀비 락 → 다음 묶음 처리 시 자동 해제
  - 동시 클릭으로 같은 doc 두 번 처리 시도 → set_processing이 False 반환
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from src.config import IRIS_DB_PATH


@dataclass
class QueueSnapshot:
    """현재 큐 상태 (V2.6.3.8 — DB 기반)."""
    waiting: int = 0          # 대기열 — DB에 있지만 K2 미분석
    in_progress: int = 0      # 처리중 — 락 박힘
    done: int = 0             # 완료 — K2 분석 통과
    archived: int = 0         # 영구보존 — 3-archive 카운트
    waiting_docs: list[dict] = field(default_factory=list)  # 대기 doc 미리보기 (doc_id, title, path)


@dataclass
class ProcessResult:
    """묶음 처리 1회 결과."""
    requested: int = 0        # 처리 요청 건수
    succeeded: int = 0
    failed: int = 0
    skipped: int = 0          # 이미 처리중이거나 처리 완료된 것
    errors: list[tuple[str, str]] = field(default_factory=list)


# ─── 큐 상태 측정 (V2.6.3.8 — DB 기반) ──────────────────────────────
def measure_queue(db_path: Path = IRIS_DB_PATH, *, max_list: int = 50) -> QueueSnapshot:
    """DB 기준으로 대기/처리중/완료 카운트.

    대기 = documents.kind='source' 행 중 K2 분석 안 됨
           (document_meta 없거나 classifier_version IS NULL이고 락 없음)
    처리중 = document_meta.processing_started_at NOT NULL
    완료 = document_meta.classifier_version NOT NULL AND 락 없음
    """
    s = QueueSnapshot()

    if not db_path.exists():
        return s

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        # 처리중 — 락 박힘
        s.in_progress = conn.execute(
            "SELECT COUNT(*) FROM document_meta "
            "WHERE processing_started_at IS NOT NULL"
        ).fetchone()[0]

        # 완료 — K2 분석 통과 (분류기 버전 박힘) AND 락 없음
        s.done = conn.execute(
            "SELECT COUNT(*) FROM document_meta "
            "WHERE classifier_version IS NOT NULL "
            "  AND processing_started_at IS NULL"
        ).fetchone()[0]

        # 대기 — DB에 source로 박혀 있지만 K2 미분석 (락 없음 = 진짜 대기)
        s.waiting = conn.execute(
            "SELECT COUNT(*) FROM documents d "
            "LEFT JOIN document_meta m ON d.doc_id = m.doc_id "
            "WHERE d.kind = 'source' "
            "  AND (m.doc_id IS NULL "
            "       OR (m.classifier_version IS NULL "
            "           AND m.processing_started_at IS NULL))"
        ).fetchone()[0]

        # 대기 doc 미리보기 (선택 처리용)
        rows = conn.execute(
            "SELECT d.doc_id, d.title, d.path FROM documents d "
            "LEFT JOIN document_meta m ON d.doc_id = m.doc_id "
            "WHERE d.kind = 'source' "
            "  AND (m.doc_id IS NULL "
            "       OR (m.classifier_version IS NULL "
            "           AND m.processing_started_at IS NULL)) "
            "ORDER BY d.doc_id "
            "LIMIT ?",
            (max_list,),
        ).fetchall()
        s.waiting_docs = [
            {"doc_id": r["doc_id"], "title": r["title"] or "(no title)",
             "path": r["path"] or ""}
            for r in rows
        ]
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


# ─── 묶음 처리 (V2.6.3.8 — DB doc_id 기반) ────────────────────────────
def fetch_waiting(n: int = 5, *, db_path: Path = IRIS_DB_PATH) -> list[str]:
    """대기열 위에서 N건 fetch (doc_id 리스트). V2.6.3.8: 디스크 path가 아니라 DB doc_id."""
    snap = measure_queue(db_path=db_path, max_list=max(n, 5))
    return [d["doc_id"] for d in snap.waiting_docs[:n]]


def _load_doc_text(conn: sqlite3.Connection, doc_id: str) -> tuple[str, str]:
    """DB chunks에서 본문 재조립. 반환 (title, body)."""
    title_row = conn.execute(
        "SELECT title FROM documents WHERE doc_id=?", (doc_id,)
    ).fetchone()
    title = title_row[0] if title_row else doc_id

    chunks = conn.execute(
        "SELECT text FROM chunks WHERE doc_id=? ORDER BY ord", (doc_id,)
    ).fetchall()
    body = "\n\n".join(c[0] for c in chunks)
    return title, body


def process_batch(doc_ids: list[str], *, use_k2: bool = True,
                  db_path: Path = IRIS_DB_PATH) -> ProcessResult:
    """주어진 doc_id들을 K2 분석. 본문은 DB chunks에서 재조립.

    V2.6.3.8: 디스크 파일이 아니라 DB doc_id를 받는다. 입력 탭이 박은
    documents/chunks가 진실원이므로 path 없어도 처리 가능.
    """
    res = ProcessResult()
    res.requested = len(doc_ids)

    if not doc_ids:
        return res

    # 좀비 락 먼저 정리 (안전망)
    clear_stale_locks(stale_minutes=30, db_path=db_path)

    if use_k2:
        from src.engine.process import k2_pipeline as k2pl
        from src import document_meta as dm
    else:
        from src.engine.process.classify import suggest_classification

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")

    if use_k2:
        dm.ensure_schema(conn=conn)
        conn.commit()

    try:
        for doc_id in doc_ids:
            # 락 시도
            if not set_processing(doc_id, db_path=db_path):
                res.skipped += 1
                continue

            try:
                title, body = _load_doc_text(conn, doc_id)
                if not body.strip():
                    res.skipped += 1
                    clear_processing(doc_id, db_path=db_path)
                    continue

                if use_k2:
                    # V2.7.0 — 3 단계 파이프라인. 각 단계 직후 timestamp 박음.
                    # ① extract (deep 모델 — fast는 JSON 안정성 낮음)
                    r_ext = k2pl.stage_extract(title, body, role="deep")
                    if r_ext.ok:
                        k2pl.mark_stage(conn, doc_id, "extract")
                        conn.commit()
                    keywords = r_ext.data if r_ext.ok else {"topics": [], "entities": [], "concepts": []}

                    # ② classify
                    r_cls = k2pl.stage_classify(title, body, keywords, role="deep")
                    if r_cls.ok:
                        k2pl.mark_stage(conn, doc_id, "classify")
                        conn.commit()
                        classification = r_cls.data
                    else:
                        # fallback 규칙
                        rule = suggest_classification(title, body) if False else None
                        from src.engine.process.classify import suggest_classification as _sc
                        rule = _sc(title, body)
                        classification = {
                            "industry": rule.get("industry"),
                            "area": rule.get("area"),
                            "level": rule.get("level"),
                            "automation_levels": [],
                            "system_domains": [],
                            "mgmt_categories": [],
                            "confidence": 0.3,
                            "reason": f"LLM classify 실패, 규칙 fallback: {r_cls.error}",
                        }

                    # ③ summarize
                    r_sum = k2pl.stage_summarize(title, body, classification, role="deep")
                    if r_sum.ok:
                        k2pl.mark_stage(conn, doc_id, "summarize")
                        conn.commit()

                    # 최종 K2Result 합쳐서 한 번에 upsert (호환)
                    from src.engine.process.k2 import K2Result, _k2_version
                    used_model = r_cls.model or r_sum.model or r_ext.model
                    classifier_version = _k2_version(used_model) if used_model else "rule-fallback"
                    any_fail = not (r_ext.ok and r_cls.ok and r_sum.ok)

                    k2_result = K2Result(
                        industry=classification.get("industry"),
                        area=classification.get("area"),
                        level=classification.get("level"),
                        summary=r_sum.data.get("summary", ""),
                        topics=keywords.get("topics", []),
                        entities=keywords.get("entities", []),
                        concepts=keywords.get("concepts", []),
                        reason=classification.get("reason", ""),
                        confidence=classification.get("confidence", 0.0),
                        elapsed_ms=r_ext.elapsed_ms + r_cls.elapsed_ms + r_sum.elapsed_ms,
                        classifier_version=classifier_version,
                        fallback_used=any_fail,
                        automation_levels=classification.get("automation_levels", []),
                        system_domains=classification.get("system_domains", []),
                        mgmt_categories=classification.get("mgmt_categories", []),
                        blurb_industry=r_sum.data.get("blurb_industry", ""),
                        blurb_system=r_sum.data.get("blurb_system", ""),
                        blurb_mgmt=r_sum.data.get("blurb_mgmt", ""),
                    )
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
                        (sg.get("industry"), sg.get("area"), sg.get("level"), doc_id),
                    )
                    # K2 OFF로도 *완료* 표식 박음 — measure_queue가 done으로 카운트하게.
                    # classifier_version='rule-only-v1' 이 식별자.
                    conn.execute(
                        "INSERT INTO document_meta (doc_id, classifier_version) "
                        "VALUES (?, 'rule-only-v1') "
                        "ON CONFLICT(doc_id) DO UPDATE SET classifier_version='rule-only-v1'",
                        (doc_id,),
                    )
                conn.commit()
                clear_processing(doc_id, db_path=db_path)
                res.succeeded += 1
            except Exception as e:
                res.errors.append((doc_id, f"{type(e).__name__}: {e}"))
                res.failed += 1
                clear_processing(doc_id, db_path=db_path)
    finally:
        conn.close()

    return res


__all__ = [
    "QueueSnapshot", "ProcessResult",
    "measure_queue", "fetch_waiting", "process_batch",
    "set_processing", "clear_processing", "clear_stale_locks",
]
