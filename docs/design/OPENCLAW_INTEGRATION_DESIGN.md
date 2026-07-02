# OpenClaw 연동 개선 설계서 — 접속 마찰 제거 + 대화 연속성 복구

- 작성일: 2026-07-02 · **Part A·B 구현 완료 (2026-07-02, 같은 날)**
- 대상: `src/tabs/external.py` (render_openclaw), `~/.openclaw/openclaw.json`,
  (옵션) 신규 `src/tabs/claw_chat.py`
- **구현 후 정정 (실측 근거)**: 아래 A1·B1·B3는 최초 작성 시 추정값이었으나,
  컨테이너에 번들된 OpenClaw 2026.5.6 공식 문서(`/app/node_modules/openclaw/docs/`)를
  대조해 실측·정정한 뒤 적용했다. 정정 사항은 §A1'·§B1'·§B3'에 명시.
- 실측 근거 (2026-07-02):
  - 컨테이너 `iris-claw` :18789, Up 3 days (healthy)
  - Control UI `X-Frame-Options: DENY` → iframe 불가, 접속 시 토큰 수동 입력 요구
  - `~/.openclaw/agents/main/sessions/`에 `.reset.2026-06-11`, `.reset.2026-06-12` 리셋 파일 다수
    — 세션 저장은 정상이나 **컨텍스트 초과 시 리셋**이 반복돼 온 물증
  - `openclaw.json`: `models.providers.ollama.models = []` (contextWindow 미선언),
    `agents.defaults.memorySearch.enabled = false`, `compaction.mode = "safeguard"`,
    primary `ollama/qwen3:30b`
  - Ollama 설치 모델: qwen3:30b, qwen3-next:80b, **bge-m3**(임베딩 — memorySearch 전제 충족)

---

## 0. 요약

| # | 문제 | 원인 | 처방 |
|---|---|---|---|
| A | 창 열 때마다 토큰 붙여넣기 | Control UI 토큰 인증 + hub 링크가 토큰 미포함 | hub가 `openclaw.json`에서 토큰을 읽어 **tokenized URL** 링크 생성 |
| B | 대화 연속성 없음 (모델 바꿔도 동일) | ① contextWindow 미선언 + Ollama 기본 num_ctx(4~8k)로 동작 ② memorySearch off ③ compaction=safeguard(잘라내기) | ① 모델별 contextWindow 32k 선언(+Ollama 측 num_ctx) ② memorySearch on (bge-m3) ③ compaction 요약형 전환 |
| C | (구조 옵션) iframe 불가 + 세션 정책 종속 | Control UI 정책 | hub 내장 채팅 패널 — gateway의 OpenAI 호환 API 사용, 이력은 hub DB 관리 |

A·B는 30분~반나절 거리의 즉효 수정, C는 선택 확장(써보고 판단).
역할 분담 원칙: **지식 질의는 hub 내장 채팅(C), 에이전트 작업(스킬·툴)은 Control UI 새 창(A).**

---

## Part A — 접속 마찰 제거 (tokenized URL)

### A1. 변경 내용 — `external.py`

```python
# 신규 헬퍼
_OPENCLAW_CONFIG = Path.home() / ".openclaw" / "openclaw.json"

def _openclaw_token() -> str | None:
    """gateway.auth.token 읽기. 실패 시 None (현행 동작 폴백)."""
    try:
        cfg = json.loads(_OPENCLAW_CONFIG.read_text(encoding="utf-8"))
        return cfg.get("gateway", {}).get("auth", {}).get("token") or None
    except Exception:
        return None

def render_openclaw() -> None:
    token = _openclaw_token()
    base = "http://127.0.0.1:18789"
    # 채팅 직행 + 세션 고정 (연속성 — 항상 main 세션으로)
    url = f"{base}/chat?session=main" + (f"&token={token}" if token else "")
    _iframe_or_help(url=url, host="127.0.0.1", port=18789,
                    name="L1-chat-claw (OpenClaw)")
    if token:
        st.caption("🔑 토큰 자동 포함 링크 — 붙여넣기 불필요.")
    else:
        st.caption("⚠️ ~/.openclaw/openclaw.json에서 토큰을 읽지 못함 — 수동 입력 필요.")
```

