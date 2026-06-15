"""폴더 로딩 — 외부 폴더 스캔 + 임시 큐 처리 + archive 구조화 저장 (V2.6.1 부록).

B안 동작 흐름 (정합성 우선, 카피 비용 감수):
  1) scan_folder()      외부 폴더 스캔 + 처리 여부 판정
  2) ingest_paths()     선택된 파일들을 다음 순서로 한 건씩 처리:
     a) 원본 → <archive>/_temp/<work_id>/staging/ 으로 복사
     b) parse + chunk + DB UPSERT (lane 적용)
     c) 분류 (K2 또는 규칙)
     d) 성공 시 → <archive>/<YYYY-MM-DD>/<doc_id>/ 로 이동
        · original.<ext>      원본 바이트 (재사용용)
        · manifest.json       doc_id, source_path, lane, K2 결과 등
     e) staging의 사본 삭제
  3) temp/<work_id>/ 빈 디렉터리 정리

invariant:
  - 처리 중 = staging/ 안에 파일 있음
  - 처리 완료 = archive/<date>/<doc_id>/ 안에 파일 있음 + staging에서 사라짐
  - DB 트랜잭션과 archive 이동은 *건별*. 한 건 실패해도 다른 건 진행.

진행 표시:
  - on_progress(i, total, status, file_path) 콜백으로 UI에 보고
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import shutil
import sqlite3
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

IRIS_SYSTEM = Path("/Users/iris/Documents/0Dev/iris-system")
if str(IRIS_SYSTEM) not in sys.path:
    sys.path.insert(0, str(IRIS_SYSTEM))

DB_PATH = IRIS_SYSTEM / "knowledge" / "_index.db"
DEFAULT_GLOB_SUFFIXES = {".md", ".txt"}

ProgressCB = Callable[[int, int, str, str], None]


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
class FileResult:
    source: Path
    doc_id: str | None = None
    chunks: int = 0
    archive_dir: Path | None = None
    k2_ms: int = 0
    classifier: str = ""        # 'k2-<model>-v1' | 'rule' | 'rule-fallback'
    industry: str | None = None
    area: str | None = None
    level: str | None = None
    error: str | None = None
    skipped_reason: str | None = None  # 'empty' | 'already' | None


@dataclass
class IngestResult:
    requested: int = 0
    upserted: int = 0
    skipped_empty: int = 0
    skipped_already: int = 0
    classified: int = 0
    archived: int = 0
    work_id: str = ""
    work_dir: Path | None = None
    files: list[FileResult] = field(default_factory=list)
    errors: list[tuple[str, str]] = field(default_factory=list)
    fts_counts: dict | None = None

    @property
    def ok(self) -> bool:
        return not self.errors


def _hash_short(p: Path) -> str:
    return hashlib.sha1(str(p.resolve()).encode("utf-8")).hexdigest()[:8]


def ingest_paths(paths: list[Path], *,
                 lane: str = "reference",
                 force: bool = False,
                 archive_root: Path | None = None,
                 use_k2: bool = False,
                 on_progress: ProgressCB | None = None) -> IngestResult:
    """선택된 파일들을 인덱싱 (B안: temp 큐 + archive 구조화).

    archive_root:
      None → temp + archive 둘 다 만들지 않음 (DB만, 옛 동작과 동일)
      <Path> → <root>/_temp/<work_id>/staging/ + <root>/<YYYY-MM-DD>/<doc_id>/

    force: True면 이미 처리된 파일도 재처리 (DB UPSERT 강제, archive 갱신).
    on_progress(i, total, status, source_path):
      status ∈ {'staging', 'parsing', 'classifying', 'archiving', 'done',
                'skip-empty', 'skip-already', 'error'}
    """
    res = IngestResult(requested=len(paths))
    if not paths:
        return res
    if not DB_PATH.exists():
        res.errors.append(("db", f"DB 없음: {DB_PATH}"))
        return res

    try:
        from apps.ingest.raw_intake import (
            doc_id_for, parse_frontmatter, split_chunks,
        )
        from apps.ingest.fts_sync import rebuild_all
    except Exception as e:
        res.errors.append(("import", f"{type(e).__name__}: {e}"))
        return res

    # 분류기
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

    # work_dir 생성
    work_id = dt.datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
    res.work_id = work_id
    staging_dir: Path | None = None
    if archive_root:
        archive_root = Path(archive_root).expanduser().resolve()
        staging_dir = archive_root / "_temp" / work_id / "staging"
        staging_dir.mkdir(parents=True, exist_ok=True)
        res.work_dir = staging_dir.parent

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")

    total = len(paths)

    def _emit(i: int, status: str, p: Path) -> None:
        if on_progress:
            try:
                on_progress(i, total, status, str(p))
            except Exception:
                pass

    try:
        for idx, src_path in enumerate(paths, start=1):
            fr = FileResult(source=src_path)
            staged: Path | None = None

            try:
                if not src_path.exists():
                    fr.error = "파일 없음"
                    _emit(idx, "error", src_path)
                    res.errors.append((src_path.name, fr.error))
                    res.files.append(fr)
                    continue

                # ① staging 복사 (archive_root 켜진 경우만)
                if staging_dir:
                    _emit(idx, "staging", src_path)
                    # 이름 충돌 회피: <stem>_<srchash><suffix>
                    staged = staging_dir / f"{src_path.stem}_{_hash_short(src_path)}{src_path.suffix}"
                    shutil.copy2(src_path, staged)

                # ② parse + chunk
                _emit(idx, "parsing", src_path)
                text = src_path.read_text(encoding="utf-8")
                meta, body = parse_frontmatter(text)
                title = meta.get("title") or src_path.stem
                chunks = split_chunks(body)
                if not chunks:
                    fr.skipped_reason = "empty"
                    res.skipped_empty += 1
                    _emit(idx, "skip-empty", src_path)
                    if staged and staged.exists():
                        staged.unlink()
                    res.files.append(fr)
                    continue

                doc_id = doc_id_for(src_path)
                fr.doc_id = doc_id
                fr.chunks = len(chunks)

                # 이미 박혔으면 force=False는 skip
                if not force:
                    cur = conn.execute(
                        "SELECT 1 FROM documents WHERE path=?",
                        (str(src_path.resolve()),)
                    ).fetchone()
                    if cur:
                        fr.skipped_reason = "already"
                        res.skipped_already += 1
                        _emit(idx, "skip-already", src_path)
                        if staged and staged.exists():
                            staged.unlink()
                        res.files.append(fr)
                        continue

                # ③ DB UPSERT
                from apps.ingest.raw_intake import upsert_raw_doc
                upsert_raw_doc(conn, doc_id, src_path, title, chunks)
                # lane / origin 갱신 (raw_intake 기본값 override)
                conn.execute(
                    "UPDATE documents SET lane=?, origin=? WHERE doc_id=?",
                    (lane, "folder_load", doc_id),
                )
                res.upserted += 1

                # ④ 분류
                _emit(idx, "classifying", src_path)
                k2_payload: dict = {}
                if use_k2:
                    k2_result = k2mod.analyze(title, body, timeout=60.0)
                    fr.industry = k2_result.industry
                    fr.area = k2_result.area
                    fr.level = k2_result.level
                    fr.k2_ms = k2_result.elapsed_ms
                    fr.classifier = k2_result.classifier_version
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
                        res.errors.append((src_path.name, f"document_meta: {e}"))
                    k2_payload = {
                        "summary": k2_result.summary,
                        "topics": k2_result.topics,
                        "entities": k2_result.entities,
                        "concepts": k2_result.concepts,
                        "confidence": k2_result.confidence,
                        "reason": k2_result.reason,
                        "fallback_used": k2_result.fallback_used,
                    }
                else:
                    clf = suggest_classification(title, body)
                    fr.industry = clf.get("industry")
                    fr.area = clf.get("area")
                    fr.level = clf.get("level")
                    fr.classifier = "rule"

                if any(v is not None for v in (fr.industry, fr.area, fr.level)):
                    conn.execute(
                        "UPDATE documents SET industry=?, area=?, level=? WHERE doc_id=?",
                        (fr.industry, fr.area, fr.level, doc_id),
                    )
                    res.classified += 1

                # ⑤ archive 이동: <archive_root>/<YYYY-MM-DD>/<doc_id>/
                if archive_root:
                    _emit(idx, "archiving", src_path)
                    today = dt.date.today().isoformat()
                    # doc_id에 ':' 등 FS 안전하지 않은 문자 회피
                    safe_doc_id = doc_id.replace(":", "_").replace("/", "_")
                    dest_dir = archive_root / today / safe_doc_id
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    # original 보존 — 원본 확장자 유지
                    original_target = dest_dir / f"original{src_path.suffix}"
                    if staged and staged.exists():
                        # staging → archive 이동 (rename)
                        shutil.move(str(staged), str(original_target))
                        staged = None
                    else:
                        # staging 우회 시 직접 복사
                        shutil.copy2(src_path, original_target)

                    manifest = {
                        "doc_id": doc_id,
                        "source_path": str(src_path.resolve()),
                        "title": title,
                        "lane": lane,
                        "kind": "source",
                        "origin": "folder_load",
                        "industry": fr.industry,
                        "area": fr.area,
                        "level": fr.level,
                        "classifier_version": fr.classifier,
                        "k2_ms": fr.k2_ms,
                        "chunks": fr.chunks,
                        "size_bytes": src_path.stat().st_size,
                        "ingested_at": dt.datetime.now(dt.timezone.utc)
                            .strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "work_id": work_id,
                        "k2": k2_payload,
                    }
                    (dest_dir / "manifest.json").write_text(
                        json.dumps(manifest, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                    fr.archive_dir = dest_dir
                    res.archived += 1

                _emit(idx, "done", src_path)

            except Exception as e:
                fr.error = f"{type(e).__name__}: {e}"
                res.errors.append((src_path.name, fr.error))
                _emit(idx, "error", src_path)
                # staging 잔여물 정리 — 실패는 archive로 보내지 않음
                if staged and staged.exists():
                    try:
                        staged.unlink()
                    except Exception:
                        pass

            res.files.append(fr)

        # FTS 동기화 (전체 1회)
        try:
            res.fts_counts = rebuild_all(conn)
        except Exception as e:
            res.errors.append(("fts_sync", f"{type(e).__name__}: {e}"))

        conn.commit()
    finally:
        conn.close()

        # work_dir 정리: staging 비었으면 삭제
        if staging_dir and staging_dir.exists():
            try:
                # staging이 비어있는지 확인 후 work_id 디렉터리째 정리
                if not any(staging_dir.iterdir()):
                    shutil.rmtree(staging_dir.parent, ignore_errors=True)
            except Exception:
                pass

    return res


__all__ = ["FolderScan", "FileEntry", "scan_folder",
           "FileResult", "IngestResult", "ingest_paths"]
