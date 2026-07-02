# OpenWebUI/L2-Gateway 보완 설계서 — 모델 정합성·응답 일관성·검색 선택·자동 반입

- 작성일: 2026-07-02
- 대상 (cross-repo):
  - `iris-stack/l2-gateway/app/main.py` (검색·일관성·자동반입 핵심 로직)
  - `iris-stack/docker-compose.yml` (OpenWebUI 모델 목록 설정)
  - `iris-hub/src/tabs/external_capture.py`, `iris-hub/src/tabs/intake.py` (중복 해소 + 자동 반입 연동)
- 전제: 사전 점검(2026-07-02) 결과 4개 요구사항 모두 코드 근거로 확인됨. 이 문서는 그 점검에서
  드러난 갭을 메우는 설계다. 점검 요약은 §0에 재수록.
- 저장 위치: 구현 대상 코드는 cross-repo(`iris-stack`·`iris-hub`)이나, 문서 자체는 iris-hub 설계서
  관리 컨벤션에 따라 `iris-hub/docs/design/`에 둔다 (2026-07-02 `iris-stack/docs/`에서 이관).
- **관련 기존 설계서**: `iris-hub/docs/design/K2_BATCH_CURATION_DESIGN.md`(V2.9 — eligible/quarantine 게이트),
  `iris-system/knowledge/IRIS_INGEST_NORMALIZATION_RULES.md`(채널별 trust 원칙). 본 설계는 이 둘의
  기존 장치를 최대한 재사용한다 — 새 큐·새 게이트를 만들지 않는다.

---

## 0. 점검 결과 재요약 (설계의 출발점)

| # | 요구사항 | 현재 상태 |
|---|---|---|
| 1 | 실제 모델만 노출 | API(`/v1/models`)는 정확 / `docker-compose.yml`의 `DEFAULT_PINNED_MODELS`가 하드코딩·미검증 |
| 2 | 모델 무관 일관성 | 공통 스타일 프롬프트·think 분리는 있음 / Qwen3 이름 매칭 특수처리로 모델군별 비대칭 존재 |
| 3 | 검색 병행(기본/선택) | 키워드 자동 트리거만 존재 / 사용자 선택식 없음(요청 스키마에 필드 자체 없음) |
| 4 | 대화→입력/흐름 반영 | 수동 붙여넣기 파이프라인(`openwebui-chat` 소스)은 있음 / 자동·전달버튼 없음, 탭 2개 중복 |

---

## Part A — 모델 목록 정합성

### A1. 즉시 교정 (지금 설치 기준)

`docker-compose.yml`의 하드코딩 값을 실제 설치 목록에 맞춘다. 단, 이 값은 **모델을 새로 받을 때마다
다시 깨진다** — 이번 세션에서만도 qwen3-next:80b, (다운로드 중인) gpt-oss:120b·qwen3-coder-next 등
목록이 계속 바뀌었다. 그래서 A2(자동화)가 핵심이고 A1은 임시 조치다.

### A2. 재발 방지 — 시작 시 자동 갱신 스크립트

**`iris-stack/scripts/refresh_model_pins.sh`** (신규):

```bash
#!/bin/bash
# Ollama 실제 설치 목록으로 OPEN_WEBUI_DEFAULT_PINNED_MODELS(.env)를 갱신.
# docker compose up 전에 실행 (또는 open-webui 재시작 전).
set -euo pipefail

OLLAMA_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
EMBED_PATTERN="bge-m3|nomic-embed|embed"

# chat 가능 모델만 추출 (임베딩 전용 제외), primary 후보를 맨 앞에
TAGS=$(curl -s "${OLLAMA_URL}/api/tags" | python3 -c "
import json, sys, re
data = json.load(sys.stdin)
names = [m['name'] for m in data.get('models', [])
         if not re.search(r'${EMBED_PATTERN}', m['name'], re.I)]
print(','.join(names))
")

ENV_FILE="$(dirname "$0")/../.env"
# OPEN_WEBUI_DEFAULT_PINNED_MODELS 라인만 교체, 없으면 추가
if grep -q '^OPEN_WEBUI_DEFAULT_PINNED_MODELS=' "$ENV_FILE" 2>/dev/null; then
  sed -i.bak "s|^OPEN_WEBUI_DEFAULT_PINNED_MODELS=.*|OPEN_WEBUI_DEFAULT_PINNED_MODELS=${TAGS}|" "$ENV_FILE"
else
  echo "OPEN_WEBUI_DEFAULT_PINNED_MODELS=${TAGS}" >> "$ENV_FILE"
fi
echo "refreshed pinned models: ${TAGS}"
```

