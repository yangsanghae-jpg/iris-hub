"""슬라이드별 machine-readable 형식 계약 (범용).

Stage 1(expand)가 pattern/roles를 마크다운 주석으로 남기고,
Stage 2(design)는 이를 추측하지 않고 그대로 따르며 검증한다.

특정 고객사·SLA·문서 문구 하드코딩 금지.
"""
from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from typing import Any, Literal

from src.engine.output.deck.schema import PATTERN_TEMPLATES

ContractMode = Literal["optional", "required"]

ALLOWED_PATTERNS: frozenset[str] = frozenset(PATTERN_TEMPLATES.keys())

ALLOWED_ROLES: frozenset[str] = frozenset({
    "context", "items", "relation", "sequence", "metrics",
    "comparison", "condition", "exception", "conclusion", "source", "output",
})

# V3.1 body_type 상위 축 — 페이지별 "내용을 어떻게 쓸지"를 명시하는 최상위 형식.
# pattern(구조 레이아웃)은 이 body_type의 하위 선택이다.
ALLOWED_BODY_TYPES: frozenset[str] = frozenset({
    "요약형", "서술형", "표형", "도형형",
})

# 각 pattern이 속하는 정본 body_type. cover는 표지라 body_type에서 면제(None).
PATTERN_BODY_TYPE: dict[str, str | None] = {
    "cover": None,
    "table": "표형",
    "narrative": "서술형",
    "summary": "요약형",
    "agenda": "도형형",
    "exec-summary": "도형형",
    "metrics-row": "도형형",
    "compare-2col": "도형형",
    "card-grid-4": "도형형",
    "phase-roadmap": "도형형",
    "dimension-5": "도형형",
}

PATTERN_MARKER_RE = re.compile(
    r"<!--\s*IRIS_PATTERN:\s*([a-z0-9-]+)\s*-->", re.IGNORECASE,
)
ROLES_MARKER_RE = re.compile(
    r"<!--\s*IRIS_ROLES:\s*([a-z0-9_,\-\s]+)\s*-->", re.IGNORECASE,
)
BODY_MARKER_RE = re.compile(
    r"<!--\s*IRIS_BODY:\s*(요약형|서술형|표형|도형형)\s*-->",
)
# 허용: **핵심 메시지:** / **핵심 메시지** / 핵심 메시지:
KEY_MESSAGE_RE = re.compile(
    r"(?:\*\*)?핵심\s*메시지(?:\*\*)?\s*[:：]?\s*(?:\*\*)?\s*\S+",
    re.IGNORECASE,
)

ALLOWED_COLORS = frozenset({"blue", "orange", "red", "green", "purple"})

# pattern이 함의하는 최소 role — LLM이 빠뜨리면 계약에 보강
PATTERN_IMPLIED_ROLES: dict[str, tuple[str, ...]] = {
    "cover": ("context",),
    "agenda": ("items",),
    "exec-summary": ("comparison",),
    "metrics-row": ("metrics",),
    "compare-2col": ("comparison",),
    "card-grid-4": ("items",),
    "phase-roadmap": ("sequence",),
    "dimension-5": ("relation",),
    "table": ("relation",),
    "narrative": ("context",),
    "summary": ("items",),
}

MAX_TABLE_ROWS = 7
MAX_TABLE_COLS = 6
MAX_TABLE_CELL_CHARS = 1200


class PatternContractError(Exception):
    """형식 계약 위반 — 메시지에 LLM 원문/thinking 넣지 말 것."""


class SlotValidationError(Exception):
    """패턴 슬롯 스키마 위반."""


@dataclass(frozen=True)
class SlideContract:
    index: int  # 0-based
    pattern: str
    roles: tuple[str, ...] = ()
    body: str = ""
    body_type: str | None = None  # 요약형/서술형/표형/도형형 (cover는 None)


