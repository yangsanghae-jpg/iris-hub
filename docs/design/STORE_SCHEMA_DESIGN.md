# 저장소·스키마 상세 설계 (S1) — 데이터볼트 + 지식저장소 + store 계층

- 작성일: 2026-07-03
- 지위: `HUB_REARCHITECTURE` §2의 상세 구현 설계. **재구축 순서 S1** — 모든 것의 기반.
- 범위: 데이터 루트 레이아웃 · DB 스키마(볼트+지식) · `src/store/` DAL · 부트스트랩/초기화.
- 전제: 데이터 처분 가능 → 마이그레이션 없이 깨끗한 스키마로 시작. 단일 사용자·로컬·SQLite.

---

## 0. 이 설계가 확정하는 것

1. **데이터가 물리적으로 어디에 있나** (단일 루트 `iris-data/`)
2. **DB 스키마** — ④데이터볼트 테이블 + ③지식저장소 테이블 (한 DB, 그룹 분리)
3. **`src/store/` 접근 계층** — 탭·엔진이 DB에 닿는 **유일한 관문** (탭→sqlite 직결 금지 강제)
4. **초기화·부트스트랩** — 빈 볼트를 세우는 스크립트

이후 모든 설계서(엔진·위키·그래프·큐레이션)는 본 스키마·DAL을 전제로 한다.

---

## 1. 데이터 루트 레이아웃

```
~/0Dev/iris-data/                     ← 단일 데이터 루트 (repo 밖, git 아님)
├── vault/                            ④ 데이터볼트 (문서층·관대)
│   ├── originals/                    원본 보존 (copy-on-ingest)
│   │   ├── doc/                        문서 채널
│   │   ├── chat/                       AI 대화 채널
│   │   └── web/                        웹 수집 채널
│   ├── extracted/                    추출 md (파서/VLM 산출)
│   ├── index.db                      단일 SQLite (→ .nosync 심볼릭)
│   └── .nosync/                      iCloud 제외 실파일 (index.db, faiss)
│       ├── index.db
│       └── faiss/                    임베딩 인덱스
└── knowledge/                        ③ 지식저장소 (개념층·엄격)
    ├── concepts.yaml                 개념 사전 (canonical + alias 시드)
    └── wiki/                         Gold 마크다운 (Obsidian vault)
```

- **config 반영**: `IRIS_DATA_ROOT = MACHINE_BASE / "iris-data"` (hostname 기반, 이미 있는 패턴).
  현 `IRIS_KNOWLEDGE_ROOT`(=iris-knowledge)를 `iris-data/vault`로 승계·개명.
- **iCloud 회피**: 대용량 바이너리(index.db, faiss)는 `.nosync/`에 두고 심볼릭. (기존 iris-system 패턴 검증됨)
- **wiki가 데이터 루트 안**: DB와 위키가 한 지붕 → "볼트 어디?" 종결. Obsidian은 `knowledge/wiki`를 연다.

---

## 2. DB 스키마 (단일 SQLite, 그룹 분리)

버전 상수 `SCHEMA_VERSION`으로 관리. 전체를 하나의 `schema.sql`로 정의(마이그레이션 누적 아님 — 새 출발).

### 2.1 ④ 데이터볼트 그룹 (문서층)