### A1'. 정정 및 실제 구현 (2026-07-02) — ✅ 완료

번들 문서(`docs/cli/dashboard.md`, `docs/web/dashboard.md`) 확인 결과 **토큰은 쿼리
파라미터가 아니라 URL 프래그먼트(`#token=`)로 전달**하는 것이 공식 방식이었다.
근거: `dashboard` 명령 설명 — *"passes the token via the URL fragment"*, 그리고
*"`token` should be passed via the URL fragment (`#token=...`) whenever possible.
Fragments are not sent to the server, which avoids request-log and Referer
leakage. Legacy `?token=` query params are still imported once for
compatibility, but only as a fallback."* Control UI는 로드 후 토큰을
sessionStorage로 옮기고 URL에서 제거한다.

실제 적용한 코드 (`src/tabs/external.py`):

```python
_OPENCLAW_CONFIG = Path.home() / ".openclaw" / "openclaw.json"

def _openclaw_token() -> str | None:
    try:
        cfg = json.loads(_OPENCLAW_CONFIG.read_text(encoding="utf-8"))
        return cfg.get("gateway", {}).get("auth", {}).get("token") or None
    except Exception:
        return None

def render_openclaw() -> None:
    alive = _port_alive("127.0.0.1", 18789)
    if alive:
        token = _openclaw_token()
        base = "http://127.0.0.1:18789/chat?session=main"
        url = f"{base}#token={quote(token)}" if token else base   # 127.0.0.1 한정
        _iframe_or_help(url=url, host="127.0.0.1", port=18789, name="L1-chat-claw (OpenClaw)")
        ...
```

검증: `urlopen`으로 프래그먼트 포함 URL에 HEAD 요청 시 정상 200 + `X-Frame-Options: DENY`
헤더 수신 확인 (프래그먼트는 HTTP 요청에 실리지 않으므로 iframe 차단 감지 로직에 영향 없음).
`~/.openclaw/openclaw.json`에서 토큰(64자) 읽기 성공 확인.
개발본(`/Users/iris/0Dev/iris-hub`) 수정 후 `iris-local/bin/sync-iris-hub.sh`로 배포본
(`/Users/iris/iris-local/iris-hub` — 실제 실행 중인 :8765 앱)에 반영, Streamlit 파일 워처로
자동 리로드 확인 (HTTP 200 유지).

### A3. 보안 제약

- 토큰 포함 링크는 **127.0.0.1 한정** — `base`가 localhost 계열이 아니면 토큰을 붙이지 않는다 (가드 코드).
- 토큰을 st.write·로그·caption에 출력 금지 (URL 내부에만 존재).
- `openclaw.json` 읽기는 read-only. 파싱 실패 시 조용히 현행 동작(수동 입력 안내)으로 폴백.
- iframe 우회(리버스 프록시로 X-Frame-Options 제거)는 **채택하지 않음** — Control UI의 WebSocket·
  origin 검증과 충돌 위험 대비 이득 없음. 새 창 패턴 유지.

---

## Part B — 대화 연속성 복구 (openclaw.json 튜닝)

### B1. 컨텍스트 윈도우 선언 — 연속성 문제의 주범

**진단**: `models.providers.ollama.models = []` 라 OpenClaw가 모델의 컨텍스트 크기를 모르고,
Ollama는 호출측이 `num_ctx`를 명시하지 않으면 기본 4~8k로 동작하는 것이 일반적이다.
→ 몇 턴 만에 앞 대화가 잘리고, 한도 초과 시 safeguard가 리셋 — `.reset.` 파일들의 원인.
**모델을 바꿔도 같은 경로(ollama provider 기본값)를 타므로 증상이 동일**했다.