PATTERN_CONTRACTS: dict[str, dict[str, Any]] = {
    "cover": {
        "required": ["title"],
        "optional": ["company", "subtitle", "target", "date_version"],
    },
    "agenda": {
        "required": ["title", "items"],
        "min_items": {"items": 2},
        "item_required": {"items": ["title"]},
    },
    "exec-summary": {
        "required": ["title", "left_items", "right_items"],
        "min_items": {"left_items": 1, "right_items": 1},
    },
    "metrics-row": {
        "required": ["title", "metrics"],
        "min_items": {"metrics": 3},
        "max_items": {"metrics": 6},
        "item_required": {"metrics": ["value", "label"]},
    },
    "compare-2col": {
        "required": ["title", "left_items", "right_items"],
        "min_items": {"left_items": 1, "right_items": 1},
    },
    "card-grid-4": {
        "required": ["title", "cards"],
        "optional": ["subtitle", "intro", "outro", "section_title"],
        "min_items": {"cards": 3},
        "max_items": {"cards": 8},
        "item_required": {"cards": ["title"]},
    },
    "phase-roadmap": {
        "required": ["title", "phases"],
        "min_items": {"phases": 3},
        "max_items": {"phases": 8},
        "item_required": {"phases": ["title"]},
    },
    "dimension-5": {
        "required": ["title", "dimensions"],
        "min_items": {"dimensions": 4},
        "max_items": {"dimensions": 8},
        "item_required": {"dimensions": ["label"]},
    },
    "table": {
        "required": ["title", "columns", "rows"],
        "optional": ["subtitle", "footnote"],
        "min_items": {"columns": 2, "rows": 2},
        "max_items": {"columns": 6},
    },
    "narrative": {
        "required": ["title", "paragraphs"],
        "optional": ["subtitle", "key_message"],
        "min_items": {"paragraphs": 1},
        "max_items": {"paragraphs": 5},
    },
    "summary": {
        "required": ["title", "points"],
        "optional": ["subtitle", "key_message"],
        "min_items": {"points": 3},
        "max_items": {"points": 8},
    },
}


def split_slide_bodies(md: str) -> list[str]:
    parts = re.split(r"(?m)^---\s*$", (md or "").strip())
    return [p.strip() for p in parts if p.strip()]


def strip_contract_markers(md: str) -> str:
    """렌더 직전 — IRIS 계약 주석 제거."""
    s = PATTERN_MARKER_RE.sub("", md or "")
    s = ROLES_MARKER_RE.sub("", s)
    s = BODY_MARKER_RE.sub("", s)
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def _parse_roles(raw: str) -> tuple[str, ...]:
    roles: list[str] = []
    for tok in re.split(r"[,\s]+", (raw or "").strip()):
        t = tok.strip().lower()
        if not t:
            continue
        if t not in ALLOWED_ROLES:
            raise PatternContractError(f"허용되지 않은 role: {t}")
        if t not in roles:
            roles.append(t)
    return tuple(roles)