`docker-compose.yml` 수정 — 하드코딩 대신 `.env` 참조:

```yaml
environment:
  - DEFAULT_MODELS=${OPEN_WEBUI_DEFAULT_MODEL:-qwen3-next:80b-a3b-instruct-q4_K_M}
  - DEFAULT_PINNED_MODELS=${OPEN_WEBUI_DEFAULT_PINNED_MODELS}
```

운영 절차: 모델을 새로 받거나 지운 뒤에는
`bash scripts/refresh_model_pins.sh && docker compose up -d open-webui` 한 줄로 갱신.
(iris-hub의 `sync-iris-hub.sh`와 같은 "실행 스크립트로 정합성 유지" 패턴 — 새 메커니즘 도입 아님.)

### A3. 검증 항목

- `python3` 및 `curl`이 OpenWebUI 컨테이너가 아니라 **호스트(Mac)** 에서 실행되는 스크립트임을 전제
  (Ollama가 host.docker.internal 경유이므로 호스트에서 직접 `localhost:11434` 접근 가능).
- 빈 목록(Ollama 다운 상태)일 때 `.env`를 망가뜨리지 않도록 `TAGS`가 비어있으면 스크립트 중단 —
  구현 시 가드 추가 필요.

---

## Part B — 모델 크기·계열 무관 응답 일관성

### B1. 핵심 수정 — 이름 매칭을 capability 조회로 교체

현행 `_is_qwen3_model(model_name)`(main.py:1208)은 **문자열 이름 매칭**이라 Qwen3 계열에만
no-think 전처리가 적용되고, gpt-oss·gemma4·devstral 등은 완전히 다른 경로를 탄다 — 이것이
"모델 바꾸면 성향이 달라진다"의 실제 코드 레벨 원인이다.

**교체안**: 이름이 아니라 **Ollama `/api/show`의 capability 태그**(`thinking` 존재 여부)로
판단한다. 이번 세션에서 OpenClaw 모델 선정 때 이미 같은 방식(`ollama show <model>` →
`Capabilities: completion/tools/thinking`)으로 실측한 바 있다 — 검증된 접근을 재사용.

```python
# l2-gateway/app/main.py — 신규 모듈 model_capabilities.py 로 분리 권장

_CAPABILITY_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_CAPABILITY_TTL_SECONDS = 3600  # 모델 목록이 자주 안 바뀌므로 1시간 캐시

async def get_model_capabilities(model: str) -> Dict[str, Any]:
    now = time.time()
    cached = _CAPABILITY_CACHE.get(model)
    if cached and (now - cached[0]) < _CAPABILITY_TTL_SECONDS:
        return cached[1]
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{OLLAMA_BASE_URL}/api/show", json={"name": model})
            r.raise_for_status()
            data = r.json()
        caps = {c: True for c in data.get("capabilities", [])}
    except Exception:
        caps = {}  # 조회 실패 시 thinking 없다고 보수적으로 가정 (no-think 전처리 skip)
    _CAPABILITY_CACHE[model] = (now, caps)
    return caps


async def has_thinking_capability(model: str) -> bool:
    caps = await get_model_capabilities(model)
    return bool(caps.get("thinking"))
```

호출부 교체 (main.py:1428 부근):

```python
# 기존
if _is_qwen3_model(req.model):
    messages_for_ollama = _apply_no_think_prefix_to_last_user(messages_for_ollama)

# 신규
if await has_thinking_capability(req.model):
    messages_for_ollama = _apply_no_think_prefix_to_last_user(messages_for_ollama)
```

효과: 이름이 무엇이든(qwen3, gpt-oss, gemma4, 향후 새 모델) **thinking capability가 있으면
동일하게 억제, 없으면 동일하게 스킵** — 모델군에 따른 비대칭이 구조적으로 사라진다.

