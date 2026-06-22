"""V2.7.6 — LLM 슬라이드 설계기."""
from __future__ import annotations

import json
import re

from src import llm
from src.deck.schema import Deck, PATTERN_TEMPLATES, Slide


class DesignError(Exception):
    pass


PATTERN_SLOTS = {
    "cover": "company, title, subtitle, target, date_version",
    "agenda": "title, subtitle, items=[{ch, title, summary}, ...]",
    "exec-summary": "title, subtitle, left_label, right_label, left_items=[{title, detail}*5], right_items=[{title, detail}*5]",
    "metrics-row": "title, subtitle, metrics=[{value, label, color in [blue,orange,red,green]}*4]",
    "compare-2col": "title, subtitle, left_label, right_label, left_items=[str], right_items=[str], footer_note?",
    "card-grid-4": "title, subtitle, intro?={label, lines}, section_title, cards=[{title, subtitle, color}*4], outro?={label, bullets}",
    "phase-roadmap": "title, subtitle, phases=[{label, title, period, color, tasks=[str]}*4], footer_note?",
    "dimension-5": "title, subtitle, dimensions=[{label, color, bullets=[str]*3}*5], footer_note?",
}


def _build_prompt(md_text: str, meta: dict) -> str:
    patterns_doc = "\n".join(f"- {pid}: {slots}" for pid, slots in PATTERN_SLOTS.items())
    # V2.8.1.2 — 응답 토큰 한도 안 깨지게 슬라이드 수 보수적으로 (8b 모델 기준)
    target_min = max(6, min(10, len(md_text) // 1500))
    target_max = min(12, target_min + 2)
    return f"""당신은 IRIS 슬라이드 디자이너입니다. 사용자가 박은 마크다운 내용을
*컨설팅급 PPT 슬라이드 사양*으로 변환합니다. JSON으로만 답하세요.

## 메타
회사명: {meta.get('company', '')}
보고서명: {meta.get('title', '')}
부제: {meta.get('subtitle', '')}
날짜: {meta.get('date', '')}

## 사용 가능 슬라이드 패턴 (이 8종만 사용)
{patterns_doc}

## ⚠️ 절대 출력 스키마 (이 형태 외 절대 금지)

```json
{{
  "slides": [
    {{"pattern": "<위 8종 중 하나>", "data": {{ ...해당 패턴의 슬롯... }}}},
    {{"pattern": "<...>", "data": {{ ... }}}}
  ]
}}
```

- **각 슬라이드는 정확히 두 키 `pattern`과 `data`만 가짐**
- `pattern` 값은 위 8종 ID 중 하나의 *문자열* (예: "cover", "agenda", "phase-roadmap")
- `data` 값은 *객체* (해당 패턴의 슬롯을 다 채움)
- `slide_id`·`type`·`id` 같은 다른 키 박지 마. *오직 `pattern`과 `data`*.
- 모든 슬롯을 `data` *안*에 박음. *밖에* 박으면 무효.

## 완전한 예시 (이 형태 그대로 따를 것)

```json
{{
  "slides": [
    {{"pattern": "cover", "data": {{"company": "회사", "title": "제목", "subtitle": "부제", "target": "대상", "date_version": "2026.06"}}}},
    {{"pattern": "agenda", "data": {{"title": "목차", "subtitle": "주요 내용", "items": [{{"ch": "1", "title": "배경", "summary": "..."}}, {{"ch": "2", "title": "전략", "summary": "..."}}]}}}},
    {{"pattern": "phase-roadmap", "data": {{"title": "로드맵", "subtitle": "12개월", "phases": [{{"label": "1", "title": "준비", "period": "0-3M", "color": "blue", "tasks": ["조사", "평가"]}}, {{"label": "2", "title": "설계", "period": "3-6M", "color": "green", "tasks": ["설계"]}}, {{"label": "3", "title": "개발", "period": "6-9M", "color": "orange", "tasks": ["개발"]}}, {{"label": "4", "title": "배포", "period": "9-12M", "color": "purple", "tasks": ["배포"]}}]}}}}
  ]
}}
```

## ⚠️ 다른 규칙
1. **슬라이드 개수**: 정확히 {target_min}~{target_max}장. 더 많이 박지 마.
2. cover 1장 + agenda 1장 + 본문 {target_min - 2}~{target_max - 2}장
3. 입력 마크다운의 핵심 섹션을 그룹핑해서 슬라이드로 전개
4. 각 슬라이드 필수 슬롯 채우되 *간결하게* (필드값 80자 이내)
5. exec-summary의 left_items / right_items는 5개씩, *짧게* (title 20자, detail 40자)
6. 색상 일관: 진단·문제 'red', 해결·혁신 'green', 중립 'blue', 강조 'orange', 분기 'purple'

## 패턴 매칭 전략
- 비교/대조 → compare-2col
- 4구역·4단계 → card-grid-4
- 시간·단계 로드맵 → phase-roadmap
- 5관점·5차원 → dimension-5
- 지표 4개 → metrics-row
- As-Is vs To-Be → exec-summary

## 사용자 입력 마크다운
{md_text[:12000]}

## 출력 시작 (JSON만, 다른 말 절대 금지)
"""


# ─── V2.8.1.2 — JSON 복구 ────────────────────────────────────────
def _repair_truncated_json(raw: str) -> dict | None:
    """LLM 응답이 num_predict로 잘렸을 때 *완성된 슬라이드만* 살림.

    전략:
      1. 정상 파싱 시도 → 성공이면 그대로
      2. 실패면 "slides": [ 위치 찾고, 각 슬라이드 객체를 brace 카운팅으로 분리
      3. 끝까지 파싱 성공한 슬라이드만 모음
    """
    raw = raw.strip()
    # 시도 1: 그대로 파싱
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # 시도 2: 끝에 닫는 ]} 박아서 재시도 (가장 흔한 케이스)
    for suffix in ("]}", "\"}}]}", "}]}", "}}]}", "\"}]}"):
        try:
            return json.loads(raw + suffix)
        except json.JSONDecodeError:
            pass

    # 시도 3: 슬라이드 객체 하나씩 brace 카운팅으로 살림
    m = re.search(r'"slides"\s*:\s*\[', raw)
    if not m:
        return None
    start = m.end()
    slides: list[dict] = []
    i = start
    n = len(raw)
    while i < n:
        # 다음 슬라이드 객체 시작 `{` 찾기
        while i < n and raw[i] in ' \t\n\r,':
            i += 1
        if i >= n or raw[i] != '{':
            break
        # brace 카운팅 + 문자열 내부 인식
        depth = 0
        j = i
        in_str = False
        escape = False
        while j < n:
            c = raw[j]
            if escape:
                escape = False
            elif c == '\\':
                escape = True
            elif c == '"':
                in_str = not in_str
            elif not in_str:
                if c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        # i..j 한 슬라이드 객체
                        try:
                            slides.append(json.loads(raw[i:j + 1]))
                        except json.JSONDecodeError:
                            pass
                        i = j + 1
                        break
            j += 1
        else:
            # 끝까지 안 닫힘 — 이 슬라이드는 버림
            break
    if slides:
        return {"slides": slides}
    return None


def design_deck(md_text: str, meta: dict, *,
                timeout: float = 300.0,
                model: str | None = None) -> Deck:
    """LLM이 마크다운을 받아 슬라이드 사양 출력.

    model 인자가 None이면 deep 슬롯 (config IRIS_LLM_DEEP, 기본 qwen3:8b/30b/80b).
    UI에서 사용자가 직접 박은 모델이 있으면 그걸 우선.

    V2.8.1.2 — JSON 잘림 복구:
      - num_predict 16384로 확장
      - num_ctx 32768
      - 그래도 잘리면 _repair_truncated_json()으로 완성된 슬라이드만 살림
    """
    prompt = _build_prompt(md_text, meta)
    resp = llm.generate_json(
        prompt, role="deep", model=model, timeout=timeout,
        num_ctx=32768, num_predict=16384,
    )

    data: dict | None = None
    raw_text = resp.get("raw", "")

    if resp.get("ok"):
        data = resp.get("data", {})
    else:
        err = resp.get("error", "")
        # JSON 파싱 실패면 raw로 복구 시도
        if "JSON 파싱 실패" in err or "Expecting" in err:
            data = _repair_truncated_json(raw_text)
            if data is None:
                raise DesignError(
                    f"LLM JSON 잘림 + 복구 실패. raw 앞 200자: {raw_text[:200]}"
                )
        else:
            raise DesignError(f"LLM 실패: {err}")

    raw_slides = (data or {}).get("slides", [])

    slides: list[Slide] = []
    for sl in raw_slides:
        if not isinstance(sl, dict):
            continue
        # V2.8.1.2 — flat 스키마 자동 변환 ({slide_id, ...} → {pattern, data})
        pid = sl.get("pattern") or sl.get("slide_id") or sl.get("type") or sl.get("id")
        if pid not in PATTERN_TEMPLATES:
            continue
        sl_data = sl.get("data")
        if not isinstance(sl_data, dict):
            # flat 형식이면 pattern/slide_id/type/id 빼고 나머지를 data로
            sl_data = {k: v for k, v in sl.items()
                       if k not in ("pattern", "slide_id", "type", "id")}
        slides.append(Slide(pattern=pid, data=sl_data))

    if not slides:
        raise DesignError("LLM 응답에서 유효한 슬라이드 0개")

    return Deck(
        title=meta.get("title", "보고서"),
        subtitle=meta.get("subtitle", ""),
        company_name=meta.get("company", ""),
        date=meta.get("date", "2026.06"),
        slides=slides,
    )


__all__ = ["DesignError", "design_deck", "PATTERN_SLOTS"]
