"""Secure 영역 명시적 등록기 (V2.6 Phase 2 백도어).

V2.5.1 §2.A: "Secure 영역 임베딩 / MCP / 인덱싱 금지"
→ 일반 ingest 경로는 secure_gate에서 차단. 본 모듈은 그 유일한 합법 우회로.

사용 패턴:
  - 사용자가 명시적으로 secure 분류를 의도한 경우만
  - 호출 시 IRIS_SECURE_GATE 토글 무관하게 secure 행 생성
  - K4 chunks 비등록 (검색·임베딩 자체 차단), documents만 메타데이터로 남김
  - K5 응답에서는 자동 필터 (secure_gate.filter_secure_rows)
  - K6 Curate 입력에서 제외 (curate.py의 lane != 'secure' 절)

V2.6 후반에 Reviewer 단계 추가 시 본 모듈에 승인 흐름 박음.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def register_secure_document(
    conn: sqlite3.Connection,
    doc_id: str,
    path: Path | str,
    title: str,
    *,
    industry: str | None = None,
    area: str | None = None,
    level: str | None = None,
    kind: str = "source",
    origin: str = "human",
) -> None:
    """secure lane 문서를 documents에만 등록 (chunks 비등록).

    secure 정책:
      - K1 게이트 우회 (정당한 유일 경로)
      - K4 chunks 비등록 → FTS5/임베딩 차단
      - K5 응답에서 자동 제외 (lane='secure' 필터)
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    conn.execute(
        """INSERT INTO documents
             (doc_id, path, lane, trust, industry, area, level, title, fetched_at, kind, origin)
           VALUES (?, ?, 'secure', 'verified', ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(doc_id) DO UPDATE SET
             path=excluded.path,
             industry=excluded.industry,
             area=excluded.area,
             level=excluded.level,
             title=excluded.title,
             fetched_at=excluded.fetched_at,
             kind=excluded.kind,
             origin=excluded.origin,
             lane='secure'""",
        (doc_id, str(path), industry, area, level, title, now, kind, origin),
    )
    # secure는 chunks 비등록 — 기존 chunks가 있으면 (다른 lane→secure 강등) 제거
    conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
