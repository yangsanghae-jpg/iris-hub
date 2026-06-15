"""Tests for classify.py — 규칙 분류기 결정성·매칭 회귀."""
from src.classify import (
    INDUSTRY_LABELS,
    AREA_LABELS,
    LEVEL_LABELS,
    suggest_classification,
    extract_keywords,
)


# ─── 매칭 케이스 ──────────────────────────────────────────────────────────────

def test_nanoln_korean_matches_industry_C_planning():
    """Nanoln (LN/LT 단결정 박막 광전자) → C, planning."""
    title = "LN/LT 単晶薄膜 광전자 半导体企业 Nanoln 생산운영 지표 체계"
    body = "본 체계는 Nanoln 박막 KPI 트리 (L0~L4 완전체) — 지표 분해 및 책임 추적."
    r = suggest_classification(title, body)
    assert r["industry"] == "C"
    assert r["area"] == "planning"
    assert r["confidence"]["industry"] >= 2
    assert r["confidence"]["area"] >= 1


def test_mes_korean_matches_industry_B_operations():
    """MES 생산실행 시스템 → B, operations."""
    title = "MES 생산실행 시스템 핵심 개념"
    body = "MES는 공장 현장의 작업지시(WO)와 라인 운영을 관리한다."
    r = suggest_classification(title, body)
    assert r["industry"] == "B"
    assert r["area"] == "operations"


def test_semiconductor_english_matches_industry_A():
    """Semiconductor wafer fab → A."""
    title = "Wafer fab yield analysis"
    body = "Foundry semiconductor lithography yields improved by 3%."
    r = suggest_classification(title, body)
    assert r["industry"] == "A"


def test_data_ai_matches_area():
    """데이터·AI·소프트웨어 영역."""
    title = "RAG 파이프라인 설계"
    body = "데이터 인덱스와 AI 모델로 검색 파이프라인을 구축한다. API와 DB 연동."
    r = suggest_classification(title, body)
    assert r["area"] == "data-ai-sw"


def test_strategy_match():
    title = "장기 전략 로드맵 v2"
    body = "비전과 포트폴리오 전략을 정리한다."
    r = suggest_classification(title, body)
    assert r["area"] == "strategy"


def test_quality_match():
    title = "품질 지표 SPC"
    body = "검사 데이터로 수율과 불량률을 관리한다."
    r = suggest_classification(title, body)
    assert r["area"] == "quality"


# ─── 매칭 없음 ────────────────────────────────────────────────────────────────

def test_unrelated_text_returns_none():
    """매칭 0건이면 None — placebo 박기 금지."""
    title = "오늘 점심 메뉴"
    body = "라면도 좋고 김밥도 좋다."
    r = suggest_classification(title, body)
    assert r["industry"] is None
    assert r["area"] is None
    assert r["level"] is None
    assert r["confidence"]["industry"] == 0


# ─── 가중치 ───────────────────────────────────────────────────────────────────

def test_title_weighted_more_than_body():
    """제목 키워드는 본문보다 가중치 2배."""
    # 본문엔 'mes' 1번, 'data' 3번 — 본문만 보면 area=data-ai-sw
    # 제목엔 'operations' 1번 → 가중 2배로 area=operations 이겨야 함
    title = "MES operations 운영 계획"
    body = "AI 데이터 데이터 데이터 — 단순 통계 분석."
    r = suggest_classification(title, body)
    assert r["industry"] == "B"   # mes는 industry B 키워드, 제목 가중치로 우세
    # area: title의 operations·운영·계획 vs body의 data·통계·분석
    # 제목 weighting으로 operations/planning 쪽이 우세해야
    assert r["area"] in ("operations", "planning")


# ─── 결정성 ───────────────────────────────────────────────────────────────────

def test_deterministic_same_input_same_output():
    """결정성 — 같은 입력 두 번 호출 → 같은 결과."""
    title = "MES 생산실행 시스템 개요"
    body = "공장 라인 운영 및 작업지시 흐름."
    r1 = suggest_classification(title, body)
    r2 = suggest_classification(title, body)
    assert r1 == r2


# ─── extract_keywords ────────────────────────────────────────────────────────

def test_extract_keywords_returns_top_n():
    text = "MES 시스템 시스템 시스템 라인 라인 작업 작업 작업 작업 운영"
    kws = extract_keywords(text, top_k=3)
    assert "작업" in kws
    assert len(kws) == 3


def test_extract_keywords_filters_stopwords():
    text = "이 시스템은 그리고 또한 데이터 데이터 데이터 분석 분석"
    kws = extract_keywords(text)
    assert "그리고" not in kws
    assert "또한" not in kws
    assert "데이터" in kws


# ─── 어휘 노출 ────────────────────────────────────────────────────────────────

def test_label_lists_nonempty():
    """UI selectbox용 라벨 리스트가 비어있지 않은지."""
    assert len(INDUSTRY_LABELS) >= 3
    assert len(AREA_LABELS) >= 3
    assert len(LEVEL_LABELS) >= 3
    assert "C" in INDUSTRY_LABELS
    assert "planning" in AREA_LABELS
    assert "default" in LEVEL_LABELS
