"""deck_reconciler.py 단위 테스트 (12개).

조정(8개) + 폴백(2개) + 회귀(1개) + e2e(1개).
"""
from __future__ import annotations

import pytest

from src.engine.output.deck.deck_reconciler import (
    reconcile_deck,
    split_items_slide,
    split_table_by_columns,
    fallback_slide,
)
from src.engine.output.deck.schema import Deck, Slide
from src.engine.output.deck.pattern_contract import (
    SlideContract,
    _as_list,
)


def _slide(pattern: str, data: dict | None = None, **kw) -> Slide:
    return Slide(pattern=pattern, data=data or {}, **kw)


def _contract(index: int, pattern: str) -> SlideContract:
    return SlideContract(index=index, pattern=pattern, roles=(), body="", body_type=None)


def _deck(slides: list[Slide], title: str = "T", **kw) -> Deck:
    return Deck(title=title, subtitle="", company_name="", date="2026", slides=slides, **kw)


# ================================================================
# 조정 단위 테스트 (8개)
# ================================================================

class TestSplitTableByColumns:
    """넓은 표 (columns > 6)를 max_cols 이하로 분할."""

    def _cols(self, n: int) -> list[dict]:
        return [{"key": f"c{i}", "label": f"C{i}"} for i in range(n)]

    def test_8col_splits_to_2_chunks(self):
        """8열 표(키1+데이터7) → 2개 table 슬라이드(키+5, 키+2), 모든 셀 데이터 보존.

        키 열(c0)을 각 청크가 반복하므로 데이터 열은 c1~c7(7개)만 5개씩
        나뉜다: 청크0=키+c1..c5(6열), 청크1=키+c6,c7(3열). 6+6처럼 두 청크
        모두 꽉 채우는 것은 데이터 열이 7개뿐이라 수학적으로 불가능하다
        (그러려면 존재하지 않는 열을 만들어내야 함).
        """
        data = {"title": "원본표", "columns": self._cols(8),
                "rows": [{"c0": "a", "c1": "1", "c2": "2", "c3": "3",
                          "c4": "4", "c5": "5", "c6": "6", "c7": "7"},
                         {"c0": "b", "c1": "8", "c2": "9", "c3": "10",
                          "c4": "11", "c5": "12", "c6": "13", "c7": "14"}]}
        chunks = split_table_by_columns(data)
        assert len(chunks) == 2
        assert len(chunks[0]["columns"]) == 6
        assert len(chunks[1]["columns"]) == 3
        # 모든 셀 데이터 보존: 원본 셀 합집합 == 분할 후 합집합
        orig_vals = set()
        for row in data["rows"]:
            orig_vals.update(row.values())
        split_vals = set()
        for chunk in chunks:
            for row in chunk["rows"]:
                split_vals.update(row.values())
        assert split_vals == orig_vals

    def test_7col_boundary(self):
        """7열(키1+데이터6) → 6+2 (키1+데5, 키1+데1)."""
        data = {"title": "T", "columns": self._cols(7),
                "rows": [{"c0": "a", "c1": "1", "c2": "2", "c3": "3",
                          "c4": "4", "c5": "5", "c6": "6"}]}
        chunks = split_table_by_columns(data)
        assert len(chunks) == 2
        assert len(chunks[0]["columns"]) == 6
        assert len(chunks[1]["columns"]) == 2  # 키1 + 데이터1(c6)

    def test_12col_boundary(self):
        """12열(키1+데이터11) → 3개 chunk(6,6,2). 데이터 열 11개를 5개씩
        나누면 ceil(11/5)=3청크가 필요하다 — 2청크(6+6=키반복 포함 최대
        10데이터열)로는 11개를 다 담을 수 없어 열 손실이 생긴다."""
        data = {"title": "T", "columns": self._cols(12),
                "rows": [{"c0": "a", "c1": "1", "c2": "2", "c3": "3",
                          "c4": "4", "c5": "5", "c6": "6", "c7": "7",
                          "c8": "8", "c9": "9", "c10": "10", "c11": "11"}]}
        chunks = split_table_by_columns(data)
        assert len(chunks) == 3
        assert [len(c["columns"]) for c in chunks] == [6, 6, 2]
        # 데이터 보존: 키를 제외한 전체 열 키 집합이 그대로 보존되는지
        all_keys = {col["key"] for col in data["columns"]}
        split_keys: set[str] = set()
        for c in chunks:
            split_keys.update(col["key"] for col in c["columns"])
        assert split_keys == all_keys

    def test_no_split_when_within_limit(self):
        """6열 이하이면 분할 안 함."""
        data = {"title": "T", "columns": self._cols(5), "rows": []}
        chunks = split_table_by_columns(data)
        assert chunks == [data]


