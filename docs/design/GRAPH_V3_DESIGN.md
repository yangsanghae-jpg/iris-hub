# 그래프 탭 V3.0 재설계서 — 분류 동치 그래프에서 지식 그래프로

- 작성일: 2026-07-02
- 대상: `src/tabs/graph.py` (V2.5.2 §3.C) → **V3.0**
- 관련 코드: `src/tabs/graph.py`, `src/document_meta.py`, `src/config.py`,
  `src/obsidian_sync.py`, (V2.9 연계) `src/eligibility.py`, `knowledge/concepts.yaml`
- 관련 설계서: `K2_BATCH_CURATION_DESIGN.md` (V2.9 — eligible·큐레이션),
  `IRIS_INGEST_NORMALIZATION_RULES.md` (개념 사전)
- 전제 실측: documents 1,799 / 노드 50 표시 시 엣지 630 (clique 붕괴) / wikilink 42개 파싱되나 미사용

---

## 0. 요약 (한 장)

| 항목 | 현행 | V3.0 |
|---|---|---|
| 엣지 의미 | 같은 industry/area·lane **분류 동치** (clique 폭발, `graph.py:148-179`) | **정보 관계 3종**: 문서—개념 언급 / wiki—wiki 참조 / 개념—개념 동시출현 |
| 노드 | documents만 (전부 보라) | 3종: **개념**(허브) / **문서** / **wiki 노트** |
| 노드 크기 | chunk 수 (분량) | **degree (연결 수)** — 옵시디언 문법 |
| 분류(industry/area) | 엣지로 표현 (원흉) | **노드 색 그룹**으로 표현 (옵시디언 그룹색 대응) |
| 표시 범위 | ORDER BY lane 앞 N개 (임의 표본) | ① 개념 지도(전역, degree 상위) ② 로컬 그래프(선택 노드 2-hop) |
| K2 concepts/entities | 미사용 | 엣지의 주 원천 |
| wikilink 42개 | 표로만 표시 (`graph.py:236-245`) | 실제 엣지 |
| 큐레이션 연동 | 없음 | eligible(active) 문서만 표시 — 전시층 원칙 준수 |
| 렌더러 | streamlit-agraph | 유지 (노드 예산 300) + 전 볼트 조망은 Obsidian(mirror)에 위임 |

설계 원칙: **"엣지 하나 = 정보 한 조각."** 분류가 같다는 사실은 엣지가 아니라 색이다.

---

## 1. 배경 — 현행 평가 (요지)

1. 엣지가 분류 동치라 같은 그룹 N개가 N(N-1)/2 완전그래프를 형성 → force-directed에서 단일 덩어리로 붕괴. 엣지당 정보량 0 — 구조적으로 인사이트 불가.
2. 진짜 링크 원천 2개가 사장됨: `_scan_wikilinks()` 결과(엣지 미사용), `document_meta.concepts_json/entities_json`(그래프 미반영).
3. 크기=chunk 수, 단색, 상시 라벨, 임의 표본(ORDER BY lane LIMIT N) — 옵시디언 시각 문법과 전부 반대.
4. clique 방식이라 노드 수 증가 시 엣지 O(N²) — 성능도 구조적 한계.

## 2. 목표 / 비목표

### 목표
1. "어떤 개념에 문서가 몰리는가"가 첫 화면에서 보인다 (개념 허브 노드가 크게).
2. 노드를 클릭하면 그 지식의 이웃(2-hop)으로 파고들 수 있다.
3. 전시층 원칙 준수: quarantine/rejected 문서는 그래프에 안 나온다 (V2.9 연동).
4. 노드 300 / 엣지 1,500 예산 내에서 항상 반응성 유지.

### 비목표
- 1,799개 전 노드 동시 렌더 — **전 볼트 조망은 Obsidian이 담당** (mirror 동기화가 그 용도).
  이 탭은 "집중 포인트 발견 + 국소 탐색" 특화.
- 그래프 DB(Neo4j) 도입 — SQLite 파생 뷰로 충분한 규모. 10만 건 이후 재평가.
- 관계 유형 추론(references/impacts 등 K3) — 개념 동시출현까지만. K3는 별도 사이클.
- 시계열 애니메이션·3D — 하지 않음.

---

## 3. 그래프 데이터 모델

### 3.1 노드 3종