def parse_slide_contract(
    body: str,
    index: int,
    *,
    require_roles: bool = False,
    require_body: bool = False,
) -> SlideContract:
    patterns = PATTERN_MARKER_RE.findall(body)
    if len(patterns) == 0:
        raise PatternContractError(
            f"{index + 1}번 슬라이드에 형식 선언(IRIS_PATTERN)이 없습니다."
        )
    if len(patterns) > 1:
        raise PatternContractError(
            f"{index + 1}번 슬라이드에 형식 선언이 {len(patterns)}개입니다. "
            "정확히 하나여야 합니다."
        )
    pattern = patterns[0].strip().lower()
    if pattern not in ALLOWED_PATTERNS:
        raise PatternContractError(
            f"{index + 1}번 슬라이드의 pattern 값이 허용 목록에 없습니다: {pattern}"
        )

    role_matches = ROLES_MARKER_RE.findall(body)
    if len(role_matches) > 1:
        raise PatternContractError(
            f"{index + 1}번 슬라이드에 IRIS_ROLES 선언이 중복입니다."
        )
    if require_roles and not role_matches:
        raise PatternContractError(
            f"{index + 1}번 슬라이드: IRIS_ROLES 누락"
        )
    roles: tuple[str, ...] = ()
    if role_matches:
        roles = _parse_roles(role_matches[0])
        if require_roles and not roles:
            raise PatternContractError(
                f"{index + 1}번 슬라이드: IRIS_ROLES 비어 있음"
            )

    # pattern이 함의하는 최소 role 보강 (선언은 유지·추가만)
    implied = PATTERN_IMPLIED_ROLES.get(pattern, ())
    if implied:
        merged = list(roles)
        for r in implied:
            if r not in merged:
                merged.append(r)
        roles = tuple(merged)

    # body_type(상위 축) 파싱·검증. pattern과 정본 매핑이 일치해야 한다.
    body_matches = BODY_MARKER_RE.findall(body)
    if len(body_matches) > 1:
        raise PatternContractError(
            f"{index + 1}번 슬라이드에 IRIS_BODY 선언이 중복입니다."
        )
    canonical = PATTERN_BODY_TYPE.get(pattern)
    declared = body_matches[0].strip() if body_matches else None
    if declared is not None and canonical is not None and declared != canonical:
        raise PatternContractError(
            f"{index + 1}번 슬라이드: IRIS_BODY({declared})와 pattern({pattern})이 "
            f"불일치합니다. {pattern} pattern은 body_type '{canonical}'이어야 합니다."
        )
    if require_body and declared is None and canonical is not None:
        raise PatternContractError(
            f"{index + 1}번 슬라이드: IRIS_BODY 선언이 없습니다 "
            f"(요약형/서술형/표형/도형형 중 하나)."
        )
    # 정본값으로 확정 — 선언이 없어도 pattern에서 파생, cover는 None.
    body_type = canonical

    return SlideContract(
        index=index, pattern=pattern, roles=roles, body=body, body_type=body_type,
    )


def parse_pattern_contracts(
    md: str,
    *,
    require_roles: bool = False,
    require_body: bool = False,
) -> list[SlideContract]:
    bodies = split_slide_bodies(md)
    if not bodies:
        raise PatternContractError("슬라이드가 없습니다.")
    return [
        parse_slide_contract(
            b, i, require_roles=require_roles, require_body=require_body,
        )
        for i, b in enumerate(bodies)
    ]


def has_pattern_contracts(md: str) -> bool:
    return bool(PATTERN_MARKER_RE.search(md or ""))


def expected_patterns(md: str) -> list[str]:
    return [c.pattern for c in parse_pattern_contracts(md)]


def contracts_to_api(contracts: list[SlideContract]) -> dict[str, Any]:
    return {
        "version": 1,
        "slides": [
            {
                "index": c.index,
                "pattern": c.pattern,
                "roles": list(c.roles),
                "body_type": c.body_type,
            }
            for c in contracts
        ],
    }


def contracts_from_api(data: dict | None) -> list[SlideContract] | None:
    if not data or not isinstance(data, dict):
        return None
    slides = data.get("slides")
    if not isinstance(slides, list):
        return None
    out: list[SlideContract] = []
    for s in slides:
        if not isinstance(s, dict):
            continue
        idx = int(s.get("index", len(out)))
        pat = str(s.get("pattern", "")).strip().lower()
        roles_raw = s.get("roles") or []
        roles = tuple(str(r).strip().lower() for r in roles_raw if str(r).strip())
        bt = s.get("body_type")
        body_type = str(bt).strip() if bt else PATTERN_BODY_TYPE.get(pat)
        out.append(SlideContract(
            index=idx, pattern=pat, roles=roles, body="", body_type=body_type,
        ))
    return out or None


def _has_markdown_table(body: str) -> bool:
    rows = [ln for ln in body.splitlines() if re.match(r"^\s*\|.+\|\s*$", ln)]
    return len(rows) >= 2


def _looks_ordered_sequence(body: str) -> bool:
    numbered = len(re.findall(r"(?m)^\s*\d+[\.\)]\s+\S+", body))
    return numbered >= 3


