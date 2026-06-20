"""V2.7.6 — 8종 템플릿 더미 deck (렌더 검증용)."""
from __future__ import annotations

from src.deck.schema import Deck, Slide


def build_demo_deck(meta: dict | None = None) -> Deck:
    """LLM 없이 8 패턴 전부 포함 demo deck."""
    meta = meta or {}
    company = meta.get("company", "NanoLN")
    title = meta.get("title", "종합 지표 관리 체계 진단 및 혁신 방안")
    return Deck(
        title=title,
        subtitle=meta.get("subtitle", "단결정 LN/LT 박막"),
        company_name=company,
        date=meta.get("date", "2026.06.01 | v2.0"),
        slides=[
            Slide(pattern="cover", data={
                "company": company,
                "title": title,
                "subtitle": "단결정 LN/LT 박막 공정 특성 기반",
                "target": "경영진 / KPI TF",
                "date_version": "2026.06.01 | v2.0",
            }),
            Slide(pattern="agenda", data={
                "title": "목 차 (Agenda)",
                "subtitle": "본 보고서 5개 챕터 / 8페이지",
                "items": [
                    {"ch": "Ch.1", "title": "보고서 개요", "summary": "작성 배경 / 사업 특성"},
                    {"ch": "Ch.2", "title": "현행 진단", "summary": "42개 리포트 / BSC 불균형"},
                    {"ch": "Ch.3", "title": "혁신 방향", "summary": "KPI Tree / 3계층"},
                    {"ch": "Ch.4", "title": "추진 로드맵", "summary": "4단계 12개월"},
                    {"ch": "Ch.5", "title": "기대 효과", "summary": "5개 관점"},
                ],
            }),
            Slide(pattern="exec-summary", data={
                "title": "보고서 핵심 요약 (Executive Summary)",
                "subtitle": "한 페이지로 보는 진단·시사점·혁신 방향",
                "left_label": "① 진 단 (As-Is)",
                "right_label": "② 혁신 방향 (To-Be)",
                "left_items": [
                    {"title": "리포트는 많지만 체계는 약함", "detail": "42개 리포트, KPI Tree 미정립"},
                    {"title": "BSC 4관점 불균형", "detail": "내부 프로세스 90% 편중"},
                    {"title": "공정 특화 지표 부족", "detail": "단결정·박막·CMP 지표 미흡"},
                    {"title": "후행 확인 위주", "detail": "선행 예방·알람 부족"},
                    {"title": "정의·자동화 미표준", "detail": "부서별 해석 차이"},
                ],
                "right_items": [
                    {"title": "KPI Tree 종합 체계", "detail": "전사↔부서↔현장 인과"},
                    {"title": "BSC 4관점 균형", "detail": "재무·고객·학습성장 보강"},
                    {"title": "공정 특화 지표", "detail": "회수율·Void·Ra·Qual"},
                    {"title": "3계층 KPI", "detail": "전략/운영/관리"},
                    {"title": "BI 자동화·SSoT", "detail": "MES/SPC/ERP 통합"},
                ],
            }),
            Slide(pattern="metrics-row", data={
                "title": "현행 리포트 체계 요약",
                "subtitle": "8개 부서 / 42개 리포트 인벤토리",
                "metrics": [
                    {"value": "42", "label": "총 리포트 수", "color": "blue"},
                    {"value": "8", "label": "관련 부서", "color": "blue"},
                    {"value": "≈90%", "label": "내부 프로세스 편중", "color": "orange"},
                    {"value": "0", "label": "학습·성장 관점", "color": "red"},
                ],
            }),
            Slide(pattern="compare-2col", data={
                "title": "지표가 많지만 체계는 약한 상태",
                "subtitle": "문제는 '지표 부족'이 아니라 '지표 간 관계 약함'",
                "left_label": "As-Is — 부서별 분절형 리포트 42종",
                "right_label": "To-Be — KPI Tree 종합 지표 체계",
                "left_items": ["설비", "품질", "생산", "물류", "PIE", "고객납기", "입고품질", "체계", "기타"],
                "right_items": ["전사 전략 KPI", "수율", "원가", "납기·고객", "SPC", "CPK", "MTBF", "OEE"],
                "footer_note": "★ 지표 추가가 아니라, 기존 42개 리포트를 인과관계로 묶는 작업이 우선",
            }),
            Slide(pattern="card-grid-4", data={
                "title": "보고서 개요 — 작성 배경",
                "subtitle": "NanoLN 사업 특성과 본 보고서의 목적",
                "intro": {
                    "label": "▌ 회사 정의 (Company Profile)",
                    "lines": ["단결정 니오브산리튬 (LN) / LT 박막 소재", "RF 필터 / 광통신 / 집적 광학"],
                },
                "section_title": "▌ 사업 특성",
                "cards": [
                    {"title": "고부가가치 소재", "subtitle": "품질 1건 이슈가 매출 직결", "color": "blue"},
                    {"title": "고난도 소재 공정", "subtitle": "단결정 성장·박막·CMP", "color": "blue"},
                    {"title": "미세 품질 관리", "subtitle": "나노급 표면·계면 품질", "color": "orange"},
                    {"title": "고객 인증 대응", "subtitle": "글로벌 Qualification", "color": "green"},
                ],
                "outro": {
                    "label": "▌ 본 보고서의 목적",
                    "bullets": ["• 기존 42개 리포트 체계 진단", "• 공정 특성 기반 KPI 설계", "• 12개월 로드맵 제시"],
                },
            }),
            Slide(pattern="phase-roadmap", data={
                "title": "단계별 추진 로드맵 — 4단계 12개월",
                "subtitle": "현행 정리 → KPI Tree → 공정 특화 → BI 자동화",
                "phases": [
                    {"label": "Phase 1", "title": "현행 리포트 정리", "period": "0~3M", "color": "blue-light",
                     "tasks": ["■ 42개 재분류", "■ 지표 통합", "■ KPI 정의서", "■ Owner 지정"]},
                    {"label": "Phase 2", "title": "KPI Tree 설계", "period": "3~6M", "color": "blue",
                     "tasks": ["■ 전사 목표", "■ 3계층 KPI", "■ 인과관계", "■ BSC 균형"]},
                    {"label": "Phase 3", "title": "공정 특화 보완", "period": "6~9M", "color": "orange",
                     "tasks": ["■ 단결정 지표", "■ 박막/CMP", "■ Qual 통과율", "■ 선행 알람"]},
                    {"label": "Phase 4", "title": "BI 자동화", "period": "9~12M", "color": "green",
                     "tasks": ["■ 데이터 매핑", "■ 대시보드", "■ SSoT", "■ 알람 체계"]},
                ],
                "footer_note": "★ 핵심: 경영 Sponsorship · 跨부서 TF · 데이터 거버넌스",
            }),
            Slide(pattern="dimension-5", data={
                "title": "기대 효과 — 5개 관점에서 본 변화",
                "subtitle": "경영 · 생산 · 품질 · 설비 · 고객",
                "dimensions": [
                    {"label": "11.1 경영", "color": "blue",
                     "bullets": ["전사 목표↔현장 연결", "통합 판단 체계", "투자 우선순위"]},
                    {"label": "11.2 생산", "color": "blue",
                     "bullets": ["병목 조기 발견", "Cycle Time 개선", "WIP 가시화"]},
                    {"label": "11.3 품질", "color": "orange",
                     "bullets": ["수율 원인 추적", "SPC 선행화", "사전 예방 전환"]},
                    {"label": "11.4 설비", "color": "purple",
                     "bullets": ["고장↔품질 영향", "MTBF/OEE", "예지보전"]},
                    {"label": "11.5 고객", "color": "green",
                     "bullets": ["납기 리스크 식별", "Qual 강화", "신뢰도 향상"]},
                ],
                "footer_note": "단순 현황 관리 → 전략적·데이터 기반 종합 경영관리 체계",
            }),
        ],
    )


__all__ = ["build_demo_deck"]
