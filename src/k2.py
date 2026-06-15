"""K2 Cleansing — LLM 본문 분석 (V2.5 §3.4).

본 모듈은 raw 자료를 *진짜* 분석한다 (규칙 매칭이 아니라 본문 이해).
qwen3:8b로 JSON 모드 호출 → industry/area/level + summary/topics/entities.

흐름:
  1. _build_prompt(title, body) — 어휘 정의 + 자료 + 출력 스키마
  2. llm.generate_json() — Ollama API 호출
  3. _validate(data) — 필수 키 + 어휘 enforce
  4. 반환: K2Result (Pydantic 안 씀, dataclass)

실패 정책:
  - LLM 실패 → 규칙 fallback (classify.suggest_classification)
  - JSON 파싱 실패 → 규칙 fallback
  - 어휘 위반 (예: industry=Z) → None으로 강등 후 raw 보존
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any

from src import llm
from src.config import IRIS_LLM_DEEP
from src.classify import (
    INDUSTRY_LABELS,
    AREA_LABELS,
    LEVEL_LABELS,
    suggest_classification,
)

K2_SCHEMA_VERSION = "v1"


def _k2_version(model: str) -> str:
    """모델명을 박은 버전 문자열. document_meta.classifier_version 추적용."""
    return f"k2-{model}-{K2_SCHEMA_VERSION}"


K2_VERSION = _k2_version(IRIS_LLM_DEEP)


@dataclass
class K2Result:
    industry: str | None = None
    area: str | None = None
    level: str | None = None
    summary: str = ""
    topics: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    concepts: list[str] = field(default_factory=list)
    reason: str = ""
    confidence: float = 0.0
    elapsed_ms: int = 0
    classifier_version: str = ""
    fallback_used: bool = False
    error: str | None = None

    def __post_init__(self) -> None:
        if not self.classifier_version:
            self.classifier_version = K2_VERSION

    def as_db_row(self, doc_id: str) -> dict[str, Any]:
        """document_meta INSERT용."""
        return {
            "doc_id": doc_id,
            "summary": self.summary,
            "topics_json": json.dumps(self.topics, ensure_ascii=False),
            "entities_json": json.dumps(self.entities, ensure_ascii=False),
            "concepts_json": json.dumps(self.concepts, ensure_ascii=False),
            "classifier_version": self.classifier_version,
            "confidence": self.confidence,
            "reason": self.reason,
        }


def _build_prompt(title: str, body: str, max_body: int = 4000) -> str:
    """본문이 길면 앞 4000자만 사용 (qwen3:8b context 절약).

    프롬프트 핵심:
      - 어휘 정의 명확히
      - JSON 스키마 강제
      - "다른 말 금지" — qwen이 chain-of-thought 안 흘리게
    """
    body_excerpt = body[:max_body] + ("\n... (생략)" if len(body) > max_body else "")

    return f"""당신은 IRIS 지식 분류기입니다. 자료를 읽고 JSON으로만 답하세요.

## 산업 (industry)
- A: 반도체, 웨이퍼, fab, foundry, 노광
- B: 일반 제조, MES, 공장, 생산실행, 작업지시(WO), 라인
- C: 디스플레이, LCD, OLED, 광전자, LN/LT 박막, 단결정
- D: 제약, 바이오, GMP, 임상
- E: 위 분류에 안 맞으면 E

## 영역 (area)
- planning: 계획, KPI, 지표, 트리, 체계
- strategy: 전략, 비전, 로드맵, 포트폴리오
- operations: 운영, 현장, 라인, 재고, 작업지시 실행
- quality: 품질, 검사, SPC, 수율, 불량
- data-ai-sw: 데이터, AI, 소프트웨어, API, DB, 파이프라인

## 수준 (level)
- exec: 경영진·임원
- manager: 관리자·팀장
- team: 현장 담당자
- default: 위에 안 맞으면 default

## 자료
제목: {title}

본문:
{body_excerpt}

## 출력 (JSON만, 다른 말 절대 금지)
{{
  "industry": "A|B|C|D|E",
  "area": "planning|strategy|operations|quality|data-ai-sw",
  "level": "exec|manager|team|default",
  "summary": "한 문장 요약",
  "topics": ["주요 주제 5개 이내"],
  "entities": ["고유명사·기관명"],
  "concepts": ["핵심 개념"],
  "reason": "분류 이유 한 줄",
  "confidence": 0.0~1.0
}}
"""


def _validate(data: dict[str, Any]) -> dict[str, Any]:
    """LLM 응답을 어휘로 강제. 위반 시 None으로 강등."""
    ind = data.get("industry")
    if ind not in INDUSTRY_LABELS:
        ind = None

    area = data.get("area")
    if area not in AREA_LABELS:
        area = None

    lvl = data.get("level")
    if lvl not in LEVEL_LABELS:
        lvl = None

    def _str_list(v) -> list[str]:
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()][:10]
        if isinstance(v, str):
            return [v.strip()] if v.strip() else []
        return []

    return {
        "industry": ind,
        "area": area,
        "level": lvl,
        "summary": str(data.get("summary", ""))[:500],
        "topics": _str_list(data.get("topics", [])),
        "entities": _str_list(data.get("entities", [])),
        "concepts": _str_list(data.get("concepts", [])),
        "reason": str(data.get("reason", ""))[:300],
        "confidence": float(data.get("confidence", 0.0) or 0.0),
    }


def analyze(title: str, body: str, *, timeout: float = 60.0) -> K2Result:
    """K2 Cleansing — LLM 분석 (deep 슬롯).

    실패 시 규칙 fallback (classify.suggest_classification).
    모델은 config.IRIS_LLM_DEEP 환경변수로 결정 (M2 기본 qwen3:8b, M5는 override).
    """
    if not body or not body.strip():
        return K2Result(error="empty body", fallback_used=True)

    prompt = _build_prompt(title, body)
    resp = llm.generate_json(prompt, role="deep", timeout=timeout)
    used_model = resp.get("model", IRIS_LLM_DEEP)

    if not resp.get("ok"):
        # Fallback — 규칙 매칭
        rule = suggest_classification(title, body)
        return K2Result(
            industry=rule.get("industry"),
            area=rule.get("area"),
            level=rule.get("level"),
            topics=rule.get("keywords", []),
            summary=f"(규칙 fallback: {resp.get('error', 'unknown')})",
            reason="LLM 호출 실패, 규칙 매칭 사용",
            confidence=0.3,
            elapsed_ms=resp.get("ms", 0),
            classifier_version="rule-fallback",
            fallback_used=True,
            error=resp.get("error"),
        )

    validated = _validate(resp.get("data", {}))
    return K2Result(
        industry=validated["industry"],
        area=validated["area"],
        level=validated["level"],
        summary=validated["summary"],
        topics=validated["topics"],
        entities=validated["entities"],
        concepts=validated["concepts"],
        reason=validated["reason"],
        confidence=validated["confidence"],
        elapsed_ms=resp.get("ms", 0),
        classifier_version=_k2_version(used_model),
        fallback_used=False,
    )


__all__ = ["K2Result", "analyze", "K2_VERSION", "K2_SCHEMA_VERSION"]