```sql
-- 문서 (원본 1건 = 1행)
CREATE TABLE documents (
  doc_id       TEXT PRIMARY KEY,          -- {channel}_{yyyymmdd}_{seq} 또는 raw:{hash}
  channel      TEXT NOT NULL,             -- doc | chat | web
  source       TEXT,                      -- 원본 경로 | 세션id | URL
  original_path TEXT,                     -- vault/originals/ 내 보존 경로 (copy-on-ingest)
  title        TEXT,
  trust        TEXT NOT NULL DEFAULT 'auto',   -- auto | clipped | verified (채널별 기본)
  status       TEXT NOT NULL DEFAULT 'active', -- active | quarantine | rejected (큐레이션 게이트)
  industry     TEXT, area TEXT, level TEXT,    -- K2 분류
  ingested_at  TEXT NOT NULL
);
CREATE INDEX idx_doc_status  ON documents(status);
CREATE INDEX idx_doc_channel ON documents(channel);

-- 청크 (검색·RAG 단위)
CREATE TABLE chunks (
  chunk_id TEXT PRIMARY KEY,
  doc_id   TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
  ord      INTEGER NOT NULL,
  text     TEXT NOT NULL,
  page_ref TEXT                            -- 원문 위치 앵커 (p.12 등) — 환각 억제
);
CREATE INDEX idx_chunk_doc ON chunks(doc_id);

-- 전문검색 (dual tokenizer — 한/영 unicode61 + CJK trigram, 검증된 패턴)
CREATE VIRTUAL TABLE documents_fts          USING fts5(text, content='chunks', content_rowid='rowid');
CREATE VIRTUAL TABLE documents_fts_trigram  USING fts5(text, tokenize='trigram');

-- K2 처리 산출 (문서별 1행)
CREATE TABLE document_meta (
  doc_id              TEXT PRIMARY KEY REFERENCES documents(doc_id) ON DELETE CASCADE,
  summary             TEXT,
  topics_json         TEXT, entities_json TEXT, concepts_json TEXT,  -- 원시 추출(정규화 전)
  extract_at          TEXT, classify_at TEXT, summarize_at TEXT,      -- 단계별 timestamp (재개)
  k2_done_at          TEXT,                    -- 3단계 완주 (done 판정 — K2_BATCH 설계)
  classifier_version  TEXT, confidence REAL, fallback_used INTEGER DEFAULT 0,
  processing_started_at TEXT,                  -- 락 (좀비 안전망)
  fail_count          INTEGER DEFAULT 0, last_error TEXT
);

-- 임베딩 (시맨틱 검색 — FAISS 사이드카가 정본, 여기는 참조 매핑)
CREATE TABLE embeddings (
  chunk_id TEXT PRIMARY KEY REFERENCES chunks(chunk_id) ON DELETE CASCADE,
  faiss_id INTEGER, model TEXT, dim INTEGER
);
```

### 2.2 ③ 지식저장소 그룹 (개념층 — 신규 핵심)

```sql
-- 개념 (1급 객체 — 방향성 검토의 "Knowledge Unit")
CREATE TABLE concepts (
  concept_id  TEXT PRIMARY KEY,          -- canonical snake_case (mes, yield_rate, rtd)
  canonical   TEXT NOT NULL,             -- 표시명
  definition  TEXT,                      -- 개념 정의 (위키 개념 페이지 본문)
  trust       TEXT DEFAULT 'candidate',  -- candidate | verified (사람 승인 게이트)
  degree      INTEGER DEFAULT 0,         -- 연결 문서 수 (자산 크기 — 캐시)
  created_at  TEXT, updated_at TEXT
);

-- 개념 별칭 (정규화의 핵심 — MES=생산실행시스템=制造执行系统)
CREATE TABLE concept_aliases (
  concept_id TEXT NOT NULL REFERENCES concepts(concept_id) ON DELETE CASCADE,
  alias      TEXT NOT NULL,
  lang       TEXT,                        -- ko | en | zh
  PRIMARY KEY (concept_id, alias)
);
CREATE INDEX idx_alias ON concept_aliases(alias);

-- 개념 ↔ 문서 링크 (degree 원천, "이 개념을 다루는 문서")
CREATE TABLE concept_docs (
  concept_id TEXT NOT NULL REFERENCES concepts(concept_id) ON DELETE CASCADE,
  doc_id     TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
  weight     REAL DEFAULT 1.0,            -- 관련도 (빈도·위치 기반)
  PRIMARY KEY (concept_id, doc_id)
);

-- 개념 ↔ 개념 관계 (동시출현 1차 → 명시적 Fact 2차)
CREATE TABLE concept_relations (
  src_id TEXT NOT NULL REFERENCES concepts(concept_id) ON DELETE CASCADE,
  dst_id TEXT NOT NULL REFERENCES concepts(concept_id) ON DELETE CASCADE,
  kind   TEXT NOT NULL DEFAULT 'cooccur', -- cooccur | uses | integrates | ... (2차)
  weight INTEGER DEFAULT 1,               -- 동시출현 문서 수
  PRIMARY KEY (src_id, dst_id, kind)
);

-- 시스템 메타
CREATE TABLE meta_kv (key TEXT PRIMARY KEY, value TEXT NOT NULL);
```