def _count_bullet_items(body: str) -> int:
    return len(re.findall(r"(?m)^\s*[-*]\s+\S+", body))


def _has_key_message(body: str) -> bool:
    return bool(KEY_MESSAGE_RE.search(body))


def validate_content_richness(c: SlideContract) -> None:
    """슬라이드별 최소 정보량·핵심 메시지 검증."""
    body = c.body
    if c.pattern != "cover" and not _has_key_message(body):
        raise PatternContractError(
            f"{c.index + 1}번 슬라이드: 핵심 메시지(**핵심 메시지:**) 누락"
        )
    if c.pattern == "phase-roadmap":
        if not _looks_ordered_sequence(body):
            raise PatternContractError(
                f"{c.index + 1}번 슬라이드: phase-roadmap에 3개 이상 단계 필요"
            )
    elif c.pattern == "metrics-row":
        nums = len(re.findall(r"\d", body))
        if nums < 3:
            raise PatternContractError(
                f"{c.index + 1}번 슬라이드: metrics-row에 3개 이상 지표 필요"
            )
    elif c.pattern in ("compare-2col", "exec-summary"):
        if _has_markdown_table(body) or _count_bullet_items(body) >= 2:
            return
        raise PatternContractError(
            f"{c.index + 1}번 슬라이드: comparison 구조(표 또는 대응 항목) 부족"
        )
    elif c.pattern == "card-grid-4":
        if _count_bullet_items(body) < 3:
            raise PatternContractError(
                f"{c.index + 1}번 슬라이드: card-grid-4에 3개 이상 항목 필요"
            )
    elif c.pattern == "dimension-5":
        items = _count_bullet_items(body) + len(re.findall(r"(?m)^\s*\d+[\.\)]", body))
        if items < 4:
            raise PatternContractError(
                f"{c.index + 1}번 슬라이드: dimension-5에 4개 이상 관점 필요"
            )
    elif c.pattern == "table":
        if not _has_markdown_table(body):
            raise PatternContractError(
                f"{c.index + 1}번 슬라이드: table pattern에 마크다운 표 필요"
            )
    elif c.pattern == "summary":
        if _count_bullet_items(body) < 3:
            raise PatternContractError(
                f"{c.index + 1}번 슬라이드: 요약형(summary)에 3개 이상 불릿 필요"
            )
    elif c.pattern == "narrative":
        # 서술형은 표·불릿 나열이 아니라 문장형 단락이어야 한다.
        if _has_markdown_table(body):
            raise PatternContractError(
                f"{c.index + 1}번 슬라이드: 서술형(narrative)에 표가 있습니다. "
                "표형(table)을 쓰세요."
            )
        prose = [
            ln for ln in body.splitlines()
            if len(ln.strip()) >= 30
            and not ln.lstrip().startswith(("-", "*", "#", "|", ">", "<!--"))
        ]
        if len(prose) < 1:
            raise PatternContractError(
                f"{c.index + 1}번 슬라이드: 서술형(narrative)에 문장형 단락 필요"
            )


def validate_semantic_contract(c: SlideContract) -> None:
    """pattern과 roles·본문 구조의 의미 일관성."""
    if c.pattern == "phase-roadmap":
        if "sequence" not in c.roles:
            raise PatternContractError(
                f"{c.index + 1}번 슬라이드: phase-roadmap에 sequence role 필요"
            )
    elif c.pattern == "metrics-row":
        if "metrics" not in c.roles:
            raise PatternContractError(
                f"{c.index + 1}번 슬라이드: metrics-row에 metrics role 필요"
            )
    elif c.pattern in ("compare-2col", "exec-summary"):
        if "comparison" not in c.roles:
            raise PatternContractError(
                f"{c.index + 1}번 슬라이드: {c.pattern}에 comparison role 필요"
            )
    elif c.pattern == "card-grid-4":
        if "items" not in c.roles:
            raise PatternContractError(
                f"{c.index + 1}번 슬라이드: card-grid-4에 items role 필요"
            )
    elif c.pattern == "dimension-5":
        if not (set(c.roles) & {"relation", "items"}):
            raise PatternContractError(
                f"{c.index + 1}번 슬라이드: dimension-5에 relation 또는 items role 필요"
            )
    elif c.pattern == "table":
        if not (set(c.roles) & {"relation", "items", "sequence"}):
            raise PatternContractError(
                f"{c.index + 1}번 슬라이드: table에 relation/items/sequence role 필요"
            )


