# iris-hub 재설계 — 4계층 구조 (UI · 엔진 · 지식저장소 · 데이터볼트)

- 작성일: 2026-07-03
- 지위: **구조 재설계 마스터.** `HUB_ARCHITECTURE_REFREEZE`(정체성·탭 재편)의 상위 골격을
  물리 구조(계층·저장소·폴더)로 확정한다. 부품 설계서 6종은 여전히 그 아래.
- 배경: 초기 구상(진도 콘솔 → 지식 OS)이 여러 번 바뀌며 **UI·엔진·데이터가 한 곳에 뒤섞이고
  저장소가 이중화**됐다. iris-system(전신)이 iris-hub(후신)에 흡수되다 만 상태가 그 증거.
  데이터가 전부 테스트용이라 **저장소·구조를 새로 잡고 소스만 재활용**하는 재설계가 가능한 시점.
- 전제: 단일 사용자·로컬 도구. 데이터 처분 가능. iris-system은 아카이브 예정(`iris-legacy-2026`).

---

## 0. 왜 4계층인가

지금 문제의 뿌리는 **"무엇이 UI이고 무엇이 데이터인지 경계가 없다"**는 것이다. 탭이 DB를 직접
쿼리하고, 엔진 로직이 UI 파일에 박혀 있고, "문서"와 "지식(개념)"이 같은 취급을 받는다.
재설계의 핵심은 **책임을 4개로 쪼개고 경계를 강제**하는 것이다.

```
┌─────────────────────────────────────────────────────────────────┐
│ ① UI 계층        사람이 보고 조작 (Streamlit 탭). 로직 없음.       │
│    └ 호출 ↓                                                        │
│ ② 엔진 계층      처리 로직. 수집·분류·개념추출·큐레이션·검색.       │
│    └ 읽고 씀 ↓↑                                                    │
│ ③ 지식저장소     개념·관계·위키(Gold). "엄격하게 전시".            │  ← 뷰어가 봄
│ ④ 데이터볼트     원본·추출md·문서·청크·임베딩. "관대하게 저장".     │  ← RAG가 봄
└─────────────────────────────────────────────────────────────────┘
   엔진이 ④(볼트)를 ③(지식)으로 승격시킨다. 이게 파이프라인의 본질.
```

핵심 구분 — **데이터볼트 ≠ 지식저장소** (사용자가 명시적으로 나눈 지점):

| | 데이터볼트 (④) | 지식저장소 (③) |
|---|---|---|
| 담는 것 | 문서·청크·임베딩·원본 | 개념·엔티티·관계·Gold 위키 |
| 단위 | 파일/문서 | 지식 단위(MES, 수율, RTD…) |
| 정책 | 관대 (다 담음, RAG 재현율) | 엄격 (검증된 것만, 전시 정밀도) |
| 소비자 | WebUI·OpenClaw RAG, 검색 | 위키·그래프 뷰어, 진단툴 A2 |
| 방향성 검토 대응 | "문서는 컨테이너" | **"실제 자산 = Knowledge Unit"** |

이 구분이 없어서 지금 위키가 "개념 위키"가 못 되고 "문서 분류 그리드"에 머물러 있다.

---

## 1. 계층별 정의와 경계

### ① UI 계층 — `iris-hub/src/tabs/` (재활용)

- Streamlit 탭. **표시와 사용자 액션만.** DB 직접 쿼리·처리 로직 금지 → 엔진 호출로.
- 탭 9종 (REFREEZE 확정): 입력 · WebUI · OpenClaw · 흐름 · 데이터 · 위키 · 그래프 · PPT · 진단툴.
- 현재 위반: 탭이 sqlite를 직접 연다(graph.py, wiki_k2.py 등). 재설계 시 **store 계층 경유로 교정**.

### ② 엔진 계층 — `iris-hub/src/engine/` (신설, 기존 소스 이주)

파이프라인 로직 전부. 지금 `src/`·`src/ingest/`에 흩어진 것을 한 곳으로 모은다.

