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
    "table": "title, subtitle?, columns=[{key, label} 2~6개], "
             "rows=[{key: value, ...} 2개 이상], footnote?",
    "narrative": "title, subtitle?, key_message, "
                 "paragraphs=[str 1~5개, 완전한 문장 단락. 불릿·표 금지]",
    "summary": "title, subtitle?, key_message, "
               "points=[str 3~8개, 짧은 핵심 불릿]",
}


def _build_prompt(md_text: str, meta: dict, *, pre_expanded: bool,
                  target_slides: int | None,
                  density: str = "standard",
                  contract_block: str = "") -> str:
    from src.engine.output.deck.theme import density_prompt_directive

    patterns_doc = "\n".join(f"- {pid}: {slots}" for pid, slots in PATTERN_SLOTS.items())

    if target_slides:
        target_min, target_max = target_slides, target_slides + 3
    elif pre_expanded:
        target_min = max(15, min(30, len(md_text) // 500))
        target_max = min(35, target_min + 5)
    else:
        target_min = max(8, min(20, len(md_text) // 800))
        target_max = min(25, target_min + 5)

    density_block = density_prompt_directive(density)
    forced = contract_block.strip()
    if forced:
        pattern_rules = f"""
## ⚠️ 패턴 강제 계약 (최우선 — 추측 금지)
{forced}

입력 마크다운의 `<!-- IRIS_PATTERN: ... -->` / `<!-- IRIS_ROLES: ... -->` 주석을
읽고, 위 계약과 동일한 pattern으로만 data 슬롯을 채운다.
"""
        matching = (
            "패턴은 이미 결정됨. 위 강제 계약을 따르고 자유롭게 재선택하지 말 것.\n"
            "card-grid-4에서 roles에 context가 있으면 intro에, "
            "condition/exception/conclusion/source가 있으면 outro에 배치. "
            "특정 카드 하나에만 속하면 cards 항목에. 원문에 없는 사실·장식 문구 금지."
        )
    else:
        pattern_rules = ""
        matching = """## 패턴 매칭 전략 (입력 구조 → 패턴) — 계약 마커가 없을 때만
- 비교/대조 → exec-summary 또는 compare-2col
- 순서·절차·로드맵 → phase-roadmap
- 병렬 독립 항목 3~8 → card-grid-4 (공통 context→intro, 공통 condition→outro)
- 다차원 분류 → dimension-5
- KPI·수치 핵심 → metrics-row
- 표의 행·열 대응이 중요하면 표를 카드로 바꾸지 말 것
"""

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

## 사용 가능 슬라이드 패턴 (이 11종만 사용)
{patterns_doc}
{pattern_rules}
## ⚠️ 절대 출력 스키마 (이 형태 외 절대 금지)

```json
{{
  "slides": [
    {{"pattern": "<위 11종 중 하나>", "data": {{ ...해당 패턴의 슬롯... }}}}
  ]
}}
```

- **각 슬라이드는 정확히 두 키 `pattern`과 `data`만 가짐**
- `pattern` 값은 위 11종 ID 중 하나의 *문자열*
- `data` 값은 *객체* (해당 패턴의 슬롯을 채움)
- `slide_id`·`type`·`id` 같은 다른 키 박지 마

## ⚠️ 풍부함·보존 규칙

1. **슬라이드 개수**: 계약이 있으면 계약 장수와 동일. 없으면 {target_min}~{target_max}장.
2. **항목은 풍부하게**: 패턴별 허용 범위 안에서 충분한 항목 수.
3. **원본 정보 손실 금지**: 수치·날짜·코드·조건·예외·결론·출처를 삭제하지 말 것.
4. **다국어 보존**: 입력이 중국어/영어면 슬라이드도 같은 언어.
5. **색상**: 진단·문제 'red', 해결·혁신 'green', 중립 'blue', 강조 'orange', 분기 'purple'.
6. **card-grid-4 intro/outro는 조건부**: 스키마 optional 유지. roles/의미상 공통
   문장만 채움. 장식 문구·환각·cards와 중복 금지.

{matching}

## 사용자 입력 마크다운
{md_text[:24000] if pre_expanded else md_text[:16000]}

## 출력 시작 (JSON만, 다른 말 절대 금지)
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


def _slides_from_payload(data: dict | None) -> list[Slide]:
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
    return slides


def _call_design_llm(prompt: str, *, model: str | None, timeout: float) -> dict:
    resp = llm.generate_json(
        prompt, role="deep", model=model, timeout=timeout,
        num_ctx=32768, num_predict=32768,
    )
    raw_text = resp.get("raw", "")
    if resp.get("ok"):
        return resp.get("data", {}) or {}
    err = resp.get("error", "")
    if "JSON 파싱 실패" in err or "Expecting" in err:
        data = _repair_truncated_json(raw_text)
        if data is None:
            raise DesignError(
                f"LLM JSON 잘림 + 복구 실패. raw 앞 200자: {raw_text[:200]}"
            )
        return data
    raise DesignError(f"LLM 실패: {err}")


def _build_single_slide_prompt(
    slide_index: int,
    contract,
    source_body: str,
    meta: dict,
    *,
    validation_errors: list[str],
    previous_output: dict | None = None,
) -> str:
    from src.engine.output.deck.pattern_contract import PATTERN_CONTRACTS

    pattern = contract.pattern
    slots = PATTERN_SLOTS.get(pattern, "")
    err_block = "\n".join(f"- {e}" for e in validation_errors)
    prev = json.dumps(previous_output or {}, ensure_ascii=False)[:2000]
    return f"""슬라이드 {slide_index + 1}만 다시 설계하세요. pattern은 **{pattern}** 고정.
roles: {",".join(contract.roles) or "-"}

## 검증 실패 (수정 대상)
{err_block}

## 이전 출력 (참고)
{prev}

## 패턴 슬롯
{slots}

## 소스 마크다운 (이 슬라이드만)
{source_body[:8000]}

## 출력 (JSON 객체 하나만)
```json
{{"pattern": "{pattern}", "data": {{ ... }}}}
```
pattern 변경·다른 슬라이드 출력 금지.
"""


def _retry_single_slide(
    deck: Deck,
    slide_index: int,
    contracts: list,
    md_text: str,
    meta: dict,
    *,
    model: str | None,
    timeout: float,
    errors: list[str],
) -> Deck:
    from src.engine.output.deck.pattern_contract import (
        SlotValidationError,
        split_slide_bodies,
        validate_slide_slots,
    )

    bodies = split_slide_bodies(md_text)
    source = bodies[slide_index] if slide_index < len(bodies) else md_text
    contract = contracts[slide_index]
    prev = deck.slides[slide_index].data if slide_index < len(deck.slides) else {}
    prompt = _build_single_slide_prompt(
        slide_index, contract, source, meta,
        validation_errors=errors, previous_output=prev,
    )
    data = _call_design_llm(prompt, model=model, timeout=timeout)
    if isinstance(data, dict) and "pattern" in data:
        payload = data
    elif isinstance(data, dict) and data.get("slides"):
        payload = data["slides"][0]
    else:
        raise DesignError(f"슬라이드 {slide_index + 1} 교정 JSON 형식 오류")

    pid = payload.get("pattern")
    if pid != contract.pattern:
        raise DesignError(
            f"슬라이드 {slide_index + 1} 교정 시 pattern 변경 금지: {pid}"
        )
    sl_data = payload.get("data") or {}
    validate_slide_slots(contract.pattern, sl_data, slide_no=slide_index + 1)
    new_slides = list(deck.slides)
    new_slides[slide_index] = Slide(pattern=contract.pattern, data=sl_data)
    return Deck(
        title=deck.title, subtitle=deck.subtitle,
        company_name=deck.company_name, date=deck.date,
        slides=new_slides,
    )


def _validate_and_guard_deck(
    deck: Deck,
    md_text: str,
    contracts: list | None,
    expected: list[str] | None,
) -> None:
    from src.engine.output.deck.pattern_contract import validate_deck_patterns
    from src.engine.output.deck.card_content_guard import guard_deck_card_grids
    from src.engine.output.deck.content_coverage import check_deck_coverage

    guard_deck_card_grids(deck, md_text)
    if expected is not None:
        validate_deck_patterns(deck, expected)
    # 정보 보존(coverage) 미달은 폴백 원칙(§5)에 따라 하드 실패가 아니라
    # 경고로 강등한다 — 덱 생성 자체를 막지 않는다.
    warns = check_deck_coverage(deck, md_text, strict=False)
    if warns:
        deck.warnings.extend(f"정보 보존 경고: {w}" for w in warns)


def design_deck(md_text: str, meta: dict, *,
                timeout: float = 300.0,
                model: str | None = None,
                pre_expanded: bool = False,
                target_slides: int | None = None,
                density: str = "standard",
                contract_mode: str = "optional",
                contract: dict | None = None) -> Deck:
    """LLM이 마크다운을 받아 슬라이드 사양 출력.

    IRIS_PATTERN 계약이 있으면 pattern을 강제하고 슬롯·coverage를 검증한다.
    계약이 없으면(8765 등 레거시) 기존처럼 자유 설계 + 가벼운 가드.
    """
    from src.engine.output.deck.pattern_contract import (
        PatternContractError,
        SlotValidationError,
        format_contract_block_for_prompt,
        resolve_contracts,
        validate_slide_slots,
    )
    from src.engine.output.deck.deck_reconciler import fallback_slide, reconcile_deck

    contracts, expected = resolve_contracts(
        md_text, contract, contract_mode=contract_mode,  # type: ignore[arg-type]
    )
    contract_block = ""
    if contracts:
        contract_block = format_contract_block_for_prompt(contracts)

    base_prompt = _build_prompt(
        md_text, meta,
        pre_expanded=pre_expanded, target_slides=target_slides,
        density=density or "standard",
        contract_block=contract_block,
    )

    last_err: Exception | None = None
    prompt = base_prompt
    deck: Deck | None = None

    for attempt in range(2):  # 전체 설계: JSON 파싱 실패 등에만
        try:
            data = _call_design_llm(prompt, model=model, timeout=timeout)
            slides = _slides_from_payload(data)
            if not slides:
                raise DesignError("LLM 응답에서 유효한 슬라이드 0개")
            deck = Deck(
                title=meta.get("title", "보고서"),
                subtitle=meta.get("subtitle", ""),
                company_name=meta.get("company", ""),
                date=meta.get("date", "2026.06"),
                slides=slides,
            )
            # 규칙 초과 슬라이드를 검증 *전에* 분할·조정한다. 조정은 슬라이드
            # 수를 바꿀 수 있으므로 contracts/expected도 함께 갱신해야
            # 뒤이은 validate_deck_patterns의 actual==expected 비교가 깨지지
            # 않는다(조정 후 재생성분을 버리고 옛 expected로 비교하면 길이
            # 불일치로 무조건 반려된다).
            deck, contracts, _ = reconcile_deck(deck, contracts)
            if contracts is not None:
                expected = [c.pattern for c in contracts]
            _validate_and_guard_deck(deck, md_text, contracts, expected)
            return deck
        except SlotValidationError as e:
            # 슬라이드 단위 1회 교정
            if contracts and deck is not None:
                msg = str(e)
                m = re.search(r"(\d+)번", msg)
                idx = int(m.group(1)) - 1 if m else 0
                if 0 <= idx < len(deck.slides):
                    try:
                        fixed = _retry_single_slide(
                            deck, idx, contracts, md_text, meta,
                            model=model, timeout=timeout, errors=[msg],
                        )
                        fixed, fixed_contracts, _ = reconcile_deck(fixed, contracts)
                        fixed_expected = [c.pattern for c in fixed_contracts] if fixed_contracts else expected
                        _validate_and_guard_deck(fixed, md_text, fixed_contracts, fixed_expected)
                        return fixed
                    except (DesignError, PatternContractError, SlotValidationError):
                        # 단일 슬라이드 교정도 실패 — 하드 실패시키지 않고
                        # 전체 재시도(그래도 안 되면 최종 폴백 tail)로 넘긴다.
                        pass
            last_err = e
            prompt = (
                base_prompt
                + "\n\n## 이전 설계 검증 실패 — 지정 pattern/슬롯을 수정해 다시 출력\n"
                + str(e)
                + "\npattern을 바꾸지 말고 계약된 pattern의 슬롯만 올바르게 채우세요.\n"
            )
            continue
        except (DesignError, PatternContractError) as e:
            # pattern 불일치 → 해당 슬라이드만 교정 시도
            if contracts and deck is not None and "pattern 계약 불일치" in str(e):
                actual = [s.pattern for s in deck.slides]
                for i, (exp, act) in enumerate(zip(expected or [], actual)):
                    if exp != act:
                        try:
                            fixed = _retry_single_slide(
                                deck, i, contracts, md_text, meta,
                                model=model, timeout=timeout,
                                errors=[str(e)],
                            )
                            fixed, fixed_contracts, _ = reconcile_deck(fixed, contracts)
                            fixed_expected = [c.pattern for c in fixed_contracts] if fixed_contracts else expected
                            _validate_and_guard_deck(
                                fixed, md_text, fixed_contracts, fixed_expected,
                            )
                            return fixed
                        except (DesignError, PatternContractError, SlotValidationError):
                            # 단일 슬라이드 교정도 실패 — 하드 실패시키지 않고
                            # 전체 재시도(그래도 안 되면 최종 폴백 tail)로 넘긴다.
                            pass
            last_err = e
            prompt = (
                base_prompt
                + "\n\n## 이전 설계 검증 실패 — 지정 pattern/슬롯을 수정해 다시 출력\n"
                + str(e)
                + "\npattern을 바꾸지 말고 계약된 pattern의 슬롯만 올바르게 채우세요.\n"
            )
            continue

    # 전체 실패 경로 — 예방(프롬프트)·조정(reconcile)·재교정을 모두 소진해도
    # 검증을 통과 못 하면, 덱 전체를 실패시키는 대신 슬라이드 단위로
    # fallback_slide 강등을 적용해 항상 유효한 덱을 반환한다(no-hard-fail).
    if deck is not None:
        deck, contracts, _ = reconcile_deck(deck, contracts)
        warnings_list: list[str] = list(deck.warnings)
        for i, s in enumerate(deck.slides):
            contract_i = contracts[i] if contracts and i < len(contracts) else None
            source_body = md_text
            if contract_i and contract_i.body:
                source_body = contract_i.body

            slot_ok = True
            try:
                validate_slide_slots(s.pattern, s.data or {}, slide_no=i + 1)
            except Exception:
                slot_ok = False

            # 슬롯은 유효하지만 계약이 요구한 pattern과 다른 경우도 조용히
            # 통과시키지 않는다 — "자체로는 유효한 엉뚱한 패턴"이 경고 없이
            # 나가면 폴백 원칙(§5.3 경고 노출)이 무의미해진다.
            pattern_ok = contract_i is None or s.pattern == contract_i.pattern

            if not slot_ok or not pattern_ok:
                new_slide, fwarn = fallback_slide(s, contract_i, source_body)
                deck.slides[i] = new_slide
                warnings_list.append(fwarn)
        deck.warnings = warnings_list
        return deck

    # deck을 단 한 번도 만들지 못한 경우(예: LLM이 매 시도 빈 응답/파싱 불가한
    # JSON만 반환) — 폴백을 적용할 대상 자체가 없다. 이때도 "설계 실패"라는
    # 의미 없는 메시지 대신 실제 원인(last_err)을 그대로 노출해야 진단이 된다.
    if last_err is not None:
        raise DesignError(f"설계 실패: {last_err}") from last_err
    raise DesignError("설계 실패: 원인 불명(LLM 응답 없음)")


BODY_TYPE_DEFAULT_PATTERN = {
    "요약형": "summary",
    "서술형": "narrative",
    "표형": "table",
    "도형형": "card-grid-4",
}

SHAPE_PATTERNS = (
    "card-grid-4",
    "phase-roadmap",
    "metrics-row",
    "compare-2col",
    "exec-summary",
    "dimension-5",
    "agenda",
)


def _density_action_directive(action: str | None) -> str:
    if action == "expand":
        return (
            "## 밀도 지시 — 내용 추가\n"
            "같은 주제·사실 범위 안에서 설명·근거·세부 항목을 *더 풍부하게* 채운다. "
            "원문에 없는 사실을 만들지 말 것. 빈 슬롯을 남기지 말 것.\n"
        )
    if action == "condense":
        return (
            "## 밀도 지시 — 내용 간략히\n"
            "핵심만 남겨 짧게 다듬는다. 중복·수식어·장식 문장을 줄이고 "
            "슬롯 상한 안에서 압축한다. 핵심 수치·고유명사는 유지.\n"
        )
    return ""


def rewrite_slides(
    deck: Deck,
    slide_indices: list[int],
    *,
    md_text: str,
    meta: dict,
    new_pattern: str | None = None,
    body_type: str | None = None,
    density_action: str | None = None,
    model: str | None = None,
    timeout: float = 300.0,
) -> Deck:
    """선택 슬라이드를 새 pattern(또는 동일 pattern)으로 LLM 재작성.

    - new_pattern / body_type 이 있으면 해당 pattern으로 변환
    - density_action: expand | condense | None
    """
    from src.engine.output.deck.pattern_contract import (
        PATTERN_BODY_TYPE,
        split_slide_bodies,
        validate_slide_slots,
    )

    if not slide_indices:
        raise DesignError("교정할 페이지가 없습니다")

    pattern = new_pattern
    if not pattern and body_type:
        pattern = BODY_TYPE_DEFAULT_PATTERN.get(body_type)
    if pattern and pattern not in PATTERN_TEMPLATES:
        raise DesignError(f"알 수 없는 pattern: {pattern}")
    if body_type and body_type not in BODY_TYPE_DEFAULT_PATTERN:
        raise DesignError(f"알 수 없는 body_type: {body_type}")
    if density_action and density_action not in ("expand", "condense"):
        raise DesignError(f"알 수 없는 density_action: {density_action}")

    bodies = split_slide_bodies(md_text) if md_text else []
    new_slides = list(deck.slides)
    density_block = _density_action_directive(density_action)

    for idx in slide_indices:
        if idx < 0 or idx >= len(new_slides):
            raise DesignError(f"잘못된 슬라이드 인덱스: {idx}")
        old = new_slides[idx]
        if old.pattern == "cover":
            raise DesignError("표지(cover) 패턴은 교정 대상이 아닙니다")
        target_pattern = pattern or old.pattern
        if target_pattern == "cover":
            raise DesignError("표지(cover) 패턴으로 변경할 수 없습니다")

        source = bodies[idx] if idx < len(bodies) else ""
        if not source.strip():
            source = json.dumps(old.data, ensure_ascii=False)

        bt = PATTERN_BODY_TYPE.get(target_pattern) or body_type or ""
        slots = PATTERN_SLOTS.get(target_pattern, "")
        prev = json.dumps(old.data, ensure_ascii=False)[:3000]
        prompt = f"""슬라이드 {idx + 1}만 다시 설계하세요.

## 목표 pattern
**{target_pattern}** (body-type: {bt or "—"})
이전 pattern: {old.pattern}

{density_block}
## 패턴 슬롯
{slots}

## 이전 슬라이드 data (참고 — 정보 보존)
{prev}

## 소스 마크다운 (이 슬라이드)
{source[:8000]}

## 출력 규칙
- JSON 객체 하나만: {{"pattern": "{target_pattern}", "data": {{ ... }}}}
- pattern은 반드시 "{target_pattern}"
- 원문에 없는 사실·장식 문구 금지
- 다른 슬라이드 출력 금지
"""
        data = _call_design_llm(prompt, model=model, timeout=timeout)
        if isinstance(data, dict) and "pattern" in data:
            payload = data
        elif isinstance(data, dict) and data.get("slides"):
            payload = data["slides"][0]
        else:
            raise DesignError(f"슬라이드 {idx + 1} 교정 JSON 형식 오류")

        pid = payload.get("pattern")
        if pid != target_pattern:
            raise DesignError(
                f"슬라이드 {idx + 1}: pattern이 {target_pattern}이어야 하는데 {pid}"
            )
        sl_data = payload.get("data") or {}
        validate_slide_slots(target_pattern, sl_data, slide_no=idx + 1)
        new_slides[idx] = Slide(pattern=target_pattern, data=sl_data)

    return Deck(
        title=deck.title,
        subtitle=deck.subtitle,
        company_name=deck.company_name,
        date=deck.date,
        slides=new_slides,
        warnings=list(deck.warnings or []),
    )


__all__ = [
    "DesignError",
    "design_deck",
    "rewrite_slides",
    "PATTERN_SLOTS",
    "BODY_TYPE_DEFAULT_PATTERN",
    "SHAPE_PATTERNS",
    "_build_prompt",
]
