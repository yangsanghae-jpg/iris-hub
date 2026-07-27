"""규칙 초과 슬라이드를 결정론적으로 분할·재조정하는 모듈.

LLM 호출 없음. 데이터 삭제·날조 금지. 슬라이드 수가 늘어날 수 있으므로
contracts/expected를 반드시 재생성한다.
"""
from __future__ import annotations

import copy
from typing import Any

from src.engine.output.deck.pattern_contract import (
    PATTERN_CONTRACTS,
    SlideContract,
    split_table_slide_data,
)
from src.engine.output.deck.schema import Deck, Slide

# pattern → 항목 리스트가 담긴 슬롯 키. 분할 로직 전역에서 공유.
_LIST_KEY_MAP: dict[str, str] = {
    "card-grid-4": "cards",
    "phase-roadmap": "phases",
    "dimension-5": "dimensions",
    "metrics-row": "metrics",
    "summary": "points",
    "narrative": "paragraphs",
}


def split_table_by_columns(data: dict, max_cols: int = 6) -> list[dict]:
    """너비 max_cols 초과 표를 max_cols 이하로 열 분할. 첫 열(키)을 모든 청 chunk에 반복."""
    cols = copy.deepcopy(data.get("columns") or [])
    rows = data.get("rows") or []
    if len(cols) <= max_cols:
        return [data]

    key_col = cols[0]
    data_cols = cols[1:]
    chunk_size = max_cols - 1  # 키 1 + 데이터 max_cols-1 = max_cols

    total = (len(data_cols) + chunk_size - 1) // chunk_size
    chunks: list[dict] = []

    for part in range(total):
        start = part * chunk_size
        end = min(start + chunk_size, len(data_cols))
        chunk_cols = [key_col] + data_cols[start:end]

        # rows에서 해당 열만 투영
        keep_keys = [key_col["key"]] + [c["key"] for c in chunk_cols[1:]]
        chunk_rows = []
        for row in rows:
            chunk_row = {k: row.get(k) for k in keep_keys}
            chunk_rows.append(chunk_row)

        base_title = str(data.get("title") or "표")
        title = f"{base_title} ({part + 1}/{total})" if total > 1 else base_title

        chunk_data = {
            "title": title,
            "subtitle": data.get("subtitle", ""),
            "columns": chunk_cols,
            "rows": chunk_rows,
        }
        # footnote은 마지막 청 chunk에만
        if part == total - 1 and data.get("footnote"):
            chunk_data["footnote"] = data["footnote"]
        chunks.append(chunk_data)

    return chunks


def split_items_slide(slide: Slide, max_n: int) -> list[Slide]:
    """항목이 max_n 초과인 슬라이드를 max_n 이하씩 분할."""
    data = (slide.data or {}).copy()
    pattern = slide.pattern

    list_key = _LIST_KEY_MAP.get(pattern)
    if not list_key:
        return [slide]

    items = data.get(list_key) or []
    if len(items) <= max_n:
        return [slide]

    total = (len(items) + max_n - 1) // max_n
    new_slides: list[Slide] = []

    for part in range(total):
        start = part * max_n
        end = min(start + max_n, len(items))
        chunk_items = items[start:end]

        base_title = str(data.get("title") or "")
        title = f"{base_title} ({part + 1}/{total})" if total > 1 else base_title

        chunk_data = data.copy()
        chunk_data[list_key] = chunk_items
        chunk_data["title"] = title

        if pattern == "card-grid-4":
            if part != 0:
                chunk_data.pop("intro", None)
            if part != total - 1:
                chunk_data.pop("outro", None)
        elif pattern in ("phase-roadmap", "dimension-5"):
            if part != total - 1:
                chunk_data.pop("footer_note", None)

        if part == 0:
            chunk_data["subtitle"] = data.get("subtitle", "")
        else:
            chunk_data.pop("subtitle", None)
        if part == total - 1:
            chunk_data["footnote"] = data.get("footnote", "")
        else:
            chunk_data.pop("footnote", None)

        new_slides.append(Slide(
            pattern=pattern,
            data=chunk_data,
        ))

    return new_slides


def _get_max_n_for_pattern(pattern: str) -> int | None:
    """PATTERN_CONTRACTS에서 해당 패턴의 max_n을 읽는다."""
    spec = PATTERN_CONTRACTS.get(pattern, {})
    max_items = spec.get("max_items", {})
    list_key = _LIST_KEY_MAP.get(pattern)
    return max_items.get(list_key) if list_key else None


