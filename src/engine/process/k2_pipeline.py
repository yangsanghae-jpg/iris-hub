"""V2.7.0 — K2 단계 분리 파이프라인.

K2 분석을 3 단계로 쪼개 각 단계가 *짧은 프롬프트 + 좁은 스키마*만 다루도록.

흐름:
  ① extract  (fast 모델 권장): topics, entities, concepts
  ② classify (deep 모델): industry, area, level, automation, system, mgmt + confidence
  ③ summarize (deep 모델): summary, blurb_industry, blurb_system, blurb_mgmt

각 단계는 독립 실패 가능. 실패 시 *그 단계만* 재시도, 이미 박힌 다른 단계 결과는 보존.

진실원 (document_meta):
  - extract_at, classify_at, summarize_at 단계별 timestamp
  - classifier_version = 모든 단계 완료 시 최종 박힘
  - processing_started_at = 락 (호출 전 set, 모든 단계 끝나면 clear)

장점 vs 기존 monolithic K2:
  - 짧은 프롬프트 → JSON 응답 안정성 ↑
  - 단계별 진척 가시화 (어디까지 됐는지 명확)
  - 단계별 모델 선택 (extract는 fast, classify·summarize는 deep)
  - 부분 실패 안전 (한 단계 죽어도 나머지 보존)

호환:
  - K2Result는 src.engine.process.k2와 호환 형태로 합쳐서 반환
  - document_meta upsert는 src.document_meta 통해
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src import llm
from src.config import IRIS_LLM_DEEP, IRIS_LLM_FAST
from src.engine.process.k2 import (
    K2Result, K2_SCHEMA_VERSION, _k2_version,
    AUTOMATION_LEVELS, SYSTEM_DOMAINS, MGMT_CATEGORIES,
)
from src.engine.process.classify import (
    INDUSTRY_LABELS, AREA_LABELS, LEVEL_LABELS,
    suggest_classification,
)


@dataclass
class StageResult:
    """한 단계 결과."""
    ok: bool = False
    elapsed_ms: int = 0
    model: str = ""
    error: str = ""
    data: dict[str, Any] = field(default_factory=dict)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _str_list(v, maxn: int = 10) -> list[str]:
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()][:maxn]
    if isinstance(v, str):
        return [v.strip()] if v.strip() else []
    return []


def _enum_list(v, allowed: set[str]) -> list[str]:
    return [x for x in _str_list(v) if x in allowed]


# ─── ① extract — 키워드 추출 ──────────────────────────────────────────
def _prompt_extract(title: str, body: str, max_body: int = 3000) -> str:
    excerpt = body[:max_body] + ("\n... (생략)" if len(body) > max_body else "")
    return f"""당신은 IRIS 키워드 추출기입니다. 자료에서 키워드만 뽑아 JSON으로 답하세요.

## 자료
제목: {title}

본문:
{excerpt}

## 출력 (JSON만, 다른 말 절대 금지)
{{
  "topics": ["주요 주제 5개 이내, 짧은 명사구"],
  "entities": ["고유명사·기관명·제품명"],
  "concepts": ["핵심 개념·기술 용어"]
}}
"""


def stage_extract(title: str, body: str, *, timeout: float = 30.0,
                  role: str = "deep") -> StageResult:
    """① 키워드 추출 — deep 모델 (V2.7.0 — fast는 JSON 안정성 낮아 deep 기본).

    role='fast'로 override 가능하지만 qwen3.5:4b는 <think> 토큰을 흘려 JSON 깨지는 경우가 많음.
    """
    res = StageResult()
    if not body.strip():
        res.error = "empty body"
        return res

    prompt = _prompt_extract(title, body)
    resp = llm.generate_json(prompt, role=role, timeout=timeout)
    res.elapsed_ms = resp.get("ms", 0)
    res.model = resp.get("model", IRIS_LLM_FAST if role == "fast" else IRIS_LLM_DEEP)

    if not resp.get("ok"):
        res.error = f"LLM 실패: {resp.get('error', 'unknown')}"
        return res

    data = resp.get("data", {})
    res.data = {
        "topics":   _str_list(data.get("topics", [])),
        "entities": _str_list(data.get("entities", [])),
        "concepts": _str_list(data.get("concepts", [])),
    }
    res.ok = True
    return res


# ─── ② classify — 5축 분류 ───────────────────────────────────────────
def _prompt_classify(title: str, body: str, keywords: dict, max_body: int = 3000) -> str:
    excerpt = body[:max_body] + ("\n... (생략)" if len(body) > max_body else "")
    topics_str = ", ".join(keywords.get("topics", [])[:5]) or "(없음)"
    entities_str = ", ".join(keywords.get("entities", [])[:5]) or "(없음)"
    concepts_str = ", ".join(keywords.get("concepts", [])[:5]) or "(없음)"

    return f"""당신은 IRIS 분류기입니다. 자료를 어휘로 분류해 JSON으로만 답하세요.