| 엔진 모듈 | 책임 | 재활용 원본 |
|---|---|---|
| `intake` | 파일·대화·웹 → 볼트 (K1) | `ingest/raw_intake, origin_rules, folder_load, converter` |
| `process` | 분류·요약·**개념/엔티티 추출**·정규화 (K2) | `k2_pipeline, k2, classify, document_meta` |
| `concept` | **개념 사전 매칭·정규화·관계**(신규 핵심) | — (concepts.yaml 기반 신규) |
| `curate` | 승격·강등·품질 게이트 | `queue`(큐레이션), 신규 |
| `retrieve` | FTS·시맨틱·개념 검색 | iris-system `apps/wiki/retrieval` 흡수 |
| `secure` | secure lane 차단 | `ingest/secure_gate, secure_intake` |

### ③ 지식저장소 계층 — 데이터(코드 아님) + `src/store/knowledge.py` DAL

- **개념 테이블**: canonical + alias(한/영/중) + 정의 + 신뢰도
- **개념-문서 링크**: 어떤 문서가 이 개념을 다루는가 (degree = 자산 크기)
- **개념-개념 관계**: 동시출현(1차) → 명시적 Fact(2차, 나중)
- **Gold 위키**: 사람이 쓰는 마크다운 (Obsidian 호환 vault)
- 소비: 위키 탭(검색·개념 페이지), 그래프 탭(개념 그래프), 진단툴 A2

### ④ 데이터볼트 계층 — 데이터 + `src/store/vault.py` DAL

- **원본 보존**: `originals/{channel}/` — copy-on-ingest (진단툴 A2 역추적용)
- **추출 md**: `extracted/` — 파서/VLM 산출
- **문서 인덱스 DB**: documents · chunks · documents_fts(+trigram) · embeddings · document_meta
- 소비: 검색, WebUI/OpenClaw RAG

---

## 2. 저장소 아키텍처 (새로 잡음)

데이터 처분 가능하므로 **마이그레이션 없이 깨끗한 스키마**로 시작.

### 2.1 DB — 단일 SQLite, 계층별 테이블 그룹

볼트와 지식을 **물리적으로 나누지 않고 한 DB**에 둔다. 이유: "개념 X를 다루는 문서"
같은 조인이 핵심이라 분리하면 오히려 복잡. 단 **테이블 그룹으로 계층을 명확히**.

```sql
-- ④ 데이터볼트 그룹 (문서층)
documents(doc_id, channel, source, ingested_at, trust, industry, area, level, status, title)
chunks(chunk_id, doc_id, ord, text)
documents_fts / documents_fts_trigram        -- 검색
embeddings(chunk_id, vec)                     -- 시맨틱 (FAISS 사이드카 or sqlite-vec)
document_meta(doc_id, summary, k2_done_at, confidence, fallback_used, ...)  -- K2 산출

-- ③ 지식저장소 그룹 (개념층) — 신규
concepts(concept_id, canonical, definition, trust, degree)
concept_aliases(concept_id, alias, lang)
concept_docs(concept_id, doc_id, weight)      -- 개념 ↔ 문서 (degree 원천)
concept_relations(src_id, dst_id, kind, weight)  -- 동시출현→Fact
```

- `documents.status`(active/quarantine/rejected) = 큐레이션 게이트 (K2_BATCH 설계).
- 개념 정규화 사전(concepts.yaml)은 `concepts`+`concept_aliases`의 시드/부트스트랩.

### 2.2 파일 레이아웃 (데이터 디렉터리 — repo 밖, git 아님)

```
~/0Dev/iris-data/                 (신규 데이터 루트 — 이름 조정 가능)
├── vault/                        ④ 데이터볼트
│   ├── originals/{doc|chat|web}/  원본 보존
│   ├── extracted/                추출 md
│   ├── index.db                  단일 DB (§2.1)
│   └── .faiss/                   임베딩 인덱스 (nosync)
└── knowledge/                    ③ 지식저장소
    ├── concepts.yaml             개념 사전 (시드)
    └── wiki/                     Gold 마크다운 (Obsidian이 여는 vault)
```

