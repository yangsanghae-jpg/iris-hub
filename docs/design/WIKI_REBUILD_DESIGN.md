# 위키 재구축 상세 설계 (S5) — 분류 그리드 → 개념 중심 검색 위키

- 작성일: 2026-07-03
- 지위: 9탭 중 **유일하게 부품 설계서가 없던 공백**(REFREEZE·GRAPH_V3에서 지적)을 채움.
  S1(스키마)·S4(개념층) 위에 얹힘.
- 범위: 위키 탭을 "K2 분류 그리드"에서 "전문 검색 위키"로 재구축.
- 사용자 지시(2026-07-02): *"위키는 전문 위키가 되어야 한다. 지금처럼 모니터링이 아니라."*

---

## 0. 현재 문제

현 위키 탭(`tabs/wiki_k2.py` 674줄)은 **K2 3파트 분류를 히트맵 그리드로 탐색**하는 화면이다.
전문 위키의 기본기(검색·개념 페이지·상호링크)가 없고, 셀 클릭→문서목록이 전부다.
전문가용 위키(Confluence/Notion/Obsidian) 대비 **검색 부재가 최대 결핍**이었다.

근본 원인: 개념이 1급 객체가 아니어서 "개념 페이지"를 만들 수 없었다 → S4가 이걸 해소.

---

## 1. 재구축 목표 — 4구성

```
📚 위키
├─ ① 검색창 (최상단)      볼트 전문 검색 — 이름으로 찾기
├─ ② 개념 인덱스          degree 순 개념 목록 — "많이 다뤄진 지식"이 위
├─ ③ 개념 페이지          개념 클릭 → 정의 + 근거문서 + 관련개념
└─ ④ 문서 열람            검색·개념에서 진입한 문서의 요약·원문
```

위키 = **"이름으로 찾고 개념 페이지를 읽는다"** (텍스트·리스트 중심).
그래프(S6) = **"관계를 시각적으로 훑는다"** (노드·엣지 중심). 같은 개념 데이터, 다른 소비 방식.

---

## 2. ① 검색 — 볼트 전문 검색 표면화

기존에 DB에 FTS(unicode61 + trigram dual, 검증됨)가 있는데 UI에 노출 안 됐다. `engine/retrieve`가
이를 표면화.

```python
# engine/retrieve/search.py
def search(query, *, limit=20) -> list[Hit]:
    # 1. FTS: unicode61 1차 → 0건 시 trigram 폴백 (CJK 대응)
    # 2. 개념 매칭: query가 개념 별칭이면 그 개념 페이지 우선 (resolve_concept)
    # 3. (2차) 시맨틱: FAISS — 가동 시
    # 결과: 개념 히트 + 문서 히트 혼합, 개념 우선
```

- **개념 우선 정렬**: "MES" 검색 시 → MES 개념 페이지가 맨 위, 그 아래 관련 문서.
- store.vault.search_fts + store.knowledge.resolve_concept 조합.
- iris-system `apps/wiki/retrieval.py`(dispatcher·폴백 로직)를 **engine/retrieve로 흡수** → S8 선결.

---

## 3. ③ 개념 페이지 — 위키의 본체

S4의 `concept_page(concept_id)` 데이터를 렌더:

```
┌─ MES (생산실행시스템)  · 근거 문서 47건 · verified ──────────────┐
│ [정의]  공정 진행·작업지시·WIP 추적·실적수집을 관리하는…          │
│                                                                  │
│ [별칭]  생산실행시스템 · 제조실행시스템 · 制造执行系统 · MES        │
│                                                                  │
│ [관련 개념]  APS · WIP · 실적수집 · SPC   (동시출현 순, 클릭→이동)  │
│                                                                  │
│ [근거 문서 47건]  (weight 순)                                     │
│   • BOM inforever 강의자료 … (요약 200자, 클릭→원문)              │
│   • MES 생산실행시스템 … (신뢰도 0.82)                            │
│   • …                                                            │
└──────────────────────────────────────────────────────────────────┘
```