def validate_expansion_contracts(
    md: str,
    *,
    require_roles: bool = True,
    check_richness: bool = True,
    require_body: bool = False,
) -> list[SlideContract]:
    """②확장 결과의 형식 계약 검증. 통과 시 계약 목록 반환."""
    contracts = parse_pattern_contracts(
        md, require_roles=require_roles, require_body=require_body,
    )
    n_slides = len(split_slide_bodies(md))
    if len(contracts) != n_slides:
        raise PatternContractError(
            f"슬라이드 수({n_slides})와 pattern 선언 수({len(contracts)})가 "
            f"일치하지 않습니다."
        )
    if contracts[0].pattern != "cover":
        raise PatternContractError("첫 슬라이드는 cover 여야 합니다.")
    for c in contracts[1:]:
        if c.pattern == "cover":
            raise PatternContractError(
                f"{c.index + 1}번 슬라이드에 cover가 반복됩니다. "
                "cover는 첫 장만 허용합니다."
            )

    for c in contracts:
        if c.pattern == "card-grid-4" and _has_markdown_table(c.body):
            raise PatternContractError(
                f"{c.index + 1}번 슬라이드: 표 구조가 있는데 card-grid-4로 "
                "지정됐습니다. table·compare-2col·exec-summary 등을 사용하세요."
            )
        if c.pattern == "card-grid-4" and "sequence" in c.roles:
            raise PatternContractError(
                f"{c.index + 1}번 슬라이드: roles에 sequence가 있는데 "
                "card-grid-4입니다. phase-roadmap을 사용하세요."
            )
        if _has_markdown_table(c.body) and c.pattern not in (
            "table", "compare-2col", "exec-summary",
        ):
            raise PatternContractError(
                f"{c.index + 1}번 슬라이드: 표가 있는데 pattern이 {c.pattern}입니다. "
                "table 패턴을 사용하세요."
            )
        validate_semantic_contract(c)
        if check_richness:
            validate_content_richness(c)
    return contracts


def format_contract_block_for_prompt(contracts: list[SlideContract]) -> str:
    lines = [
        "각 슬라이드의 pattern은 이미 룰엔진에서 결정됐다.",
        "pattern을 변경하거나 다시 추측하지 마라.",
        "지정된 pattern의 슬롯만 채워라.",
        "슬라이드 순서와 개수를 유지하라.",
        "",
        "## 강제 패턴 계약 (이 순서·이 pattern만)",
    ]
    for c in contracts:
        roles = ",".join(c.roles) if c.roles else "-"
        bt = c.body_type or "-"
        lines.append(
            f"- 슬라이드 {c.index + 1} → [{bt}] {c.pattern} (roles: {roles})"
        )
    return "\n".join(lines)


def _nonempty_str(v: Any) -> bool:
    return isinstance(v, str) and bool(v.strip())


def _as_list(v: Any) -> list:
    return v if isinstance(v, list) else []


def _slug_key(label: str, used: set[str], index: int = 0) -> str:
    base = re.sub(r"[^a-z0-9]+", "_", (label or "col").lower()).strip("_")
    if not base:
        base = f"col_{index}"
    key = base
    n = 2
    while key in used:
        key = f"{base}_{n}"
        n += 1
    used.add(key)
    return key


