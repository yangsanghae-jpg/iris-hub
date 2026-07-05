"""dx_* 회귀 테스트 — v1.5 실제 스키마 형태로 6개 버그 방어.

기존 픽스처는 단순화된 형태(industry_code='A', 블록키 'mvp', 인라인 sub_industries)라
아래 실제-형태 이슈들을 못 잡았다. 이 테스트는 진단툴 v1.5 실제 키/구조를 재현한다:
  - industry_code='IND_A' (파일 stem 접미사 포함)
  - default_profile 블록키 mvp_functions/core_modules/smart_directions/kpi_keywords
  - 분류(sub_industries: list) 와 가중치(sub_profiles: dict) 분리
  - routing overlay = {mvp_boost:[codes]}
  - catalog context_explain = 중첩 dict (sqlite 바인딩 크래시 유발)
  - step 프로필의 legacy_slug 로 A01↔이름 브릿지
"""
import json
from pathlib import Path

from src.store import db, dx, dx_export, dx_import, dx_validate


def _write(root: Path, rel: str, obj) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def _build_v15_like(root: Path) -> Path:
    data = root / "server" / "data"
    _write(data, "ch1/industry_packs/IND_A_project_special.json", {
        "industry_code": "IND_A",
        "industry_label_ko": "프로젝트형 제조",
        "industry_label_zh": "项目型制造",
        "industry_message_theme": "DELIVERY_SYNC",
        "priority_axes": ["ORDER", "RESOURCE", "DELIVERY"],
        "characteristics": ["CHR_PROJECT_FLOW", "CHR_LOW_VOLUME"],
        "default_profile": {
            "routing": "RT_PROJECT",
            "flow_style": "project_flow",
            "control_unit": "project",
            "mvp_functions": [
                {"code": "MVP_PROGRESS_MON", "weight": 0.9},
                {"code": "MVP_SUPPLY_SYNC", "weight": 0.6},
            ],
            "core_modules": [{"code": "MOD_PLM", "weight": 0.8}],
            "smart_directions": ["DIR_VISIBILITY"],
            "kpi_keywords": ["KPI_PROJECT_PROGRESS"],
        },
        "sub_industries": [
            {"code": "aerospace_equipment", "label_ko": "항공·우주 장비", "label_zh": "航空航天装备"},
            {"code": "medical_imaging_equipment", "label_ko": "의료영상장비", "label_zh": "医学影像设备"},
        ],
        "sub_profiles": {
            "aerospace_equipment": {
                "primary_routing": "RT_PROJECT",
                "mvp_functions": [{"code": "MVP_PROGRESS_MON", "weight": 0.85}],
                "core_modules": [{"code": "MOD_PLM", "weight": 0.7}],
                "kpi_keywords": ["KPI_PROJECT_PROGRESS"],
            },
        },
    })
    _write(data, "ch1/routing_packs/RT_PROJECT.json", {
        "routing_code": "RT_PROJECT",
        "routing_label_ko": "프로젝트",
        "flow_style": "project_flow",
        "control_unit": "project",
        "priority_axes": ["ORDER", "RESOURCE", "DELIVERY"],
        "overlay": {"mvp_boost": ["MVP_PROGRESS_VIS"], "module_boost": [], "kpi_boost": []},
    })
    # context_explain 이 중첩 dict — 과거 크래시 지점
    _write(data, "ch1/catalogs/mvp_codes.json", [
        {"code": "MVP_PROGRESS_MON", "label_ko": "진도 모니터", "label_zh": "进度监控",
         "context_explain": {"industry": {"A": "설명"}, "default": "기본"}},
        {"code": "MVP_SUPPLY_SYNC", "label_ko": "공급 동기화", "label_zh": "供应协同"},
        {"code": "MVP_PROGRESS_VIS", "label_ko": "진도 가시화", "label_zh": "进度可视化"},
    ])
    _write(data, "ch1/catalogs/module_codes.json", [
        {"code": "MOD_PLM", "label_ko": "PLM", "label_zh": "PLM"},
    ])
    # step3: A01 → legacy_slug=aerospace_equipment (이름형 브릿지)
    _write(data, "step3/scale_profile_v3.json", {"subindustry_profiles": {
        "A01": {"industry_code": "A", "legacy_slug": "aerospace_equipment",
                "scale_profile": "P1", "override": {"domain_modifiers": {"x": 0.5}}},
    }})
    # step5_2: aerospace 만 override, medical 은 누락 → Q5_MGMT 갭
    _write(data, "step5_2/management_analysis_v3.json", {"subindustry_overrides": {
        "aerospace_equipment": {"executive_concerns_prepend": [{"point": "리드타임", "why": "..."}]},
    }})
    return data


def test_realistic_roundtrip_and_bugs(vault_root):
    data_root = _build_v15_like(vault_root)
    # 1) context_explain dict 여도 크래시 없이 임포트
    dx_import.import_from_path(data_root, branch="test")

    counts = dx.count_rows()
    # 2) 프로필 아이템(가중치) 실제 적재 — mvp_functions 등 실제 키 인식
    assert counts["dx_profile_item"] > 0
    # 3) routing overlay(*_boost) 적재
    assert counts["dx_routing_effect"] > 0

    er = dx_export.export_ch1()
    # 4) 파일명 이중접두 없이 slug 사용
    assert "server/data/ch1/industry_packs/IND_A_project_special.json" in er.files
    assert not any("IND_IND_" in p for p in er.files)

    pack = json.loads(er.files["server/data/ch1/industry_packs/IND_A_project_special.json"])
    # 5) 엔진 구조: default_profile + sub_profiles 분리 재생성
    assert pack["industry_code"] == "IND_A"
    assert len(pack["default_profile"]["mvp"]) == 2
    assert "sub_profiles" in pack and "aerospace_equipment" in pack["sub_profiles"]
    assert "sub_industries" in pack  # 분류는 별도

    # 6) 라운드트립 멱등: export→재import→재export 동일
    tmp = vault_root / "roundtrip"
    dx_export.write_files(tmp, er.files)
    dx_import.import_from_path(tmp / "server" / "data")
    er2 = dx_export.export_ch1()
    assert er.files == er2.files


def test_realistic_q5_mgmt_gap(vault_root):
    data_root = _build_v15_like(vault_root)
    dx_import.import_from_path(data_root)
    gaps = {(g["canon_code"], g["question"]) for g in dx.coverage_gaps()}
    # aerospace 는 override 있음 → 갭 아님, medical 은 누락 → Q5_MGMT 갭
    assert ("medical_imaging_equipment", "Q5_MGMT") in gaps
    assert ("aerospace_equipment", "Q5_MGMT") not in gaps
