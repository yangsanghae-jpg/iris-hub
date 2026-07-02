# K2 배치 안정화 + 지식 큐레이션 V2.9 설계서

- 작성일: 2026-07-02
- 대상 버전: queue V2.6.3.8 / k2_pipeline V2.7.0 / flow V2.6.3.5 → **V2.9**
- 관련 코드: `src/queue.py`, `src/k2_pipeline.py`, `src/flow.py`, `src/obsidian_sync.py`,
  `src/document_meta.py`, `src/tabs/flow.py`, `src/ingest/schema.sql`, `src/ingest/migrations/`
- 전제 실측 (2026-07-02): documents 1,792 / source 1,162 / 대기 1,135 / done 27 / eligible 25 /
  mirror 0 / archive 0 / 신 3단계 파이프라인 통과 0건

---

## 0. 요약 (한 장)

이 설계서는 두 축을 하나의 릴리스로 묶는다. **1,135건(이후 10만 건) 배치를 돌리기 전에** 둘 다 있어야 한다.

**Part A — 배치 안정화**: "실패가 어디에 남고 어떻게 재시도되는가"를 바로잡는다.

| # | 결함 | 현행 | V2.9 |
|---|---|---|---|
| A1 | 실패가 done으로 둔갑, 재시도 불가 | `any_fail`이어도 `classifier_version` 기록 (`queue.py:294`) | 실패 상태 분리 + `fail_count`/`last_error` 영속화 + 재시도 큐 |
| A2 | 본문 앞 3,000자만 분석 → 오분류·부실요약 | `k2_pipeline.py:74,124,233` | 청크 Map-Reduce (extract=map, summarize=reduce) |
| A3 | 단계 재개 미구현 (독스트링과 불일치) | 항상 ①②③ 전부 재실행 (`queue.py:255-289`) | stage timestamp 있으면 스킵 |
| A4 | Streamlit 버튼 안 동기 실행 | `tabs/flow.py:250` | 독립 워커 `scripts/k2_worker.py`, UI는 감시 전용 |
| A5 | mirror 동기화 수동 (25건 미동기) | 버튼 클릭 필요 | 워커 배치 사이클 말미 자동 sync |
| A6 | archive 0건 — 원본 보전 미이행 | No-Copy 로딩, path만 참조 | 신규 유입 copy-on-ingest + 기존분 백필 잡 + path 생존 점검 |
| A7 | 3단계 전부 deep — 전량 며칠 소요 | `role="deep"` 고정 | extract=fast(`format=json`) + external 채널 extract 스킵 |

**Part B — 큐레이션**: 원칙은 **"저장은 관대하게, 전시는 엄격하게."**

| # | 항목 | 내용 |
|---|---|---|
| B1 | 강등 경로 | `documents.status` (active/quarantine/rejected) 신설. 전시층(eligible→mirror/graph)에서만 내려가고 검색층(DB/chunks/FTS)에는 남음 |
| B2 | 입구 게이트 | `confidence < 임계값` → 자동 quarantine (eligible 부여 안 함) |
| B3 | 정리 큐 탭 | 강등 후보 5종 규칙 자동 탐지 → 사람이 [강등/유지] 클릭. 자동 삭제 없음 |
| B4 | 감사 로그 | 모든 상태 전이를 `curation_log`에 기록 (누가·언제·왜) |

---

# Part A — 배치 파이프라인 안정화

## A1. 실패 상태 모델 재정의

### A1.1 문서 처리 상태 기계 (신규 정의)

```
                    ┌─────────────┐
        set_processing│            │clear
  waiting ──────────→ in_progress ─┼→ done          (3단계 모두 성공)
     ↑                             ├→ failed        (1단계 이상 실패, fail_count < 3)
     │          재시도 fetch        │
     └─────────────────────────────┘
                                   └→ failed_perm   (fail_count ≥ 3 — 사람 개입 대상)
```

상태는 별도 컬럼이 아니라 **기존·신규 필드의 조합으로 판정**한다 (상태 컬럼 이중화 방지):

| 상태 | 판정식 |
|---|---|
| waiting | `document_meta` 없음 OR (`k2_done_at IS NULL` AND 락 없음 AND `fail_count < 3`) |
| in_progress | `processing_started_at IS NOT NULL` |
| done | `k2_done_at IS NOT NULL` |
| failed | `k2_done_at IS NULL` AND `fail_count BETWEEN 1 AND 2` AND 락 없음 |
| failed_perm | `k2_done_at IS NULL` AND `fail_count >= 3` |

