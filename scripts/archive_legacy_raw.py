"""V2.6.3.2 — legacy raw → iris-knowledge/3-archive 카피 보존.

정책:
  - raw/*.md, raw/*.txt → 3-archive/<YYYY-MM-DD>/<doc_id>/original.<ext>
  - manifest.json: 원 경로·해시·인제스트 시점·doc_id 매핑
  - raw/_external/* 도 포함 (외부응답 자료)
  - legacy raw 디렉토리는 *그대로 보존* (V2.6.3.4까지)

원본 보존 원칙:
  - 3-archive는 *불변* (한번 박히면 수정 X)
  - 카피만, 원본 변경 없음
  - 같은 doc_id 두 번 시도 시 *skip* (중복 처리 안전)

사용:
  python scripts/archive_legacy_raw.py [--dry-run] [--source PATH] [--target PATH]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# iris-hub root에서 호출 가정
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.config import IRIS_KNOWLEDGE_ARCHIVE
from src.ingest.raw_intake import doc_id_for


LEGACY_RAW_DEFAULT = Path("/Users/iris/Documents/0Dev/iris-system/knowledge/raw")
INCLUDE_SUFFIXES = {".md", ".txt"}
EXCLUDE_NAMES = {"README.md", ".DS_Store"}


def _walk(source: Path):
    """raw 루트 + _external 하위 재귀 — INCLUDE_SUFFIXES만."""
    if not source.exists():
        return
    for p in source.rglob("*"):
        if not p.is_file():
            continue
        if p.name in EXCLUDE_NAMES:
            continue
        if p.suffix.lower() not in INCLUDE_SUFFIXES:
            continue
        yield p


def _archive_one(src_path: Path, target_root: Path, date_str: str, dry_run: bool):
    """1건 카피. 반환: ('written'|'skipped'|'error', message)."""
    try:
        doc_id_str = doc_id_for(src_path)              # "raw:<hash12>"
        hash_dir = doc_id_str.split(":", 1)[1]         # "<hash12>"
    except Exception as e:
        return "error", f"doc_id 계산 실패: {e}"

    target_dir = target_root / date_str / hash_dir
    target_file = target_dir / f"original{src_path.suffix.lower()}"
    manifest_path = target_dir / "manifest.json"

    if target_file.exists() and manifest_path.exists():
        return "skipped", f"이미 존재: {target_dir}"

    if dry_run:
        return "written", f"[DRY] {src_path.name} → {target_dir}"

    target_dir.mkdir(parents=True, exist_ok=True)

    # 카피 (mtime 보존)
    shutil.copy2(src_path, target_file)

    # manifest
    content_hash_full = hashlib.sha1(src_path.read_bytes()).hexdigest()
    manifest = {
        "doc_id": doc_id_str,
        "original_path": str(src_path),
        "original_name": src_path.name,
        "extension": src_path.suffix.lower(),
        "content_sha1": content_hash_full,
        "size_bytes": src_path.stat().st_size,
        "archived_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mtime_iso": datetime.fromtimestamp(
            src_path.stat().st_mtime, tz=timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema_version": "v1",
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return "written", f"{src_path.name} → {hash_dir}/"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", type=Path, default=LEGACY_RAW_DEFAULT,
                    help="legacy raw 디렉토리 (재귀)")
    ap.add_argument("--target", type=Path, default=IRIS_KNOWLEDGE_ARCHIVE,
                    help="3-archive 루트")
    ap.add_argument("--dry-run", action="store_true", help="실제 카피 안 함")
    ap.add_argument("--date", default=None,
                    help="archive 날짜 prefix (기본: 오늘 YYYY-MM-DD)")
    args = ap.parse_args()

    date_str = args.date or datetime.now().strftime("%Y-%m-%d")

    print(f"source: {args.source}")
    print(f"target: {args.target}/{date_str}/")
    print(f"dry-run: {args.dry_run}")
    print()

    if not args.source.exists():
        print(f"[FATAL] source 없음: {args.source}", file=sys.stderr)
        return 1

    args.target.mkdir(parents=True, exist_ok=True)

    counts = {"written": 0, "skipped": 0, "error": 0}
    errors = []

    for src in sorted(_walk(args.source)):
        status, msg = _archive_one(src, args.target, date_str, args.dry_run)
        counts[status] += 1
        if status == "error":
            errors.append((src.name, msg))
            print(f"  ✗ {src.name}: {msg}")
        else:
            mark = "·" if status == "skipped" else "+"
            print(f"  {mark} {msg}")

    print()
    print(f"=== 결과 ===")
    print(f"  written: {counts['written']}")
    print(f"  skipped: {counts['skipped']}")
    print(f"  error:   {counts['error']}")

    if errors:
        print()
        print("=== 오류 ===")
        for name, msg in errors:
            print(f"  - {name}: {msg}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