### B2. 구조적 일관성 보강 — 답변 계약(answer contract)

`_iris_answer_style_rules_text()`(main.py:545)는 "지침 문장"일 뿐 구조를 강제하지 않는다.
지침 준수도는 모델 능력에 비례하므로, 같은 문장이어도 작은 모델일수록 덜 지켜진다.
**후처리로 구조를 뜯어고치는 건 하지 않는다** (내용 왜곡 위험 — 기존 `sanitize_final_answer`가
이미 안전한 후처리만 하는 원칙을 따름). 대신:

1. 스타일 규칙을 더 구체적인 계약으로 보강:
   ```
   [IRIS_ANSWER_STYLE]
   - 최종 답변만 출력. 분석·계획·내부 추론 노출 금지.
   - 질문 의도에 맞게 깊이 조절. 분석/비교/설계 요청은 충분히, 단답 요청은 간결하게.
   - 사실 주장에는 근거(원문·검색결과·직접 확인)를 구분해 표현. 추측은 추측이라고 명시.
   [/IRIS_ANSWER_STYLE]
   ```
   (3번째 항목 신규 — 모델 크기와 무관하게 "확신 없는 걸 확신 있게 말하는" 격차를 줄이는 방향)
2. **관측(telemetry)만 하는 구조 점검**을 `iris_trace`(main.py:928 `build_iris_trace`)에 추가:
   응답이 규칙을 지켰는지 정규식 기반 저비용 체크(예: 첫 줄이 "Okay,"/"Let me" 등으로 시작하는지 —
   기존 `_REASON_LINE_PREFIXES_EN`에 이미 그 목록 있음)만 하고, **내용은 건드리지 않고 플래그만
   iris_trace에 기록**. 이렇게 모델별 위반율이 쌓이면 이후 실제 튜닝(프롬프트 강화 대상 모델 특정)의
   근거 데이터가 된다 — 지금 당장 강한 후처리를 넣기보다 데이터부터 쌓는 게 안전하다.

### B3. num_ctx 등 균일 강제값의 per-model 적정성 확인 (경량 보강)

`options.setdefault(...)`(main.py:1367-1371)가 선택된 모델과 무관하게 동일값을 강제하는 것은
**의도된 일관성 장치**이므로 유지한다. 다만 `num_ctx=32768`이 그 모델의 실제 advertised context보다
크면 Ollama가 무시하거나 truncate할 수 있다 — B1의 `get_model_capabilities()`가 이미 `/api/show`를
조회하므로, 같은 호출에서 `context_length`도 함께 읽어 `min(32768, model_context_length)`로
클램프하는 방어 코드를 추가한다 (작은 모델 보호, 큰 모델은 32768 그대로).

---

## Part C — 외부 검색 병행 (기본 + 선택식)

### C1. 기본(자동) 경로는 유지

`should_use_search()`(main.py:839)의 키워드 트리거 자동 감지는 그대로 둔다 — 이미 동작 중이고
요구사항의 "기본" 절반을 충족한다.

### C2. 선택식 — 메시지 마커 방식 (권장)

OpenWebUI는 유지보수 중인 업스트림 이미지(`ghcr.io/open-webui/open-webui:main`)라 프론트엔드에
커스텀 토글 버튼을 넣는 건 업데이트마다 깨질 위험이 커 배제한다. 대신 **표준 OpenAI 호환 요청의
`content` 문자열 안에 마커를 넣는 방식**으로 사용자가 명시적으로 켜고 끌 수 있게 한다.

```python
_FORCE_SEARCH_RE = re.compile(r"^\s*!search\b\s*", re.IGNORECASE)
_FORCE_NOSEARCH_RE = re.compile(r"^\s*!nosearch\b\s*", re.IGNORECASE)

def resolve_search_override(text: str) -> Tuple[str, Optional[bool]]:
    """마커 감지 → (마커 제거된 텍스트, 강제값 True/False/None[자동])."""
    if _FORCE_SEARCH_RE.match(text):
        return _FORCE_SEARCH_RE.sub("", text, count=1), True
    if _FORCE_NOSEARCH_RE.match(text):
        return _FORCE_NOSEARCH_RE.sub("", text, count=1), False
    return text, None
```

