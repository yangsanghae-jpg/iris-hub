"""Obsidian mirror sync — iris _index.db → ~/LearningMaster/iris-mirror/ (V2.6.2.5 → V2.6.3.6).

정책 (V2.5.2 §3.B 정합 + V2.6.3.6 진입 자격):
  - 단방향 export: SQLite truth → Obsidian는 *뷰어/거울*. 사용자 편집 덮어씀.
  - **mirror는 *지식화된 자료*만 받는다 (저장소 X).**
    진입 자격 = K2 분석 완료(document_meta 행) AND 매트릭스 키(industry+area NOT NULL)
  - 자격 미달 → mirror 진입 거절. 기존 .md는 sync 시 삭제.
  - 좀비(DB에 없는데 mirror에 .md만 있음) → sync 시 삭제.
  - 자료 1건 = .md 1건. 같은 자료가 3 파트(산업·시스템·관리)에 동시 노출되는
    의도된 중복은 frontmatter 멀티라벨 + Dataview 동적 뷰로 처리. 파일 복제 X.
  - 증분: iris_synced_at < (k2_at 또는 fetched_at)인 자료만 다시 씀.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from src.config import IRIS_DB_PATH, IRIS_MIRROR_PATH

DB_PATH = IRIS_DB_PATH
MIRROR_ROOT = IRIS_MIRROR_PATH

# Vault 안에서 iris 소유를 명시 (사용자가 다른 영역과 구분)
README = """# iris-mirror

🪞 **iris-hub의 단방향 거울입니다.** 이 디렉토리의 `.md` 파일은
iris _index.db에서 자동 생성되며, 다음 sync에 *덮어씌워집니다*.

**진입 자격 (V2.6.3.6)** — *지식화*가 완료된 자료만 박힙니다:
- K2 LLM 분석 통과 (`document_meta.classifier_version` 박힘)
- 매트릭스 키 부여 (`industry`, `area` 모두 NOT NULL)

자격 미달 자료는 *진입 거절*되며, 기존 .md는 다음 sync에 삭제됩니다.
DB에 없는 좀비 `raw_*.md`, `ref_*.md`, `sec_*.md`도 함께 청소됩니다.

- 정본: `iris-knowledge/2-processed/_index.db`
- 자료별 .md: `<doc_id>.md`
- frontmatter `iris_*` 필드는 Dataview에서 직접 쿼리 가능
- `tags: [iris/industry/B, iris/system/APS, ...]` — Obsidian 그래프뷰 자동 클러스터링