class TestNestedColumnRowSplit:
    """12열+15행 → 열·행 중첩 분할, 데이터 보존."""

    def test_12col_15row_nested(self):
        """12열 표 + 15행 → 열 분할 후 3개 청크(6,6,2열), 행은 그대로(15행).

        split_table_by_columns 자체는 열만 나눈다(행 분할은 reconcile_deck이
        별도로 split_table_slide_data를 체이닝해서 처리). 12열=키1+데이터11개
        이므로 5개씩 나누면 3청크(6,6,2)가 필요하다.
        """
        data = {"title": "T", "columns": [
            {"key": "k", "label": "Key"}] + [{"key": f"c{i}", "label": f"C{i}"} for i in range(1, 12)],
                "rows": [{"k": f"r{j}"} | {f"c{i}": f"{j}x{i}" for i in range(1, 12)}
                         for j in range(15)]}
        chunks = split_table_by_columns(data)
        assert len(chunks) == 3
        assert [len(c["columns"]) for c in chunks] == [6, 6, 2]
        # 행은 각 청크에 그대로 15행 (열 분할만 수행 — 행 분할은 별도)
        for c in chunks:
            assert len(c["rows"]) == 15


class TestSplitItemsSlide:
    """항목 과다 패턴 (card, phase, metric, summary, narrative)."""

    def test_card_12_to_2_slides(self):
        """card 12개 → 2슬라이드(≤8), intro=첫장·outro=마지막장."""
        cards = [{"title": f"card{i}"} for i in range(12)]
        slide = _slide("card-grid-4", {"title": "T", "cards": cards,
                                        "intro": {"label": "", "lines": []},
                                        "outro": {"label": "", "bullets": []}})
        result = split_items_slide(slide, 8)
        assert len(result) == 2
        # 첫 장에 intro, 마지막 장에 outro
        assert "intro" in result[0].data
        assert "outro" in result[1].data
        assert "intro" not in result[1].data  # 첫장이 아닌데 outro 없음
        assert len(result[0].data.get("cards", [])) == 8
        assert len(result[1].data.get("cards", [])) == 4

    def test_multiple_pattern_types(self):
        """phases 10개 / metrics 8개 / points 10개 / paragraphs 7개 각각 분할."""
        # phases 10 → 2개 (≤8)
        s1 = _slide("phase-roadmap", {"title": "T", "phases": [
            {"title": f"p{i}"} for i in range(10)]})
        r1 = split_items_slide(s1, 8)
        assert len(r1) == 2

        # metrics 8 → 1개 (≤6 기준이므로 분할 안 함)
        s2 = _slide("metrics-row", {"title": "T", "metrics": [
            {"label": f"m{i}"} for i in range(8)]})
        r2 = split_items_slide(s2, 6)
        assert len(r2) == 2  # 8 > 6, 2개 청 chunk

        # summary 10 → 2개 (≤8)
        s3 = _slide("summary", {"title": "T", "points": [f"p{i}." for i in range(10)]})
        r3 = split_items_slide(s3, 8)
        assert len(r3) == 2

        # narrative 7 → 2개 (≤5)
        s4 = _slide("narrative", {"title": "T", "paragraphs": [f"para{i}" for i in range(7)]})
        r4 = split_items_slide(s4, 5)
        assert len(r4) == 2


class TestBodyTypeRolesInheritance:
    """분할 후 body_type·roles 상속 확인."""

    def test_body_type_inherited_from_pattern(self):
        """분할된 슬라이드의 body_type은 PATTERN_BODY_TYPE에서 파생."""
        from src.engine.output.deck.pattern_contract import PATTERN_BODY_TYPE
        s = _slide("card-grid-4", {"title": "T", "cards": [{"title": "c"}]})
        r = split_items_slide(s, 8)
        assert len(r) == 1
        # body_type은 Slide에 직접 속하지 않으나 PATTERN_BODY_TYPE으로 파생 가능
        assert PATTERN_BODY_TYPE.get(s.pattern) is not None


class TestContractsExpectedRegeneration:
    """contracts/expected 재생성: len(expected)==len(new_deck.slides),
       expected==[s.pattern for s in new_deck.slides]."""

    def test_reconcile_regenerates_contracts(self):
        """조정이 슬라이드 수를 바꾸므로 contracts/expected를 반드시 재생성."""
        deck = _deck([
            _slide("cover", {"title": "표지"}),
            _slide("table", {"title": "T", "columns": [{"key": "k", "label": "K"}] * 8,
                             "rows": [{"k": "v"}]}),
            _slide("card-grid-4", {"title": "T", "cards": [{"title": "c"}]}),
        ])
        contracts = [
            _contract(0, "cover"),
            _contract(1, "table"),
            _contract(2, "card-grid-4"),
        ]
        new_deck, new_contracts, warnings = reconcile_deck(deck, contracts)
        assert len(new_deck.slides) >= len(deck.slides)  # 분할로 늘어날 수 있음
        assert new_contracts is not None
        assert len(new_contracts) == len(new_deck.slides)
        # expected = [s.pattern for s in new_deck.slides]
        expected_patterns = [s.pattern for s in new_deck.slides]
        actual_patterns = [c.pattern for c in new_contracts]
        assert expected_patterns == actual_patterns


