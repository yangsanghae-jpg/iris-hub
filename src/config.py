"""Paths and constants for iris-hub."""
import os
import socket
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# ─── 머신 인식 (2026-07-02 정책) ─────────────────────────────────────────────
# 운영 경로는 hostname으로 결정한다. M5는 ~/Documents(iCloud 미러)를 절대 참조하지 않는다.
# 배포본은 ~/iris-local/iris-hub에서 돌아 REPO_ROOT.parent가 무의미하므로 hostname 사용.
_IS_M5 = socket.gethostname().startswith("irisM5")
MACHINE_BASE = Path("/Users/iris/0Dev") if _IS_M5 else Path("/Users/iris/Documents/1Dev")
DEV_ROOT = MACHINE_BASE  # 개발 워크스페이스 루트 (M5: /0Dev, M2: /Documents/1Dev)

# diagnosis-tool Git 정본 (평가·표시 기준 URL)
DIAGNOSIS_TOOL_GITHUB = os.getenv(
    "DIAGNOSIS_TOOL_GITHUB",
    "https://github.com/yangsanghae-jpg/diagnosis-tool",
)
# 로컬 clone 경로 override: DIAGNOSIS_TOOL_GIT=/path/to/clone

# ─── iris-knowledge 데이터 루트 (V2.6.3.0) ──────────────────────────────────
# 새 구조: iris-knowledge/{1-inbox,2-processed,3-archive}/
#   M2: /Users/iris/Documents/1Dev/iris-knowledge
#   M5: /Users/iris/0Dev/iris-knowledge
# env IRIS_KNOWLEDGE_ROOT 로 override 가능.
def _default_knowledge_root() -> Path:
    """머신별 데이터 루트 — hostname 기반. M5는 ~/0Dev, iCloud 미러 미참조."""
    return MACHINE_BASE / "iris-knowledge"


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

# ─── 활성 경로: S2 컷오버로 신 볼트(iris-data)로 재지정. IRIS_SYSTEM_* 폴백 전면 제거.
#     실제 상수(IRIS_DB_PATH·IRIS_WIKI_PATH·IRIS_RAW_PATH·IRIS_MIRROR_PATH)는
#     아래 iris-data 데이터 루트 블록에서 IRIS_VAULT_DB 계열에 바인딩한다.

# ─── iris-data 단일 데이터 루트 (S1 / HUB_REARCHITECTURE §2) ─────────────────
# 재구축 저장소. STORE_SCHEMA_DESIGN §1·§5. repo 밖, git 아님.
#   M5: /Users/iris/0Dev/iris-data · M2: /Users/iris/Documents/1Dev/iris-data
# 대용량 바이너리(index.db, faiss)는 .nosync/ 실파일 + 심볼릭으로 iCloud 회피.
#
# 주의(S1 방침): 아래는 신규 store 계층(src/store)이 물는 독립 경로다.
# 라이브 IRIS_DB_PATH 재지정 + IRIS_SYSTEM_* 폴백 제거는 소비자(엔진·탭) 이주와
# 함께 S2/S3 에서 착지한다. S1 은 기반만 깔고 앱을 깨지 않는다.
IRIS_DATA_ROOT   = Path(os.getenv("IRIS_DATA_ROOT") or MACHINE_BASE / "iris-data")

# ④ 데이터볼트 (문서층)
IRIS_VAULT         = IRIS_DATA_ROOT / "vault"
IRIS_VAULT_NOSYNC  = IRIS_VAULT / ".nosync"          # iCloud 제외 실파일
IRIS_VAULT_DB      = IRIS_VAULT / "index.db"         # 심볼릭 → .nosync/index.db
IRIS_ORIGINALS     = IRIS_VAULT / "originals"        # 원본 보존 (copy-on-ingest)
IRIS_EXTRACTED     = IRIS_VAULT / "extracted"        # 추출 md
IRIS_FAISS_DIR     = IRIS_VAULT_NOSYNC / "faiss"     # 임베딩 인덱스 (사이드카)
IRIS_ORIGINAL_CHANNELS = ("doc", "chat", "web")      # originals/ 하위 채널

# ③ 지식저장소 (개념층) — 레거시 IRIS_KNOWLEDGE_ROOT(문서볼트)와 별개
IRIS_KNOWLEDGE_STORE = IRIS_DATA_ROOT / "knowledge"
IRIS_CONCEPTS_YAML   = IRIS_KNOWLEDGE_STORE / "concepts.yaml"
IRIS_WIKI_STORE      = IRIS_KNOWLEDGE_STORE / "wiki"  # Gold md (Obsidian vault)

# concepts.yaml 시드 정본 (repo 내 — init_vault 가 IRIS_CONCEPTS_YAML 로 배포)
CONCEPTS_SEED_YAML   = REPO_ROOT / "data" / "concepts.seed.yaml"

# ─── 활성 경로 (S2 컷오버 — 신 볼트 단일 진실원, 폴백 없음) ───────────────────
IRIS_DB_PATH     = IRIS_VAULT_DB      # 구 iris-knowledge/iris-system DB 대체
IRIS_WIKI_PATH   = IRIS_WIKI_STORE    # 위키 전면 재구축(S5) 전까지 신 위키 스토어
IRIS_RAW_PATH    = IRIS_ORIGINALS     # 원본 보존 루트
IRIS_MIRROR_PATH = IRIS_EXTRACTED     # 추출 md

# 알다 격차 비교 기준 (V2.5.2 §6.1)
ALDA_BASELINE = {
    "documents": 9719,
    "documents_fts": 1228,
    "entity": 9089,
    "concept": 4229,
}

HUB_PORT = 8765
HUB_HOST = "127.0.0.1"

# 작업 산출물 (presenton/deck/pptx). M5는 ~/0Dev/work, ~/Documents 미참조.
IRIS_HUB_WORK_DIR = Path(
    os.getenv("IRIS_HUB_WORK_DIR", str(MACHINE_BASE / "work" / "iris-hub"))
)


def hub_work_subdir(name: str) -> Path:
    """presenton / deck / pptx 등 하위 작업 폴더."""
    p = IRIS_HUB_WORK_DIR / name
    p.mkdir(parents=True, exist_ok=True)
    return p

# ─── LLM 3슬롯 (V2.5.4 부록) ─────────────────────────────────────────────────
OLLAMA_URL = os.getenv("IRIS_OLLAMA_URL", "http://localhost:11434")

# 기본값은 크로스머신 공통 시드. 실제 설치 여부는 llm.resolve_available_model()
# / /api/models 가 런타임에 검증·fallback 한다 (한 머신의 list로 전역 기본을 바꾸지 않음).
IRIS_LLM_DEEP  = os.getenv("IRIS_LLM_DEEP",  "qwen3:8b")
IRIS_LLM_FAST  = os.getenv("IRIS_LLM_FAST",  "qwen3.5:4b")
IRIS_LLM_EMBED = os.getenv("IRIS_LLM_EMBED", "bge-m3")

LLM_MODELS = {
    "deep":  IRIS_LLM_DEEP,
    "fast":  IRIS_LLM_FAST,
    "embed": IRIS_LLM_EMBED,
}