여기서 노트 *기록*하고 싶으면 격납소 밖 (예: `~/LearningMaster/notes/`)에
파일 만들고 mirror 노트를 `[[wikilink]]`로 참조하세요. Obsidian이 자동으로
양방향 백링크를 잡아줍니다.
"""


@dataclass
class SyncResult:
    scanned: int = 0
    eligible: int = 0       # V2.6.3.6 — 진입 자격 통과
    written: int = 0
    skipped: int = 0
    rejected: int = 0       # V2.6.3.6 — 자격 미달로 mirror 진입 거절 (DB에는 있음)
    purged: int = 0         # V2.6.3.6 — 자격 미달로 기존 .md 삭제됨
    zombies: int = 0        # V2.6.3.6 — DB에 없는데 mirror에만 있던 .md 삭제됨
    errors: list[tuple[str, str]] = field(default_factory=list)
    deleted: int = 0  # 호환 — 향후 제거 가능

    @property
    def ok(self) -> bool:
        return not self.errors


# ─── 진입 자격 (V2.6.3.6) ─────────────────────────────────────────────
def _is_eligible(d: dict) -> bool:
    """mirror 진입 자격: K2 분석 완료 + 매트릭스 키.

    - document_meta 행 존재 (classifier_version NOT NULL)
    - industry, area 둘 다 NOT NULL
    이 둘이 박혀야 *지식화된 자료*로 간주.
    """
    if not d.get("classifier_version"):
        return False
    if not d.get("industry") or not d.get("area"):
        return False
    return True


# ─── frontmatter 직렬화 (의존성 X — PyYAML 회피) ──────────────────────
def _yaml_str(s: str) -> str:
    """단순 1줄 문자열 — Obsidian/Dataview가 받을 수 있는 안전한 인용."""
    if not s:
        return '""'
    # 줄바꿈은 공백으로 — frontmatter 1줄 정책
    s = s.replace("\r", " ").replace("\n", " ").strip()
    # 항상 큰따옴표로 감싸고 내부 " 와 \ 만 escape — YAML double-quoted 규칙
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _yaml_list(items: list[str]) -> str:
    if not items:
        return "[]"
    return "[" + ", ".join(_yaml_str(x) for x in items) + "]"


def _parse_json_list(s: str | None) -> list[str]:
    if not s:
        return []
    try:
        v = json.loads(s)
        return [str(x) for x in v] if isinstance(v, list) else []
    except Exception:
        return []


def _safe_filename(doc_id: str) -> str:
    """파일명 안전화 — Obsidian/macOS 양쪽 안전. doc_id는 보통 영숫자라 통과."""
    bad = '<>:"/\\|?*'
    out = "".join("_" if c in bad else c for c in doc_id)
    return (out or "unknown")[:200]


# ─── 본문 빌드 ────────────────────────────────────────────────────────
def _build_tags(d: dict) -> list[str]:
    """Obsidian 그래프뷰 클러스터링용 nested tags."""
    tags = []
    if d.get("industry"):
        tags.append(f"iris/industry/{d['industry']}")
    if d.get("lane"):
        tags.append(f"iris/lane/{d['lane']}")
    for lvl in _parse_json_list(d.get("automation_levels_json")):
        tags.append(f"iris/automation/{lvl}")
    for sys in _parse_json_list(d.get("system_domains_json")):
        tags.append(f"iris/system/{sys}")
    for cat in _parse_json_list(d.get("mgmt_categories_json")):
        tags.append(f"iris/mgmt/{cat}")
    return tags


def _build_frontmatter(d: dict, synced_at: str) -> str:
    """YAML frontmatter — Dataview 쿼리 가능 형태."""
    fm: list[str] = ["---"]

    fm.append(f"doc_id: {_yaml_str(d['doc_id'])}")
    fm.append(f"title: {_yaml_str(d.get('title') or d['doc_id'])}")

    # 단일값 필드
    for key, src in [
        ("iris_lane",       d.get("lane")),
        ("iris_industry",   d.get("industry")),
        ("iris_area",       d.get("area")),
        ("iris_level",      d.get("level")),
        ("iris_classifier", d.get("classifier_version")),
    ]:
        if src:
            fm.append(f"{key}: {_yaml_str(src)}")

    # 멀티라벨
    auto = _parse_json_list(d.get("automation_levels_json"))
    sys_  = _parse_json_list(d.get("system_domains_json"))
    mgmt  = _parse_json_list(d.get("mgmt_categories_json"))
    topics = _parse_json_list(d.get("topics_json"))
    if auto:
        fm.append(f"iris_automation: {_yaml_list(auto)}")
    if sys_:
        fm.append(f"iris_system: {_yaml_list(sys_)}")
    if mgmt:
        fm.append(f"iris_mgmt: {_yaml_list(mgmt)}")
    if topics:
        fm.append(f"iris_topics: {_yaml_list(topics)}")

    # 신뢰도/타임스탬프
    conf = d.get("confidence")
    if conf is not None:
        try:
            fm.append(f"iris_confidence: {float(conf):.3f}")
        except (TypeError, ValueError):
            pass

    if d.get("k2_at"):
        fm.append(f"iris_k2_at: {_yaml_str(d['k2_at'])}")
    if d.get("fetched_at"):
        fm.append(f"iris_fetched_at: {_yaml_str(d['fetched_at'])}")

    fm.append(f"iris_synced_at: {_yaml_str(synced_at)}")

    # 그래프뷰 클러스터 tags
    tags = _build_tags(d)
    if tags:
        fm.append(f"tags: {_yaml_list(tags)}")

    fm.append("---")
    return "\n".join(fm)


def _build_body(d: dict) -> str:
    """본문 템플릿 — 3 시점 발췌 + 메타 한 눈에."""
    title = d.get("title") or d["doc_id"]
    summary = (d.get("summary") or "").strip()
    bi = (d.get("blurb_industry") or "").strip()
    bs = (d.get("blurb_system")   or "").strip()
    bm = (d.get("blurb_mgmt")     or "").strip()
    topics = _parse_json_list(d.get("topics_json"))

    auto  = _parse_json_list(d.get("automation_levels_json"))
    sys_  = _parse_json_list(d.get("system_domains_json"))
    mgmt  = _parse_json_list(d.get("mgmt_categories_json"))

    lines = [
        f"# {title}",
        "",
        "> 🪞 **iris-hub mirror** — 자동 생성. 수정해도 다음 sync에 덮어씀.",
        "",
    ]

    if not (summary or bi or bs or bm):
        lines += [
            "_(K2 분석 미완 — 데이터 탭 → 🔄 재처리 후 다시 sync 하면 채워집니다.)_",
            "",
        ]
    else:
        if summary:
            lines += ["## 요약", summary, ""]
        if bi:
            lines += ["## 산업 시점 (industry)", bi, ""]
        if bs:
            lines += ["## 시스템 시점 (system)", bs, ""]
        if bm:
            lines += ["## 관리 시점 (management)", bm, ""]

    if topics:
        lines += ["## 주제 (topics)",
                  " · ".join(f"`{t}`" for t in topics), ""]

    # 메타 요약 (한 눈에)
    meta_bits = []
    if d.get("industry"):
        meta_bits.append(f"산업 `{d['industry']}`")
    if d.get("area"):
        meta_bits.append(f"영역 `{d['area']}`")
    if auto:
        meta_bits.append(f"자동화 `{', '.join(auto)}`")
    if sys_:
        meta_bits.append(f"시스템 `{', '.join(sys_)}`")
    if mgmt:
        meta_bits.append(f"관리 `{', '.join(mgmt)}`")
    if meta_bits:
        lines += ["## 분류 요약", " · ".join(meta_bits), ""]

    if d.get("path"):
        lines += ["---",
                  f"원본 경로: `{d['path']}`"]

    return "\n".join(lines)


# ─── DB 로드 ──────────────────────────────────────────────────────────
_SQL = """
SELECT d.doc_id, d.title, d.path, d.industry, d.area, d.level,
       d.fetched_at, d.lane,
       m.summary, m.topics_json, m.confidence, m.fallback_used,
       m.classifier_version, m.k2_at,
       m.automation_levels_json, m.system_domains_json, m.mgmt_categories_json,
       m.blurb_industry, m.blurb_system, m.blurb_mgmt
  FROM documents d
  LEFT JOIN document_meta m ON d.doc_id = m.doc_id
