"""Paths and constants for iris-hub."""
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