**설계 결정**:
- `documents.status`(active/quarantine/rejected)가 큐레이션 게이트. 전시층(위키·그래프)은 active만.
- 개념은 `trust=candidate`로 태어나 사람 승인 시 `verified`. concepts.yaml이 verified 시드.
- `concept_docs`가 위키(개념 페이지의 근거 문서)·그래프(개념-문서 엣지) 공통 원천.
- 원시 추출(`concepts_json`)과 정규화 결과(`concept_docs`)를 **분리** — 정규화 실패/미매칭 추적 가능.

---

## 3. `src/store/` 접근 계층 (DAL)

**핵심 규칙: 탭·엔진은 sqlite3를 직접 열지 않는다. store를 통해서만.** 이 한 규칙이 현재의
"UI에 로직·쿼리가 샌다" 문제를 구조적으로 막는다.

```
src/store/
├── db.py          연결 관리 (경로=config.IRIS_DATA_ROOT, PRAGMA, 트랜잭션, 스키마 보장)
├── vault.py       ④ 볼트 DAL — 문서·청크·검색·메타
└── knowledge.py   ③ 지식 DAL — 개념·별칭·링크·관계
```

### 3.1 `db.py` — 연결·스키마 관문

```python
def get_conn() -> sqlite3.Connection:
    """단일 연결 팩토리. WAL, busy_timeout, foreign_keys 강제."""
def ensure_schema() -> None:
    """schema.sql 적용 + SCHEMA_VERSION 확인. 없으면 생성(빈 볼트)."""
```

### 3.2 `vault.py` — 볼트 DAL (인터페이스 예시)

```python
# 쓰기 (엔진 intake/process가 호출)
def upsert_document(doc: DocRow) -> None
def insert_chunks(doc_id: str, chunks: list[ChunkRow]) -> None
def upsert_meta(doc_id: str, **k2_fields) -> None
def set_status(doc_id: str, status: str, reason: str) -> None   # 큐레이션
# 읽기 (탭·엔진이 호출)
def search_fts(query: str, limit: int) -> list[DocHit]          # dual tokenizer 폴백 내장
def queue_snapshot() -> QueueStats                              # 대기/처리중/완료 (흐름·데이터 탭)
def doc_distribution() -> DistStats                             # 산업·채널 분포 (데이터 탭)
def get_document(doc_id) -> DocRow
```

### 3.3 `knowledge.py` — 지식 DAL (인터페이스 예시)

```python
def resolve_concept(raw: str) -> str | None      # 별칭→canonical (정규화 핵심)
def upsert_concept(c: ConceptRow) -> None
def link_concept_doc(concept_id, doc_id, weight)
def concept_page(concept_id) -> ConceptPage       # 정의+근거문서+관련개념 (위키 탭)
def top_concepts(n) -> list[ConceptRow]           # degree 순 (위키 인덱스·그래프)
def concept_graph(center=None, hops=2) -> Graph   # 그래프 탭
def recompute_degree() -> None                    # concept_docs 집계 → degree 캐시
```

- 탭은 이 함수들만 부른다. SQL은 store 안에만 존재.

---

## 4. 초기화 / 부트스트랩