핵심 변경: **done 판정 기준을 `classifier_version`에서 신규 컬럼 `k2_done_at`으로 교체.**
`k2_done_at`은 ①②③ 모두 성공했을 때만 기록한다. `classifier_version`은 "어떤 버전이 처리했나"라는
본래 의미로 되돌린다 (rule-only 경로도 `k2_done_at`을 기록하되 `classifier_version='rule-only-v1'`).

### A1.2 스키마 변경 — migration 007

```sql
-- 007_fail_tracking.sql
ALTER TABLE document_meta ADD COLUMN k2_done_at   TEXT;             -- 3단계 완주 시각
ALTER TABLE document_meta ADD COLUMN fail_count   INTEGER DEFAULT 0;
ALTER TABLE document_meta ADD COLUMN last_error   TEXT;             -- "stage=classify | TimeoutError: ..."
ALTER TABLE document_meta ADD COLUMN last_fail_at TEXT;

-- 백필: 기존 done(구 기준) 27건을 신 기준으로 이관
UPDATE document_meta SET k2_done_at = COALESCE(summarize_at, classify_at, extract_at, '2026-07-02T00:00:00Z')
WHERE classifier_version IS NOT NULL;
```

```sql
-- 007_fail_tracking_down.sql : 컬럼 4개 DROP (SQLite 3.35+)
```

### A1.3 `queue.py` 변경 명세

**`process_batch()` 실패 처리 (현행 240~361행 교체 요지):**

```python
# 단계 실패 시 (r_ext/r_cls/r_sum 중 하나라도 not ok):
#   - 성공한 단계의 timestamp·데이터는 보존 (기존 mark_stage 그대로)
#   - k2_done_at 기록하지 않음
#   - fail_count += 1, last_error = f"stage={실패단계} | {err}", last_fail_at = now
#   - classify 실패 시의 rule fallback은 유지하되 (industry/area 임시 채움)
#     k2_done_at은 여전히 기록하지 않음 → 재시도 대상 유지
# 3단계 모두 성공 시:
#   - k2_done_at = now, fail_count = 0, last_error = NULL
```

**`measure_queue()` 쿼리 교체:**

```sql
-- 대기 (재시도 포함)
SELECT COUNT(*) FROM documents d
LEFT JOIN document_meta m ON d.doc_id = m.doc_id
WHERE d.kind='source' AND d.status='active'          -- ← Part B 연동
  AND (m.doc_id IS NULL
       OR (m.k2_done_at IS NULL AND m.processing_started_at IS NULL
           AND COALESCE(m.fail_count,0) < 3));

-- 완료
SELECT COUNT(*) FROM document_meta WHERE k2_done_at IS NOT NULL;

-- 실패(재시도 예정) / 영구실패 — QueueSnapshot에 필드 추가
failed:      k2_done_at IS NULL AND fail_count BETWEEN 1 AND 2 AND 락 없음
failed_perm: k2_done_at IS NULL AND fail_count >= 3
```

`QueueSnapshot`에 `failed: int`, `failed_perm: int`, `failed_docs: list[dict]` (doc_id, last_error, fail_count) 추가.

**`fetch_waiting()` 우선순위:** 신규(fail_count=0) 먼저, 재시도(1~2)는 뒤로. `ORDER BY COALESCE(m.fail_count,0), d.doc_id`.

### A1.4 UI 반영 (`tabs/flow.py`)

- 큐 카드에 `실패(재시도)` / `영구실패` 카운트 추가.
- 영구실패 목록 expander: doc_id, title, fail_count, last_error + [재시도 초기화] 버튼
  (`UPDATE document_meta SET fail_count=0 WHERE doc_id=?`).

## A2. 본문 잘림 제거 — 청크 Map-Reduce

### A2.1 설계 원칙

- **extract = Map**: 청크별로 keyword 추출 후 합집합. 문서 전체가 빠짐없이 분석된다.
- **summarize = Reduce**: 원문 대신 "청크별 추출 결과 + 대표 발췌"를 입력으로. 입력이 작고 균질해져
  로컬 모델 헛소리가 줄어든다.
- **classify = Head + Keywords**: 분류는 전문이 필요 없다. "앞 3,000자 + 전체 keyword 합집합"이면 충분.