호출부(main.py:1393 대체):

```python
cleaned_content, force_search = resolve_search_override(last_user_content)
if force_search is not None:
    search_used = force_search
    last_user_content = cleaned_content  # 마커 제거된 텍스트로 이후 로직 진행
else:
    search_used = should_use_search(last_user_content, settings)
```

사용법: `!search 이 회사 최근 소식 알려줘` → 트리거 매칭 없어도 강제 검색.
`!nosearch 오늘 날씨 어때` → "오늘" 트리거가 있어도 검색 생략.

### C3. 대안(참고, 미채택) — OpenWebUI 네이티브 검색 토글

OpenWebUI 자체의 웹 검색 토글(있다면 Admin Settings에서 활성화 가능)을 켜고 검색 엔진을
"External"로 지정해 `l4-search`를 가리키게 하는 방법도 있다. 실제 UI 버튼이 생기는 장점은 있으나,
그 경로는 l2-gateway의 `filter_search_results`/`build_search_context`/저신뢰도 판정 로직을
전혀 거치지 않는다 — 검색 결과 품질 관리가 이원화된다. **C2(마커)를 1차로 채택**하고, 이 대안은
OpenWebUI의 External Search Engine 스펙을 l4-search가 그대로 만족하는지 확인된 뒤 재검토.

---

## Part D — OpenWebUI 대화 → 입력/흐름 탭 자동 반영

### D0. 탭 중복 해소 (선결 작업)

`iris-hub/src/tabs/intake.py`의 독스트링 "C 패턴: 챗 응답 저장"은 `external_capture.py`와
동일 책임을 주장하고 있다. `intake.py`에서 이 항목을 제거하고, "OpenWebUI 응답은 🌐 외부응답
탭 또는 자동 반입(D2)을 사용" 안내로 교체한다. `intake.py`는 A패턴(파일 업로드)만 담당하도록 범위를
좁힌다. (코드 삭제 없이 docstring·안내문 정리 수준 — 파이프라인 자체는 손대지 않음.)

### D1. 데이터 모델 — 세션 단위 캡처 (턴 단위 아님)

**중요한 설계 결정**: 매 turn마다 파일을 만들면 짧은 대화도 수십 개 문서로 파편화되고 K2 큐가
불필요하게 부풀어 오른다(V2.9에서 잡으려는 "희석" 문제를 자동반입이 스스로 재생산하게 됨). 대신
**OpenWebUI 세션(대화) 단위로 누적 캡처**한다.

```
doc_id 규약: chat_openwebui_{session_id}          # session_id는 OpenWebUI가 부여하는 chat id
파일 경로:   IRIS_KNOWLEDGE_EXTERNAL/openwebui-chat/{session_id}.md   (세션당 파일 1개, 갱신)
```

버퍼링·flush 정책 (l2-gateway 인메모리, 프로세스 재시작 시 유실 허용 — 유실돼도 대화 자체는
OpenWebUI DB에 남으므로 D3 백필로 복구 가능):

```python
_SESSION_BUFFER: Dict[str, Dict[str, Any]] = {}  # session_id -> {turns, last_activity, char_count}

FLUSH_IDLE_SECONDS = 300        # 5분간 새 turn 없으면 flush
FLUSH_MAX_TURNS = 40            # 또는 40턴 넘으면 flush (둘 중 먼저)
FLUSH_MAX_CHARS = 20000

def _should_flush(sess: Dict[str, Any]) -> bool:
    idle = time.time() - sess["last_activity"] >= FLUSH_IDLE_SECONDS
    return idle or len(sess["turns"]) >= FLUSH_MAX_TURNS or sess["char_count"] >= FLUSH_MAX_CHARS
```

flush 시 `external_capture.py`가 지금 수동으로 만드는 것과 **동일한 frontmatter/본문 포맷**으로
파일을 쓴다 (형식 재사용 — 새 스키마 만들지 않음):