def reconcile_deck(
    deck: Deck,
    contracts: list[SlideContract] | None,
) -> tuple[Deck, list[SlideContract] | None, list[str]]:
    """규칙 초과 슬라이드를 분할·재배치해 규칙에 맞는 새 Deck을 만든다.

    반환: (새 deck, 재생성된 contracts, 변경 로그(warnings))
    - 결정론적. LLM 호출 없음. 데이터 삭제·날조 금지.
    - 슬라이드 수가 늘어날 수 있으므로 contracts/expected를 반드시 재생성한다.
    """
    new_slides: list[Slide] = []
    origins: list[int] = []  # new_slides[i]가 유래한 원본 slide_index
    warnings: list[str] = []

    for slide_index, slide in enumerate(deck.slides):
        # cover는 조정 대상 아님
        if slide.pattern == "cover":
            new_slides.append(slide)
            origins.append(slide_index)
            continue

        data = slide.data or {}
        cols = data.get("columns") or []
        rows = data.get("rows") or []

        produced: list[Slide] | None = None

        # 1. 표 계열 — 열 분할과 행 분할을 체이닝(중첩) 적용
        if cols and (len(cols) > 6 or len(rows) > 7):
            col_chunks = split_table_by_columns(data) if len(cols) > 6 else [data]
            need_row_split = len(rows) > 7
            table_slides: list[Slide] = []
            for chunk in col_chunks:
                row_chunks = split_table_slide_data(chunk) if need_row_split else [chunk]
                for rc in row_chunks:
                    table_slides.append(Slide(pattern=slide.pattern, data=rc))
            if len(table_slides) > 1:
                produced = table_slides
                reasons = []
                if len(cols) > 6:
                    reasons.append(f"{len(cols)}열")
                if len(rows) > 7:
                    reasons.append(f"{len(rows)}행")
                warnings.append(
                    f"슬라이드 {slide_index + 1}({slide.pattern}): "
                    f"{'·'.join(reasons)} 표를 {len(table_slides)}개 슬라이드로 분할"
                )

        # 2. 항목 과다 패턴 분할 (표 분할이 적용되지 않은 경우만)
        if produced is None:
            max_n = _get_max_n_for_pattern(slide.pattern)
            if max_n:
                result = split_items_slide(slide, max_n)
                if len(result) > 1:
                    produced = result
                    list_key = _LIST_KEY_MAP.get(slide.pattern)
                    item_count = len(data.get(list_key) or []) if list_key else 0
                    warnings.append(
                        f"슬라이드 {slide_index + 1}({slide.pattern}): "
                        f"항목 {item_count}개를 {len(result)}개 슬라이드로 분할"
                    )

        if produced is None:
            produced = [slide]

        new_slides.extend(produced)
        origins.extend([slide_index] * len(produced))

    # 3. 새 덱 생성 + contracts/expected 재생성
    new_deck = Deck(
        title=deck.title,
        subtitle=deck.subtitle,
        company_name=deck.company_name,
        date=deck.date,
        slides=new_slides,
        warnings=list(deck.warnings),
    )

    # contracts 재생성 — origins로 각 새 슬라이드의 "진짜" 원본 계약을 추적해
    # roles/body/body_type을 정확히 상속한다(단순 min(i, len-1) 매핑은 분할이
    # 여러 슬라이드에 걸치면 뒤쪽 인덱스에서 엉뚱한 계약을 붙이는 버그가 있었음).
    #
    # pattern은 반드시 원본 계약(contracts[origins[i]].pattern)에서 가져와야
    # 한다 — new_slides[i].pattern(실제 생성된 슬라이드의 패턴)을 쓰면, 이후
    # validate_deck_patterns(deck, expected)가 "실제 패턴 vs 실제 패턴에서
    # 파생한 expected"를 비교하는 자기참조가 되어 패턴 불일치 검증이 무력화된다.
    # 분할된 슬라이드는 원래 원본과 같은 pattern을 유지하므로(분할 로직이
    # pattern을 바꾸지 않음) 이 값은 분할 여부와 무관하게 항상 올바르다.
    new_contracts: list[SlideContract] | None = None
    if contracts:
        new_contracts = [SlideContract(
            index=i,
            pattern=contracts[origins[i]].pattern,
            roles=contracts[origins[i]].roles,
            body=contracts[origins[i]].body,
            body_type=contracts[origins[i]].body_type,
        ) for i in range(len(new_slides))]

    return new_deck, new_contracts, warnings


def fallback_slide(
    slide: Slide,
    contract: SlideContract | None,
    source_body: str,
) -> tuple[Slide, str]:
    """검증 불가 슬라이드를 안전 패턴(summary 또는 narrative)으로 강등.

    - 표/도형형 데이터가 깨졌으면 -> summary(핵심 불릿) 또는 narrative(문단).
    - title은 유지. 데이터에서 추출 가능한 텍스트를 불릿/문단으로 재구성(날조 금지).
    - 아무 텍스트도 못 살리면 source_body에서 문장을 뽑아 narrative로.
    """
    data = slide.data or {}
    title = str(data.get("title") or "")
    subtitle = str(data.get("subtitle") or "")

    # 이미 유효한 항목 데이터가 있으면 summary로 복원
    points: list[str] = []
    for key in ("cards", "phases", "dimensions", "metrics", "points", "paragraphs"):
        items = data.get(key)
        if isinstance(items, list):
            for item in items:
                if isinstance(item, str) and item.strip():
                    points.append(item.strip())
                elif isinstance(item, dict):
                    item_title = item.get("title") or item.get("label") or ""
                    if item_title:
                        points.append(str(item_title))
                    for subkey in ("detail", "subtitle", "content", "key_message"):
                        sub = item.get(subkey)
                        if sub and str(sub).strip():
                            points.append(str(sub).strip())
    if points:
        return Slide(
            pattern="summary",
            data={"title": title, "points": points, "subtitle": subtitle},
        ), f"슬라이드 강등(summary): 검증 실패로 summary로 변환"

    # source_body에서 문장 추출하여 narrative로
    prose = [
        ln.strip()
        for ln in source_body.splitlines()
        if len(ln.strip()) >= 5
        and not ln.strip().startswith(("-", "*", "#", "|", ">", "<!--"))
    ]
    if prose:
        return Slide(
            pattern="narrative",
            data={"title": title, "paragraphs": prose[:5], "subtitle": subtitle},
        ), f"슬라이드 강등(narrative): 검증 실패로 narrative로 변환"

    # 완전히 빈 데이터 -> summary + 빈 불릿
    return Slide(
        pattern="summary",
        data={"title": title, "points": []},
    ), f"슬라이드 강등(summary): 데이터 손실로 빈 summary 생성"


__all__ = [
    "reconcile_deck",
    "split_table_by_columns",
    "split_items_slide",
    "fallback_slide",
]
