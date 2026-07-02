# 개념층 상세 설계 (S4) — concepts.yaml · 정규화 · K2 개념 추출

- 작성일: 2026-07-03
- 지위: `HUB_REARCHITECTURE` §4의 신규 핵심 역량. S1(스키마)·S2(engine/concept) 위에 얹힘.
- 범위: 개념 사전 · 정규화 로직 · K2에 개념 추출 단계 추가 · 후보 큐 · degree 집계.
- 왜: 방향성 검토(2026-06-09)가 지목한 **"지식 단위(Knowledge Unit)가 정의 안 됨"** 결핍 해소.
  이게 있어야 위키(S5)·그래프(S6)가 "문서 나열"이 아닌 "개념 중심"이 된다.

---

## 0. 핵심 명제

> **문서는 컨테이너, 개념이 자산이다.** MES·수율·RTD·Queue Time 같은 개념이 1급 객체가 되어
> 자기 페이지·연결·degree를 가져야 위키·그래프에서 "집중 포인트 = 인사이트"가 작동한다.

현재 K2는 concept를 **자유 텍스트 JSON**(`concepts_json`)으로 문서 행에 넣을 뿐이라,
"MES"·"생산실행시스템"·"制造执行系统"이 별개 문자열로 파편화된다. S4가 이를 **정규화된
1급 개념**으로 승격시킨다.

---

## 1. 개념 사전 — `concepts.yaml`

지식저장소(`iris-data/knowledge/concepts.yaml`)에 위치. `concepts`+`concept_aliases` 테이블의 시드.

```yaml
# concepts.yaml
concepts:
  mes:
    canonical: "MES (생산실행시스템)"
    aliases: [MES, 생산실행시스템, 생산 실행 시스템, 제조실행시스템, 制造执行系统, manufacturing execution system]
    definition: "공정 진행·작업지시·WIP 추적·실적수집을 관리하는 제조 현장 실행 시스템."
    trust: verified
  yield_rate:
    canonical: "수율 (Yield)"
    aliases: [수율, yield, yield rate, 良率, 收率]
    trust: verified
  # ...

stopwords: [시스템, 관리, 데이터, 방법, 정보]   # 너무 일반적이라 개념화 안 함
```

- `trust: verified` = 사람이 승인한 정본 개념. 시드는 기존 iris-system wiki 44노트의 개념명에서 출발.
- `stopwords` = 정규화에서 거부할 과도하게 일반적인 단어.
- 파일이 정본, DB는 부트스트랩 시 로드(S1 init_vault). 사전 갱신 → 재로드.

---

## 2. 정규화 — `engine/concept/resolve.py`

```python
def resolve_concept(raw: str) -> str | None:
    """자유 텍스트 개념 → canonical concept_id. 실패 시 None(후보 큐로)."""
    # 1. 사전 별칭 매칭 (concept_aliases, 대소문자·공백 무시)
    #    "생산실행시스템" → "mes"
    # 2. 폴백 정규화: NFKC → 소문자 → 공백·기호 제거 → 동일 키 병합
    #    "M.E.S", "mes " → "mes"  (단 "MES"↔"생산실행시스템"은 사전만 가능)
    # 3. 거부: 길이 1자 / 순수 숫자 / stopwords → None
```

- **핵심**: 사전 매칭이 1차(다국어 병합 가능), 폴백은 2차(표기 변형만). 사전 없이 폴백만으로도
  동작하되 병합 품질은 사전에 비례 → 사전 등록이 곧 품질 향상(선순환).
- 이 함수는 위키(S5)·그래프(S6)가 공유하는 정규화 단일 원천.

---

## 3. K2 파이프라인에 개념 단계 추가

현 K2 3단계(extract→classify→summarize)에 **개념 정규화·연결**을 추가.

```
① extract    (기존) topics/entities/concepts 자유 추출 → concepts_json
② classify   (기존) industry/area/level
③ summarize  (기존) 요약
④ conceptize (신규) concepts_json 각 항목을 resolve_concept →
             매칭: concept_docs(concept_id, doc_id, weight) upsert
             미매칭: candidates 테이블/큐로
```

