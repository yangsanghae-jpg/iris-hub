# 엔진 재구조 상세 설계 (S2) — src 3분할 + 엔진 이주

- 작성일: 2026-07-03
- 지위: `HUB_REARCHITECTURE` §1·§4의 상세 구현. **재구축 순서 S2** — S1(저장소) 위에 얹힘.
- 범위: 현 `src/` 평면 구조 → `src/{tabs, engine, store, integrations}` 계층 분리 + 소스 이주 매핑.
- 원칙: **로직을 UI에서 떼어내 engine으로, 데이터 접근은 store로.** 소스 재활용(재작성 아님).

---

## 0. 문제 — 현 src는 평면이라 계층이 없다

현재 `src/`에 27개 파일이 평면으로 있고, UI(tabs)·처리로직(k2/ingest)·측정(measurements)·
출력(deck)이 섞여 있다. 탭이 sqlite를 직접 열고, ingest 로직이 iris-system 사본으로 존재한다.
S2는 이걸 **4계층 디렉터리로 물리 분리**하고 import 경계를 세운다.

---

## 1. 목표 디렉터리

```
src/
├── tabs/          ① UI — Streamlit 탭 (표시·액션만)
├── engine/        ② 처리 로직
│   ├── intake/       수집 (K1)
│   ├── process/      분류·요약·개념추출 (K2)
│   ├── concept/      개념 정규화·관계 (S4에서 채움)
│   ├── curate/       승격·강등·품질
│   ├── retrieve/     검색 (FTS·시맨틱·개념)
│   ├── secure/       secure lane 차단
│   └── output/       PPT·문서 생성
├── store/         ③④ 저장소 DAL (S1: db/vault/knowledge)
├── integrations/  외부 서비스 클라이언트 (openclaw/openwebui/presenton)
├── ui_kit.py      UI 공통
├── llm.py         LLM 래퍼 (엔진·인테그레이션 공용)
└── config.py      경로·상수
```

---

## 2. 소스 이주 매핑 (재활용 — 파일 이동 + import 경로 갱신)

| 현재 | → 새 위치 | 변경 |
|---|---|---|
| `ingest/raw_intake.py` | `engine/intake/documents.py` | DB 접근을 store.vault로 |
| `ingest/origin_rules.py` | `engine/intake/origin.py` | 그대로 |
| `ingest/reference_diagnosis.py` | `engine/intake/reference.py` | store 경유 |
| `folder_load.py`, `converter.py` | `engine/intake/` | 그대로 |
| `ingest/secure_gate.py`, `secure_intake.py` | `engine/secure/` | 그대로 |
| `ingest/fts_sync.py` | `store/vault.py`에 흡수 | FTS는 store 책임 |
| `k2_pipeline.py`, `k2.py` | `engine/process/pipeline.py` | K2_BATCH 개선 반영 |
| `classify.py` | `engine/process/classify.py` | 그대로 |
| `document_meta.py` | `store/vault.py`에 흡수 | meta는 볼트 DAL |
| `queue.py` | `engine/curate/queue.py` + `store` | 측정은 store, 처리는 engine |
| `reprocess.py` | `engine/curate/` | 그대로 |
| `measurements.py`, `flow.py`(측정) | `store/vault.py` (통계 함수) | 탭은 store 호출 |
| `obsidian_sync.py` | `store/knowledge.py` (mirror) | 지식 DAL |
| `graph.py`(모델) | `store/knowledge.py::concept_graph` | 지식 DAL |
| `deck/*`, `exporter*.py`, `presenton.py` | `engine/output/` | 그대로 (Deck V3) |
| `external.py`, `_openclaw_token` | `integrations/` | 그대로 |
| `k5`/retrieval (iris-system apps 흡수) | `engine/retrieve/` | S5·S8에서 |
| `phases.py`, `diagnosis_migration.py` | 진단툴 탭 전용 — `engine/` 밖 유지 | 독립 |
| `tabs/*` | `tabs/` (9종으로 정리) | REFREEZE R1~R3 |

---

## 3. import 경계 (계층 규칙 — 강제)

```
tabs        →  engine, store, integrations, ui_kit     (역방향 금지)
engine      →  store, llm                               (tabs import 금지)
store       →  config, db만                             (engine·tabs import 금지)
integrations→  config, llm                              (외부 API)
```

- **탭이 sqlite3·store 내부 SQL을 직접 만지지 않는다.** store DAL 함수만 호출.
- **엔진이 streamlit을 import하지 않는다.** UI 비의존 → 테스트·CLI·워커에서 재사용 가능.
- 위반 감지: 간단한 테스트로 각 계층의 금지 import를 정적 검사(`test_layer_boundaries`).

---

## 4. 이주 순서 (앱 안 깨뜨리며)

큰 이동을 한 번에 하면 위험. **아래→위 순**으로, 각 단계 후 앱 기동 확인.

| 단계 | 작업 | 검증 |
|---|---|---|
| E1 | `store/` 신설 (S1 DAL) + config `IRIS_DATA_ROOT` | 빈 볼트 기동 |
| E2 | `engine/output/` (deck 이동 — 가장 독립적) | PPT 탭 정상 |
| E3 | `engine/secure/` + `engine/intake/` 이주 + store 경유 | 입력·외부응답 정상 |
| E4 | `engine/process/` (k2) 이주 + store 경유 | 흐름 처리 정상 |
| E5 | `engine/curate/` (queue) 이주 | 데이터 탭 정상 |
| E6 | `integrations/` (external) 이주 | WebUI·OpenClaw 링크 정상 |
| E7 | 탭이 store DAL만 부르게 리팩터 (sqlite 직결 제거) | 전 탭 정상 |
| E8 | `test_layer_boundaries` 통과 | 경계 성립 |

- 각 단계는 별도 커밋 (원복 방지). E7이 "UI에 로직 새는 문제"의 실제 해소 지점.
- `engine/concept/`·`engine/retrieve/`는 빈 골격만 두고 S4·S5에서 채움.

---

## 5. 이 재구조가 여는 것

- 엔진이 UI 비의존 → **CLI 워커**(K2 배치, K2_BATCH 설계의 k2_worker)가 같은 엔진 코드 재사용.
- store가 유일 관문 → 볼트/지식 스키마 변경이 한 곳으로 국소화.
- 탭이 얇아짐 → REFREEZE의 9탭 정리·UI-UX 통일이 쉬워짐.
- iris-system apps 사본 중복 제거 → S8 아카이브의 선결.

---

## 6. 비고

- 본 문서는 **구조 이동**만. 각 엔진 모듈의 *내부 로직 개선*은 해당 부품 설계서
  (process=K2_BATCH, output=Deck V3, retrieve=WIKI_REBUILD)가 담당.
- 이주는 기계적(파일 mv + import 갱신)이라 위험 낮음. 단 E7(탭 리팩터)만 탭별 실사 필요.
- 후속: S4(개념층) — `engine/concept/`와 `store/knowledge` 개념 함수를 실제로 채운다.
