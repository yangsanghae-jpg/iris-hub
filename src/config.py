"""Paths and constants for iris-hub."""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEPS_YAML = REPO_ROOT / "data" / "phase_deps.yaml"

DEV_ROOT = Path("/Users/iris/Documents/0Dev")
IRIS_SYSTEM_DB = DEV_ROOT / "iris-system" / "knowledge" / "_index.db"

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
