"""Tests for obsidian_sync — V2.6.2.5 1단계 코어 엔진."""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

import pytest

from src import obsidian_sync as osync


@pytest.fixture
def temp_db(tmp_path):
    """document_meta + documents 풀세트 임시 DB."""
    db = tmp_path / "test.db"
    conn = sqlite3.connect(db)
    conn.executescript("""
      CREATE TABLE documents (
        doc_id TEXT PRIMARY KEY, title TEXT, path TEXT,
        industry TEXT, area TEXT, level TEXT,
        fetched_at TEXT, lane TEXT
      );
      CREATE TABLE document_meta (
        doc_id TEXT PRIMARY KEY,
        summary TEXT, topics_json TEXT,
        confidence REAL, fallback_used INTEGER,
        classifier_version TEXT, k2_at TEXT,
        automation_levels_json TEXT, system_domains_json TEXT,
        mgmt_categories_json TEXT,
        blurb_industry TEXT, blurb_system TEXT, blurb_mgmt TEXT
      );
    """)
    # 자료 3건 — 풀라벨 / K2미완 / lane만 있는 자료
    conn.execute("""
      INSERT INTO documents VALUES
      ('doc_full', 'Nanoln 지표 트리', '/raw/n.md',
       'B', 'planning', 'L4', '2026-06-15T10:00:00Z', 'reference'),
      ('doc_no_k2', '미분석 자료', '/raw/x.md',
       NULL, NULL, NULL, '2026-06-15T11:00:00Z', 'bronze'),
      ('doc_partial', '"인용 따옴표" 포함', '/raw/q.md',
       'A', NULL, NULL, '2026-06-15T12:00:00Z', 'reference')
    """)
    conn.execute("""
      INSERT INTO document_meta VALUES
      ('doc_full', 'B 반도체 fab 사례', '["KPI", "거버넌스"]',
       0.84, 0, 'k2-qwen3.8b-v2', '2026-06-15T10:30:00Z',
       '["auto2", "auto3"]', '["APS", "MES"]', '["gov_kpi"]',
       '산업 시점 발췌', '시스템 시점 발췌', '관리 시점 발췌'),
      ('doc_partial', '제목에 "인용" 들어감', '[]',
       0.5, 1, 'rule-v1', '2026-06-15T12:30:00Z',
       NULL, NULL, NULL, NULL, NULL, NULL)
    """)
    conn.commit()
    conn.close()
    return db


def test_sync_all_writes_md_per_doc(temp_db, tmp_path):
    """3건 자료 → 3개 .md + README."""
    mirror = tmp_path / "mirror"
    res = osync.sync_all(mirror_root=mirror, db_path=temp_db)

    assert res.ok
    assert res.scanned == 3
    assert res.written == 3
    assert res.skipped == 0

    files = sorted(p.name for p in mirror.glob("*.md"))
    assert "doc_full.md"    in files
    assert "doc_no_k2.md"   in files
    assert "doc_partial.md" in files
    assert (mirror / "README.md").exists()


def test_full_doc_frontmatter_has_multilabels(temp_db, tmp_path):
    """풀라벨 자료의 frontmatter에 멀티라벨 + tags 박힘."""
    mirror = tmp_path / "mirror"
    osync.sync_all(mirror_root=mirror, db_path=temp_db)

    text = (mirror / "doc_full.md").read_text(encoding="utf-8")
    assert text.startswith("---\n")

    # 단일/멀티 라벨 모두
    assert 'iris_industry: "B"' in text
    assert 'iris_lane: "reference"' in text
    assert 'iris_automation: ["auto2", "auto3"]' in text
    assert 'iris_system: ["APS", "MES"]' in text
    assert 'iris_mgmt: ["gov_kpi"]' in text
    assert 'iris_topics: ["KPI", "거버넌스"]' in text
    assert "iris_confidence: 0.840" in text

    # 그래프뷰 클러스터 tags
    assert "iris/industry/B" in text
    assert "iris/automation/auto2" in text
    assert "iris/system/APS" in text
    assert "iris/mgmt/gov_kpi" in text

    # 본문 3 시점 발췌
    assert "산업 시점 발췌" in text
    assert "시스템 시점 발췌" in text
    assert "관리 시점 발췌" in text