| 종류 | id 규약 | 원천 | 색 | 크기 |
|---|---|---|---|---|
| **concept** | `c:{canonical}` | concepts.yaml 정규화 통과한 개념 | 연두 `#7CB342` | degree 비례 (주인공) |
| **document** | `d:{doc_id}` | documents (eligible AND status='active') | industry 그룹색 (8색 팔레트) | degree 비례, concept보다 작게 |
| **wiki** | `w:{filename}` | `IRIS_WIKI_PATH/*.md` | 금색 `#F9A825` (Gold 의미) | degree 비례 |

- document 노드 라벨: title 앞 20자, **줌 임계 이하에서는 라벨 숨김** (agraph `font.size` + 소형 노드 라벨 생략 — 4.4).
- concept 노드 라벨: canonical 명 상시 표시 (허브는 항상 읽혀야 함).

### 3.2 엣지 3종

| 종류 | 방향 | 생성 규칙 | 스타일 |
|---|---|---|---|
| **E1 mention** (d→c) | 무방향 | 문서의 정규화 concepts에 개념 포함 | 기본 회색, 폭 1 |
| **E2 wikilink** (w→w) | 방향 | wiki md 본문 `[[대상]]` (기존 `WIKILINK_RE` 재사용) | 파랑, 화살표 |
| **E3 co-occur** (c—c) | 무방향 | 두 개념이 **같은 문서 K건 이상**에서 동시 언급 (기본 K=3) | 연두 점선, 동시출현 수를 width에 반영 (상한 4) |

- E3는 개념 지도 모드에서 개념 간 구조(예: MES—WIP—실적수집 군집)를 드러내는 용도. K 슬라이더로 조절.
- **폐기**: same-matrix·same-lane 엣지 전면 삭제. industry/area는 문서 노드 색으로 이동.
- 장래 확장(비목표 아님, 자리만): E4 source (w→d) — wiki frontmatter `sources:`의 doc_id. 데이터가 쌓이면 자동 활성.

### 3.3 개념 정규화 — 그래프 품질의 전제

```
resolve_concept(raw: str) -> str | None
  1. concepts.yaml alias 테이블 매칭 (대소문자 무시) → canonical 반환
  2. 사전 미존재 시 폴백 정규화: NFKC → 소문자 → 공백·기호 제거 → 동일 키 병합
     (예: "MES", "mes ", "M.E.S" → "mes")  ※ "MES"와 "생산실행시스템"은 폴백으로 못 합침 — 사전만 가능
  3. 반환 None 조건: 길이 1자, 순수 숫자, 불용어(stopword 소목록)
```

- 사전 위치: `config.IRIS_CONCEPTS_YAML = IRIS_KNOWLEDGE_ROOT / "concepts.yaml"` (신설).
- 사전이 없어도 그래프는 동작(폴백만으로), 사전이 생기면 자동으로 병합 품질 상승 —
  **ingest 규칙서(concepts.yaml)와 같은 파일을 공유**하여 두 시스템의 개념 축을 일치시킨다.
- 미매칭(폴백 처리된) 개념은 `후보` 배지 — 정리큐/사전 등록 워크플로(V2.9 B6)와 연결 지점.

### 3.4 데이터 계층 — `src/graph_model.py` (신규)

```python
@dataclass
class KnowledgeGraph:
    nodes: dict[str, GNode]          # id → {kind, label, degree, meta}
    edges: list[GEdge]               # {src, dst, kind, weight}
    stats: dict                      # 개념 수·문서 수·미매칭 수 등

def build_graph(*, conf_min: float, k_cooccur: int = 3) -> KnowledgeGraph:
    # ① eligible 문서 로드: eligibility.eligible_sql() (V2.9) — status/confidence 필터 포함
    #    V2.9 미적용 상태에서는 현행 kind='source' + classifier_version 조건으로 폴백
    # ② document_meta.concepts_json 파싱 → resolve_concept → E1 생성
    # ③ wiki md 스캔 → wiki 노드 + E2 (기존 _scan_wikilinks 확장: 출발 파일 보존)
    # ④ E1 집계로 개념쌍 동시출현 → E3 (K 이상만)
    # ⑤ degree 계산 → 노드 크기 필드
```

- 캐싱: `@st.cache_data(ttl=120)` + DB mtime·wiki 디렉터리 mtime을 캐시 키에 포함
  (워커가 문서를 처리하면 2분 내 그래프 반영).
- 예상 비용: 1,799행 JSON 파싱 + wiki 44파일 스캔 — 수백 ms. 문제없음.
- 렌더와 분리된 순수 함수 → 단위 테스트 대상. 다른 소비자(향후 API·리포트)도 재사용.

---

## 4. 뷰 모드 2종

### 4.1 모드 ① 개념 지도 (기본 화면 — "집중 포인트 발견")