def parse_markdown_table(body: str) -> dict[str, Any] | None:
    """본문에서 첫 마크다운 표를 columns/rows dict로 파싱."""
    lines = [ln.strip() for ln in body.splitlines() if re.match(r"^\s*\|.+\|\s*$", ln)]
    if len(lines) < 2:
        return None
    header_cells = [c.strip() for c in lines[0].strip("|").split("|")]
    if not header_cells or not all(header_cells):
        return None
    sep = lines[1]
    if not re.match(r"^\s*\|[\s:|-]+\|\s*$", sep):
        return None
    used: set[str] = set()
    columns = []
    for i, label in enumerate(header_cells):
        columns.append({"key": _slug_key(label, used, i), "label": label})
    rows: list[dict[str, str]] = []
    for ln in lines[2:]:
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if len(cells) != len(columns):
            continue
        row = {columns[i]["key"]: cells[i] for i in range(len(columns))}
        rows.append(row)
    if len(rows) < 2:
        return None
    return {"columns": columns, "rows": rows}


def _table_cell_char_total(data: dict) -> int:
    total = 0
    for row in data.get("rows") or []:
        if isinstance(row, dict):
            total += sum(len(str(v)) for v in row.values())
    return total


def table_needs_split(data: dict) -> bool:
    rows = data.get("rows") or []
    cols = data.get("columns") or []
    if len(rows) > MAX_TABLE_ROWS:
        return True
    if len(cols) > MAX_TABLE_COLS:
        return True
    if _table_cell_char_total(data) > MAX_TABLE_CELL_CHARS:
        return True
    return False


def split_table_slide_data(data: dict) -> list[dict]:
    """큰 표를 여러 table 슬라이드 데이터로 분할. header 반복."""
    if not table_needs_split(data):
        return [data]
    base_title = str(data.get("title") or "표")
    columns = copy.deepcopy(data.get("columns") or [])
    rows = list(data.get("rows") or [])
    chunk_size = MAX_TABLE_ROWS
    chunks: list[list[dict]] = []
    for i in range(0, len(rows), chunk_size):
        chunks.append(rows[i:i + chunk_size])
    total = len(chunks)
    out: list[dict] = []
    for part, chunk in enumerate(chunks, 1):
        title = f"{base_title} ({part}/{total})" if total > 1 else base_title
        out.append({
            "title": title,
            "subtitle": data.get("subtitle", ""),
            "columns": columns,
            "rows": chunk,
            "footnote": data.get("footnote"),
        })
    return out


def validate_table_data(data: dict, *, slide_no: int = 1) -> None:
    cols = _as_list(data.get("columns"))
    rows = _as_list(data.get("rows"))
    if len(cols) < 2 or len(cols) > MAX_TABLE_COLS:
        raise SlotValidationError(
            f"{slide_no}번(table): column은 2~6개, 현재 {len(cols)}개"
        )
    keys: list[str] = []
    for i, col in enumerate(cols):
        if not isinstance(col, dict):
            raise SlotValidationError(f"{slide_no}번(table): columns[{i}] 형식 오류")
        label = col.get("label")
        key = col.get("key")
        if not _nonempty_str(str(label or "")):
            raise SlotValidationError(f"{slide_no}번(table): 빈 header")
        if not _nonempty_str(str(key or "")):
            raise SlotValidationError(f"{slide_no}번(table): columns[{i}].key 누락")
        if key in keys:
            raise SlotValidationError(f"{slide_no}번(table): 중복 column key {key}")
        keys.append(str(key))
    if len(rows) < 2:
        raise SlotValidationError(
            f"{slide_no}번(table): row는 2개 이상, 현재 {len(rows)}개"
        )
    for ri, row in enumerate(rows):
        if not isinstance(row, dict):
            raise SlotValidationError(f"{slide_no}번(table): rows[{ri}] 형식 오류")
        for k in keys:
            if k not in row:
                raise SlotValidationError(
                    f"{slide_no}번(table): rows[{ri}]에 column key '{k}' 누락"
                )