**수정 (openclaw.json):**

```json
"models": {
  "providers": {
    "ollama": {
      "baseUrl": "http://host.docker.internal:11434",
      "models": [
        { "id": "qwen3:30b",                          "contextWindow": 32768 },
        { "id": "qwen3-next:80b-a3b-instruct-q4_K_M", "contextWindow": 32768 }
      ]
    }
  }
}
```

### B1'. 정정 및 실제 구현 (2026-07-02) — ✅ 완료

번들 문서(`docs/providers/ollama.md` "Context windows" 항목) 확인 결과:

> *"Native Ollama requests leave `options.num_ctx` unset unless you explicitly
> configure `params.num_ctx`, so Ollama can apply its own model,
> `OLLAMA_CONTEXT_LENGTH`, or VRAM-based default."*

즉 진단(models=[] → Ollama 기본 num_ctx로 동작)이 정확했다. 다만 실제 적용 중
**provider 레벨 `contextWindow`만으로는 부족**했다 — `models list` CLI로 실측한 결과
provider-level만 설정했을 때 OpenClaw가 `/api/show` 자동탐지로 모델이 광고하는 이론상
컨텍스트(195k)를 그대로 표시했다. **모델 항목마다 `contextWindow`를 명시해야 override가
적용**된다 (문서에 없던 실측 사실 — 이 설계서에 새로 기록).

최종 적용 (`~/.openclaw/openclaw.json`, 백업: `openclaw.json.bak.2026-07-02`):

```json
"models": {
  "providers": {
    "ollama": {
      "baseUrl": "http://host.docker.internal:11434",
      "apiKey": "ollama-local",
      "contextWindow": 32768,
      "maxTokens": 8192,
      "models": [
        { "id": "qwen3:30b", "name": "qwen3:30b",
          "contextWindow": 32768, "maxTokens": 8192, "params": { "num_ctx": 32768 } },
        { "id": "qwen3.5:4b", "name": "qwen3.5:4b",
          "contextWindow": 32768, "maxTokens": 8192, "params": { "num_ctx": 32768 } },
        { "id": "qwen3-next:80b-a3b-instruct-q4_K_M", "name": "qwen3-next:80b-a3b-instruct-q4_K_M",
          "contextWindow": 32768, "maxTokens": 8192, "params": { "num_ctx": 32768 } },
        { "id": "bge-m3", "name": "bge-m3" }
      ]
    }
  }
}
```

`"name"` 필드는 스키마 필수(생략 시 gateway가 crash-loop, `models.providers.ollama.models.N.name:
Invalid input: expected string, received undefined`로 즉시 실패 — 재시작 로그로 확인 후 추가).

**검증 결과** (`docker exec iris-claw /app/node_modules/.bin/openclaw models list --provider ollama`):

```
Model                          Input   Ctx    Local Auth  Tags
ollama/qwen3:30b                text   32k    no    yes   default,configured
ollama/qwen3.5:4b               text   32k    no    yes   configured
ollama/qwen3-coder:30b          text   195k   no    yes   configured   ← 미설치·미사용 모델, 손대지 않음
```

주 모델(primary) qwen3:30b와 보조 fast 모델 qwen3.5:4b 모두 32k로 확정 반영됨.
컨테이너 재시작 후 `docker inspect --format '{{.State.Health.Status}}'` → `healthy` 확인,
기동 로그에 config 에러 없음, 기존 webchat 세션 재연결 정상.

- 메모리 참고: qwen3:30b(MoE a3b) 32k 컨텍스트의 실제 메모리 부담은 `ollama ps`로 후속 관찰
  필요 (이번 세션에서는 미실측 — 압박 시 24576으로 하향).

### B2. memorySearch 활성화 — 밀려난 대화의 회수 — ✅ 완료