- 현재 `0Dev/iris-knowledge`(빈 새 구조)를 이 레이아웃으로 재편하거나 `iris-data`로 신설.
- **DB·wiki가 한 데이터 루트 아래** 모여 "볼트가 어디 있나" 혼란 종결. iCloud 회피는 `.nosync`.

---

## 3. 폴더 / repo 구조 (모노repo)

**단일 활성 repo = iris-hub.** 단일 사용자 로컬 도구에 프론트/백 repo 분리는 과함
(그게 iris-system 이중화의 원인이었음). 코어 파이프라인은 하나로.

```
iris-hub/  (유일 활성 repo)
├── app.py                    진입점
├── src/
│   ├── tabs/                 ① UI 계층 (9탭)
│   ├── engine/               ② 엔진 계층 (intake/process/concept/curate/retrieve/secure)
│   ├── store/                ③④ 저장소 접근 (vault.py, knowledge.py) — DB/파일 유일 관문
│   ├── integrations/         외부 서비스 클라이언트 (openclaw, openwebui, presenton)
│   ├── ui_kit.py             UI 공통
│   └── config.py             경로·상수 (hostname 기반, 이미 정리됨)
├── data/                     앱 자산 (템플릿·테마) — 데이터 아님
├── docs/design/              설계서
└── tests/

~/0Dev/iris-data/             데이터 (repo 밖, §2.2)
```

원칙: **탭은 store를 통해서만 데이터에 닿는다.** 탭→sqlite 직결 금지. 이 한 규칙이
"UI에 로직이 샌다"는 현 문제를 구조적으로 막는다.

### 외부 서비스 (별도 유지 — 흡수 안 함)

로컬 컨테이너로 각자 도는 것들. iris-hub은 `src/integrations/`로 호출/링크만.

| 서비스 | repo | iris-hub 관계 |
|---|---|---|
| OpenWebUI + l2-gateway + l4-search | iris-stack | 대화·RAG·웹검색 (볼트 참조) |
| OpenClaw | iris-claw | 에이전트 (볼트 참조) |
| Presenton | (docker) | PPT 생성 |
| ~~Grafana / iris-gateway~~ | — | REFREEZE에서 폐기·보류 |
| diagnosis-tool | diagnosis-tool | 별도 앱. iris-hub 지식을 A2 소스로 소비 |

---

## 4. 기존 소스 재활용 매핑 (소스만 활용)

| 새 위치 | 재활용 원본 (현 iris-hub) | 조치 |
|---|---|---|
| `engine/intake/` | `ingest/{raw_intake,origin_rules,folder_load}`, `converter.py` | 이주 + 경로 config화 |
| `engine/process/` | `k2_pipeline.py`, `k2.py`, `classify.py`, `document_meta.py` | 이주 + 개념추출 단계 추가 |
| `engine/concept/` | — | **신규** (concepts.yaml 정규화) |
| `engine/curate/` | `queue.py`(큐레이션부), `reprocess.py` | 이주 + 강등 경로(K2_BATCH) |
| `engine/retrieve/` | iris-system `apps/wiki/{retrieval,dispatcher,semantic}` | **흡수** (iris-system 퇴역) |
| `store/vault.py` | `measurements.py`, `flow.py`(측정부), 직접 sqlite | 통합 — DB 유일 관문 |
| `store/knowledge.py` | `obsidian_sync.py`, `graph.py`(모델부) | 통합 |
| `tabs/` | 현 `tabs/` 13개 → 9개 | 폐기 4·통합 2·위키 재구축 |
| `engine/output` / `deck/` | `deck/*`, `exporter*.py`, `presenton.py` | 재활용 (Deck V3) |
| `integrations/` | `external.py`, `_openclaw_token`, l2 클라이언트 | 이주 |

