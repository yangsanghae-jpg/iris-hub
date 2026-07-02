#!/usr/bin/env python3
"""iris-data 볼트 부트스트랩 (S1) — STORE_SCHEMA_DESIGN §4.

멱등: 재실행 안전(있으면 스킵). 빈 볼트를 세운다.
  1. iris-data/{vault,knowledge} 레이아웃 + .nosync 심볼릭
  2. db.ensure_schema() → 빈 index.db (스키마만)
  3. concepts.seed.yaml → concepts + concept_aliases (verified)
  4. knowledge/wiki/ 초기화 (README + _templates)

사용:  python -m scripts.init_vault
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import config                       # noqa: E402
from src.store import db, knowledge          # noqa: E402
from src.store.models import ConceptRow      # noqa: E402


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def make_layout() -> None:
    """디렉터리 레이아웃 + .nosync 심볼릭."""
    config.IRIS_VAULT_NOSYNC.mkdir(parents=True, exist_ok=True)
    for ch in config.IRIS_ORIGINAL_CHANNELS:
        (config.IRIS_ORIGINALS / ch).mkdir(parents=True, exist_ok=True)
    config.IRIS_EXTRACTED.mkdir(parents=True, exist_ok=True)
    config.IRIS_FAISS_DIR.mkdir(parents=True, exist_ok=True)
    config.IRIS_KNOWLEDGE_STORE.mkdir(parents=True, exist_ok=True)
    config.IRIS_WIKI_STORE.mkdir(parents=True, exist_ok=True)
    # index.db 심볼릭(→ .nosync/index.db)은 db.get_conn 이 보장하지만 여기서도 선반영.
    link = config.IRIS_VAULT_DB
    if not link.is_symlink() and not link.exists():
        link.symlink_to(Path(".nosync") / "index.db")
    print(f"  ✓ 레이아웃: {config.IRIS_DATA_ROOT}")


def load_concept_seed() -> int:
    """concepts.seed.yaml → IRIS_CONCEPTS_YAML 배포 + DB 로드(verified). Returns 개념 수."""
    try:
        import yaml
    except ImportError:
        print("  ! PyYAML 미설치 — 개념 시드 스킵")
        return 0
    seed = config.CONCEPTS_SEED_YAML
    if not seed.exists():
        print(f"  ! 시드 없음: {seed} — 스킵")
        return 0
    # repo 시드 → 데이터 루트로 배포(멱등: 이미 있으면 유지)
    dest = config.IRIS_CONCEPTS_YAML
    if not dest.exists():
        dest.write_text(seed.read_text(encoding="utf-8"), encoding="utf-8")
    data = yaml.safe_load(seed.read_text(encoding="utf-8")) or {}
    concepts = data.get("concepts", [])
    conn = db.get_conn()
    try:
        for c in concepts:
            knowledge.upsert_concept(
                ConceptRow(
                    concept_id=c["concept_id"],
                    canonical=c["canonical"],
                    definition=c.get("definition"),
                    trust="verified",
                    created_at=_now(),
                ),
                conn=conn,
            )
            for a in c.get("aliases", []):
                knowledge.add_alias(c["concept_id"], a["alias"], a.get("lang"), conn=conn)
        conn.commit()
    finally:
        conn.close()
    print(f"  ✓ 개념 시드: {len(concepts)}개 (verified)")
    return len(concepts)


def init_wiki() -> None:
    tpl = config.IRIS_WIKI_STORE / "_templates"
    tpl.mkdir(parents=True, exist_ok=True)
    readme = config.IRIS_WIKI_STORE / "README.md"
    if not readme.exists():
        readme.write_text(
            "# iris 위키 (Gold)\n\n"
            "개념 중심 검색 위키. 개념 페이지는 S5(WIKI_REBUILD)에서 생성된다.\n"
            "이 폴더를 Obsidian vault 로 연다.\n",
            encoding="utf-8",
        )
    concept_tpl = tpl / "concept.md"
    if not concept_tpl.exists():
        concept_tpl.write_text(
            "# {{canonical}}\n\n"
            "> 별칭: \n\n## 정의\n\n## 근거 문서\n\n## 관련 개념\n",
            encoding="utf-8",
        )
    print(f"  ✓ 위키: {config.IRIS_WIKI_STORE}")


def main() -> int:
    print(f"iris-data 부트스트랩 → {config.IRIS_DATA_ROOT}")
    make_layout()
    ver = db.ensure_schema()
    print(f"  ✓ 스키마: SCHEMA_VERSION={ver} ({config.IRIS_VAULT_DB})")
    load_concept_seed()
    init_wiki()
    print("완료. 빈 볼트 준비됨.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