### A2.2 `k2_pipeline.py` 변경 명세

```python
# ① stage_extract_mapped(title, chunks: list[str], *, role="fast") -> StageResult
#    - 청크를 CHUNK_GROUP_CHARS(기본 2,500자)씩 그룹핑 → 그룹당 _prompt_extract 1회
#    - 그룹 수 상한 MAX_EXTRACT_CALLS = 8 (초과분은 균등 샘플링 — 초대형 문서 비용 상한)
#    - 결과 병합: topics/entities/concepts 각각 빈도순 dedup, 상한 topics 10 / entities 15 / concepts 15
#    - 부분 실패 허용: 그룹 N개 중 1개 실패면 나머지로 진행, meta에 extract_partial=True

# ② stage_classify(title, head_3000, keywords, role="deep")   # 현행 유지 + keywords가 전문 대표
# ③ stage_summarize_reduced(title, keywords, chunk_digests, classification, role="deep")
#    - chunk_digests: 그룹별 첫 문장 + 수치 라인 추출 (규칙 기반, LLM 없음, 총 4,000자 상한)
#    - 프롬프트에 "아래 발췌·키워드에 있는 내용만 요약" 명시
```

`process_batch`의 `_load_doc_text()`는 `(title, chunks: list[str])` 반환으로 변경 (`ORDER BY ord` 유지, join 제거).

### A2.3 예상 효과·비용

- 호출 수: 문서당 extract 1회 → 평균 2~3회(fast). classify·summarize는 1회 유지(deep).
- BOM PDF류(26페이지): 현행 "앞 1.5페이지 분석" → 전 페이지 keyword 반영.
- fast 모델 사용(A7)과 결합 시 문서당 총 시간은 현행 대비 동등~단축.

## A3. 단계 재개 (resume)

`process_batch` 각 단계 앞에 스킵 분기 (독스트링 약속의 이행):

```python
meta = dm.get(doc_id) or {}
if meta.get("extract_at"):
    keywords = _keywords_from_meta(meta)     # topics/entities/concepts JSON 역직렬화
else:
    r_ext = k2pl.stage_extract_mapped(...)   # 성공 시 mark_stage + 데이터 upsert
# classify, summarize 동일 패턴
```

전제: extract 성공 시 keyword를 **그 시점에 upsert** (현행은 3단계 끝의 일괄 upsert라 중간 실패 시 데이터 유실 —
단계별 즉시 저장으로 변경). `dm.upsert`는 부분 필드 갱신을 이미 지원하므로 호출 위치만 이동.

## A4. 독립 워커 — `scripts/k2_worker.py` (신규)

### A4.1 요구사항

1. 터미널/launchd에서 실행, Streamlit과 독립된 프로세스.
2. 기존 DB 큐·락을 그대로 사용 (`set_processing`이 프로세스 간 중복을 이미 방지).
3. 우아한 정지: `Ctrl-C`(SIGINT) 시 현재 문서까지 처리 후 종료. `data/k2_worker.stop` 파일 존재 시에도 정지
   (UI 정지 버튼용).
4. 사이클 로그를 파일과 stdout에 기록, UI가 읽을 수 있는 상태 파일 갱신.

### A4.2 구조 (의사코드)

```python
# scripts/k2_worker.py
# 사용: python3 -m scripts.k2_worker --batch 5 --sleep 2 --max-docs 0 --sync-every 20
def main(batch=5, sleep_s=2, max_docs=0, sync_every=20):
    processed = 0
    while not stop_requested():
        q.clear_stale_locks(30)
        ids = q.fetch_waiting(batch)
        if not ids:
            write_state("idle"); time.sleep(30); continue
        r = q.process_batch(ids)                       # A1~A3 적용판
        processed += r.succeeded
        log(f"batch done: +{r.succeeded} fail {r.failed} skip {r.skipped}")
        write_state("running", processed=processed, last=r)
        if processed and processed % sync_every < batch:
            osync.sync_all()                           # A5 — 주기 자동 동기화
        if max_docs and processed >= max_docs: break
        time.sleep(sleep_s)
    osync.sync_all()                                   # 종료 직전 최종 동기화
    write_state("stopped")
```