- `④ conceptize`는 LLM 불필요(사전 매칭+규칙) → 빠르고 결정적. `engine/concept/conceptize.py`.
- weight = 문서 내 개념 등장 빈도·위치 기반 (요약/제목 등장 시 가중).
- K2 배치(K2_BATCH 설계)의 각 문서 처리 끝에 conceptize 호출.

---

## 4. 후보 큐 — 미매칭 개념의 사람 승인

```sql
-- 사전에 없는 개념 (정규화 실패분)
CREATE TABLE concept_candidates (
  raw_norm   TEXT PRIMARY KEY,       -- 폴백 정규화 키
  sample     TEXT,                   -- 원문 표기 예
  doc_count  INTEGER DEFAULT 0,      -- 몇 문서에서 나왔나 (우선순위)
  first_seen TEXT, last_seen TEXT
);
```

- 워크플로: 배치가 미매칭 개념을 `concept_candidates`에 누적(doc_count++) → 데이터 탭의 "개념 후보"
  섹션이 doc_count 순으로 노출 → 사람이 [사전 등록](concepts.yaml에 추가) or [기각].
- 등록 시 concepts.yaml 갱신 → 재로드 → 다음 배치부터 매칭.
- **주 1회 10분 리뷰**로 사전이 성장. 10만 건 배치 전 파일럿 100건으로 후보 유형 파악 권장.

---

## 5. degree 집계 — 자산 크기

```python
def recompute_degree():
    """concept_docs 집계 → concepts.degree 캐시. 배치 후 or 주기적."""
    # UPDATE concepts SET degree = (SELECT COUNT(*) FROM concept_docs WHERE concept_id=...)
```

- degree = "이 개념을 다루는 active 문서 수" (status='active'만 — 큐레이션 연동).
- 위키 인덱스(개념 정렬)·그래프(노드 크기)의 공통 기준. 이게 "집중 포인트"의 정량 표현.

---

## 6. 개념 관계 (1차: 동시출현)

```python
def recompute_cooccurrence(min_docs=3):
    """같은 문서 min_docs건 이상에서 함께 등장한 개념쌍 → concept_relations(kind='cooccur')."""
```

- 그래프(S6)의 개념-개념 엣지 원천. `kind='cooccur'`, weight=동시출현 문서 수.
- 명시적 Fact(uses/integrates 등, kind 확장)는 2차 — LLM 관계 추출 별도 사이클(비목표).

---

## 7. `store/knowledge.py` 연동 (S1 DAL 구현)

S1에서 인터페이스만 정의한 함수들을 S4가 실제 구현:

```python
resolve_concept(raw) -> concept_id | None      # §2
upsert_concept / link_concept_doc              # §3
add_candidate(raw_norm, sample, doc_id)        # §4
concept_page(concept_id) -> {정의, 근거문서[], 관련개념[]}  # 위키(S5)
top_concepts(n) / concept_graph(...)           # 위키·그래프
recompute_degree / recompute_cooccurrence      # §5·§6
```

---

## 8. 착수 체크리스트

```
[ ] concepts.yaml 시드 작성 (기존 44노트 개념 추출 — 20~50개로 시작)
[ ] engine/concept/resolve.py (정규화)
[ ] engine/concept/conceptize.py (K2 ④단계)
[ ] store/knowledge.py 개념 함수 구현
[ ] concept_candidates 테이블 + 데이터 탭 후보 섹션
[ ] recompute_degree / cooccurrence
[ ] 파일럿 100건 배치 → 후보 큐 검토 → 사전 보강
[ ] 테스트: test_resolve(별칭·폴백·stopword), test_conceptize, test_degree
```

## 9. 후속

- 개념층이 서면 **S5(위키 재구축)** 가 개념 페이지를 렌더할 데이터를 갖게 됨 → 바로 이어짐.
- **S6(그래프)** 는 GRAPH_V3 설계의 concepts.yaml·concept_docs를 본 문서 산출로 충족.
- 정규화 사전은 ingest 규칙서(`IRIS_INGEST_NORMALIZATION_RULES`)와 **같은 concepts.yaml 공유**.