```
scripts/init_vault.py
  1. iris-data/{vault,knowledge} 디렉터리 생성 (.nosync 심볼릭 포함)
  2. db.ensure_schema()  → 빈 index.db (스키마만)
  3. concepts.yaml 시드 로드 → concepts + concept_aliases (verified)
  4. knowledge/wiki/ 초기화 (README + _templates)
```

- concepts.yaml 시드는 기존 iris-system wiki 44노트의 개념명에서 출발(이관 아닌 개념 추출).
- 멱등: 재실행 안전 (있으면 스킵).

---

## 5. config 반영 (S1 실행 시)

```python
IRIS_DATA_ROOT   = Path(os.getenv("IRIS_DATA_ROOT") or MACHINE_BASE / "iris-data")
IRIS_VAULT       = IRIS_DATA_ROOT / "vault"
IRIS_DB_PATH     = IRIS_VAULT / "index.db"           # 폴백 없음 — 단일 진실원
IRIS_ORIGINALS   = IRIS_VAULT / "originals"
IRIS_EXTRACTED   = IRIS_VAULT / "extracted"
IRIS_KNOWLEDGE   = IRIS_DATA_ROOT / "knowledge"
IRIS_CONCEPTS_YAML = IRIS_KNOWLEDGE / "concepts.yaml"
IRIS_WIKI        = IRIS_KNOWLEDGE / "wiki"
```

- **`IRIS_SYSTEM_*` 폴백 전면 제거** — 단일 진실원. (iris-system은 S8에서 아카이브)
- 단 위키 폴백은 위키 재구축(S5) 전까지 임시 유지 가능 — S1에서는 볼트/DB만 확정, wiki 폴백은 S5까지 잔존 허용.

---

## 6. 마이그레이션 정책 — 없음 (재출발)

- 데이터 처분 가능 → 기존 iris-system/knowledge·0Dev/iris-knowledge의 데이터를 옮기지 않는다.
- 빈 볼트로 시작 → 실문서를 새로 ingest (파일럿 100건 → 배치).
- 기존 것은 아카이브(S8)로 보존만.

---

## 7. 착수 체크리스트 (S1 실행 시 — 별도 실행 승인 후)

```
[ ] iris-data/ 레이아웃 생성 (init_vault.py)
[ ] schema.sql 작성 (§2 전체)
[ ] src/store/{db,vault,knowledge}.py 작성
[ ] config.py IRIS_DATA_ROOT 계열 추가, IRIS_SYSTEM_* 폴백 제거(위키 제외)
[ ] concepts.yaml 시드 (기존 44노트 개념 추출)
[ ] 빈 볼트로 앱 기동 확인 (탭이 store 경유로 정상)
[ ] 테스트: test_store_vault, test_store_knowledge, test_schema
```

---

## 8. 후속 설계서 (본 스키마 위에 얹힘)

| 순서 | 설계서 | 다루는 것 | 상태 |
|---|---|---|---|
| S1 | **본 문서** | 저장소·스키마·store 계층 | ✅ |
| S2 | `ENGINE_RESTRUCTURE_DESIGN` | src 3분할, 엔진 이주 | 대기 |
| S3 | (REFREEZE R1~R3) | 탭 9종 정리 | REFREEZE 참조 |
| S4 | `CONCEPT_LAYER_DESIGN` | concepts.yaml·정규화·K2 개념추출 | 대기 |
| S5 | `WIKI_REBUILD_DESIGN` | 개념 중심 검색 위키 | 대기 (유일 공백) |
| S6 | (GRAPH_V3 기존) | 개념 그래프 | 기존 |
| S7 | (K2_BATCH 기존) | 큐레이션 게이트 | 기존 |
| S8 | `IRIS_SYSTEM_RETIRE_DESIGN` | 아카이브·폴백 제거 | 대기 |

본 문서가 S1 기반이므로, 다음은 S2(엔진 재구조) 또는 S4(개념층)가 자연스러운 후속.
