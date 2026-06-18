"""Paths and constants for iris-hub."""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEPS_YAML = REPO_ROOT / "data" / "phase_deps.yaml"

DEV_ROOT = REPO_ROOT.parent  # iris-hub의 부모 (M2: /1Dev, M5: /0Dev)

# ─── iris-knowledge 데이터 루트 (V2.6.3.0) ──────────────────────────────────
# 새 구조: iris-knowledge/{1-inbox,2-processed,3-archive}/
#   M2: /Users/iris/Documents/1Dev/iris-knowledge
#   M5: /Users/iris/0Dev/iris-knowledge
# env IRIS_KNOWLEDGE_ROOT 로 override 가능.
def _default_knowledge_root() -> Path:
    """머신별 기본값 — M2(1Dev) 우선, 없으면 M5(0Dev 홈)."""
    for candidate in (
        Path("/Users/iris/Documents/1Dev/iris-knowledge"),
        Path("/Users/iris/0Dev/iris-knowledge"),
    ):
        if candidate.exists():
            return candidate
    return Path("/Users/iris/Documents/1Dev/iris-knowledge")


IRIS_KNOWLEDGE_ROOT = Path(
    os.getenv("IRIS_KNOWLEDGE_ROOT") or _default_knowledge_root()
)

# 새 경로 (V2.6.3.3 이후 활성화)
IRIS_KNOWLEDGE_INBOX     = IRIS_KNOWLEDGE_ROOT / "1-inbox"
IRIS_KNOWLEDGE_PROCESSED = IRIS_KNOWLEDGE_ROOT / "2-processed"
IRIS_KNOWLEDGE_ARCHIVE   = IRIS_KNOWLEDGE_ROOT / "3-archive"
IRIS_KNOWLEDGE_DB_NEW    = IRIS_KNOWLEDGE_PROCESSED / "_index.db"
IRIS_KNOWLEDGE_MIRROR    = IRIS_KNOWLEDGE_PROCESSED / "mirror"
IRIS_KNOWLEDGE_WIKI      = IRIS_KNOWLEDGE_PROCESSED / "wiki"
IRIS_KNOWLEDGE_CHUNKS    = IRIS_KNOWLEDGE_PROCESSED / "chunks"

# 1-inbox 채널
IRIS_KNOWLEDGE_RAW       = IRIS_KNOWLEDGE_INBOX / "intake"
IRIS_KNOWLEDGE_EXTERNAL  = IRIS_KNOWLEDGE_INBOX / "external"
IRIS_KNOWLEDGE_STAGING   = IRIS_KNOWLEDGE_INBOX / "folder-staging"

# ─── legacy 경로 (V2.6.3.4까지 fallback 유지) ───────────────────────────────
# iris-system은 /Users/iris/iris-system (홈) 본체. 심볼릭들로 어디서든 접근 가능.
IRIS_SYSTEM_LEGACY = Path("/Users/iris/iris-system")
IRIS_SYSTEM_DB     = IRIS_SYSTEM_LEGACY / "knowledge" / "_index.db"
IRIS_SYSTEM_RAW    = IRIS_SYSTEM_LEGACY / "knowledge" / "raw"
IRIS_SYSTEM_WIKI   = IRIS_SYSTEM_LEGACY / "knowledge" / "wiki"

# ─── 활성 경로 (자동 분기 — 새 위치 있으면 새 위치, 없으면 legacy) ──────────
IRIS_DB_PATH = (
    IRIS_KNOWLEDGE_DB_NEW if IRIS_KNOWLEDGE_DB_NEW.exists() else IRIS_SYSTEM_DB
)
IRIS_RAW_PATH = (
    IRIS_KNOWLEDGE_RAW if IRIS_KNOWLEDGE_RAW.exists() and any(IRIS_KNOWLEDGE_RAW.iterdir())
    else IRIS_SYSTEM_RAW
)
IRIS_WIKI_PATH = (
    IRIS_KNOWLEDGE_WIKI if IRIS_KNOWLEDGE_WIKI.exists() and any(IRIS_KNOWLEDGE_WIKI.iterdir())
    else IRIS_SYSTEM_WIKI
)
IRIS_MIRROR_PATH = (
    IRIS_KNOWLEDGE_MIRROR if IRIS_KNOWLEDGE_MIRROR.exists() else
    Path.home() / "Documents" / "LearningMaster" / "iris-mirror"
)

# 알다 격차 비교 기준 (V2.5.2 §6.1)
ALDA_BASELINE = {
    "documents": 9719,
    "documents_fts": 1228,
    "entity": 9089,
    "concept": 4229,
}

HUB_PORT = 8765
HUB_HOST = "127.0.0.1"

# ─── LLM 3슬롯 (V2.5.4 부록) ─────────────────────────────────────────────────
OLLAMA_URL = os.getenv("IRIS_OLLAMA_URL", "http://localhost:11434")

IRIS_LLM_DEEP  = os.getenv("IRIS_LLM_DEEP",  "qwen3:8b")
IRIS_LLM_FAST  = os.getenv("IRIS_LLM_FAST",  "qwen3.5:4b")
IRIS_LLM_EMBED = os.getenv("IRIS_LLM_EMBED", "bge-m3")

LLM_MODELS = {
    "deep":  IRIS_LLM_DEEP,
    "fast":  IRIS_LLM_FAST,
    "embed": IRIS_LLM_EMBED,
}