번들 문서(`docs/concepts/memory-search.md`, `docs/reference/memory-config.md`)로
정확한 키 구조 확인 후 적용. `provider: "ollama"`는 기존 `models.providers.ollama`
항목(baseUrl 등)을 그대로 재사용한다 (별도 커스텀 provider id 불필요 — 이미 같은
Ollama 데몬을 가리키고 있으므로).

```json
"agents": {
  "defaults": {
    "memorySearch": {
      "enabled": true,
      "provider": "ollama",
      "model": "bge-m3",
      "experimental": { "sessionMemory": true },
      "sources": ["memory", "sessions"]
    }
  }
}
```

- `experimental.sessionMemory: true` + `sources: ["memory","sessions"]` — 메모리 파일뿐
  아니라 **세션 트랜스크립트 자체를 색인**해 `memory_search`로 과거 대화를 회수 (문서:
  "Session memory search (experimental)" 절, opt-in 기능).
- **검증 결과** (`docker exec iris-claw ... openclaw memory status`):
  ```
  Memory Search (main)
  Provider: ollama (requested: ollama)
  Model: bge-m3
  Sources: memory, sessions
  Indexed: 0/12 files · 0 chunks   ← 재시작 직후, 다음 대화부터 색인 시작 (정상)
  FTS: ready
  ```
  provider·model이 설정대로 인식됨, 색인 대상 12개 파일(memory 2 + sessions 10) 포착 확인.
  실제 색인 완료(`Indexed: N/N`)는 앞으로 사용하면서 누적 확인 필요 — **구현 시 검증
  잔여 항목**으로 남김 (`openclaw memory index --force`로 강제 색인 가능).

### B3'. compaction — 정정: mode는 유지, 가시성만 추가 — ✅ 완료

**정정**: 최초 진단에서 `compaction.mode: "safeguard"`를 "요약 없이 잘라내기(안전 우선)"로
추정했으나, 이는 **오독**이었다. 번들 문서(`docs/gateway/config-agents.md`) 확인 결과:

> *"`mode`: `default` or `safeguard` (chunked summarization for long histories)."*

즉 **safeguard는 오히려 긴 히스토리용 청크 단위 요약 + `qualityGuard`(요약 실패 시 재시도)가
기본 활성화되는 더 견고한 모드**다 — 로컬 모델(qwen3:30b)처럼 요약 품질이 들쭉날쭉할 수 있는
환경에 오히려 적합하다. 따라서 **mode를 바꾸지 않고 그대로 `safeguard` 유지**, 대신
가시성 부재(사용자가 compaction이 언제 일어나는지 전혀 알 수 없었던 점)만 해소한다.

```json
"compaction": {
  "mode": "safeguard",
  "notifyUser": true
}
```

- `notifyUser: true` — compaction 시작/완료 시 채팅에 짧은 알림 표시 (기본은 무음).
  이제 "대화가 갑자기 예전 걸 까먹는" 순간이 **눈에 보이는 이벤트**가 된다 —
  실제 원인(B1의 컨텍스트 예산 문제)과 증상을 사용자가 직접 연결 지을 수 있게 됨.
- `keepRecentTokens`·`reserveTokensFloor` 등 세부 튜닝은 이번 라운드에서 보류 —
  B1(contextWindow 32k) 반영 후 실사용 관찰이 우선이며, 기본값(`reserveTokensFloor`
  20000)으로도 32k 예산에서 동작 가능.

### B4. 적용 절차 (실행 완료 로그)

```
1. cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak.2026-07-02   ✅ 완료
2. B1'·B2·B3' 반영 (수동 JSON 편집)                                        ✅ 완료
3. python3 -c "json.load(...)" 로 JSON 유효성 확인                          ✅ 완료
4. docker restart iris-claw                                                ✅ 완료 (1차: models[].name 누락으로
   크래시루프 → 로그로 원인 확인 → name 필드 추가 → 재시작 → healthy)
5. models list / memory status CLI로 검증                                  ✅ 완료 (§B1'·§B2)
6. B5 시나리오 1~4는 실사용 중 확인 필요 (자동화된 실측 불가 — 아래 명시)
```