## 자료
제목: {title}

본문 (앞부분):
{excerpt}

## 사전 추출 키워드 (참고)
- topics: {topics_str}
- entities: {entities_str}
- concepts: {concepts_str}

## 어휘 — *반드시* 아래 enum에서만 선택

산업 (industry, 단일):
- A 프로젝트형 (ETO, 조선·플랜트·항공·국방)
- B 반도체 (wafer, fab, foundry)
- C 전자조립 (SMT, EMS, PCB)
- D 디스플레이·신에너지 (LCD, OLED, 배터리, 태양광)
- E 프로세스·화학 (정유, petrochemical)
- F 소비재·식품 (FMCG)
- G 의약품·바이오 (GMP, biotech)
- H 자동차·장비
- I 정밀 소재·부품

영역 (area, 단일):
- planning · strategy · operations · quality · data-ai-sw

수준 (level, 단일):
- exec · manager · team · default

자동화 (automation_levels, 다중):
- auto1 (수작업·엑셀) · auto2 (부분 시스템) · auto3 (통합 시스템) · aiplus (AI/자율)

시스템 도메인 (system_domains, 다중):
- APS·MES·MOM·WES·ERP·PLM·EAM·QMS·LIMS·Historian·WMS·TMS·SCM·SCADA·HMI·BI·RPA·EAP·FDC·SPC

관리 카테고리 (mgmt_categories, 다중):
- org_design·org_role·gov_committee·gov_kpi·gov_policy·gov_audit
- exec_phase·exec_milestone·exec_resource
- change_management·risk_mitigation·stakeholder_alignment
- comm_reporting·comm_escalation

## 출력 (JSON만, 다른 말 절대 금지)
{{
  "industry": "A|B|C|D|E|F|G|H|I",
  "area": "planning|strategy|operations|quality|data-ai-sw",
  "level": "exec|manager|team|default",
  "automation_levels": ["..."],
  "system_domains": ["..."],
  "mgmt_categories": ["..."],
  "confidence": 0.0~1.0,
  "reason": "분류 이유 한 줄"
}}
"""


def stage_classify(title: str, body: str, keywords: dict, *,
                   timeout: float = 60.0, role: str = "deep") -> StageResult:
    """② 5축 분류 — deep 모델."""
    res = StageResult()
    if not body.strip():
        res.error = "empty body"
        return res

    prompt = _prompt_classify(title, body, keywords)
    resp = llm.generate_json(prompt, role=role, timeout=timeout)
    res.elapsed_ms = resp.get("ms", 0)
    res.model = resp.get("model", IRIS_LLM_DEEP)

    if not resp.get("ok"):
        res.error = f"LLM 실패: {resp.get('error', 'unknown')}"
        return res

    data = resp.get("data", {})

    ind = data.get("industry")
    if ind not in INDUSTRY_LABELS:
        ind = None
    area = data.get("area")
    if area not in AREA_LABELS:
        area = None
    lvl = data.get("level")
    if lvl not in LEVEL_LABELS:
        lvl = None

    res.data = {
        "industry": ind,
        "area": area,
        "level": lvl,
        "automation_levels": _enum_list(data.get("automation_levels", []), AUTOMATION_LEVELS),
        "system_domains":   _enum_list(data.get("system_domains", []),   SYSTEM_DOMAINS),
        "mgmt_categories":  _enum_list(data.get("mgmt_categories", []),  MGMT_CATEGORIES),
        "confidence": float(data.get("confidence", 0.0) or 0.0),
        "reason": str(data.get("reason", ""))[:300],
    }
    res.ok = True
    return res


# ─── ③ summarize — 요약 + 3 시점 blurb ────────────────────────────────
def _prompt_summarize(title: str, body: str, classification: dict,
                      max_body: int = 4000) -> str:
    excerpt = body[:max_body] + ("\n... (생략)" if len(body) > max_body else "")
    ind = classification.get("industry") or "?"
    area = classification.get("area") or "?"
    auto = ", ".join(classification.get("automation_levels", [])) or "(없음)"
    sys_ = ", ".join(classification.get("system_domains", [])) or "(없음)"
    mgmt = ", ".join(classification.get("mgmt_categories", [])) or "(없음)"

    return f"""당신은 IRIS 요약기입니다. 자료를 3 시점에서 1줄씩 발췌해 JSON으로만 답하세요.

## 자료
제목: {title}

본문:
{excerpt}

## 분류 결과 (참고 — 시점 결정용)
- 산업: {ind}, 영역: {area}
- 자동화: {auto}
- 시스템: {sys_}
- 관리: {mgmt}