- 노드: **degree 상위 개념 M개** (기본 40, 슬라이더 10~80) + 각 개념의 **상위 연결 문서 t개** (기본 3)
  + wiki 노드 전부 (44개 수준).
- 엣지: 표시된 노드 사이의 E1·E2·E3만.
- 노드 예산 초과 시(300) t를 자동 하향 → 그래도 초과면 M 하향. 예산 로직은 graph_model이 아닌 뷰 계층.
- 이 화면의 존재 이유: "노드가 큰 개념 = 문서가 몰린 지식" — 사용자가 말한
  "집중된 포인트를 통해 인사이트 발견"의 직접 구현.

### 4.2 모드 ② 로컬 그래프 (탐색 — 옵시디언 local graph 대응)

- 진입: (a) 개념 지도에서 노드 클릭 → 상세 패널의 [로컬 그래프] 버튼, (b) 검색창에서 선택.
- 표시: 중심 노드 + 1-hop 전체 + 2-hop은 degree 상위만 (예산 내).
- hop 토글 (1/2), 중심 고정(physics에서 중심 노드 fixed).
- 문서 중심이면: 그 문서의 개념들 + 같은 개념을 공유하는 이웃 문서 → "이 문서와 관련된 지식" 뷰.
- 개념 중심이면: 그 개념의 문서 전부 + 동시출현 개념 → "이 주제의 근거 문서" 뷰.

### 4.3 상세 패널 (그래프 우측 st.column)

agraph의 클릭 반환값(선택 노드 id)을 사용:

```
[document]  title / industry·area·level / confidence / 요약 200자
            개념 칩 목록 (클릭 → 그 개념 로컬 그래프)
            [로컬 그래프] [mirror .md 열기(경로 표시)] [강등(→정리큐, V2.9 연동)]
[concept]   canonical + alias / 연결 문서 수 / 동시출현 개념 상위 5
            연결 문서 목록 (제목, 클릭 → 문서 로컬 그래프)
            사전 미등록(폴백) 개념이면 "후보" 배지 + [concepts.yaml 등록 안내]
[wiki]      파일명 / 인·아웃 링크 수 / [Obsidian에서 열기(경로)]
```

### 4.4 시각 문법 (agraph Config)

| 요소 | 규칙 |
|---|---|
| 크기 | `8 + 3·log2(degree+1)`, 상한 40 — 옵시디언식 로그 스케일 (선형이면 허브가 화면 장악) |
| 색 | concept 연두 / wiki 금색 / document는 industry 8색 팔레트 (`COLOR_BY_KIND`·`COLOR_BY_LANE` 대체). 미분류 회색 |
| 라벨 | concept·wiki 상시. document는 degree ≥ 3 또는 로컬 모드에서만 (`font.size=0` 트릭으로 숨김) |
| 엣지 | E1 회색 실선 1px / E2 파랑 화살표 / E3 연두 점선 width=min(cooccur,4). 엣지 라벨 없음 (현행 "same matrix" 라벨 제거) |
| 물리 | barnesHut, gravitationalConstant 완화 — clique 제거 후엔 기본값 근사로 충분. 노드 150 초과 시 physics 안정화 후 자동 off (진동 방지) |
| 하이라이트 | 현행 `nodeHighlightBehavior` 유지 |

---

## 5. UI 재구성 (`tabs/graph.py` 재작성)

```
🕸️ 그래프
├─ 상단 바: [모드: 개념 지도 | 로컬] · 검색(제목/개념 자동완성 selectbox) · ⚙️ 컨트롤 expander
│    ⚙️ 컨트롤: 개념 수 M (10~80) · 문서/개념 t (1~5) · 동시출현 K (2~5)
│              · industry 멀티셀렉트 · 미매칭(후보) 개념 포함 토글
├─ 본문: 좌 그래프 (agraph, height 640) · 우 상세 패널 (선택 시)
├─ 캡션: "개념 40 · 문서 96 · wiki 44 · 엣지 512 | 미매칭 개념 132 (사전 등록 대기)"
└─ 하단 expander: 미매칭 개념 상위 30 표 (빈도순) — concepts.yaml 등록 후보 목록
     (현행 wikilink 시드 표는 E2가 본 그래프에 들어가므로 삭제)
```

제거되는 현행 요소: Type 필터(kind 3종 → 노드 종류가 대체), Concept 포함 체크(항상 포함이 본질),
고립 노드 숨기기(개념 지도 구성상 고립이 원천 감소, 로컬 모드엔 무의미), 활성 트리거 안내 expander(역할 종료).

## 6. V2.9(큐레이션·배치)와의 결합