- **정의**는 concepts.yaml/DB의 definition (사람이 쓰거나 LLM 초안).
- **근거 문서**가 개념↔문서(concept_docs)의 시각화 — "이 지식은 어디에 근거하나".
- **관련 개념**이 concept_relations(동시출현) — 개념 간 탐색.
- verified/candidate 배지 — 사람 승인 상태.

---

## 4. ② 개념 인덱스 — 집중 포인트

```
개념 인덱스 (degree 순)
  MES ████████████ 47      APS ████████ 31      수율 ██████ 24
  ERP █████ 19             WIP ████ 15          …
  ─────────────────────────────────────────────
  후보 개념 132건 (사전 미등록) → [데이터 탭에서 검토]
```

- degree 순 = "가장 많이 다뤄진 지식"이 위 → **집중 포인트가 한눈에** (사용자가 원한 인사이트).
- industry/area 필터 (기존 분류축 재활용 — 버리지 않고 필터로 강등).
- 미등록 후보(concept_candidates)는 개수만 표시, 처리는 데이터 탭 큐레이션(S4/S7).

---

## 5. Gold 위키(사람 작성) 통합

- `iris-data/knowledge/wiki/`의 마크다운(Obsidian vault)은 사람이 직접 쓰는 정본 지식.
- 개념 페이지의 definition을 이 마크다운과 연결(개념 = 위키 노트 1:1 가능).
- Obsidian은 이 폴더를 열어 그래프·편집 → hub 위키 탭은 **검색·개념 뷰**, Obsidian은 **편집**. 역할 분리.
- mirror(store.knowledge)가 verified 개념/문서를 이 폴더로 단방향 동기 (전시층, K2_BATCH 원칙).

---

## 6. 기존 자산 처리

| 현재 | 조치 |
|---|---|
| `tabs/wiki_k2.py` 분류 그리드 | 폐기 → 개념 인덱스의 industry/area 필터로 축소 계승 |
| `wiki_k2.py` 자체 CSS(inventory 중복) | 삭제 → hub_ui.css (UI-UX 설계) |
| K2 3파트 분류축(산업×자동화 등) | 개념 인덱스 필터로 재활용 (버리지 않음) |
| iris-system `apps/wiki/{retrieval,dispatcher,lint}` | engine/retrieve로 흡수 (S8 선결) |
| :8081 K5 위키 서버 | 흡수 후 폐기 (별도 서비스 불필요) |

---

## 7. 뷰어 역할 분리 (위키 vs 그래프) — 경계 확정

REFREEZE 열린결정 1의 해소:

| | 위키 (S5) | 그래프 (S6) |
|---|---|---|
| 진입 | 검색·이름 | 시각 탐색 |
| 표현 | 텍스트·리스트·개념 페이지 | 노드·엣지 |
| 강점 | "MES가 뭐고 근거가 뭔가" 정독 | "MES 주변에 뭐가 몰렸나" 조망 |
| 데이터 | concept_page (S4) | concept_graph (S4) |

같은 S4 개념 데이터를 두 방식으로 소비. 겹치지 않음.

---

## 8. 착수 체크리스트

```
[ ] engine/retrieve/search.py (FTS 표면화 + 개념 우선)
[ ] tabs/wiki.py 재작성 — 검색창·개념인덱스·개념페이지·문서열람
[ ] store.knowledge.concept_page / top_concepts 연동 (S4)
[ ] iris-system retrieval 흡수 → engine/retrieve (S8 선결분)
[ ] Gold wiki 마크다운 ↔ 개념 definition 연결
[ ] 기존 wiki_k2.py 폐기, 분류축을 필터로 이전
[ ] 테스트: test_search(FTS 폴백·개념우선), test_concept_page
```

## 9. 선행 의존

- **S4(개념층) 필수** — 개념 페이지·인덱스가 concept_docs/degree에 의존. S4 없이는 검색만 가능.
- **부분 선행 가능**: 개념층 전이라도 ①검색(FTS 표면화)만 먼저 붙이면 "위키에 검색이 생김" 즉효.
  전체(개념 페이지)는 S4 후. → REFREEZE 열린결정 2의 답: **검색 먼저, 개념 페이지는 S4 후**.