## 출력 (JSON만, 다른 말 절대 금지)
{{
  "summary": "본문 전체를 한 문장으로 요약 (500자 이내)",
  "blurb_industry": "산업×자동화 시점 1줄 발췌 (해당 없으면 빈 문자열)",
  "blurb_system": "시스템 시점 1줄 발췌 (해당 없으면 빈 문자열)",
  "blurb_mgmt": "관리 시점 1줄 발췌 (해당 없으면 빈 문자열)"
}}
"""


def stage_summarize(title: str, body: str, classification: dict, *,
                    timeout: float = 60.0, role: str = "deep") -> StageResult:
    """③ 요약 + 3 시점 blurb — deep 모델."""
    res = StageResult()
    if not body.strip():
        res.error = "empty body"
        return res

    prompt = _prompt_summarize(title, body, classification)
    resp = llm.generate_json(prompt, role=role, timeout=timeout)
    res.elapsed_ms = resp.get("ms", 0)
    res.model = resp.get("model", IRIS_LLM_DEEP)

    if not resp.get("ok"):
        res.error = f"LLM 실패: {resp.get('error', 'unknown')}"
        return res

    data = resp.get("data", {})
    res.data = {
        "summary":        str(data.get("summary", ""))[:500],
        "blurb_industry": str(data.get("blurb_industry", ""))[:300],
        "blurb_system":   str(data.get("blurb_system", ""))[:300],
        "blurb_mgmt":     str(data.get("blurb_mgmt", ""))[:300],
    }
    res.ok = True
    return res


# ─── 파이프라인 실행 + DB upsert ──────────────────────────────────────
def run_pipeline(title: str, body: str, *,
                 extract_role: str = "fast",
                 classify_role: str = "deep",
                 summarize_role: str = "deep") -> K2Result:
    """3 단계 순차 실행 → K2Result 형태로 반환.

    한 단계 실패 시 다음 단계 *skip*, fallback 규칙 분류 사용.
    """
    if not body.strip():
        return K2Result(error="empty body", fallback_used=True)

    total_ms = 0
    used_model = ""

    # ① extract
    r1 = stage_extract(title, body, role=extract_role)
    total_ms += r1.elapsed_ms
    if r1.ok:
        used_model = r1.model

    # ② classify (extract 키워드 활용)
    keywords = r1.data if r1.ok else {"topics": [], "entities": [], "concepts": []}
    r2 = stage_classify(title, body, keywords, role=classify_role)
    total_ms += r2.elapsed_ms
    if r2.ok:
        used_model = r2.model

    # classify 실패 시 fallback 규칙 분류
    if not r2.ok:
        rule = suggest_classification(title, body)
        r2.data = {
            "industry": rule.get("industry"),
            "area": rule.get("area"),
            "level": rule.get("level"),
            "automation_levels": [],
            "system_domains": [],
            "mgmt_categories": [],
            "confidence": 0.3,
            "reason": f"LLM classify 실패, 규칙 fallback: {r2.error}",
        }

    # ③ summarize
    r3 = stage_summarize(title, body, r2.data, role=summarize_role)
    total_ms += r3.elapsed_ms
    if r3.ok:
        used_model = r3.model

    classifier_version = _k2_version(used_model) if used_model else "rule-fallback"
    any_fail = not (r1.ok and r2.ok and r3.ok)

    return K2Result(
        industry=r2.data.get("industry"),
        area=r2.data.get("area"),
        level=r2.data.get("level"),
        summary=r3.data.get("summary", ""),
        topics=r1.data.get("topics", []),
        entities=r1.data.get("entities", []),
        concepts=r1.data.get("concepts", []),
        reason=r2.data.get("reason", ""),
        confidence=r2.data.get("confidence", 0.0),
        elapsed_ms=total_ms,
        classifier_version=classifier_version,
        fallback_used=any_fail,
        automation_levels=r2.data.get("automation_levels", []),
        system_domains=r2.data.get("system_domains", []),
        mgmt_categories=r2.data.get("mgmt_categories", []),
        blurb_industry=r3.data.get("blurb_industry", ""),
        blurb_system=r3.data.get("blurb_system", ""),
        blurb_mgmt=r3.data.get("blurb_mgmt", ""),
        error=" / ".join(filter(None, [r1.error, r2.error, r3.error])) or None,
    )


def mark_stage(conn: sqlite3.Connection, doc_id: str, stage: str) -> None:
    """document_meta에 단계별 timestamp 박음. stage ∈ {extract, classify, summarize}."""
    col = f"{stage}_at"
    if col not in {"extract_at", "classify_at", "summarize_at"}:
        return
    conn.execute(
        f"INSERT INTO document_meta (doc_id, {col}) VALUES (?, ?) "
        f"ON CONFLICT(doc_id) DO UPDATE SET {col}=excluded.{col}",
        (doc_id, _now_iso()),
    )


__all__ = [
    "StageResult", "K2Result",
    "stage_extract", "stage_classify", "stage_summarize",
    "run_pipeline", "mark_stage",
]