### B5. 검증 프로토콜 (수용 기준) — 실사용 확인 대기 (⏳)

코드·설정 레벨 검증(§A1'·§B1'·§B2·B4)은 이번 세션에서 완료했으나, 아래 시나리오는
**실제 대화를 통해서만** 확인 가능하므로 사용하면서 점검 필요:

| # | 시나리오 | 기대 |
|---|---|---|
| 1 | 20턴 이상 잡담+정보 섞인 대화 후 1턴째 내용 질문 | 정확 회상 (컨텍스트 내 유지) |
| 2 | 창 닫고 재접속 (tokenized URL) → 직전 대화 이어 질문 | `session=main` 이어짐, 토큰 입력 없음 |
| 3 | 대화를 의도적으로 매우 길게 (컨텍스트 초과 유도) | 리셋 파일 미생성, 요약 compaction 후 계속. 초반 핵심 사실 질문에 요약/메모리 경유 응답 |
| 4 | `docker restart iris-claw` 후 재접속 | 세션 이력 보존 (디스크 세션 확인됨 — 회귀 확인용) |
| 5 | `ollama ps` / 게이트웨이 로그 | n_ctx=32768 적용 확인, 메모리 사용량 기록 |

---

## Part C — (옵션) hub 내장 채팅 패널 `src/tabs/claw_chat.py`

> A·B 적용 후 2주 사용해보고 여전히 "hub 안에서 대화"가 필요하면 착수. 선판단 금지.

### C1. 원리

`openclaw.json`에 `gateway.http.endpoints.chatCompletions`가 활성 — 게이트웨이가
**OpenAI 호환 API**를 제공한다. hub가 이 API의 클라이언트가 되면:
- iframe 문제 원천 소멸 (Streamlit 네이티브 UI)
- 대화 이력을 **hub DB가 소유** — OpenClaw 세션·compaction 정책과 무관한 연속성
- 대화 → 지식볼트 ingest(chat 채널) 연결이 자연스러움

### C2. 데이터 모델 (hub `_index.db`)

```sql
CREATE TABLE chat_sessions (
  session_id TEXT PRIMARY KEY,          -- "cs_YYYYMMDD_HHMMSS"
  title      TEXT,                      -- 첫 질문 앞 40자
  created_at TEXT, updated_at TEXT
);
CREATE TABLE chat_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL REFERENCES chat_sessions(session_id),
  role TEXT NOT NULL,                   -- user | assistant
  content TEXT NOT NULL,
  model TEXT, created_at TEXT
);
```

### C3. 호출·컨텍스트 정책

```python
POST http://127.0.0.1:18789/v1/chat/completions
Authorization: Bearer {gateway.auth.token}     # _openclaw_token() 재사용
body: { "model": "ollama/qwen3:30b-32k", "stream": true,
        "messages": [system] + 최근 턴 }
```

- 전송 컨텍스트: **최근 12턴 전문 + 그 이전은 세션 요약 1블록** (요약은 12턴 초과 시점에
  fast 모델로 생성해 chat_sessions에 캐시). 단순·예측 가능한 자체 정책 — OpenClaw compaction 비의존.
- 스트리밍: SSE → `st.write_stream` (체감 반응성).
- 엔드포인트 경로·인증 헤더 형식은 **구현 시 실측** (버전에 따라 `/v1/...` prefix 상이 가능).

### C4. UI

```
💬 Claw 채팅 (신규 탭 또는 OpenClaw 탭 내 서브탭)
├─ 좌: 세션 목록 (최근순, 새 세션 버튼)
├─ 본문: st.chat_message 스레드 + st.chat_input
├─ 헤더: 모델 선택 (ollama 설치 목록) · [Control UI 새 창] (에이전트 작업용 동선 유지)
└─ 메시지 액션: [🗄 지식볼트로] — 이 대화를 md로 만들어 1-inbox/external에 저장
     → 기존 external 채널 파이프라인(K2 → chat 채널 trust=auto)에 합류. 수동 복붙 제거
```

