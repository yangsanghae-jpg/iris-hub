"""K2-lite — 규칙 기반 분류 추천기.

본 모듈은 본문 키워드 매칭으로 industry/area/level과 토픽 키워드를 *추천*만 한다.
사용자가 hub UI에서 검토·수정 후 확정하면 intake.py가 DB에 박는다.

설계 원칙:
  - 외부 의존성 0 (re, collections.Counter만)
  - 결정성: 같은 입력 → 같은 출력 (시드 없음)
  - 매칭 0건이면 None 반환 — placebo 박기 금지
  - 사전 확장은 KEYWORDS dict 한 곳에서만

V2.6.2.7 9 산업 정정 — 진단툴 IND_A~I와 정합:
  industry: A(프로젝트형 제조)/B(반도체)/C(전자조립)/D(디스플레이·신에너지)/
            E(프로세스·화학)/F(소비재·식품)/G(의약품·바이오)/H(자동차·장비)/
            I(정밀 소재·부품)
  area:     planning/strategy/operations/quality/data-ai-sw
  level:    default/exec/manager/team
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Iterable

# ─── 어휘 — 진단툴 server/data/ch1/industry_packs/IND_*.json 정합 (V2.6.2.7) ──

INDUSTRY_LABELS = ["A", "B", "C", "D", "E", "F", "G", "H", "I"]
AREA_LABELS = ["planning", "strategy", "operations", "quality", "data-ai-sw"]
LEVEL_LABELS = ["default", "exec", "manager", "team"]

# 사전 — 키워드 → 라벨. 소문자 비교.
# 한국어/영어/중국어 혼용. 정확 부분 문자열 매칭.
KEYWORDS: dict[str, dict[str, list[str]]] = {
    "industry": {
        "A": [  # 프로젝트형 제조 (ETO/조선·플랜트·항공·국방)
            "프로젝트형", "eto", "engineer-to-order", "조선", "shipbuilding",
            "플랜트", "plant", "항공", "aerospace", "국방", "defense",
            "项目型", "プロジェクト",
        ],
        "B": [  # 반도체
            "반도체", "semiconductor", "wafer", "fab", "foundry",
            "晶圆", "半导体", "lithography", "노광",
        ],
        "C": [  # 전자 조립 (job-shop / SMT / EMS)
            "전자조립", "전자 조립", "smt", "ems", "pcb",
            "job shop", "jobshop", "电子装配", "조립",
        ],
        "D": [  # 디스플레이·신에너지
            "디스플레이", "display", "lcd", "oled", "광전자", "光电子",
            "ln", "lt", "薄膜", "박막", "nanoln", "晶正", "단결정",
            "신에너지", "new energy", "배터리", "battery", "태양광", "solar",
        ],
        "E": [  # 프로세스·화학
            "프로세스", "process industry", "화학", "chemical", "petrochemical",
            "정유", "refinery", "流程", "化工",
        ],
        "F": [  # 소비재·식품
            "소비재", "consumer goods", "fmcg", "식품", "food",
            "음료", "beverage", "消费品", "食品",
        ],
        "G": [  # 의약품·바이오
            "제약", "pharma", "biotech", "바이오", "gmp", "임상",
            "制药", "生物制药",
        ],
        "H": [  # 자동차·장비
            "자동차", "automotive", "auto", "차량", "vehicle",
            "장비", "equipment", "machinery", "汽车", "装备",
        ],
        "I": [  # 정밀 소재·부품
            "정밀", "precision", "소재", "material", "부품", "components",
            "精密", "材料", "零部件",
        ],
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