**버릴 것**: `phases.py`(진도 콘솔 잔재), iris-system apps 사본 중복, 스플릿브레인 폴백.
**진단툴 관련**(`diagnosis_*.py`)은 독립 탭이라 그대로.

---

## 5. 재구축 순서

데이터가 새것이라 "마이그레이션"이 아니라 "새로 세우고 소스 이주". REFREEZE 로드맵과 통합:

| 단계 | 내용 | 산출 |
|---|---|---|
| S1 | 데이터 루트 확정(`iris-data`) + 새 DB 스키마(§2.1) | 빈 볼트+지식 스키마 |
| S2 | `src/` 3분할(tabs/engine/store) — 소스 이주, 로직 UI에서 분리 | 계층 경계 성립 |
| S3 | 폐기 4탭 삭제 + 통합 2쌍(입력·데이터) + 흐름/데이터 분리 | 탭 9종 (REFREEZE R1~R3) |
| S4 | 개념층: concepts.yaml + `engine/concept` + K2 개념추출 | 지식저장소 채움 시작 |
| S5 | 위키 재구축(검색+개념 페이지) → iris-system retrieval 흡수 | 전문 위키 |
| S6 | 그래프 개념 그래프 (Graph V3) | 뷰어 완성 |
| S7 | 큐레이션 게이트(데이터 탭) | 품질 |
| S8 | iris-system → `iris-legacy-2026` 아카이브, 폴백 config 삭제 | 이중화 종결 |

S1~S3 = "구조 세우기"(가장 큰 혼잡 해소). S4~S7 = "지식층 채우기". S8 = 정리 종결.

---

## 6. 결정 필요 지점 (내 권고 포함)

| # | 결정 | 내 권고 | 근거 |
|---|---|---|---|
| 1 | 모노repo vs 멀티repo | **모노(iris-hub 단일)** | 단일사용자 로컬. 분리가 이중화의 원인이었음 |
| 2 | 볼트·지식 DB 분리 vs 통합 | **단일 DB, 테이블 그룹** | 개념↔문서 조인이 핵심. 분리하면 복잡만 늘어 |
| 3 | 데이터 루트 이름/위치 | `~/0Dev/iris-data/` (신규) | DB·wiki를 한 지붕 아래로 → "볼트 어디?" 종결 |
| 4 | 외부 서비스 흡수 여부 | **별도 유지** (integrations로 호출) | 컨테이너 독립 배포. 흡수는 과함 |
| 5 | iris-system 처리 | **아카이브**(삭제 아님), retrieval만 흡수 | git 히스토리 = 싼 보험 |
| 6 | 임베딩 저장 | FAISS 사이드카 우선, sqlite-vec 검토 | 기존 자산(nomic-embed) 재활용 |

---

## 7. 이 재설계가 해소하는 것 (착수 전/후)

| 현 혼잡 | 재설계 후 |
|---|---|
| UI가 DB 직접 쿼리 | 탭 → store 계층만 |
| 엔진 로직이 UI·ingest·iris-system에 3중 산재 | `engine/` 한 곳 |
| 문서=지식 뭉뚱그림 | 볼트(문서) ↔ 지식저장소(개념) 분리 |
| 볼트 2곳(iris-system vs 0Dev) | `iris-data/` 단일 |
| repo 2개 중복(iris-system 전신) | iris-hub 단일 + 아카이브 |
| 15탭 잡탕 | 9탭 계층 정렬 |
| 위키=분류 그리드 | 위키=개념 검색 |

---

## 8. 비고

- 본 문서는 **구조(물리)** 를 확정. **정체성·탭 성격**은 `HUB_ARCHITECTURE_REFREEZE`, **개별 기능**은
  부품 설계서 6종. 세 층위가 마스터→구조→부품으로 정렬됨.
- "소스만 재활용, 저장소는 새로"라는 사용자 결정을 §4(재활용)·§2(새 저장소)로 구현.
- 착수는 S1~S3(구조 세우기)부터. 여기까지가 "혼잡 해소"의 8할. S4 이후는 "지식 OS로 성장".
