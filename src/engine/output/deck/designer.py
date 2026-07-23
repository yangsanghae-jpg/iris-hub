"""V2.7.6 → V2.8.2 — LLM 슬라이드 설계기.

V2.8.2 핵심:
- PATTERN_SLOTS 항목 수 *유연화* (4·5 고정 → 범위)
- 프롬프트에서 "80자 이내", "20자/40자" 글자수 제한 *제거*
- target_min/max 공식 확장 (6~10 → 15~30)
- pre_expanded 인자 — Stage 1 확장 결과를 받았으면 자르기 X
"""
from __future__ import annotations

import json
import re

from src import llm
from src.engine.output.deck.schema import Deck, PATTERN_TEMPLATES, Slide


class DesignError(Exception):
    pass


PATTERN_SLOTS = {
    "cover": "company, title, subtitle, target, date_version",
    "agenda": "title, subtitle, items=[{ch, title, summary} 4~10개]",
    "exec-summary": "title, subtitle, left_label, right_label, "
                    "left_items=[{title, detail} 4~8개], right_items=[{title, detail} 4~8개]",
    "metrics-row": "title, subtitle, "
                   "metrics=[{value, label, color in [blue,orange,red,green]} 3~6개]",
    "compare-2col": "title, subtitle, left_label, right_label, "
                    "left_items=[str 4~10개], right_items=[str 4~10개], footer_note?",
    "card-grid-4": "title, subtitle, intro?={label, lines}, section_title, "
                   "cards=[{title, subtitle, color} 3~8개], outro?={label, bullets}",
    "phase-roadmap": "title, subtitle, "
                     "phases=[{label, title, period, color, tasks=[str 2~6개]} 3~8개], footer_note?",
    "dimension-5": "title, subtitle, "
                   "dimensions=[{label, color, bullets=[str 2~6개]} 4~8개], footer_note?",
}