| 접점 | 내용 |
|---|---|
| eligible 필터 | `build_graph`가 `eligibility.eligible_sql()` 사용 → quarantine/rejected 문서는 그래프 미표시. **demote 클릭 → 다음 렌더에서 노드 소멸** — "전시는 엄격하게"의 그래프 구현 |
| 상세 패널 [강등] | `curation.demote(doc_id, reason="manual: graph")` 직접 호출 — 그래프에서 쓰레기 노드 발견 즉시 처리하는 동선 (정리큐 탭 왕복 불필요) |
| 개념 사전 | ingest 규칙서의 `concepts.yaml`과 동일 파일 — 사전 등록이 곧 그래프 품질 향상. 미매칭 상위 30 표가 등록 우선순위를 제공 |
| 워커 반영 | 캐시 TTL 120s + mtime 키 → 배치 진행에 따라 그래프가 자라는 게 보임 (1,135건 처리 관전 뷰) |

## 7. 성능 예산

| 항목 | 예산 | 초과 시 |
|---|---|---|
| 렌더 노드 | ≤ 300 | t 하향 → M 하향 (4.1) |
| 렌더 엣지 | ≤ 1,500 | E3의 K 자동 상향 → E1 degree 하위 컷 |
| build_graph | ≤ 1s (1,799 docs) | 캐시 히트 시 0. 10만 건 도달 시 파생 테이블(graph_edges) 사전 계산으로 전환 — 부록 B |
| agraph 렌더 | ≤ 2s | physics off 전환 임계 150 노드 |

## 8. 구현 순서 (PR 단위)

| PR | 내용 | 규모 | 의존 |
|---|---|---|---|
| PR-G1 | `graph_model.py` (노드·엣지 빌더 + resolve_concept 폴백) + 단위 테스트 | 중 | — |
| PR-G2 | 개념 지도 모드 + 시각 문법 + 컨트롤 (탭 재작성 1차, 분류 동치 엣지 폐기) | 중 | G1 |
| PR-G3 | 로컬 그래프 모드 + 상세 패널 + 검색 포커스 | 중 | G2 |
| PR-G4 | concepts.yaml 로더 (config 경로 신설, ingest 쪽과 공유) + 미매칭 후보 표 | 소 | G1 |
| PR-G5 | V2.9 연동 (eligible 필터 전환 + [강등] 버튼) | 소 | V2.9 PR4 |

- G1~G3는 V2.9와 독립적으로 진행 가능 (eligible 폴백 조건 내장).
- 권장: **V2.9 PR1~3(배치) → G1~G2 → 100건 배치 관전 → G3~G5.**
  배치가 돌아야 concepts_json이 쌓여 그래프에 보일 게 생긴다 — 현재 K2 완료 27건뿐이므로
  그래프 개편의 체감은 배치 진행과 비례.

## 9. 테스트

```
test_resolve_concept:  사전 매칭(alias·대소문자), 폴백 병합("MES"/"mes "), 불용어·1자 거부
test_build_graph:      E1 생성(정규화 경유), E2 방향성, E3 K 임계(2건 동시출현 K=3에서 미생성),
                       degree 계산, quarantine 문서 제외 (fixture DB)
test_budget:           개념 80·문서 5000 mock → 노드 300 이하로 강제되는지
test_cache_key:        DB mtime 변경 시 캐시 무효화
통합(수동):            27건 현 데이터로 개념 지도 렌더 — 덩어리 없음·라벨 가독 확인,
                       100건 배치 후 재확인 (허브 개념 부상 여부)
```

## 10. 수용 기준

1. 같은 화면 조건(노드 50)에서 **완전그래프 덩어리 소멸** — 최대 clique 크기 ≤ 8.
2. 첫 화면에서 상위 개념 허브가 크기로 식별 가능 (degree 1위 개념이 최대 노드).
3. 문서 노드 클릭 → 상세 패널 → 로컬 그래프 전환이 3클릭 이내.
4. demote한 문서가 캐시 만료 후 그래프에서 사라짐.
5. 1,135건 전량 처리 후에도 개념 지도 렌더 총 시간 ≤ 3s.

## 11. 리스크와 완화

