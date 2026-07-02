"""store 계층 데이터 모델 (S1) — DAL 입출력 타입.

탭·엔진은 dict/tuple 대신 이 타입들로 store 와 주고받는다.
경량 dataclass — DB 행과 1:1 대응하되, 계산·표시용 파생 결과는 별도 타입.
"""
from __future__ import annotations

from dataclasses import dataclass, field


# ─── ④ 볼트 행 ────────────────────────────────────────────────────────────
@dataclass
class DocRow:
    doc_id: str
    channel: str                       # doc | chat | web
    ingested_at: str
    source: str | None = None
    original_path: str | None = None
    title: str | None = None
    trust: str = "auto"                # auto | clipped | verified
    status: str = "active"             # active | quarantine | rejected
    industry: str | None = None
    area: str | None = None
    level: str | None = None


@dataclass
class ChunkRow:
    chunk_id: str
    ord: int
    text: str
    page_ref: str | None = None


@dataclass
class DocHit:
    """검색 결과 1건 (문서 단위)."""
    doc_id: str
    title: str | None
    snippet: str
    score: float
    channel: str | None = None


@dataclass
class QueueStats:
    """흐름·데이터 탭 — 대기/처리중/완료 스냅샷."""
    total: int = 0
    pending: int = 0        # K2 미완주 (k2_done_at IS NULL)
    processing: int = 0     # processing_started_at 세팅, 미완주
    done: int = 0           # k2_done_at 세팅
    failed: int = 0         # fail_count > 0


@dataclass
class DistStats:
    """데이터 탭 — 산업·채널 분포."""
    by_channel: dict[str, int] = field(default_factory=dict)
    by_industry: dict[str, int] = field(default_factory=dict)
    by_status: dict[str, int] = field(default_factory=dict)


# ─── ③ 지식 행 ────────────────────────────────────────────────────────────
@dataclass
class ConceptRow:
    concept_id: str                    # canonical snake_case
    canonical: str                     # 표시명
    definition: str | None = None
    trust: str = "candidate"           # candidate | verified
    degree: int = 0
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class ConceptPage:
    """위키 탭 — 개념 페이지(정의 + 근거문서 + 관련개념)."""
    concept: ConceptRow
    aliases: list[str] = field(default_factory=list)
    docs: list[DocRow] = field(default_factory=list)          # 근거 문서
    related: list[ConceptRow] = field(default_factory=list)   # 관련 개념


@dataclass
class GraphNode:
    concept_id: str
    canonical: str
    degree: int
    trust: str


@dataclass
class GraphEdge:
    src_id: str
    dst_id: str
    kind: str
    weight: int


@dataclass
class Graph:
    """그래프 탭 — 개념 노드 + 관계 엣지."""
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
