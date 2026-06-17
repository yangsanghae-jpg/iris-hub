"""Origin auto-judgment (V2.6 Phase 3 — Echo Chamber 차단).

Spec V2.5.1 §2.D, §7 Phase 3.1.

Rules:
  - User Drop (raw/, manual upload)             → 'human'
  - External reference (no-copy, verified)      → 'human'
  - LLM-generated wiki (K6 Curate output)       → 'ai'
  - Human-edited LLM output (K6 Reviewer pass)  → 'hybrid'
"""
from __future__ import annotations

from enum import Enum


class IngestSource(str, Enum):
    USER_DROP = "user_drop"            # raw_intake.py — sources from knowledge/raw/
    REFERENCE = "reference"            # reference_diagnosis.py — external no-copy
    LLM_GENERATED = "llm_generated"    # K6 Curate output (future)
    LLM_REVIEWED = "llm_reviewed"      # K6 Curate output + human Reviewer (future)


_SOURCE_TO_ORIGIN: dict[IngestSource, str] = {
    IngestSource.USER_DROP: "human",
    IngestSource.REFERENCE: "human",
    IngestSource.LLM_GENERATED: "ai",
    IngestSource.LLM_REVIEWED: "hybrid",
}


def origin_for(source: IngestSource) -> str:
    """Return one of {'human', 'ai', 'hybrid'}."""
    return _SOURCE_TO_ORIGIN[source]