| 리스크 | 완화 |
|---|---|
| concepts_json 품질 낮음 (자유 텍스트 파편화) | 폴백 정규화로 1차 병합 + 미매칭 상위 30 표로 사전 등록 유도. 그래프가 사전 구축의 동기·우선순위를 제공하는 선순환 |
| 개념이 너무 일반적 ("시스템", "관리") | 불용어 소목록 + 상세 패널에서 발견 시 stopword 추가하는 운영 절차 (concepts.yaml에 `stopwords:` 섹션) |
| agraph 한계 (줌 라벨 페이드 미지원 등) | degree 기반 라벨 생략으로 근사. 부족 판명 시 렌더러만 교체 (graph_model은 렌더러 중립) — 후보: ECharts graph, sigma.js 임베드 |
| 27건 상태에서 빈약해 보임 | 캡션에 "처리 N건 기준" 명시 + 배치 진행과 함께 성장하는 구조임을 8절 순서로 해소 |

## 부록 A — 색 팔레트 (industry 8색)

```
A 프로젝트ETO #6A5ACD   B 반도체 #1E88E5   C 전자조립 #00897B   D 패널·신에너지 #43A047
E 화학공정 #F4511E      F FMCG #8D6E63     G 제약바이오 #D81B60  H 자동차 #5E35B1
미분류 #9E9E9E · concept #7CB342 · wiki #F9A825
```

## 부록 B — 10만 건 대비 파생 테이블 (설계만, V3.0 미구현)

```sql
CREATE TABLE graph_edges (
  src TEXT, dst TEXT, kind TEXT, weight INTEGER,
  PRIMARY KEY (src, dst, kind)
);
-- 워커 사이클 말미에 증분 갱신. build_graph는 이 테이블 SELECT만.
-- 이 시점에 Neo4j/GraphRAG 재평가 (중심성·커뮤니티 탐지 수요 발생 시).
```

---

## 부록 C — UX 스펙 (확정 목업 기준 2026-07-03)

목업을 확정 스펙으로 고정. 구현은 이 레이아웃·컴포넌트·상태를 그대로 따른다.

### C.1 레이아웃

```
┌ 컨트롤 [개념 지도|로컬 2-hop] [개념 40] [동시출현 K≥3] ······ [개념검색] ┐
├──────────────────────────────────────────────┬───────────────────────────┤
│ 그래프 캔버스 (SVG, 방사형)                    │ 상세 패널 190px           │
│        ERP(19)          APS(31)                │ ● MES                     │
│           \            /                       │ 생산실행시스템 · verified │
│      O문서  MES(47) --- O문서                  │ degree 47 / 연결 6        │
│           /    |    \                          │ 이웃: APS WIP SPC         │
│      WIP(15)  SPC(7)  수율(24)                 │ [위키에서 열기]           │
│  범례: ●개념(크기=degree) O문서 ┄동시출현 ─언급 │ [로컬 그래프]             │
└──────────────────────────────────────────────┴───────────────────────────┘
"덩어리 아님 — 개념 허브 중심 방사형. 큰 노드 = 문서 몰린 지식."
```

### C.2 컴포넌트 스펙

| 영역 | 컴포넌트 | 데이터 바인딩 | 규칙 |
|---|---|---|---|
| 컨트롤 | 모드 토글(개념 지도/로컬) | 뷰 상태 | 로컬=선택 노드 2-hop |
| 컨트롤 | 개념 수 N / 동시출현 K | `top_concepts(N)`·relations 필터 | 노드 예산 300 초과 시 자동 하향 |
| 컨트롤 | 개념 검색 | `resolve_concept` | 매치 시 해당 노드 포커스 |
| 캔버스 | 개념 노드 | `concepts`(degree) | 크기=`8+3·log2(degree+1)`, 색 accent |
| 캔버스 | 문서 노드 | `concept_docs` | 소형 회색, degree≥3 or 로컬에서만 라벨 |
| 캔버스 | 엣지 E1 언급(개념-문서) | `concept_docs` | 실선 회색 |
| 캔버스 | 엣지 E3 동시출현(개념-개념) | `concept_relations` | 점선 청록, width=min(weight,4) |
| 범례 | 4종 (개념·문서·동시출현·언급) | — | 하단 고정 |
| 상세 | 선택 노드 정보 | `concept_page` 요약 | degree·이웃 + [위키에서 열기][로컬 그래프] |

### C.3 상태 전이
- 노드 클릭 → 상세 패널 갱신 (session_state `graph_sel`).
- [위키에서 열기] → 위키 탭 그 개념 페이지. [로컬 그래프] → 모드=로컬, 중심=선택 노드.
- 폐기: same-matrix·same-lane 엣지(분류 동치) 전면 제거 — 본 스펙엔 존재하지 않음.

### C.4 위키와의 경계 (상호)
- 위키=개념 정독(근거·출처), 그래프=관계 조망. 같은 S4 데이터, 상호 링크로 왕복.