- `write_state()`: `data/k2_worker_state.json` — `{status, pid, started_at, processed, last_batch, updated_at}`.
- 로그: `logs/k2_worker_YYYYMMDD.log` (일 단위 롤링, 간단히 날짜 파일명).
- `--max-docs 10` → A1 파일럿 실행 그 자체. `--max-docs 100` → 2차 배치.

### A4.3 UI 역할 재정의 (`tabs/flow.py`)

- 처리 섹션에 워커 상태 카드: state.json 읽어 `상태/처리량/최근 배치/워커 로그 tail 20줄` 표시.
- [워커 정지 요청] 버튼 = stop 파일 생성. [정지 해제] = 삭제.
- 기존 [묶음 처리] 버튼은 **10건 이하로 제한** (안내문: "대량 처리는 워커 사용") — 소량 수동 처리·디버깅 용도로 존치.

## A5. mirror 자동 동기화

- 워커: `--sync-every N` (기본 20건)마다 + 종료 시 `sync_all()` 호출 (A4.2).
- 수동 배치(UI 10건 이하): 처리 완료 직후 `sync_all()` 자동 호출 (버튼 클릭 제거).
- `sync_all`은 이미 멱등 (`_needs_update`로 변경분만) — 추가 비용 미미.

## A6. 원본 보전 (archive) 정책

### A6.1 결정 사항

| 대상 | 정책 |
|---|---|
| 신규 유입 (intake/external/folder) | **copy-on-ingest**: 인덱싱 시점에 `3-archive/<date>/<doc_id>/`로 원본+추출md 복사 (기존 intake 경로는 이미 이 구조 — folder No-Copy 로딩에만 예외가 있었음. 예외 제거) |
| 기존 1,162건 (path만 참조) | **백필 잡** `scripts/archive_backfill.py`: path 생존 확인 → 존재하면 archive로 복사 + `documents.path` 갱신, 소실이면 `archive_missing` 리포트에 기록 (chunks로 본문은 보존되므로 데이터 유실은 아님) |
| 대용량 예외 | 파일 500MB 초과는 복사 대신 심볼릭 링크 + manifest에 원경로·해시 기록 |
| 주기 점검 | 워커 기동 시 1회 path 생존 샘플링(임의 50건) → 소실률 리포트를 state.json에 포함 |

### A6.2 백필 잡 명세

```
python3 -m scripts.archive_backfill --dry-run   # 복사 대상·용량 합계 리포트만
python3 -m scripts.archive_backfill             # 실행. 재실행 안전(멱등): 이미 archive에 있으면 스킵
```
출력: `복사 N건 / 스킵 N건 / 소실 N건 (목록 → data/archive_missing.txt)`.
디스크 요구량을 dry-run이 먼저 보여주므로 사용자가 실행 여부 판단.

## A7. 속도 최적화

| 항목 | 내용 |
|---|---|
| extract → fast | A2의 map 호출은 `role="fast"` + Ollama `format="json"` 강제. qwen 계열 `<think>` 누출은 (a) format=json, (b) 응답 전처리 `re.sub(r"<think>.*?</think>", "", raw, flags=re.S)` 이중 방어. `llm.generate_json`에 `format_json=True` 인자 추가 |
| external 채널 스킵 | `documents.origin='external'`(LLM 응답 저장분)은 이미 정제 텍스트 → extract 생략, 본문 앞부분에서 규칙 기반 keyword(헤딩·볼드어) 추출로 대체 |
| 처리량 실측 게이트 | 100건 배치에서 문서당 평균 시간 실측 → `1135 × t̄` 를 UI에 표시. 예측이 24h 초과면 fast 모델 상향(qwen3:8b를 fast로) 검토 |

## A8. 지표 정합 (flow 탭)

- `done`(큐) 과 `eligible`(전시 자격) 을 **한 카드에서 분리 표기**: `K2 완료 N / 전시 자격 M / 격리 Q`.
- `eligible` 정의를 단일 함수 `src/eligibility.py :: is_eligible(d) / eligible_sql()`로 통합 —
  현행 3곳 중복(`flow.py:143-149`, `obsidian_sync.py:68`, curation 탭 신설분)을 제거해 정의 불일치 재발 차단.

---

# Part B — 지식 큐레이션 (전시층 강등 체계)

## B0. 원칙

