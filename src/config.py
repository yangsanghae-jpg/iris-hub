"""Paths and constants for iris-hub."""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEPS_YAML = REPO_ROOT / "data" / "phase_deps.yaml"

DEV_ROOT = Path("/Users/iris/Documents/0Dev")

# ─── iris-knowledge 데이터 루트 (V2.6.3.0) ──────────────────────────────────
# 새 구조: iris-knowledge/{1-inbox,2-processed,3-archive}/
#   M2: /Users/iris/Documents/1Dev/iris-knowledge
#   M5: /Users/iris/Documents/0Dev/iris-knowledge
# env IRIS_KNOWLEDGE_ROOT 로 override 가능.
#
# V2.6.3.0 시점: 골격만 박힘. 데이터·DB는 V2.6.3.2/3에서 이전.
# 그 전까지는 IRIS_SYSTEM_DB(legacy)를 그대로 사용.
def _default_knowledge_root() -> Path:
    """머신별 기본값 — 1Dev (M2) 우선, 없으면 0Dev (M5)."""
    for candidate in (
        Path("/Users/iris/Documents/1Dev/iris-knowledge"),
        Path("/Users/iris/Documents/0Dev/iris-knowledge"),
    ):
        if candidate.exists():
            return candidate
    # 둘 다 없으면 일단 1Dev (생성 시점에 자동 발견)
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

# ─── legacy 경로 (V2.6.3.2까지 활성) ────────────────────────────────────────
IRIS_SYSTEM_DB = DEV_ROOT / "iris-system" / "knowledge" / "_index.db"

# 활성 DB 경로 — 새 위치에 있으면 새 위치, 없으면 legacy
IRIS_DB_PATH = (
    IRIS_KNOWLEDGE_DB_NEW if IRIS_KNOWLEDGE_DB_NEW.exists() else IRIS_SYSTEM_DB
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
# M2 기본값 = 가벼운 모델, M5는 .zshrc/venv-activate에서 env override.
OLLAMA_URL = os.getenv("IRIS_OLLAMA_URL", "http://localhost:11434")

IRIS_LLM_DEEP  = os.getenv("IRIS_LLM_DEEP",  "qwen3:8b")      # K2 본문 분석 (배치, 품질↑)
IRIS_LLM_FAST  = os.getenv("IRIS_LLM_FAST",  "qwen3.5:4b")    # 분류 추천·UI 즉응 (1~3초)
IRIS_LLM_EMBED = os.getenv("IRIS_LLM_EMBED", "bge-m3")        # 임베딩 (한·중·영)

LLM_MODELS = {
    "deep":  IRIS_LLM_DEEP,
    "fast":  IRIS_LLM_FAST,
    "embed": IRIS_LLM_EMBED,
}