"""


def _load_docs(db_path: Path, doc_id: str | None = None) -> list[dict]:
    if not db_path.exists():
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        # document_meta 컬럼 존재 여부 (V2.6.1 이전 DB 안전)
        cols = {r[1] for r in conn.execute("PRAGMA table_info(document_meta)")}
        sql = _SQL
        if "automation_levels_json" not in cols:
            # V2.6.2 이전 DB — 멀티라벨 컬럼 없음, NULL로 채워 받음
            sql = sql.replace(
                "m.automation_levels_json, m.system_domains_json, m.mgmt_categories_json,\n"
                "       m.blurb_industry, m.blurb_system, m.blurb_mgmt",
                "NULL AS automation_levels_json, NULL AS system_domains_json,"
                " NULL AS mgmt_categories_json,"
                " NULL AS blurb_industry, NULL AS blurb_system, NULL AS blurb_mgmt"
            )
        if doc_id:
            sql += " WHERE d.doc_id = ?"
            return [dict(r) for r in conn.execute(sql, (doc_id,)).fetchall()]
        return [dict(r) for r in conn.execute(sql).fetchall()]
    finally:
        conn.close()


# ─── 증분 판정 ────────────────────────────────────────────────────────
def _read_synced_at(path: Path) -> str | None:
    """기존 .md의 frontmatter에서 iris_synced_at 추출. 없으면 None."""
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            head = f.read(2048)  # frontmatter 1KB 이내 가정
    except OSError:
        return None
    if not head.startswith("---\n"):
        return None
    end = head.find("\n---", 4)
    if end < 0:
        return None
    block = head[4:end]
    for line in block.splitlines():
        if line.startswith("iris_synced_at:"):
            return line.split(":", 1)[1].strip().strip('"')
    return None


def _needs_update(d: dict, target: Path, force: bool) -> bool:
    if force or not target.exists():
        return True
    prev = _read_synced_at(target)
    if not prev:
        return True
    # K2 분석 시각 또는 인제스트 시각이 prev보다 새로우면 갱신
    cmp_keys = [d.get("k2_at"), d.get("fetched_at")]
    latest = max((c for c in cmp_keys if c), default=None)
    if not latest:
        return False  # 비교 기준 없으면 보존
    return latest > prev


# ─── 공개 API ─────────────────────────────────────────────────────────
def sync_all(*, force: bool = False,
             mirror_root: Path = MIRROR_ROOT,
             db_path: Path = DB_PATH) -> SyncResult:
    """전체 자료 → mirror_root/. force=True면 변경 없어도 다시 씀.

    V2.6.3.6 정책:
      - 진입 자격(K2+매트릭스) 미달 doc은 mirror 진입 거절 + 기존 .md 삭제
      - DB에 없는 좀비 .md 삭제 (raw_*.md, ref_*.md, sec_*.md 패턴만)
      - README.md 등 사용자 자산은 보존
    """
    res = SyncResult()
    mirror_root.mkdir(parents=True, exist_ok=True)
    # README 1회만 박음 (사용자 편집 가능 영역으로 보지만, 부재 시 박아둠)
    readme_path = mirror_root / "README.md"
    if not readme_path.exists():
        readme_path.write_text(README, encoding="utf-8")

    docs = _load_docs(db_path)
    res.scanned = len(docs)

    synced_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # mirror가 *관리하는* 파일명 집합. 자격 통과 doc의 파일명을 모은다.
    eligible_filenames: set[str] = set()
    # DB에 어떤 형태로든 박혀 있는 모든 doc의 파일명 (좀비 판별용)
    db_filenames: set[str] = set()

    for d in docs:
        fname = _safe_filename(d["doc_id"]) + ".md"
        db_filenames.add(fname)
        target = mirror_root / fname

        if not _is_eligible(d):
            # 자격 미달 — 진입 거절. 기존 .md가 있으면 삭제.
            res.rejected += 1
            if target.exists():
                try:
                    target.unlink()
                    res.purged += 1
                except OSError as e:
                    res.errors.append((d["doc_id"], f"purge failed: {e}"))
            continue

        # 자격 통과
        res.eligible += 1
        eligible_filenames.add(fname)
        try:
            if not _needs_update(d, target, force):
                res.skipped += 1
                continue
            content = _build_frontmatter(d, synced_at) + "\n\n" + _build_body(d) + "\n"
            target.write_text(content, encoding="utf-8")
            res.written += 1
        except Exception as e:
            res.errors.append((d.get("doc_id", "?"), f"{type(e).__name__}: {e}"))

    # 좀비 청소 — DB에 없는데 mirror에만 있는 .md (raw_/ref_/sec_ 패턴)
    # README.md, index.md, 사용자 노트는 *보존*. doc_id 명명 규약 따른 것만 정리.
    _ZOMBIE_PREFIXES = ("raw_", "ref_", "sec_")
    for p in mirror_root.iterdir():
        if not p.is_file() or p.suffix != ".md":
            continue
        if not p.name.startswith(_ZOMBIE_PREFIXES):
            continue
        if p.name in db_filenames:
            continue
        try:
            p.unlink()
            res.zombies += 1
        except OSError as e:
            res.errors.append((p.name, f"zombie purge failed: {e}"))

    return res


def sync_one(doc_id: str, *,
             force: bool = False,
             mirror_root: Path = MIRROR_ROOT,
             db_path: Path = DB_PATH) -> SyncResult:
    """자료 1건만 동기화 — 향후 자동 hook용.

    V2.6.3.6 — 자격 미달이면 진입 거절 + 기존 .md 삭제.
    """
    res = SyncResult()
    mirror_root.mkdir(parents=True, exist_ok=True)
    docs = _load_docs(db_path, doc_id=doc_id)
    res.scanned = len(docs)
    if not docs:
        res.errors.append((doc_id, "DB에 없음"))
        return res
    d = docs[0]
    fname = _safe_filename(d["doc_id"]) + ".md"
    target = mirror_root / fname

    if not _is_eligible(d):
        res.rejected += 1
        if target.exists():
            try:
                target.unlink()
                res.purged += 1
            except OSError as e:
                res.errors.append((doc_id, f"purge failed: {e}"))
        return res

    res.eligible += 1
    synced_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        if not _needs_update(d, target, force):
            res.skipped += 1
            return res
        content = _build_frontmatter(d, synced_at) + "\n\n" + _build_body(d) + "\n"
        target.write_text(content, encoding="utf-8")
        res.written += 1
    except Exception as e:
        res.errors.append((doc_id, f"{type(e).__name__}: {e}"))
    return res


__all__ = [
    "MIRROR_ROOT", "DB_PATH",
    "SyncResult", "sync_all", "sync_one",
]
