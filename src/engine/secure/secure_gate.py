"""Secure Lane 차단 게이트 (V2.6 Phase 2).

V2.5.1 §2.A: "Secure 영역 임베딩 / MCP / 인덱싱 금지" 정책 흡수.

게이트 6단:
  K1 (Intake)     — secure 등록 시 RuntimeError (별도 secure_intake.py 없으면 차단)
  K2 (Cleansing)  — K2는 K1a~c 의존, 본 사이클 외 (V2.6 추후)
  K3 (Classify)   — matrix key 부여 직전 secure 차단
  K4 (Store)      — chunks 진입 거부
  K5 (Retrieval)  — 결과셋 필터 + X-IRIS-Secure-Excluded 헤더
  K6 (Curate)     — Trigger A/B/C 입력 제외 (이미 curate.py에 박힘)

환경변수 토글 (V2.5.1 §10 롤백 정책):
  IRIS_SECURE_GATE=off  → 게이트 전면 비활성 (테스트/회복용)
"""
from __future__ import annotations

import os

SECURE_LANE = "secure"


def is_gate_active() -> bool:
    """기본 ON. IRIS_SECURE_GATE=off 시 OFF."""
    return os.environ.get("IRIS_SECURE_GATE", "on").lower() != "off"


def assert_not_secure(lane: str, stage: str, doc_id: str | None = None) -> None:
    """K1/K3/K4 진입점에서 호출. secure lane 진입 시 RuntimeError.

    `stage`는 어느 게이트에서 차단됐는지 추적 (K1/K3/K4).
    """
    if not is_gate_active():
        return
    if lane == SECURE_LANE:
        suffix = f" (doc_id={doc_id})" if doc_id else ""
        raise RuntimeError(
            f"[SECURE GATE/{stage}] lane='secure' 진입 차단 — "
            f"의도적 secure 등록은 별도 apps/ingest/secure_intake.py 사용{suffix}"
        )


def filter_secure_rows(rows: list[dict], lane_field: str = "lane") -> tuple[list[dict], int]:
    """K5 응답에서 secure 행 제거.

    Returns: (filtered_rows, excluded_count)
    """
    if not is_gate_active():
        return rows, 0
    kept = [r for r in rows if r.get(lane_field) != SECURE_LANE]
    excluded = len(rows) - len(kept)
    return kept, excluded


def assert_chunk_lane(conn, doc_id: str, stage: str = "K4") -> None:
    """K4 chunks 등록 직전 호출. documents.lane이 secure면 차단.

    raw_intake/reference_diagnosis는 모듈 상수로 lane 고정이라 K1에서 차단되지만,
    별도 chunks 직접 등록 경로(예: K6 Curate 미래 구현)에서 안전망.
    """
    if not is_gate_active():
        return
    row = conn.execute("SELECT lane FROM documents WHERE doc_id=?", (doc_id,)).fetchone()
    if row is None:
        return
    lane = row[0] if isinstance(row, tuple) else row["lane"]
    if lane == SECURE_LANE:
        raise RuntimeError(
            f"[SECURE GATE/{stage}] doc_id={doc_id} is in secure lane — chunks 진입 차단"
        )