1. **저장은 관대하게**: 검색층(documents/chunks/FTS)에서는 삭제하지 않는다. RAG 재현율 우선.
2. **전시는 엄격하게**: mirror/graph/wiki는 `active + eligible + confidence 통과`만. 정밀도 우선.
3. **내려가는 길은 사람이 승인**: 자동은 후보 탐지까지. 강등 클릭은 사람. (예외: 입구 quarantine은 자동 — 아직 전시된 적 없는 문서라 강등이 아님)
4. **모든 전이는 기록**: 원복 가능 + 이후 자동화 판단의 데이터.

## B1. 스키마 — migration 008

```sql
-- 008_curation.sql
ALTER TABLE documents ADD COLUMN status TEXT NOT NULL DEFAULT 'active';
--   active     : 정상 (전시 가능)
--   quarantine : 격리 (입구 게이트 미달 or 사람 강등) — 검색층에는 존재, 전시층 제외
--   rejected   : 퇴출 (사람 확정) — 전시 제외 + 정리큐 후보에서도 제외
CREATE INDEX IF NOT EXISTS idx_doc_status ON documents(status);

CREATE TABLE IF NOT EXISTS curation_log (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  doc_id     TEXT NOT NULL,
  from_state TEXT NOT NULL,
  to_state   TEXT NOT NULL,
  reason     TEXT NOT NULL,     -- 규칙 코드 or 자유 텍스트 ("C-CONF<0.6", "manual: 중복")
  actor      TEXT NOT NULL,     -- 'auto-gate' | 'user'
  at         TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_clog_doc ON curation_log(doc_id);
```

## B2. 상태 전이 API — `src/curation.py` (신규)

```python
def demote(doc_id, to="quarantine", *, reason, actor="user") -> None
    # documents.status 갱신 + curation_log INSERT + sync_one(doc_id) 즉시 호출
    #   → obsidian_sync의 기존 로직(obsidian_sync.py:420-424: 자격 미달이면 mirror md unlink)이
    #     그래프에서 곧바로 제거. 삭제 코드 신규 작성 없음.
def restore(doc_id, *, reason, actor="user") -> None      # → active + sync_one
def reject(doc_id, *, reason, actor="user") -> None       # quarantine → rejected (확정)
def history(doc_id) -> list[dict]                          # curation_log 조회
```

## B3. eligible 정의 확장 (A8의 단일 함수에 반영)

```sql
-- src/eligibility.py :: eligible_sql()
d.kind = 'source'
AND d.status = 'active'                                   -- B1 신설
AND m.k2_done_at IS NOT NULL                              -- A1 신설 (구: classifier_version)
AND d.industry IS NOT NULL AND d.area IS NOT NULL
AND COALESCE(m.confidence, 0) >= :threshold               -- B4 입구 게이트
```

- `:threshold` = `config.IRIS_CURATION_CONF_MIN` (기본 **0.6**, env로 조정).
- 적용처: `flow.py` eligible 카운트, `obsidian_sync._is_eligible`, 정리큐 탭. 3곳 모두 이 함수 참조.

## B4. 입구 게이트 (자동 quarantine)

`process_batch`의 3단계 성공 직후:

```python
if k2_result.confidence < CONF_MIN:
    curation.demote(doc_id, reason=f"C-CONF {k2_result.confidence:.2f}<{CONF_MIN}",
                    actor="auto-gate")
# fallback_used(규칙 분류)도 동일하게 quarantine (reason="C-FALLBACK")
```

- quarantine이어도 K2 결과(요약·keyword)는 저장된다 — 검색층에서는 정상 검색됨.
- 임계값 캘리브레이션: 100건 배치 후 confidence 분포 히스토그램을 정리큐 탭에 표시,
  사용자가 임계값을 보고 조정 (초기 0.6은 가설).

## B5. 강등 후보 탐지 — `curation.find_candidates()` 

전부 기존 산출물의 SQL 조합. LLM·신규 분석 엔진 없음.

| 코드 | 규칙 | 데이터 원천 |
|---|---|---|
| C-CONF | `confidence < threshold` 인데 active (게이트 도입 전 처리분) | document_meta.confidence |
| C-ORPHAN | mirror 진입 후 개념 연결 0: `concepts_json='[]'` AND topics 2개 이하 | document_meta |
| C-WEAK | 본문 빈약: chunks 합계 < 320자 OR summary < 50자 | chunks, document_meta |
| C-DUP | 제목 유사: 정규화 제목(공백·기호 제거) 완전일치 그룹, 나중 doc이 후보 | documents.title |
| C-STALE | `origin='web'` AND `fetched_at` < 1년 전 | documents |