```yaml
---
title: "OpenWebUI 대화 — {첫 사용자 turn 앞 40자}"
source: "openwebui-chat"
channel: "chat"
doc_id: "chat_openwebui_{session_id}"
ingested_at: "{flush 시각}"
trust: "auto"          # IRIS_INGEST_NORMALIZATION_RULES.md 채널별 기본값 그대로
model: "{turn 시 사용된 모델, 여러 개면 배열}"
search_used_count: N
tags: []
---

## 대화
**User**: ...
**Assistant**: ...
(turn 반복)
```

### D2. 자동 반입 — l2-gateway fire-and-forget 훅

`/v1/chat/completions` 핸들러(main.py:1352, 스트리밍·비스트리밍 양쪽 경로) 응답 생성 직후에
버퍼 적재만 하고 즉시 반환 — **flush는 별도 백그라운드 태스크**로 돌려 사용자 응답 지연을
만들지 않는다.

```python
# 응답 반환 직전 (스트리밍 경로는 SSE 종료 후, main.py의 _ollama_chat_stream_sse 내부에도 동일 적용)
_SESSION_BUFFER.setdefault(session_id, {"turns": [], "last_activity": 0, "char_count": 0, "models": set()})
sess = _SESSION_BUFFER[session_id]
sess["turns"].append({"user": last_user_content, "assistant": content, "model": req.model,
                      "search_used": search_used, "ts": time.time()})
sess["last_activity"] = time.time()
sess["char_count"] += len(last_user_content) + len(content)
sess["models"].add(req.model)

if _should_flush(sess):
    asyncio.create_task(_flush_session_to_inbox(session_id, sess))
    del _SESSION_BUFFER[session_id]
```

`session_id` 획득: OpenWebUI가 OpenAI 호환 요청에 세션을 실어 보내는 표준 필드가 없으므로,
**요청 헤더**(`X-OpenWebUI-Chat-Id` 등, OpenWebUI 버전별로 상이 — 구현 시 실제 요청 헤더 덤프로
확인 필요) 또는 없으면 **대화 내용 해시**(첫 user turn 텍스트 해시)로 대체 식별하는 폴백을 둔다.
이 부분은 **구현 시 검증 필수 항목**으로 명시(§검증 항목).

토글: `IRIS_AUTO_CAPTURE_ENABLED`(기본 true), 사용자가 특정 대화를 반입에서 빼고 싶으면
그 대화의 아무 turn에나 `!nocapture`를 포함 — 그 세션 전체를 버퍼에서 제거하고 이후 turn도 무시.

### D3. 백필 — 자동반입 이전 대화 + 프로세스 재시작 유실분 복구 (보조, 선택)

OpenWebUI REST API(`/api/v1/chats/`, 실측 결과 401 "Not authenticated" 반환 — 즉 엔드포인트는
존재하며 인증 필요. `WEBUI_AUTH=false`인데도 API 레벨엔 인증이 걸려 있어 **정확한 인증 방식은
구현 시 확인 필요** — API 키 발급 방식 또는 내부 서비스 토큰 확인)를 폴링해 D2 도입 이전 대화·
버퍼 유실분을 캐치업하는 `scripts/backfill_openwebui_chats.py`. **1회성/보조 도구**로 설계 —
상시 폴러가 아니다. D2(실시간 훅)가 정상 동작하면 이 스크립트는 예외 복구용으로만 쓴다.

### D4. K2 큐 재편입 — flush가 기존 문서를 갱신할 때

세션이 이어져 같은 `doc_id`가 이미 K2 처리(완료: `k2_done_at` NOT NULL, V2.9 기준)된 뒤 새
turn이 추가돼 flush가 재발생하면, 내용이 바뀌었으니 재분류가 맞다:

```sql
UPDATE document_meta SET k2_done_at = NULL, classifier_version = NULL,
       extract_at = NULL, classify_at = NULL, summarize_at = NULL
WHERE doc_id = ?;
```

이 문서가 V2.9의 `waiting` 쿼리에 자동으로 다시 걸린다 — **새 큐 로직 불필요, 기존 V2.9 정의
그대로 재사용**되는 게 이 설계가 K2_BATCH_CURATION_DESIGN.md와 맞물리는 지점이다.

### D5. 품질 게이트 — 별도 필터링 안 함, V2.9 게이트에 위임

