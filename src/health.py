"""좀비 안전망 (V2.6.3.8).

목적: 데이터 파이프라인 어딘가가 *반쪽 박힘*으로 부패하는 것을 자동 감지·정리.

좀비 패턴:
  (1) 처리 락 좀비 — processing_started_at NOT NULL이 N분 이상 → 해제
  (2) 본문 없는 doc — documents 행 있는데 chunks 0개 → 삭제
  (3) FTS 불일치 — documents 카운트 ≠ documents_fts 카운트 → 재구축
  (4) 고아 chunks — chunks.doc_id가 documents에 없음 → 삭제
  (5) 고아 document_meta — meta.doc_id가 documents에 없음 → 삭제
  (6) mirror 좀비 — V2.6.3.6 obsidian_sync.sync_all이 이미 처리 (raw_/ref_/sec_ 패턴)

호출:
  - 흐름 탭 측정 시: clear_stale_locks 자동 호출 (이미 박혀 있음)
  - process_batch 시작 시: clear_stale_locks 자동
  - 수동 점검: src.health.audit() — 흐름 탭 UI에서 "🛡 안전망 점검" 버튼
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from src.config import IRIS_DB_PATH


@dataclass
class AuditReport:
    """무결성 점검 결과."""
    stale_locks: int = 0          # 좀비 락 — 자동 해제됨
    empty_docs: list[str] = field(default_factory=list)        # chunks 0개인 doc_id
    orphan_chunks: int = 0        # 고아 chunks 행 수
    orphan_meta: int = 0          # 고아 document_meta 행 수
    fts_mismatch: int = 0         # documents 카운트 ≠ documents_fts 카운트 (양수=fts 부족, 음수=fts 잉여)
    missing_archive: list[str] = field(default_factory=list)   # V2.6.3.9 — DB path가 archive 경로 가리키는데 파일 없음
    auto_fixed: int = 0           # 자동 정정된 항목 수
    notes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return (not self.empty_docs
                and self.orphan_chunks == 0
                and self.orphan_meta == 0
                and self.fts_mismatch == 0
                and self.stale_locks == 0
                and not self.missing_archive)


def audit(db_path: Path = IRIS_DB_PATH, *, auto_fix: bool = True,
          stale_minutes: int = 30) -> AuditReport:
    """무결성 점검 + (옵션) 자동 정정."""
    rep = AuditReport()
    if not db_path.exists():
        rep.notes.append(f"DB 없음: {db_path}")
        return rep

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=OFF")  # 일부 정리 단계에서 임시 OFF
    try:
        # (1) 좀비 락 정리
        from src import queue as q
        cleared = q.clear_stale_locks(stale_minutes=stale_minutes, db_path=db_path)
        rep.stale_locks = cleared
        if cleared:
            rep.auto_fixed += cleared
            rep.notes.append(f"좀비 락 {cleared}건 해제 ({stale_minutes}분 이상)")

        # (2) 본문 없는 doc (kind='source')
        rows = conn.execute(
            "SELECT d.doc_id FROM documents d "
            "LEFT JOIN chunks c ON d.doc_id = c.doc_id "
            "WHERE d.kind = 'source' AND c.doc_id IS NULL"
        ).fetchall()
        rep.empty_docs = [r[0] for r in rows]
        if rep.empty_docs and auto_fix:
            conn.executemany(
                "DELETE FROM documents WHERE doc_id=?",
                [(d,) for d in rep.empty_docs],
            )
            conn.commit()
            rep.auto_fixed += len(rep.empty_docs)
            rep.notes.append(f"본문 없는 doc {len(rep.empty_docs)}건 삭제")

        # (4) 고아 chunks (doc_id가 documents에 없음)
        orphan_chunks = conn.execute(
            "SELECT COUNT(*) FROM chunks c "
            "LEFT JOIN documents d ON c.doc_id = d.doc_id "
            "WHERE d.doc_id IS NULL"
        ).fetchone()[0]
        rep.orphan_chunks = orphan_chunks
        if orphan_chunks and auto_fix:
            conn.execute(
                "DELETE FROM chunks WHERE doc_id NOT IN "
                "(SELECT doc_id FROM documents)"
            )
            conn.commit()
            rep.auto_fixed += orphan_chunks
            rep.notes.append(f"고아 chunks {orphan_chunks}건 삭제")

        # (5) 고아 document_meta
        orphan_meta = conn.execute(
            "SELECT COUNT(*) FROM document_meta m "
            "LEFT JOIN documents d ON m.doc_id = d.doc_id "
            "WHERE d.doc_id IS NULL"
        ).fetchone()[0]
        rep.orphan_meta = orphan_meta
        if orphan_meta and auto_fix:
            conn.execute(
                "DELETE FROM document_meta WHERE doc_id NOT IN "
                "(SELECT doc_id FROM documents)"
            )
            conn.commit()
            rep.auto_fixed += orphan_meta
            rep.notes.append(f"고아 document_meta {orphan_meta}건 삭제")

        # (3) FTS 카운트 불일치
        d_count = conn.execute(
            "SELECT COUNT(*) FROM documents"
        ).fetchone()[0]
        f_count = conn.execute(
            "SELECT COUNT(*) FROM documents_fts"
        ).fetchone()[0]
        rep.fts_mismatch = d_count - f_count
        if rep.fts_mismatch != 0 and auto_fix:
            try:
                from src.ingest.fts_sync import rebuild_all
                rebuild_all(db_path)
                rep.auto_fixed += abs(rep.fts_mismatch)
                rep.notes.append(
                    f"FTS 재구축 (격차 {rep.fts_mismatch})"
                )
            except Exception as e:
                rep.notes.append(f"FTS 재구축 실패: {e}")

        # (7) V2.6.3.9 — archive 정합성: DB path가 archive 경로 가리키는데 파일 없음
        from src.config import IRIS_KNOWLEDGE_ARCHIVE
        archive_str = str(IRIS_KNOWLEDGE_ARCHIVE)
        rows = conn.execute(
            "SELECT doc_id, path FROM documents WHERE path LIKE ?",
            (archive_str + "%",),
        ).fetchall()
        missing = []
        for doc_id, path in rows:
            if not Path(path).exists():
                missing.append(doc_id)
        rep.missing_archive = missing
        if missing:
            rep.notes.append(
                f"archive 파일 누락 {len(missing)}건 — 자동 정정 안 함 (수동 검토 필요)"
            )
    finally:
        conn.close()

    return rep


__all__ = ["AuditReport", "audit"]