### C5. C의 비목표

- OpenClaw 스킬/툴 실행 UI 재구현 — Control UI 담당 (새 창).
- 멀티유저·권한 — 로컬 단일 사용자 전제.

---

## Part D — 구현 순서·리스크

### D0. 배포 구조 (구현 중 확인된 사실 — 향후 작업 시 필수 숙지)

`/Users/iris/0Dev/iris-hub`는 **개발본**, 실제 :8765에서 실행 중인 것은
`/Users/iris/iris-local/iris-hub` (**배포본**)이다. 둘은 git 관계가 아니라
`iris-local/bin/sync-iris-hub.sh`의 `rsync -a --delete`로 동기화된다.
**개발본만 수정하고 이 스크립트를 안 돌리면 hub 화면에 반영되지 않는다** —
이번 Part A 구현 중 실제로 이 문제로 한 차례 확인 단계가 필요했다. 앞으로 hub
코드를 수정할 때는 반드시 `bash ~/iris-local/bin/sync-iris-hub.sh` 실행 후
Streamlit 파일 워처의 자동 리로드(또는 HTTP 200 재확인)로 반영을 확인할 것.

### D1. 순서

| 단계 | 내용 | 규모 | 상태 |
|---|---|---|---|
| D-1 | Part A: tokenized URL (external.py) + 배포본 sync | 1시간 | ✅ 완료 (2026-07-02) |
| D-2 | Part B: openclaw.json 튜닝(contextWindow·memorySearch·notifyUser) + 재시작 + CLI 검증 | 반나절 | ✅ 완료 (2026-07-02) |
| D-2' | B5 실사용 시나리오 1~4 확인 | — | ⏳ 대기 (실사용 필요) |
| D-3 | 2주 사용 관찰 → C 착수 여부 결정 | — | ⏳ 대기 |
| D-4 | (조건부) Part C: PR-C1 데이터모델+API 클라이언트 / PR-C2 UI / PR-C3 볼트 저장 연계 | 2~3일 | 보류 |

### D2. 리스크

| 리스크 | 완화 |
|---|---|
| OpenClaw 버전별 config 키 상이 (memorySearch·models 스키마) | B2 명시대로 schema 실측 후 기입. 백업본으로 즉시 롤백 가능 |
| 32k 컨텍스트로 Mac 메모리 압박 | `ollama ps` 실측 → 24k 하향 옵션. 80b 모델은 32k 미적용(30b 우선) |
| 토큰 파라미터 형식 오추정 | ✅ 해소 — 번들 문서로 실측, `#token=` 프래그먼트 확인·적용 |
| chatCompletions 경유 시 스킬 미작동 | C의 역할 분담 명시 (지식 질의 전용). 스킬 필요 작업은 Control UI |
| compaction 요약이 로컬 모델에서 부정확 | ✅ 해소 — safeguard가 이미 qualityGuard(재시도) 내장 모드임을 확인, mode 변경 없이 notifyUser만 추가 |
| provider-level contextWindow만으로 미반영 | ✅ 해소 — 모델별 `models[].contextWindow` 명시 필요함을 실측으로 발견·반영 |
| `models[].name` 필드 누락 시 gateway crash-loop | ✅ 해소 — 스키마 필수 필드로 확인, 전 모델 항목에 `name` 추가 |

### D3. 최종 수용 기준

1. hub에서 클릭 1회로 인증된 Control UI 채팅 진입 (토큰 붙여넣기 0회).
2. B5 시나리오 1~4 통과 — 특히 "20턴 후 1턴째 회상"과 "재접속 후 이어짐".
3. (C 착수 시) hub 채팅에서 세션 재선택 시 이력 완전 복원 + 대화 1클릭 볼트 저장.
