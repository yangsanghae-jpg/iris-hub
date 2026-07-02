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

from src.config import IRIS_DB_PATH

# V2.6.3.3: iris-knowledge로 경로 단일화. legacy IRIS_SYSTEM 참조 제거.
DB_PATH = IRIS_DB_PATH
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
    """선택된 파일들을 인덱싱 (V2.6.3.9 archive 우선).

    archive_root:
      None → IRIS_KNOWLEDGE_ARCHIVE 기본값 사용 (V2.6.3.9 — No-Copy 폐지)
      <Path> → 명시 경로 사용

    archive 구조 (자료당):
      <archive_root>/<YYYY-MM-DD>/<doc_id>/
        ├── original.<ext>  ← 원본 그대로 (불변)
        ├── content.md      ← 추출된 마크다운 본문 (검색·처리·표시)
        └── manifest.json   ← {doc_id, content_sha1, original_sha1, ingested_at, source_path, ...}

    DB의 documents.path는 *archive 경로*로 박힘 (원본 경로는 manifest.source_path).
    이렇게 하면 DB가 날아가도 archive에서 *100% 복원* 가능.

    지원: 마크다운(.md), 텍스트(.txt). 그 외는 skip (V2.7+ 별도 변환기).

    force: True면 이미 처리된 파일도 재처리.
    on_progress(i, total, status, source_path):
      status ∈ {'staging', 'parsing', 'classifying', 'archiving', 'done',
                'skip-empty', 'skip-already', 'skip-unsupported', 'error'}
    """
    # V2.6.3.9 — archive_root 기본값
    if archive_root is None:
        from src.config import IRIS_KNOWLEDGE_ARCHIVE
        archive_root = IRIS_KNOWLEDGE_ARCHIVE

    res = IngestResult(requested=len(paths))
    if not paths:
        return res
    if not DB_PATH.exists():
        res.errors.append(("db", f"DB 없음: {DB_PATH}"))
        return res

    try:
        from src.engine.intake.raw_intake import (
            doc_id_for, parse_frontmatter, split_chunks,
        )
        from src.engine.intake.fts_sync import rebuild_all
    except Exception as e:
        res.errors.append(("import", f"{type(e).__name__}: {e}"))
        return res

    # 분류기 (V2.6.3.8 정책: 입력 단계에서 K2 안 함, use_k2=False 권장)
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

    # V2.6.3.10: 지원 포맷 = converter.SUPPORTED_SUFFIXES (.md/.txt/.pdf/.pptx/.docx)
    from src.engine.intake import converter
    SUPPORTED_SUFFIXES = converter.SUPPORTED_SUFFIXES

    # work_dir 생성
    work_id = dt.datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
    res.work_id = work_id
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

                # V2.6.3.9 — 마크다운/텍스트만 지원
                if src_path.suffix.lower() not in SUPPORTED_SUFFIXES:
                    fr.skipped_reason = "unsupported"
                    res.skipped_empty += 1  # 카운트는 skipped_empty에 합산 (별도 필드 추가는 호환성 위해 보류)
                    _emit(idx, "skip-unsupported", src_path)
                    res.files.append(fr)
                    continue

                # ① staging 복사 (V2.6.3.9 — 항상 켜짐)
                _emit(idx, "staging", src_path)
                staged = staging_dir / f"{src_path.stem}_{_hash_short(src_path)}{src_path.suffix}"
                shutil.copy2(src_path, staged)

                # ② parse + chunk (V2.6.3.10 — converter 위임, V2.6.3.11 — OCR 메타 박힘)
                _emit(idx, "parsing", src_path)
                try:
                    conv = converter.convert_with_meta(src_path)
                    body = conv.body
                except converter.ConversionError as e:
                    fr.error = f"변환 실패: {e}"
                    res.errors.append((src_path.name, fr.error))
                    _emit(idx, "error", src_path)
                    if staged and staged.exists():
                        staged.unlink()
                    res.files.append(fr)
                    continue
                # 마크다운/텍스트는 frontmatter 메타에서 title 추출, 그 외는 stem
                if src_path.suffix.lower() in converter.LOSSLESS_SUFFIXES:
                    meta, _ = parse_frontmatter(src_path.read_text(encoding="utf-8"))
                    title = meta.get("title") or src_path.stem
                else:
                    title = src_path.stem
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

                # V2.6.3.9: archive 경로를 먼저 계산 — DB path로 박을 진실원
                today = dt.date.today().isoformat()
                safe_doc_id = doc_id.replace(":", "_").replace("/", "_")
                dest_dir = archive_root / today / safe_doc_id
                original_target = dest_dir / f"original{src_path.suffix}"
                content_target = dest_dir / "content.md"

                # 이미 박혔으면 force=False는 skip (source_path 또는 archive path로 검사)
                if not force:
                    cur = conn.execute(
                        "SELECT 1 FROM documents WHERE path IN (?, ?)",
                        (str(original_target), str(src_path.resolve())),
                    ).fetchone()
                    if cur:
                        fr.skipped_reason = "already"
                        res.skipped_already += 1
                        _emit(idx, "skip-already", src_path)
                        if staged and staged.exists():
                            staged.unlink()
                        res.files.append(fr)
                        continue

                # ③ archive 카피 (V2.6.3.9: 항상)
                _emit(idx, "archiving", src_path)
                dest_dir.mkdir(parents=True, exist_ok=True)
                # original 보존 (staging → archive 이동)
                if staged and staged.exists():
                    shutil.move(str(staged), str(original_target))
                    staged = None
                else:
                    shutil.copy2(src_path, original_target)
                # content.md = 마크다운 본문 (frontmatter 제외, 검색/처리/표시용)
                content_target.write_text(body, encoding="utf-8")

                # ④ DB UPSERT — path는 *archive 경로*로 박음 (진실원 분리)
                from src.engine.intake.raw_intake import upsert_raw_doc
                upsert_raw_doc(conn, doc_id, original_target, title, chunks)
                # lane / origin 갱신 (raw_intake 기본값 override)
                conn.execute(
                    "UPDATE documents SET lane=?, origin=? WHERE doc_id=?",
                    (lane, "folder_load", doc_id),
                )
                res.upserted += 1

                # ⑤ 분류
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

                # ⑥ manifest 박기 (V2.6.3.9 — content_sha1 + original_sha1, V2.6.3.11 — OCR 메타)
                import hashlib as _hashlib
                original_bytes = original_target.read_bytes()
                content_bytes = content_target.read_bytes()
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
                    "content_sha1": _hashlib.sha1(content_bytes).hexdigest(),
                    "original_sha1": _hashlib.sha1(original_bytes).hexdigest(),
                    "extraction_method": conv.extraction_method,
                    "pages": conv.pages,
                    "ocr_pages": conv.ocr_pages,
                    "ingested_at": dt.datetime.now(dt.timezone.utc)
                        .strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "work_id": work_id,
                    "schema_version": "v2",
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