def test_no_k2_doc_has_placeholder(temp_db, tmp_path):
    """K2 미분석 자료는 안내 문구 박고 frontmatter 멀티라벨은 비어있음."""
    mirror = tmp_path / "mirror"
    osync.sync_all(mirror_root=mirror, db_path=temp_db)

    text = (mirror / "doc_no_k2.md").read_text(encoding="utf-8")
    assert "K2 분석 미완" in text
    # 멀티라벨 키 자체가 없어야 함 (Dataview에서 매치 안 됨)
    assert "iris_automation:" not in text
    assert "iris_system:" not in text
    # tags는 lane만 박힐 수 있음
    assert "iris/lane/bronze" in text


def test_yaml_escape_quotes(temp_db, tmp_path):
    """제목에 큰따옴표 들어가도 frontmatter 깨지지 않음."""
    mirror = tmp_path / "mirror"
    osync.sync_all(mirror_root=mirror, db_path=temp_db)

    text = (mirror / "doc_partial.md").read_text(encoding="utf-8")
    # 큰따옴표는 \" 로 escape
    assert '\\"인용 따옴표\\"' in text
    # frontmatter 닫힘 정상
    fm_end = text.find("\n---\n", 4)
    assert fm_end > 0


def test_incremental_skip_when_unchanged(temp_db, tmp_path):
    """2회차 sync에서 변경 없는 자료는 skip."""
    mirror = tmp_path / "mirror"
    r1 = osync.sync_all(mirror_root=mirror, db_path=temp_db)
    assert r1.written == 3

    # 즉시 두 번째 호출 — 변경 없으므로 모두 skip
    r2 = osync.sync_all(mirror_root=mirror, db_path=temp_db)
    assert r2.scanned == 3
    assert r2.written == 0
    assert r2.skipped == 3


def test_incremental_rewrite_when_k2_at_advances(temp_db, tmp_path):
    """k2_at이 .md의 iris_synced_at보다 새로우면 다시 씀."""
    mirror = tmp_path / "mirror"
    osync.sync_all(mirror_root=mirror, db_path=temp_db)

    # K2가 *나중에* 다시 돌았다고 가정 — k2_at을 먼 미래로
    conn = sqlite3.connect(temp_db)
    conn.execute(
        "UPDATE document_meta SET k2_at='2099-01-01T00:00:00Z' WHERE doc_id='doc_full'"
    )
    conn.commit()
    conn.close()

    r = osync.sync_all(mirror_root=mirror, db_path=temp_db)
    assert r.written == 1   # doc_full만 다시
    assert r.skipped == 2


def test_force_rewrites_all(temp_db, tmp_path):
    """force=True면 변경 없어도 다시 씀."""
    mirror = tmp_path / "mirror"
    osync.sync_all(mirror_root=mirror, db_path=temp_db)
    r = osync.sync_all(mirror_root=mirror, db_path=temp_db, force=True)
    assert r.written == 3
    assert r.skipped == 0


def test_sync_one(temp_db, tmp_path):
    """sync_one — 단일 자료만 박음."""
    mirror = tmp_path / "mirror"
    r = osync.sync_one("doc_full", mirror_root=mirror, db_path=temp_db)
    assert r.ok
    assert r.written == 1
    assert (mirror / "doc_full.md").exists()
    assert not (mirror / "doc_no_k2.md").exists()


def test_sync_one_unknown_doc(temp_db, tmp_path):
    mirror = tmp_path / "mirror"
    r = osync.sync_one("missing_doc", mirror_root=mirror, db_path=temp_db)
    assert not r.ok
    assert r.written == 0
    assert any("DB에 없음" in err for _, err in r.errors)


def test_safe_filename_strips_bad_chars():
    assert osync._safe_filename("doc/with:bad*chars?") == "doc_with_bad_chars_"
    assert osync._safe_filename("normal_id_123") == "normal_id_123"


def test_db_missing_returns_empty(tmp_path):
    """DB가 없을 때 polling 안전 — 빈 결과 반환, 예외 X."""
    mirror = tmp_path / "mirror"
    fake_db = tmp_path / "no_such.db"
    r = osync.sync_all(mirror_root=mirror, db_path=fake_db)
    assert r.ok
    assert r.scanned == 0
    assert r.written == 0