"사소한 잡담까지 다 반입되면 희석되지 않냐"는 우려에는 **사전 필터링을 추가하지 않는다** —
`trust: "auto"` + V2.9의 confidence 임계값 quarantine 게이트가 이미 이 문제를 위해 설계돼 있다
(K2_BATCH_CURATION_DESIGN.md §B4). 저품질 대화는 자동으로 quarantine되어 전시층(mirror/graph)엔
안 뜨고 검색층(DB)에만 남는다 — 기존 원칙("저장은 관대하게, 전시는 엄격하게") 그대로 적용.

---

## 구현 순서 (PR 단위)

| PR | 내용 | 규모 | 의존 |
|---|---|---|---|
| PR-1 | A1(즉시 교정) + A2(refresh_model_pins.sh) | 소 | — |
| PR-2 | B1(capability 기반 thinking 판단) + B3(context 클램프) | 중 | — |
| PR-3 | B2(답변 계약 보강 + telemetry 플래그) | 소 | PR-2 |
| PR-4 | C2(검색 선택 마커) | 소 | — |
| PR-5 | D0(탭 중복 정리) | 극소 | — |
| PR-6 | D1·D2(세션 버퍼 + 자동 flush + K2 재편입) | 대 | D0, V2.9 PR1(k2_done_at) |
| PR-7 | D3(백필 스크립트, 선택) | 중 | PR-6, OpenWebUI API 인증 방식 확인 |

권장 착수 순서: PR-1(가장 저렴·즉효) → PR-2(핵심 버그 수정) → PR-4 → PR-6 → 나머지.
PR-6은 V2.9의 `k2_done_at` 컬럼(migration 007)이 먼저 있어야 D4가 의미가 있다 — 순서 준수 필요.

## 테스트 계획

```
test_capability_cache:   /api/show mock — thinking 있는/없는 모델 각각 no-think 전처리 적용 여부
test_context_clamp:      advertised context < 32768인 모델 mock → clamp 확인
test_search_override:    "!search"/"!nosearch" 마커 감지·제거·강제값 확인, 마커 없을 때 기존 자동판단 유지
test_session_flush:      idle/turns/chars 3가지 flush 조건 각각 단위테스트
test_flush_format:       flush 산출물이 external_capture.py 수동 저장 포맷과 스키마 일치하는지 diff
test_k2_reopen:          이미 k2_done_at 있는 doc_id에 재flush → NULL 초기화 확인
test_pin_refresh:        mock ollama tags → .env 값 정확히 교체, 빈 목록 시 중단
```

## 리스크

| 리스크 | 완화 |
|---|---|
| OpenWebUI가 세션 id를 요청에 안 실어줌 | 폴백(내용 해시) 설계됨 §D2, 구현 시 실제 헤더 덤프로 1차 확인 필수 |
| 자동 flush가 응답 지연 유발 | `asyncio.create_task` fire-and-forget, 실패해도 사용자 응답과 무관 |
| `/api/show` 매 요청 호출 시 지연 | 1시간 캐시(§B1)로 상시 조회 방지 |
| 세션 버퍼가 l2-gateway 재시작 시 유실 | 설계상 허용(대화 자체는 OpenWebUI DB에 남음) + D3 백필로 복구 가능 |
| OpenWebUI API 인증 방식 불명 | D3는 보조 기능으로 격리, PR-7에서 별도 확인 후 착수 — PR-6(핵심 자동반입)과 독립 |
| refresh_model_pins.sh가 Ollama 다운 시 .env 훼손 | 빈 TAGS면 스크립트 중단하는 가드 필수(§A3) |

## 부록 — 이 설계가 재사용하는 기존 장치 (새로 안 만든 것)

- 문서 저장 포맷·frontmatter 스키마 — `external_capture.py` 그대로
- K2 큐 재진입 조건 — `K2_BATCH_CURATION_DESIGN.md`의 `k2_done_at` 정의 그대로
- 채널별 trust 기본값 — `IRIS_INGEST_NORMALIZATION_RULES.md`의 `chat: trust=auto` 그대로
- 품질 필터링 — V2.9의 confidence quarantine 게이트 그대로 (신규 필터 없음)
- capability 조회 방식 — 이번 세션 OpenClaw 모델 선정 때 쓴 `ollama show` capability 태그 방식 재사용
