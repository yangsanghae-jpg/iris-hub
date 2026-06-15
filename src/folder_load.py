"""폴더 로딩 — 외부 폴더 스캔 + 처리 여부 판정 + 결과 저장.

V2.6/Phase8 후보 — 진단툴 등 외부 산출물 폴더를 *경로 그대로* 인덱싱.

설계:
  - 원본 파일은 *복사하지 않음* (raw_intake와 다름) — 외부 절대경로 그대로 인덱싱
  - 처리 여부 = `documents.path` 컬럼에 해당 절대경로가 박혀있는지로 판정
  - 강제 재파싱 = 처리 여부 무시하고 doc_id 재계산 + UPSERT
  - 결과 저장 = (a) DB는 자동 (b) 가공된 파일을 별도 dest_dir로 복사 (선택)
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

DB_PATH = IRIS_SYSTEM / "knowledge" / "_index.db"
DEFAULT_GLOB_SUFFIXES = {".md", ".txt"}


@dataclass
class FileEntry:
    path: Path
    size: int
    mtime: float
    processed: bool          # documents.path에 이미 박혔는가
    last_doc_id: str | None  # 박힌 경우의 doc_id


@dataclass
class FolderScan:
    folder: Path
    entries: list[FileEntry] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.entries)

    @property
    def processed_count(self) -> int:
        return sum(1 for e in self.entries if e.processed)

    @property
    def pending_count(self) -> int:
        return self.total - self.processed_count


def _processed_paths(folder: Path) -> dict[str, str]:
    """해당 folder 하위 path들이 documents에 박혔는지 lookup. {abs_path: doc_id}."""
    if not DB_PATH.exists():
        return {}
    conn = sqlite3.connect(DB_PATH)
    try:
        prefix = str(folder.resolve()) + "/"
        rows = conn.execute(
            "SELECT path, doc_id FROM documents WHERE path LIKE ?",
            (prefix + "%",),
        ).fetchall()
        return {row[0]: row[1] for row in rows}
    finally:
        conn.close()


def scan_folder(folder: str | Path,
                suffixes: Iterable[str] = DEFAULT_GLOB_SUFFIXES,
                recursive: bool = True) -> FolderScan:
    """폴더 스캔 → FileEntry 리스트.

    suffixes: 인덱싱 대상 확장자 (소문자 기준). 빈 set이면 모든 파일.
    recursive: True면 하위 디렉터리도.
    """
    folder = Path(folder).expanduser().resolve()
    scan = FolderScan(folder=folder)
    if not folder.is_dir():
        return scan

    suffix_lower = {s.lower() for s in suffixes}
    iterator = folder.rglob("*") if recursive else folder.iterdir()
    files = [p for p in iterator if p.is_file()
             and (not suffix_lower or p.suffix.lower() in suffix_lower)]

    processed = _processed_paths(folder)
    for p in sorted(files):
        st = p.stat()
        abs_str = str(p.resolve())
        scan.entries.append(FileEntry(
            path=p,
            size=st.st_size,
            mtime=st.st_mtime,
            processed=abs_str in processed,
            last_doc_id=processed.get(abs_str),
        ))
    return scan


@dataclass
class IngestResult:
    requested: int = 0
    upserted: int = 0
    skipped_empty: int = 0
    classified: int = 0
    saved_copies: int = 0
    errors: list[tuple[str, str]] = field(default_factory=list)
    fts_counts: dict | None = None

    @property
    def ok(self) -> bool:
        return not self.errors


def ingest_paths(paths: list[Path], *,
                 lane: str = "reference",
                 force: bool = False,
                 dest_dir: Path | None = None,
                 use_k2: bool = False) -> IngestResult:
    """선택된 파일들을 인덱싱.

    lane:
      'reference' — 외부 원본 그대로 path-pointer로 박음 (No-Copy)
      'bronze'    — raw로 복사 후 박음 (raw_intake와 동일 흐름) — 미구현
    force: True면 이미 처리된 파일도 재처리 (doc_id UPSERT).
    dest_dir: 지정 시 처리 완료된 파일을 해당 폴더로 *복사* (원본 보존).
    use_k2: K2 LLM 분류 적용 여부.
    """
    res = IngestResult(requested=len(paths))
    if not paths:
        return res
    if not DB_PATH.exists():
        res.errors.append(("db", f"DB 없음: {DB_PATH}"))
        return res

    try:
        from apps.ingest.raw_intake import (
            doc_id_for, parse_frontmatter, split_chunks, upsert_raw_doc,
        )
        from apps.ingest.fts_sync import rebuild_all
    except Exception as e:
        res.errors.append(("import", f"{type(e).__name__}: {e}"))
        return res

    # 분류기 — K2 우선 옵션, 기본은 규칙
    if use_k2:
        try:
            from src import k2 as k2mod
            from src import document_meta
            document_meta.ensure_schema()
        except Exception as e:
            res.errors.append(("k2", f"K2 import 실패, 규칙 사용: {e}"))
            use_k2 = False

    if not use_k2:
        try:
            from src.classify import suggest_classification
        except Exception as e:
            res.errors.append(("classify", f"import 실패: {e}"))
            return res

    if dest_dir:
        dest_dir = Path(dest_dir).expanduser().resolve()
        dest_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")

    try:
        for p in paths:
            try:
                if not p.exists():
                    res.errors.append((p.name, "파일 없음"))
                    continue

                text = p.read_text(encoding="utf-8")
                meta, body = parse_frontmatter(text)
                title = meta.get("title") or p.stem
                chunks = split_chunks(body)
                if not chunks:
                    res.skipped_empty += 1
                    continue

                doc_id = doc_id_for(p)

                # force=False이고 이미 박힌 경우 skip
                if not force:
                    cur = conn.execute(
                        "SELECT 1 FROM documents WHERE path=?",
                        (str(p.resolve()),)
                    ).fetchone()
                    if cur:
                        continue

                upsert_raw_doc(conn, doc_id, p, title, chunks)
                # lane 갱신 (reference 등)
                conn.execute(
                    "UPDATE documents SET lane=?, origin=? WHERE doc_id=?",
                    (lane, "folder_load", doc_id),
                )
                res.upserted += 1

                # 분류
                if use_k2:
                    k2_result = k2mod.analyze(title, body, timeout=60.0)
                    ind, area, lvl = k2_result.industry, k2_result.area, k2_result.level
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
                        )
                    except Exception as e:
                        res.errors.append((p.name, f"document_meta: {e}"))
                else:
                    clf = suggest_classification(title, body)
                    ind, area, lvl = clf.get("industry"), clf.get("area"), clf.get("level")

                if any(v is not None for v in (ind, area, lvl)):
                    conn.execute(
                        "UPDATE documents SET industry=?, area=?, level=? "
                        "WHERE doc_id=?",
                        (ind, area, lvl, doc_id),
                    )
                    res.classified += 1

                # dest_dir로 *복사* (원본 보존)
                if dest_dir:
                    try:
                        target = dest_dir / p.name
                        if target.exists():
                            target = dest_dir / f"{p.stem}_{doc_id[:8]}{p.suffix}"
                        target.write_bytes(p.read_bytes())
                        res.saved_copies += 1
                    except Exception as e:
                        res.errors.append((p.name, f"dest_dir 복사 실패: {e}"))

            except Exception as e:
                res.errors.append((p.name, f"{type(e).__name__}: {e}"))

        try:
            res.fts_counts = rebuild_all(conn)
        except Exception as e:
            res.errors.append(("fts_sync", f"{type(e).__name__}: {e}"))

        conn.commit()
    finally:
        conn.close()

    return res


__all__ = ["FolderScan", "FileEntry", "scan_folder",
           "IngestResult", "ingest_paths"]