def _build_prompt(md_text: str, meta: dict, *, pre_expanded: bool,
                  target_slides: int | None,
                  density: str = "standard") -> str:
    from src.engine.output.deck.theme import density_prompt_directive

    patterns_doc = "\n".join(f"- {pid}: {slots}" for pid, slots in PATTERN_SLOTS.items())

    # V2.8.2 — 슬라이드 수 *확장*. pre_expanded면 입력이 이미 풍부하므로 더 박을 수 있음
    if target_slides:
        target_min, target_max = target_slides, target_slides + 3
    elif pre_expanded:
        # Stage 1 확장 통과한 입력 → 글자당 슬라이드 밀도 ↑
        target_min = max(15, min(30, len(md_text) // 500))
        target_max = min(35, target_min + 5)
    else:
        target_min = max(8, min(20, len(md_text) // 800))
        target_max = min(25, target_min + 5)

    density_block = density_prompt_directive(density)

    return f"""당신은 컨설팅급 PPT 슬라이드 디자이너입니다. 사용자가 박은 마크다운을
*정보를 풍부하게 유지*하면서 슬라이드 사양으로 변환합니다. JSON으로만 답하세요.

## 메타
회사명: {meta.get('company', '')}
보고서명: {meta.get('title', '')}
부제: {meta.get('subtitle', '')}
날짜: {meta.get('date', '')}

{density_block}
※ 밀도는 슬라이드 *장수*를 바꾸지 않는다. 목표 장수({target_min}~{target_max})는 유지하고
  슬라이드별 설명량·구조적 풍부함만 조절한다.

## 사용 가능 슬라이드 패턴 (이 8종만 사용)
{patterns_doc}

## ⚠️ 절대 출력 스키마 (이 형태 외 절대 금지)

```json
{{
  "slides": [
    {{"pattern": "<위 8종 중 하나>", "data": {{ ...해당 패턴의 슬롯... }}}}
  ]
}}
```

- **각 슬라이드는 정확히 두 키 `pattern`과 `data`만 가짐**
- `pattern` 값은 위 8종 ID 중 하나의 *문자열* (예: "cover", "phase-roadmap")
- `data` 값은 *객체* (해당 패턴의 슬롯을 다 채움)
- `slide_id`·`type`·`id` 같은 다른 키 박지 마

## ⚠️ 풍부함 규칙 (V2.8.2 핵심)

1. **슬라이드 개수**: {target_min}~{target_max}장. 입력의 *모든 섹션·소절을 슬라이드로 전개*.
2. **항목은 풍부하게**: 각 슬롯의 항목 수는 위 패턴 정의의 *범위 안에서 많은 쪽으로*.
   예: phases는 3~8개면 6~8개 박음, dimensions 4~8개면 5~7개 박음.
3. **항목 내용도 풍부하게**: title은 *완전한 구절* (10~30자), detail/summary는
   *문장형* (40~150자). 단어 나열·줄임 금지. **3~4단어로 줄이지 마**.
4. **원본 정보 손실 금지**: 마크다운의 표·리스트·인용을 *그대로* 슬롯에 박음.
   원본이 27개 항목이면 27개 다 박음 (여러 슬라이드로 쪼개도 좋음).
5. **표는 그대로 보존**: 마크다운 표가 있으면 compare-2col·exec-summary·dimension-5로 전개.
6. **수치 인용**: 원본에 박힌 수치(99.9%, 24시간, 1년, 27항목, 7단계 등)는 슬라이드에 *그대로* 박음.
7. **다국어 보존**: 입력이 중국어/영어면 슬라이드도 같은 언어로 박음.
8. cover 1장 + agenda 1장 + 본문 {target_min - 2}~{target_max - 2}장.
9. 색상 일관: 진단·문제 'red', 해결·혁신 'green', 중립 'blue', 강조 'orange', 분기 'purple'.
10. **card-grid-4의 intro/outro는 장식이 아니라 손실 방지 슬롯**: 스키마엔 `?`(선택)로
    표시돼 있지만, 원본에 카드 목록 *앞*에 도입 설명이 있으면 반드시 `intro`에, *뒤*에
    요약·조건·부가설명(예: "지원: 7×24시간 기술지원, 2회/년 현장서비스")이 있으면 반드시
    `outro`에 채운다. 카드 3~8개 슬롯에 안 들어가는 문장이 하나라도 원본에 있다면
    그건 버릴 항목이 아니라 intro/outro에 넣을 항목이다. **다 카드에 안 들어간다고
    그 문장을 버리면 정보 손실.**

## 패턴 매칭 전략 (입력 구조 → 패턴)

- 비교/대조 (As-Is vs To-Be 등) → exec-summary 또는 compare-2col
- N단계·N구역·N카드 → card-grid-4 (N=3~8). 카드 앞뒤에 남는 문장은 규칙 10대로
  intro/outro에 반드시 채움 — 버리면 정보 손실.
- 시간·단계 로드맵 → phase-roadmap (단계 3~8)
- N관점·N차원·N측면 → dimension-5 (N=4~8)
- 지표·KPI 나열 → metrics-row (3~6 지표)
- 일반 항목 리스트 → agenda 또는 dimension-5

## 풍부한 예시 (이 정도 밀도로 박을 것)

```json
{{
  "slides": [
    {{"pattern": "cover", "data": {{"company": "赛美特 (SEMI-TECH)", "title": "SSIM项目实施方法论完整文档", "subtitle": "标准化·可复制·高可靠的产品交付体系", "target": "项目管理团队、客户方、实施顾问", "date_version": "2026.06 | CMMI 5级认证"}}}},
    {{"pattern": "phase-roadmap", "data": {{"title": "SSIM七大实施阶段", "subtitle": "从启动到关闭的完整生命周期", "phases": [
       {{"label": "IM100", "title": "投入与准备", "period": "项目启动会", "color": "blue", "tasks": ["制定详细项目日程", "项目整体启动落地", "输出WBS工作分解结构", "输出SOW工作说明书"]}},
       {{"label": "IM200", "title": "业务分析", "period": "分析结果报告会", "color": "blue", "tasks": ["第一轮：现场现状调研", "第二轮：业务现状深度分析", "输出现状分析书"]}},
       {{"label": "IM300", "title": "蓝图设计", "period": "蓝图报告会", "color": "green", "tasks": ["初步方案讲解", "详细方案讲解", "确认定稿业务蓝图", "签署蓝图完成报告书"]}}
    ]}}}}
  ]
}}
```

## 사용자 입력 마크다운
{md_text[:24000] if pre_expanded else md_text[:16000]}

## 출력 시작 (JSON만, 다른 말 절대 금지, 풍부하게)
"""


# ─── V2.8.1.2 — JSON 복구 ────────────────────────────────────────
def _repair_truncated_json(raw: str) -> dict | None:
    """LLM 응답이 num_predict로 잘렸을 때 *완성된 슬라이드만* 살림."""
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    for suffix in ("]}", "\"}}]}", "}]}", "}}]}", "\"}]}"):
        try:
            return json.loads(raw + suffix)
        except json.JSONDecodeError:
            pass

    m = re.search(r'"slides"\s*:\s*\[', raw)
    if not m:
        return None
    start = m.end()
    slides: list[dict] = []
    i = start
    n = len(raw)
    while i < n:
        while i < n and raw[i] in ' \t\n\r,':
            i += 1
        if i >= n or raw[i] != '{':
            break
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
                        try:
                            slides.append(json.loads(raw[i:j + 1]))
                        except json.JSONDecodeError:
                            pass
                        i = j + 1
                        break
            j += 1
        else:
            break
    if slides:
        return {"slides": slides}
    return None


def design_deck(md_text: str, meta: dict, *,
                timeout: float = 300.0,
                model: str | None = None,
                pre_expanded: bool = False,
                target_slides: int | None = None,
                density: str = "standard") -> Deck:
    """LLM이 마크다운을 받아 슬라이드 사양 출력.

    V2.8.2 새 인자:
      pre_expanded: Stage 1 확장 통과한 입력이면 True (자르기 24k, 더 밀도 높게)
      target_slides: 사용자가 슬라이드 수 직접 박았으면 (auto면 None)

    V2.8.4:
      density: spacious|standard|dense — 슬라이드 장수는 유지, 콘텐츠 정보량만 조절.
               기본 standard → 기존 8765 호출과 동일.
    """
    prompt = _build_prompt(
        md_text, meta,
        pre_expanded=pre_expanded, target_slides=target_slides,
        density=density or "standard",
    )
    # V2.8.2 — num_predict 32768로 더 키움 (풍부한 슬라이드 30장 박을 여유)
    resp = llm.generate_json(
        prompt, role="deep", model=model, timeout=timeout,
        num_ctx=32768, num_predict=32768,
    )

    data: dict | None = None
    raw_text = resp.get("raw", "")

    if resp.get("ok"):
        data = resp.get("data", {})
    else:
        err = resp.get("error", "")
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
        pid = sl.get("pattern") or sl.get("slide_id") or sl.get("type") or sl.get("id")
        if pid not in PATTERN_TEMPLATES:
            continue
        sl_data = sl.get("data")
        if not isinstance(sl_data, dict):
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

