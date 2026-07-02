# iris-system 퇴역 상세 설계 (S8) — 아카이브 + 폴백 제거

- 작성일: 2026-07-03
- 지위: 재구축 마지막 단계. `HUB_REARCHITECTURE` §3·§5의 종결. **위키 재구축(S5) 완료 후** 착수.
- 범위: iris-system(전신)을 활성 repo에서 제외 → 아카이브. iris-hub 단일화 완성.
- 전제: iris-hub이 iris-system 코드를 런타임 import하지 않음(실측 완료). 남은 탯줄은 3개.

---

## 0. 배경 — 전신/후신

`iris-system`은 iris-hub의 **전신**이다. iris-hub이 필요한 것을 복사해오며 흡수하다 만 상태라,
같은 로직이 두 repo에 이중 존재한다("너무 혼잡"의 뿌리). 데이터 처분 가능·단일 사용자 로컬이므로
프론트/백 repo 분리는 과함 → **iris-hub 단일 활성 repo로 종결**하고 iris-system은 아카이브.

---

## 1. 남은 탯줄 3개 (실측 2026-07-02)

| # | 결합 | 성격 | 끊는 시점 |
|---|---|---|---|
| A | config `IRIS_SYSTEM_*` 폴백 (DB·raw·wiki) | 코드 | S1(DB)·S5(wiki) 후 |
| B | `apps/wiki/{retrieval,dispatcher,lint}` — :8081 K5 서버 | 코드(별도 서비스) | S5에서 engine/retrieve로 흡수 |
| C | `knowledge/`(1792 문서 + Gold 44노트) | 데이터 | 처분(테스트) |

**iris-hub은 iris-system apps를 import하지 않음** — 이미 사본을 가짐. 그래서 A·B만 처리하면 분리 완료.

---

## 2. 선결 조건 (S8 착수 전 반드시)

```
[ ] S1 완료 — IRIS_DB_PATH가 iris-data 단일, iris-system DB 폴백 미사용
[ ] S5 완료 — 위키 검색·개념이 engine/retrieve로 동작 (iris-system retrieval 흡수)
[ ] :8081 K5 서버에 의존하는 외부 호출자 없음 확인
     (diagnosis-tool의 IRIS_K5_MODE=http 등 — grep으로 확인)
```

S5 없이 S8을 하면 위키가 데이터를 잃으므로 **순서 엄수**.

---

## 3. 작업

### 3.1 config 폴백 전면 제거

```python
# 제거 대상 (config.py)
IRIS_SYSTEM_LEGACY / IRIS_SYSTEM_DB / IRIS_SYSTEM_RAW / IRIS_SYSTEM_WIKI
IRIS_DB_PATH   = ... else IRIS_SYSTEM_DB        # → iris-data 단일 (폴백 삭제)
IRIS_WIKI_PATH = ... else IRIS_SYSTEM_WIKI      # → iris-data/knowledge/wiki 단일
IRIS_RAW_PATH  = ... else IRIS_SYSTEM_RAW       # → iris-data/vault 단일
```
- 검증: `grep -rn "IRIS_SYSTEM\|iris-system" src/` → 주석·docstring 외 0건.

### 3.2 :8081 K5 서버 흡수 확인

- S5에서 `engine/retrieve`가 retrieval·dispatcher·폴백을 이미 담당.
- lint(broken/orphan/duplicate)는 `engine/curate` 또는 데이터 탭 큐레이션으로.
- :8081 uvicorn 서버 중지 → placeholders의 :8081 링크·안내 제거.

### 3.3 iris-system repo 아카이브

```
1. GitHub: yangsanghae-jpg/iris-system → 개명 iris-legacy-2026 (또는 -archive)
   Settings → Archive this repository (read-only)
2. 로컬: ~/0Dev/iris-system → ~/0Dev-archive-20260703/ 로 이동 (심볼릭 정리)
   - ~/iris-system(홈 본체)도 함께 아카이브 or 보존 판단
3. _layers/L4-K-knowledge 심볼릭 제거 (진도콘솔 잔재)
```
- **삭제 아님** — git 히스토리·옛 엔진 로직은 참고용 보존. 개명+Archive+로컬 이동.

### 3.4 데이터 처분

- iris-system/knowledge(1792 문서·Gold 44노트)는 테스트 데이터 → 아카이브와 함께 동결.
- 실지식은 iris-data 볼트에 새로 ingest (S1 이후 파일럿→배치).

---

## 4. 검증 (분리 완료 기준)

```
[ ] 앱 기동 시 iris-system 경로 미접근 (config grep 0건)
[ ] 위키·검색이 engine/retrieve로 정상 (iris-system 없이)
[ ] :8081 미가동 상태로 전 탭 정상
[ ] 심볼릭 참조 없음 (_layers 정리)
[ ] iris-hub이 유일 활성 repo — 코드·데이터·설계서 한 곳
```

---

## 5. 이 단계가 종결하는 것

| 재구축 전 | S8 후 |
|---|---|
| repo 2개(전신+후신) 중복 | iris-hub 단일 활성 + iris-legacy 아카이브 |
| config 폴백으로 behavior가 파일 존재에 의존 | 단일 진실원, 폴백 없음 |
| :8081 별도 위키 서버 | engine/retrieve 내장 |
| _layers 심볼릭 지도(진도콘솔 잔재) | 제거 |
| "볼트·코드가 어디?" 혼란 | iris-hub + iris-data 두 곳으로 명확 |

---

## 6. 비고

- S8은 **정리의 종착점**. S1~S7이 iris-hub을 자립시킨 뒤라야 안전.
- 아카이브는 보수적으로(개명+Archive+이동, 삭제 아님). 필요 시 되돌리기 가능.
- 이로써 재설계 전체 완료: UI·엔진·지식저장소·데이터볼트 4계층이 iris-hub 단일 repo +
  iris-data 단일 데이터 루트로 정렬.
