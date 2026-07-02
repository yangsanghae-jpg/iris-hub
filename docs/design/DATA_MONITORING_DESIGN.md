# 데이터 모니터링 탭 상세 설계 — 볼트 계기판 + 큐레이션

- 작성일: 2026-07-03
- 지위: REFREEZE의 "데이터=모니터링" 탭 상세. 흐름(처리 액션)과 분리된 **관측 전용** 화면.
  K2_BATCH_CURATION(큐레이션)·STORE_SCHEMA(집계 함수)를 UI로 표면화.
- 원칙: **"흐름은 돌리는 곳, 데이터는 보는 곳."** 실행 버튼 없음(흐름에), 관측·큐레이션 리뷰만.

---

## 0. 이 탭이 흡수하는 것 (REFREEZE)

| 흡수원 | 내용 |
|---|---|
| 흐름 탭의 모니터링 | 대기/처리중/완료 카드, K2 단계별 진척 |
| 인사이트 탭 (폐기) | Grafana/Prometheus/Loki 관측 링크 |
| 큐레이션 (신규) | 강등 후보 리뷰 (K2_BATCH §B) |
| 데이터 탭 기존 | 산업·채널 분포 |

**단일 화면 = "볼트가 지금 어떤 상태인가"의 진실원.**

---

## 1. UX 스펙 (확정 목업 기준 2026-07-03)

목업을 확정 스펙으로 고정. 구현은 이 레이아웃·컴포넌트·데이터바인딩을 그대로 따른다.

### 1.1 레이아웃

```
┌ KPI 4카드 ──────────────────────────────────────────────────────────┐
│ 문서 1,304  개념 96  전시active 1,180(녹)  격리quarantine 124(앰버)   │
├──────────────────────────────┬───────────────────────────────────────┤
│ K2 파이프라인 진척            │ 처리 큐                               │
│ extract   ████████ 1304/1304 │ 대기14 처리중0 완료1180 실패6(앰버)   │
│ classify  ████████ 1290/1304 │                                       │
│ summarize ███████░ 1180/1304 │                                       │
├──────────────────────────────┴───────────────────────────────────────┤
│ 큐레이션 · 강등 후보 [주 1회 검토] ················· 18건            │
│ ┌ GPT 대화 저장—잡담 섞임  [신뢰0.31][고아]      [강등][유지] ┐      │
│ │ 웹검색 클리핑 2025.06     [stale][web]         [강등][유지] │      │
│ │ mes_생산실행 (중복후보)   [중복][본문짧음]     [강등][유지] │      │
├──────────────────────────────┬───────────────────────────────────────┤
│ 산업 분포                     │ 관측 백엔드                           │
│ ▓B35 ▓C26 ▓D15 ▓H12 ░기타     │ ● Grafana:3030  ● Prometheus:9090     │
│ 채널: doc71 chat22 web7        │ ○ Loki:3100          (외부 링크)      │
└──────────────────────────────┴───────────────────────────────────────┘
```

### 1.2 컴포넌트 스펙

| 영역 | 컴포넌트 | 데이터 바인딩(store) | 규칙 |
|---|---|---|---|
| KPI | 문서·개념·active·quarantine (4 metric 카드) | `vault.counts()`·`knowledge.count()` | active=녹, quarantine=앰버, round |
| 진척 | extract/classify/summarize 3 막대 | `document_meta` 단계 timestamp 집계 | %+분수, summarize<100%면 accent |
| 큐 | 대기/처리중/완료/실패 (4 미니) | `vault.queue_snapshot()` (K2_BATCH) | 실패>0면 border-warning |
| 큐레이션 | 후보 행: 제목+규칙뱃지+[강등][유지] | `curate.find_candidates()` | 규칙 5종 뱃지, 클릭=demote/keep+log |
| 분포 | 산업 stacked bar + 채널 캡션 | `vault.doc_distribution()` | active만 집계 |
| 관측 | Grafana/Prometheus/Loki 상태점+링크 | port alive 점검 | 인사이트 탭 흡수, 링크만 |

### 1.3 큐레이션 규칙 뱃지 (K2_BATCH §B5)
- `신뢰도 N` (confidence<임계) · `고아`(concepts 0) · `본문짧음`(weak) · `중복`(dup) · `stale`(web 1년경과).
- 뱃지 색: 경고성(신뢰도·중복)=앰버, 중립(고아·stale·web)=회색.

### 1.4 상태 전이
- [강등] → `curate.demote(doc_id, reason=규칙)` → status=quarantine → 다음 렌더에서 후보 목록·전시층에서 제거.
- [유지] → 스누즈 30일(meta_kv) → 후보 재등장 억제.
- KPI·분포는 status='active'만 집계 → 강등 즉시 반영.
- **실행 버튼(배치 처리) 없음** — 그건 흐름 탭. 여기는 관측+큐레이션 리뷰만.

---

## 2. 흐름 탭과의 분리 (REFREEZE 지시 2)

| | 흐름 (처리) | 데이터 (모니터링) |
|---|---|---|
| 성격 | 명령 (실행) | 관측 (관찰) |
| 요소 | 배치/개별/선택 처리, K2 on/off, 동기화, 안전망 버튼 | KPI·진척·큐·큐레이션·분포·관측링크 |
| 원칙 | 얇은 실행 콘솔 | 볼트 현황 단일 화면 |

흐름의 모니터링 카드(대기/완료/진척)가 데이터로 이관됨 → 흐름은 "돌리고 나면 여기서 본다".

---

## 3. 데이터 바인딩 요약 (store DAL — S1)

```python
# vault.py
counts() -> {documents, chunks, active, quarantine}
queue_snapshot() -> {waiting, in_progress, done, failed}
stage_progress() -> {extract, classify, summarize}   # (완료수, 전체수)
doc_distribution() -> {industry: [...], channel: [...]}   # active만
# knowledge.py
count() -> concepts 수
# curate.py (engine)
find_candidates() -> [{doc_id, title, rules[], reason}]
demote(doc_id, reason) / keep(doc_id, snooze_days=30)
```

- 탭은 위 함수만 호출. SQL은 store/engine 안에만.

---

## 4. 착수 체크리스트

```
[ ] tabs/data.py — KPI·진척·큐·큐레이션·분포·관측 (목업 1.1 그대로)
[ ] store.vault 집계 함수 (counts/queue_snapshot/stage_progress/distribution)
[ ] engine.curate.find_candidates/demote/keep (K2_BATCH §B)
[ ] 흐름 탭에서 모니터링 카드 제거 (액션만 남김)
[ ] 관측 링크 (인사이트 탭 폐기, 여기로)
[ ] 테스트: test_curate_candidates, test_demote_reflects_kpi
```

## 5. 선행 의존
- **S1(store)·S7(큐레이션)** 필요. K2_BATCH_CURATION 설계의 status/confidence 게이트가 전제.
- 분포·진척은 S1만으로 가능(선행). 큐레이션 섹션은 S7 후.
