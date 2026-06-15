"""K2-lite — 규칙 기반 분류 추천기.

본 모듈은 본문 키워드 매칭으로 industry/area/level과 토픽 키워드를 *추천*만 한다.
사용자가 hub UI에서 검토·수정 후 확정하면 intake.py가 DB에 박는다.

설계 원칙:
  - 외부 의존성 0 (re, collections.Counter만)
  - 결정성: 같은 입력 → 같은 출력 (시드 없음)
  - 매칭 0건이면 None 반환 — placebo 박기 금지
  - 사전 확장은 KEYWORDS dict 한 곳에서만

V2.5 사양 어휘 (구현 시점에 사용자 재확정):
  industry: A(반도체)/B(제조)/C(디스플레이·광전자)/D(제약·바이오)/E(기타)
  area:     planning/strategy/operations/quality/data-ai-sw
  level:    default/exec/manager/team
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Iterable

# ─── 어휘 ────────────────────────────────────────────────────────────────────

INDUSTRY_LABELS = ["A", "B", "C", "D", "E"]
AREA_LABELS = ["planning", "strategy", "operations", "quality", "data-ai-sw"]
LEVEL_LABELS = ["default", "exec", "manager", "team"]

# 사전 — 키워드 → 라벨. 소문자 비교.
# 한국어/영어/중국어 혼용. 정확 부분 문자열 매칭.
KEYWORDS: dict[str, dict[str, list[str]]] = {
    "industry": {
        "A": [
            "반도체", "semiconductor", "wafer", "fab", "foundry",
            "晶圆", "半导体", "lithography", "노광",
        ],
        "B": [
            "mes", "생산실행", "생산 운영", "제조", "manufacturing",
            "공장", "factory", "shop floor", "shopfloor",
        ],
        "C": [
            "디스플레이", "display", "lcd", "oled", "광전자", "光电子",
            "ln", "lt", "薄膜", "박막", "nanoln", "晶正", "단결정",
        ],
        "D": ["제약", "pharma", "biotech", "바이오", "GMP", "임상"],
        "E": [],  # fallback — 매칭 안 되면 None 반환
    },
    "area": {
        "planning": [
            "계획", "planning", "스케줄", "schedule", "ppc",
            "지표", "kpi", "metric", "트리", "tree", "체계",
        ],
        "strategy": [
            "전략", "strategy", "비전", "vision", "로드맵", "roadmap",
            "장기", "포트폴리오", "portfolio",
        ],
        "operations": [
            "운영", "operation", "현장", "실행", "execution",
            "작업", "wo", "work order", "라인", "line", "재고", "inventory",
        ],
        "quality": [
            "품질", "quality", "qc", "qa", "불량", "defect",
            "검사", "inspection", "spc", "yield", "수율",
        ],
        "data-ai-sw": [
            "데이터", "data", "ai", "machine learning", "ml",
            "소프트웨어", "software", "system", "시스템",
            "api", "database", "db", "elt", "etl", "pipeline",
        ],
    },
    "level": {
        "exec": ["경영", "executive", "c-level", "ceo", "cto", "cfo", "임원"],
        "manager": ["관리자", "manager", "팀장", "부서장", "리더", "leader"],
        "team": ["담당자", "operator", "현장", "팀원", "기술자"],
        "default": [],
    },
}

# 명사 빈도 추출용 불용어 (한·영 자주 쓰는 것만 — 점진 확장)
_STOPWORDS = {
    # 한국어
    "그리고", "또한", "하지만", "그러나", "그래서", "따라서", "그", "이", "저",
    "있다", "없다", "이다", "한다", "된다", "하는", "되는",
    "있", "없", "되", "하", "것", "수", "들",
    "또", "및", "위", "후", "전", "내", "외", "중",
    # 영어
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "of", "in", "on", "at", "to", "for", "with", "by", "from",
    "this", "that", "these", "those", "it", "its",
    "as", "if", "than", "then", "so", "such",
}


# ─── 코어 ────────────────────────────────────────────────────────────────────

def _normalize(s: str) -> str:
    return s.lower().strip()


def _count_keyword_hits(text: str, dictionary: dict[str, list[str]]) -> Counter:
    """text 안에 dictionary의 각 라벨 키워드가 몇 번 나오는지 카운트."""
    text_lc = _normalize(text)
    counts: Counter = Counter()
    for label, keywords in dictionary.items():
        for kw in keywords:
            if not kw:
                continue
            # 부분 문자열 매칭 (한·중·영 혼용에서 안전)
            hits = text_lc.count(kw.lower())
            if hits:
                counts[label] += hits
    return counts


def _best_label(counts: Counter) -> tuple[str | None, int]:
    """가장 많이 매칭된 라벨. 동률이면 첫 등장. 매칭 0이면 None."""
    if not counts:
        return None, 0
    label, n = counts.most_common(1)[0]
    return label, n


def extract_keywords(text: str, top_k: int = 5) -> list[str]:
    """본문에서 의미 있는 단어 top_k. 단순 빈도 + 불용어 제거.

    한·중·영 토큰을 길이 ≥ 2로 잘라 빈도순. 점진적 개선 가능.
    """
    text_lc = _normalize(text)
    # 영문/한글/한자 단어 분리. 숫자만 단어 제외.
    tokens = re.findall(r"[A-Za-z가-힣一-鿿]{2,}", text_lc)
    filtered = [t for t in tokens if t not in _STOPWORDS]
    return [w for w, _ in Counter(filtered).most_common(top_k)]


def suggest_classification(title: str, body: str) -> dict:
    """본문 + 제목 기반 분류 추천.

    반환::

        {
          "industry": "C" | None,
          "area":     "planning" | None,
          "level":    "default" | None,
          "keywords": ["nanoln", "지표", ...],
          "confidence": {"industry": 7, "area": 4, "level": 0},
          "raw_counts": {"industry": Counter({...}), ...},
        }

    제목은 본문보다 가중치 2배 (= 같은 키워드가 제목에 있으면 2배 카운트).
    """
    title = title or ""
    body = body or ""
    weighted = (title + "\n") * 2 + body

    industry_counts = _count_keyword_hits(weighted, KEYWORDS["industry"])
    area_counts = _count_keyword_hits(weighted, KEYWORDS["area"])
    level_counts = _count_keyword_hits(weighted, KEYWORDS["level"])

    ind_label, ind_n = _best_label(industry_counts)
    area_label, area_n = _best_label(area_counts)
    lvl_label, lvl_n = _best_label(level_counts)

    return {
        "industry": ind_label,
        "area": area_label,
        "level": lvl_label,
        "keywords": extract_keywords(body or title),
        "confidence": {
            "industry": ind_n,
            "area": area_n,
            "level": lvl_n,
        },
        "raw_counts": {
            "industry": dict(industry_counts),
            "area": dict(area_counts),
            "level": dict(level_counts),
        },
    }


__all__ = [
    "INDUSTRY_LABELS",
    "AREA_LABELS",
    "LEVEL_LABELS",
    "KEYWORDS",
    "suggest_classification",
    "extract_keywords",
]