def validate_slide_slots(pattern: str, data: dict, *, slide_no: int = 1) -> None:
    if pattern == "table":
        validate_table_data(data, slide_no=slide_no)
        if not _nonempty_str(data.get("title")):
            raise SlotValidationError(f"{slide_no}번(table): title이 비어 있습니다.")
        return
    if pattern not in PATTERN_CONTRACTS:
        raise SlotValidationError(f"{slide_no}번: 알 수 없는 pattern {pattern}")
    spec = PATTERN_CONTRACTS[pattern]
    data = data or {}

    for key in spec.get("required", []):
        if key not in data or data[key] in (None, "", [], {}):
            raise SlotValidationError(
                f"{slide_no}번({pattern}): 필수 슬롯 누락 또는 비어 있음: {key}"
            )
        if key == "title" and not _nonempty_str(data.get("title")):
            raise SlotValidationError(
                f"{slide_no}번({pattern}): title이 비어 있습니다."
            )

    for key, vmin in (spec.get("min_items") or {}).items():
        items = _as_list(data.get(key))
        if len(items) < vmin:
            raise SlotValidationError(
                f"{slide_no}번({pattern}): {key} 최소 {vmin}개 필요, "
                f"현재 {len(items)}개"
            )
    for key, vmax in (spec.get("max_items") or {}).items():
        items = _as_list(data.get(key))
        if len(items) > vmax:
            raise SlotValidationError(
                f"{slide_no}번({pattern}): {key} 최대 {vmax}개, "
                f"현재 {len(items)}개"
            )

    for key, req_fields in (spec.get("item_required") or {}).items():
        for i, item in enumerate(_as_list(data.get(key))):
            if not isinstance(item, dict):
                if isinstance(item, str) and item.strip():
                    continue
                raise SlotValidationError(
                    f"{slide_no}번({pattern}): {key}[{i}]가 객체가 아닙니다."
                )
            for f in req_fields:
                val = item.get(f)
                if f == "value" and val is not None and str(val).strip() != "":
                    continue
                if not _nonempty_str(val):
                    raise SlotValidationError(
                        f"{slide_no}번({pattern}): {key}[{i}].{f} 누락"
                    )
            color = item.get("color")
            if color is not None and str(color) not in ALLOWED_COLORS:
                raise SlotValidationError(
                    f"{slide_no}번({pattern}): 허용되지 않은 색상 {color}"
                )


def validate_deck_patterns(deck, expected: list[str]) -> None:
    actual = [s.pattern for s in deck.slides]
    if actual != expected:
        raise PatternContractError(
            f"pattern 계약 불일치. expected={expected}, actual={actual}"
        )
    for i, slide in enumerate(deck.slides):
        validate_slide_slots(slide.pattern, slide.data or {}, slide_no=i + 1)


def role_requires_card_intro(roles: tuple[str, ...] | list[str]) -> bool:
    return "context" in roles


def role_requires_card_outro(roles: tuple[str, ...] | list[str]) -> bool:
    return bool(set(roles) & {"condition", "exception", "conclusion", "source"})


def resolve_contracts(
    md_text: str,
    contract_api: dict | None = None,
    *,
    contract_mode: ContractMode = "optional",
) -> tuple[list[SlideContract] | None, list[str] | None]:
    """contract_mode=required이면 계약 필수. optional이면 마커 있을 때만."""
    if contract_mode == "required":
        if contract_api:
            api_contracts = contracts_from_api(contract_api)
            if api_contracts:
                md_contracts = parse_pattern_contracts(
                    md_text, require_roles=True,
                )
                if [c.pattern for c in md_contracts] != [c.pattern for c in api_contracts]:
                    raise PatternContractError("markdown과 contract API 불일치")
                return md_contracts, [c.pattern for c in md_contracts]
        if not has_pattern_contracts(md_text):
            raise PatternContractError(
                "형식 계약(IRIS_PATTERN/IRIS_ROLES)이 없습니다. "
                "8766에서는 계약이 필수입니다."
            )
        contracts = validate_expansion_contracts(md_text, require_roles=True)
        return contracts, [c.pattern for c in contracts]
    if has_pattern_contracts(md_text):
        contracts = validate_expansion_contracts(
            md_text, require_roles=False, check_richness=False,
            require_body=False,
        )
        return contracts, [c.pattern for c in contracts]
    return None, None