반환: `[{doc_id, title, rules:[...], detail, suggested: 'quarantine'}]` — 한 문서가 여러 규칙에 걸리면 병합.

## B6. 정리 큐 탭 — `src/tabs/curation.py` (신규)

```
🧹 정리 큐
├─ 요약 카드: active N / quarantine N / rejected N / 후보 N
├─ confidence 분포 히스토그램 (B4 임계값 캘리브레이션용)
├─ [후보 스캔 실행] → find_candidates() (수 초, LLM 없음)
├─ 후보 테이블: ☑ | 제목 | 규칙 배지 | confidence | 사유 상세 | 미리보기(요약 200자)
│    └ 일괄 [선택 강등] / 개별 [강등] [유지(스누즈 30일)] 
│       유지 선택 시 meta_kv에 `curation_snooze:<doc_id>` = 만료일 기록 → 후보 재등장 억제
├─ 격리 목록 탭: quarantine 문서 + [복원] [퇴출 확정] + 강등 사유·이력
└─ 이력 탭: curation_log 최근 200건
```

운영 리듬: **주 1회 후보 스캔 → 10분 리뷰.** 배치(A4) 직후에는 후보가 몰리므로
워커 완료 시 state.json에 `curation_pending: N`을 포함해 흐름 탭에 배지 표시.

## B7. 하지 않는 것 (명시적 비목표)

- 자동 삭제·자동 rejected 전이 (사람 확정 필수).
- 점수화 모델·임베딩 기반 품질 스코어 — 데이터(curation_log) 축적 후 V3 검토.
- wiki(Gold) 노트의 강등 — wiki는 사람이 쓰는 층이므로 이 체계 밖. 기존 wiki lint로 관리.
- chunks/FTS 물리 삭제 — rejected여도 검색층 보존 (법적·용량 사유 발생 시 별도 스크립트로).

---

# Part C — 구현·검증 계획

## C1. 구현 순서 (PR 단위)

| PR | 내용 | 규모 | 의존 |
|---|---|---|---|
| PR1 | migration 007 + queue.py 실패 모델(A1) + 단계 재개(A3) + 단계별 즉시 upsert | 중 | — |
| PR2 | k2_pipeline Map-Reduce(A2) + fast extract·format=json(A7) | 중 | PR1 |
| PR3 | k2_worker.py + state.json + UI 워커 카드(A4) + 자동 sync(A5) | 중 | PR1 |
| PR4 | migration 008 + eligibility.py 통합(A8·B3) + curation.py API(B2) + 입구 게이트(B4) | 중 | PR1 |
| PR5 | 정리 큐 탭(B5·B6) | 중 | PR4 |
| PR6 | archive_backfill.py + copy-on-ingest 예외 제거(A6) | 소 | — (병행 가능) |

권장 순서: PR1 → PR2 → PR3 → **10건 파일럿** → PR4 → PR5 → **100건 배치** → PR6 → 전량.

## C2. 실행 계획 (배치 롤아웃)

```
0. PR1~3 머지 후: 기존 done 27건 백필 확인 (k2_done_at 27건)
1. 파일럿:  python3 -m scripts.k2_worker --batch 5 --max-docs 10
   - 긴 문서(BOM PDF급) 2~3건 포함되도록 선택 처리 병용
   - 점검: 요약 vs 원문 대조(수동), fail_count 분포, extract_partial 발생률
2. PR4~5 머지 → 100건: --max-docs 100
   - 점검: 문서당 평균 시간 → 전량 예상치, confidence 분포 → 임계값 확정,
     정리큐 후보 유형 분포
3. 전량:   --batch 5 (상시 실행) — 1,135건 완주
   - 완료 후: 정리큐 첫 리뷰, mirror·graph 상태 확인, archive 백필 실행
4. 이후 10만 건 유입 시 동일 파이프 (워커 상시화는 launchd plist — 별도 문서)
```

## C3. 테스트

