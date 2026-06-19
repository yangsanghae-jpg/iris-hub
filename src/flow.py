"""V2.6.3.5 — 처리 흐름 측정. 1-inbox → 3-archive ↔ _index.db ↔ mirror ↔ wiki.

각 단계의 *현 잔량*과 *최근 활동*을 측정. 디스크 + DB 양쪽에서 박는다.

설계 요점:
- 1-inbox 4개 채널: intake/external/folder-staging/_failed (디스크 카운트)
- 3-archive: 누적 doc 카운트 + 마지막 날짜
- _index.db: documents/chunks/fts (measurements 위임)
- mirror/wiki: 디스크 md 카운트
- 동기 점검: documents(kind=source) ↔ mirror_md 카운트 차이로 정합성 표시
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .config import (
    IRIS_KNOWLEDGE_ARCHIVE,
    IRIS_KNOWLEDGE_EXTERNAL,
    IRIS_KNOWLEDGE_INBOX,
    IRIS_KNOWLEDGE_MIRROR,
    IRIS_KNOWLEDGE_RAW,
    IRIS_KNOWLEDGE_STAGING,
    IRIS_KNOWLEDGE_WIKI,
)
from .measurements import measure


@dataclass
class InboxStage:
    intake: int = 0          # 1-inbox/intake (사용자가 박은 자료)
    external: int = 0        # 1-inbox/external (외부 LLM 응답)
    staging: int = 0         # 1-inbox/folder-staging (폴더 일괄)
    failed: int = 0          # 1-inbox/_failed (처리 실패)

    @property
    def total(self) -> int:
        return self.intake + self.external + self.staging + self.failed


@dataclass
class ArchiveStage:
    docs: int = 0            # 3-archive/<date>/<doc_id>/ 카운트
    days: int = 0            # 날짜 폴더 수
    last_date: str = "-"     # 마지막 활동 날짜


@dataclass
class DBStage:
    exists: bool = False
    documents: int = 0
    source_docs: int = 0     # kind=source인 행만 (mirror와 매칭)
    eligible: int = 0        # V2.6.3.6 — mirror 진입 자격 통과 (K2+매트릭스)
    chunks: int = 0
    fts: int = 0
    db_size_mb: float = 0.0
    # V2.7.0 — K2 단계별 진척
    extract_done: int = 0
    classify_done: int = 0
    summarize_done: int = 0


@dataclass
class MirrorStage:
    md_count: int = 0
    exists: bool = False


@dataclass
class WikiStage:
    md_count: int = 0
    exists: bool = False


@dataclass
class FlowSnapshot:
    inbox: InboxStage = field(default_factory=InboxStage)
    archive: ArchiveStage = field(default_factory=ArchiveStage)
    db: DBStage = field(default_factory=DBStage)
    mirror: MirrorStage = field(default_factory=MirrorStage)
    wiki: WikiStage = field(default_factory=WikiStage)

    @property
    def mirror_db_gap(self) -> int:
        """양수면 자격 통과 DB가 mirror보다 많음(미동기), 음수면 mirror가 더 많음(좀비/거절 잔재)."""
        return self.db.eligible - self.mirror.md_count

    @property
    def archive_db_gap(self) -> int:
        """양수면 3-archive가 DB보다 많음 (정상: archive는 누적 보존)."""
        return self.archive.docs - self.db.source_docs


def _count_files(dir_path: Path, suffixes: set[str] | None = None) -> int:
    if not dir_path.exists():
        return 0
    if suffixes is None:
        return sum(1 for p in dir_path.iterdir() if p.is_file())
    return sum(1 for p in dir_path.iterdir() if p.is_file() and p.suffix.lower() in suffixes)


def _measure_inbox() -> InboxStage:
    return InboxStage(
        intake=_count_files(IRIS_KNOWLEDGE_RAW),
        external=_count_files(IRIS_KNOWLEDGE_EXTERNAL),
        staging=_count_files(IRIS_KNOWLEDGE_STAGING),
        failed=_count_files(IRIS_KNOWLEDGE_INBOX / "_failed"),
    )


def _measure_archive() -> ArchiveStage:
    s = ArchiveStage()
    if not IRIS_KNOWLEDGE_ARCHIVE.exists():
        return s
    date_dirs = sorted(
        [d for d in IRIS_KNOWLEDGE_ARCHIVE.iterdir() if d.is_dir()],
        reverse=True,
    )
    s.days = len(date_dirs)
    if date_dirs:
        s.last_date = date_dirs[0].name
    for d in date_dirs:
        s.docs += sum(1 for p in d.iterdir() if p.is_dir())
    return s


def _measure_db() -> DBStage:
    import sqlite3
    m = measure()
    s = DBStage(exists=m.db_exists)
    if not m.db_exists:
        return s
    s.documents = m.documents_total
    s.source_docs = m.kind_dist.get("source", 0)
    s.chunks = m.chunks_total
    s.fts = m.fts_total
    s.db_size_mb = round(m.db_size / (1024 * 1024), 1)

    # V2.6.3.6 — mirror 진입 자격 통과 카운트 (K2 분석 + 매트릭스 키)
    try:
        with sqlite3.connect(str(m.db_path)) as c:
            row = c.execute(
                "SELECT COUNT(*) FROM documents d "
                "JOIN document_meta meta ON d.doc_id = meta.doc_id "
                "WHERE meta.classifier_version IS NOT NULL "
                "  AND d.industry IS NOT NULL AND d.area IS NOT NULL "
                "  AND d.kind = 'source'"
            ).fetchone()
            s.eligible = row[0] if row else 0

            # V2.7.0 — K2 단계별 진척 카운트
            try:
                s.extract_done = c.execute(
                    "SELECT COUNT(*) FROM document_meta WHERE extract_at IS NOT NULL"
                ).fetchone()[0]
                s.classify_done = c.execute(
                    "SELECT COUNT(*) FROM document_meta WHERE classify_at IS NOT NULL"
                ).fetchone()[0]
                s.summarize_done = c.execute(
                    "SELECT COUNT(*) FROM document_meta WHERE summarize_at IS NOT NULL"
                ).fetchone()[0]
            except sqlite3.OperationalError:
                # 마이그레이션 v006 안 박힌 DB
                pass
    except sqlite3.Error:
        s.eligible = 0
    return s


def _measure_mirror() -> MirrorStage:
    s = MirrorStage(exists=IRIS_KNOWLEDGE_MIRROR.exists())
    if s.exists:
        # iris가 관리하는 doc_id 패턴(raw_/ref_/sec_)만 카운트 — 사용자 노트(README, 데일리) 제외
        _IRIS_PREFIXES = ("raw_", "ref_", "sec_")
        s.md_count = sum(
            1 for p in IRIS_KNOWLEDGE_MIRROR.iterdir()
            if p.is_file() and p.suffix == ".md" and p.name.startswith(_IRIS_PREFIXES)
        )
    return s


def _measure_wiki() -> WikiStage:
    s = WikiStage(exists=IRIS_KNOWLEDGE_WIKI.exists())
    if s.exists:
        s.md_count = _count_files(IRIS_KNOWLEDGE_WIKI, {".md"})
    return s


def measure_flow() -> FlowSnapshot:
    return FlowSnapshot(
        inbox=_measure_inbox(),
        archive=_measure_archive(),
        db=_measure_db(),
        mirror=_measure_mirror(),
        wiki=_measure_wiki(),
    )
