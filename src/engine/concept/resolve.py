"""engine/concept/resolve — 자유텍스트 개념 → canonical concept_id 정규화 (S4 §2).

사전 매칭(store.knowledge, 다국어 병합)이 1차, 폴백 정규화(표기 변형)가 2차.
stopwords·길이·숫자는 거부. conceptize(§3)와 위키(S5)·그래프(S6)가 공유하는 단일 원천.
"""
from __future__ import annotations

import functools
import re
import sqlite3
import unicodedata

from src import config
from src.store import knowledge

_PUNCT = re.compile(r"[\s.\-_/()\[\]{}·,:;'\"]+")


def normalize_key(raw: str) -> str:
    """폴백 정규화 키: NFKC → 소문자 → 공백·기호 제거. 후보 dedup·재조회 공용."""
    s = unicodedata.normalize("NFKC", raw or "").lower().strip()
    return _PUNCT.sub("", s)


@functools.lru_cache(maxsize=1)
def _load_stopwords() -> frozenset[str]:
    """배포된 concepts.yaml → stopwords. 없으면 repo 시드 폴백."""
    try:
        import yaml
    except ImportError:
        return frozenset()
    for path in (config.IRIS_CONCEPTS_YAML, config.CONCEPTS_SEED_YAML):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except (FileNotFoundError, OSError):
            continue
        words = data.get("stopwords") or []
        if words:
            return frozenset(normalize_key(w) for w in words)
    return frozenset()


def is_rejected(raw: str) -> bool:
    """개념화 거부 대상: 길이<2 · 순수 숫자 · stopword."""
    s = (raw or "").strip()
    if len(s) < 2 or s.isdigit():
        return True
    return normalize_key(s) in _load_stopwords()


def resolve(raw: str, conn: sqlite3.Connection | None = None) -> str | None:
    """개념 → canonical concept_id. 거부·미매칭이면 None.

    1) 거부 필터, 2) 사전 직접 매칭, 3) 폴백 정규화 후 재매칭.
    """
    if is_rejected(raw):
        return None
    cid = knowledge.resolve_concept(raw, conn=conn)
    if cid:
        return cid
    key = normalize_key(raw)
    if key and key != raw.strip().lower():
        cid = knowledge.resolve_concept(key, conn=conn)
        if cid:
            return cid
    return None