```
test_queue_fail:      단계 실패 mock → k2_done_at 없음·fail_count 증가·대기 재등장,
                      3회 실패 → failed_perm, 재시도 초기화 동작
test_resume:          extract_at 존재 시 stage_extract 미호출 (mock call count)
test_map_reduce:      10청크 문서 → 그룹핑 수·keyword 병합·dedup, 그룹 1개 실패 시 부분 진행
test_eligibility:     status/confidence/k2_done_at 조합 매트릭스 (8케이스)
test_curation:        demote→sync_one으로 mirror md 삭제, restore로 재생성, log 기록
test_candidates:      규칙 5종 양성·음성 fixture
test_worker:          stop 파일·SIGINT 정지, state.json 갱신 (subprocess 통합테스트)
test_backfill:        멱등성 (2회 실행 시 스킵), 소실 path 리포트
```

## C4. 수용 기준 (V2.9 출시 판정)

1. 실패 문서가 done으로 집계되는 경우 0 (강제 실패 주입 테스트).
2. 26페이지 문서의 summarize 입력에 후반부 청크 유래 keyword 포함 (BOM PDF 실검증).
3. 워커 SIGINT 후 좀비 락 0, 재기동 시 이어서 처리.
4. demote 클릭 → 다음 graph 조회에서 해당 노드 부재 (mirror md 삭제 확인).
5. quarantine 문서가 open-webui RAG 검색에는 나옴 (검색층 보존 확인).
6. 1,135건 완주 후: failed_perm 목록과 사유가 UI에서 전부 확인 가능.

## C5. 리스크와 완화

| 리스크 | 완화 |
|---|---|
| 워커·UI 동시 처리 경합 | 기존 `set_processing` 락이 이미 방지 (`queue.py:125-151`). UI 배치를 10건 이하로 제한해 충돌 표면 축소 |
| SQLite 동시 쓰기 잠금 | 워커·UI 모두 `busy_timeout=5000` 유지, 워커 트랜잭션은 문서 단위로 짧게. 필요 시 WAL 모드 활성화 (`PRAGMA journal_mode=WAL` — migration 007에 포함) |
| confidence 임계값 오설정 → 과잉 격리 | 게이트는 quarantine(가역)이지 rejected가 아님. 히스토그램 보고 조정 + restore 일괄 가능 |
| Map 호출 수 증가로 Ollama 과부하 | MAX_EXTRACT_CALLS=8 상한 + 워커 단일 프로세스 순차 처리 (병렬은 V3 검토) |
| 백필 디스크 부족 | dry-run이 용량 합계 선보고, 500MB 초과 심링크 정책 |
| done 기준 변경으로 기존 통계 단절 | 007 백필로 27건 이관, flow 탭 지표는 신 기준으로 일괄 전환 (혼용 표기 금지) |

## 부록 A — 변경 파일 총괄

| 파일 | 변경 |
|---|---|
| `src/ingest/migrations/007_fail_tracking.sql` (+down) | 신규 — A1 |
| `src/ingest/migrations/008_curation.sql` (+down) | 신규 — B1 |
| `src/queue.py` | 실패 모델·재개·상태 확장·게이트 훅 (A1·A3·B4) |
| `src/k2_pipeline.py` | Map-Reduce·fast extract (A2·A7) |
| `src/eligibility.py` | 신규 — eligible 단일 정의 (A8·B3) |
| `src/curation.py` | 신규 — 전이 API·후보 탐지 (B2·B5) |
| `src/obsidian_sync.py` | `_is_eligible` → eligibility 참조로 교체 |
| `src/flow.py` | 지표 신 기준 (done/eligible/quarantine 분리) |
| `src/tabs/flow.py` | 워커 카드·실패 목록·배치 10건 제한 |
| `src/tabs/curation.py` | 신규 — 정리 큐 탭 |
| `scripts/k2_worker.py` | 신규 — 워커 (A4) |
| `scripts/archive_backfill.py` | 신규 — 원본 백필 (A6) |
| `src/llm.py` | `format_json` 인자 + think 태그 스트립 (A7) |
| `app.py` | 정리 큐 탭 등록 |

## 부록 B — 상태·계층 관계도

```
                      [검색층]  documents + chunks + FTS  ← 삭제 없음 (rejected 포함)
                          │
              eligible_sql() 통과?  ──  status=active
              (k2_done_at ∧ industry/area ∧ confidence≥θ)
                          │ yes
                      [전시층]  mirror(.md) → Obsidian graph / Quartz wiki 뷰
                          │
        demote(사람/입구게이트) ↓        ↑ restore(사람)
                     quarantine ─(사람 확정)→ rejected
```