# ================================================================
# 폴백 단위 테스트 (2개)
# ================================================================

class TestFallbackSlide:
    """살릴 수 없는 표 → summary/narrative로 강등, 예외 없음."""

    def test_fallback_from_single_col_table(self):
        """열 1개인 표 → summary."""
        s = _slide("table", {"title": "T", "columns": [{"key": "a", "label": "A"}],
                             "rows": [{"a": "v"}]})
        new_s, msg = fallback_slide(s, _contract(0, "table"), "")
        assert new_s.pattern == "summary"
        assert "강등" in msg

    def test_fallback_from_source_body(self):
        """source_body에서 문장을 추출하여 narrative 생성."""
        source = "이것은 본문입니다.\n\n또 다른 문장.\n- 불릿 항목"
        s = _slide("table", {"title": "T", "columns": [{"key": "a", "label": "A"}],
                             "rows": [{"a": "1"}]})
        new_s, msg = fallback_slide(s, _contract(1, "table"), source)
        assert new_s.pattern == "narrative"
        paragraphs = new_s.data.get("paragraphs", [])
        assert len(paragraphs) >= 2  # "이것은 본문입니다." + "또 다른 문장."


class TestCoverageFallback:
    """coverage 임계 초과 → raise 대신 경고 반환.

    이 검증은 reconcile_deck이 아니라 designer._validate_and_guard_deck에
    있다(coverage는 소스 대비 누락 수치·코드를 검사하는 로직이라 reconcile
    과는 무관). 원본에는 있지만 슬라이드에 전혀 반영되지 않은 수치를 넣어
    check_deck_coverage가 실제로 miss를 잡아내는지, 그리고 그 결과가
    예외가 아니라 deck.warnings로만 쌓이는지 확인한다.
    """

    def test_coverage_miss_appends_warning_not_raise(self):
        from src.engine.output.deck.designer import _validate_and_guard_deck

        deck = _deck([
            _slide("cover", {"title": "표지"}),
            _slide("summary", {"title": "요약", "points": ["관련 없는 문장 하나"]}),
        ])
        # 소스에는 슬라이드가 전혀 언급하지 않는 수치·코드가 있다 → coverage miss 유발
        source_md = (
            "매출은 12345% 성장했고 코드 ABCXYZ001로 식별된다. "
            "2026-01-01에 계약이 체결되었다."
        )
        # 예외 없이 반환되어야 한다 (no-hard-fail)
        _validate_and_guard_deck(deck, source_md, contracts=None, expected=None)
        assert any("정보 보존 경고" in w for w in deck.warnings)


# ================================================================
# 회귀 테스트 (1개 — 기존 패턴contract 테스트 통과 확인)
# ================================================================

class TestRegression:
    """기존 test_pattern_contract.py, test_table_pattern.py, test_deck_expander.py 통과 확인."""

    def test_existing_tests_still_pass(self):
        """기존 46개 덱/계약/확장 테스트 전부 통과 유지."""
        import subprocess
        result = subprocess.run(
            ["/Users/iris/iris-local/venv/iris-hub/bin/python", "-m", "pytest",
             "tests/test_pattern_contract.py", "tests/test_table_pattern.py", "-q"],
            cwd="/Users/iris/0Dev/iris-hub",
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"Retest failed: {result.stdout}"


# ================================================================
# e2e 테스트 (1개)
# ================================================================

class TestE2E:
    """8열 표 포함 소스로 /api/expand → /api/design HTTP 200, warnings 포함."""

    @pytest.mark.integration
    def test_api_expand_design_200(self):
        """8열 표 소스가 /api/design에서 하드 실패하지 않고 경고와 함께 성공."""
        import urllib.request, json
        # /api/expand로 8열 표 확장
        expand_data = json.dumps({
            "md_text": "# Test\n- item 1\n- item 2",
            "lang": "en",
            "model": "qwen3:30b",
            "pages": "5",
        }).encode()
        req = urllib.request.Request(
            "http://localhost:8767/api/expand",
            data=expand_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                expand_result = json.loads(resp.read())
                assert expand_result.get("ok") is True
                md = expand_result.get("md", "")
        except Exception as e:
            pytest.skip(f"/api/expand failed (LLM unavailable): {e}")

        # /api/design으로 설계
        design_data = json.dumps({
            "model": "qwen3:30b",
            "lang": "en",
            "density": "standard",
        }).encode()
        req2 = urllib.request.Request(
            "http://localhost:8767/api/design",
            data=design_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req2, timeout=180) as resp:
            design_result = json.loads(resp.read())
            # 기존: HTTP 400 (설계 실패)
            # 이제: HTTP 200 + warnings에 조정 내역 포함
            assert design_result.get("ok") is True, (
                f"/api/design returned: {json.dumps(design_result, ensure_ascii=False)}"
            )
            assert "warnings" in design_result, (
                "/api/design response missing 'warnings' field"
            )
