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

K2_SCHEMA_VERSION = "v4"


def _k2_version(model: str) -> str:
    """모델명을 박은 버전 문자열. document_meta.classifier_version 추적용."""
    return f"k2-{model}-{K2_SCHEMA_VERSION}"


K2_VERSION = _k2_version(IRIS_LLM_DEEP)


# ─── 위키 3-파트 멀티라벨 어휘 (V2.6.2.8 — system·mgmt 풍부화) ──────────
AUTOMATION_LEVELS = {"auto1", "auto2", "auto3", "aiplus"}

# 시스템 도메인 20개 — 진단툴 systems_catalog 정합 + 알다 운영 어휘.
# enforce는 20개로 *넓게*, UI는 Top-N으로 *좁게* (위키 탭 정책).
SYSTEM_DOMAINS = {
    # 계획·실행 (4)
    "APS", "MES", "MOM", "WES",
    # 전사 (3)
    "ERP", "PLM", "EAM",
    # 품질·추적 (3)
    "QMS", "LIMS", "Historian",
    # 물류·공급망 (3)
    "WMS", "TMS", "SCM",
    # 데이터·자동화 (4)
    "SCADA", "HMI", "BI", "RPA",
    # MES 보조 (3)
    "EAP", "FDC", "SPC",
}

# 관리 카테고리 14개 — risk·change·comm 추가.
MGMT_CATEGORIES = {
    # 조직 (2)
    "org_design", "org_role",
    # 거버넌스 (4)
    "gov_committee", "gov_kpi", "gov_policy", "gov_audit",
    # 실행계획 (3)
    "exec_phase", "exec_milestone", "exec_resource",
    # 변화·리스크 (3)
    "change_management", "risk_mitigation", "stakeholder_alignment",
    # 커뮤니케이션 (2)
    "comm_reporting", "comm_escalation",
}


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
    # 위키 3-파트 멀티라벨
    automation_levels: list[str] = field(default_factory=list)
    system_domains: list[str] = field(default_factory=list)
    mgmt_categories: list[str] = field(default_factory=list)
    blurb_industry: str = ""
    blurb_system: str = ""
    blurb_mgmt: str = ""

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

## 산업 (industry, 단일) — 진단툴 IND_A~I 정합
- A: 프로젝트형 제조 (ETO, 조선·플랜트·항공·국방)
- B: 반도체 제조 (wafer, fab, foundry, 노광)
- C: 전자 조립 제조 (SMT, EMS, PCB, job-shop)
- D: 디스플레이·신에너지 제조 (LCD, OLED, 박막, 배터리, 태양광)
- E: 프로세스·화학 제조 (정유, petrochemical, 流程化工)
- F: 소비재·식품 제조 (FMCG, 음료, 식품)
- G: 의약품·바이오 제조 (제약, GMP, 임상, biotech)
- H: 자동차·장비 제조 (automotive, equipment, 차량, 장비)
- I: 정밀 소재·부품 제조 (정밀 부품, 소재)

## 영역 (area, 단일)
- planning: 계획, KPI, 지표, 트리, 체계
- strategy: 전략, 비전, 로드맵, 포트폴리오
- operations: 운영, 현장, 라인, 재고, 작업지시 실행
- quality: 품질, 검사, SPC, 수율, 불량
- data-ai-sw: 데이터, AI, 소프트웨어, API, DB, 파이프라인

## 수준 (level, 단일)
- exec: 경영진·임원
- manager: 관리자·팀장
- team: 현장 담당자
- default: 위에 안 맞으면 default

## 자동화 수준 (automation_levels, 다중 가능, 없으면 [])
- auto1: 수작업·엑셀 위주
- auto2: 부분 시스템 도입 (개별 모듈)
- auto3: 통합 시스템 운영 (실시간 연동)
- aiplus: AI/예측/자율 운영

## 시스템 도메인 (system_domains, 다중 가능, 없으면 [])
계획·실행:
- APS: 고급 계획·스케줄링 (Advanced Planning & Scheduling)
- MES: 제조 실행 (Manufacturing Execution)
- MOM: 제조 운영 관리 (Manufacturing Operations Management)
- WES: 창고 실행 (Warehouse Execution)
전사:
- ERP: 전사 자원 관리
- PLM: 제품 수명 주기 관리 (Product Lifecycle)
- EAM: 설비 자산 관리 (Enterprise Asset)
품질·추적:
- QMS: 품질 관리
- LIMS: 실험실 정보 관리 (Laboratory Info)
- Historian: 공정 이력 관리 (process historian)
물류·공급망:
- WMS: 창고 관리
- TMS: 운송 관리 (Transportation)
- SCM: 공급망
데이터·자동화:
- SCADA: 감시·제어 (Supervisory Control)
- HMI: 인터페이스 (Human-Machine Interface)
- BI: 비즈니스 인텔리전스·리포팅
- RPA: 로보틱 프로세스 자동화
MES 보조:
- EAP: 장비 자동화 (Equipment Automation)
- FDC: 공정 결함 분류 (Fault Detection & Classification)
- SPC: 통계적 공정 관리 (Statistical Process Control)

## 관리 카테고리 (mgmt_categories, 다중 가능, 없으면 [])
조직:
- org_design: 조직 설계
- org_role: R&R·역할
거버넌스:
- gov_committee: 위원회·의사결정 체계
- gov_kpi: KPI·성과 지표
- gov_policy: 정책·기준·표준
- gov_audit: 감사·내부통제
실행계획:
- exec_phase: 단계별 추진 계획
- exec_milestone: 마일스톤·납기
- exec_resource: 자원·예산 배분
변화·리스크:
- change_management: 변화 관리·확산
- risk_mitigation: 리스크 식별·완화
- stakeholder_alignment: 이해관계자 정렬
커뮤니케이션:
- comm_reporting: 보고 체계·문서
- comm_escalation: 이슈 에스컬레이션

## 자료
제목: {title}

본문:
{body_excerpt}

## 출력 (JSON만, 다른 말 절대 금지)
{{
  "industry": "A|B|C|D|E|F|G|H|I",
  "area": "planning|strategy|operations|quality|data-ai-sw",
  "level": "exec|manager|team|default",
  "summary": "한 문장 요약",
  "topics": ["주요 주제 5개 이내"],
  "entities": ["고유명사·기관명"],
  "concepts": ["핵심 개념"],
  "reason": "분류 이유 한 줄",
  "confidence": 0.0~1.0,
  "automation_levels": ["auto1|auto2|auto3|aiplus", ...],
  "system_domains": ["APS|MES|MOM|WES|ERP|PLM|EAM|QMS|LIMS|Historian|WMS|TMS|SCM|SCADA|HMI|BI|RPA|EAP|FDC|SPC", ...],
  "mgmt_categories": ["org_design|org_role|gov_committee|gov_kpi|gov_policy|gov_audit|exec_phase|exec_milestone|exec_resource|change_management|risk_mitigation|stakeholder_alignment|comm_reporting|comm_escalation", ...],
  "blurb_industry": "산업×자동화 시점 1줄 발췌 (해당 없으면 빈 문자열)",
  "blurb_system": "시스템 시점 1줄 발췌 (해당 없으면 빈 문자열)",
  "blurb_mgmt": "관리 시점 1줄 발췌 (해당 없으면 빈 문자열)"
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

    def _enum_list(v, allowed: set[str]) -> list[str]:
        return [x for x in _str_list(v) if x in allowed]

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
        "automation_levels": _enum_list(data.get("automation_levels", []), AUTOMATION_LEVELS),
        "system_domains":   _enum_list(data.get("system_domains", []),   SYSTEM_DOMAINS),
        "mgmt_categories":  _enum_list(data.get("mgmt_categories", []),  MGMT_CATEGORIES),
        "blurb_industry": str(data.get("blurb_industry", ""))[:300],
        "blurb_system":   str(data.get("blurb_system", ""))[:300],
        "blurb_mgmt":     str(data.get("blurb_mgmt", ""))[:300],
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
        automation_levels=validated["automation_levels"],
        system_domains=validated["system_domains"],
        mgmt_categories=validated["mgmt_categories"],
        blurb_industry=validated["blurb_industry"],
        blurb_system=validated["blurb_system"],
        blurb_mgmt=validated["blurb_mgmt"],
    )


__all__ = ["K2Result", "analyze", "K2_VERSION", "K2_SCHEMA_VERSION"]
