"""V2.9 — PPT 탭 다중 포맷 소스 업로드 테스트.

커버:
  - converter._convert_xlsx() 왕복 (시트/표 마크다운화)
  - converter.convert_with_meta(enable_ocr=False) PDF 경로 보존
  - v31 /api/ppt/source/formats, /api/ppt/source/convert 계약
  - 레거시 바이너리(.ppt/.doc/.xls) 거부, 크기 초과 거부, md/txt 회귀
"""
from __future__ import annotations

import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.engine.intake import converter
from v31 import server

client = TestClient(server.app)


# ─── converter._convert_xlsx 단위 테스트 ──────────────────────────────
def _make_xlsx(tmp_path: Path) -> Path:
    from openpyxl import Workbook

    wb = Workbook()
    ws1 = wb.active
    ws1.title = "매출"
    ws1.append(["월", "매출액", "비고"])
    ws1.append(["1월", 1000, "정상"])
    ws1.append(["2월", 1200, None])

    ws2 = wb.create_sheet("메모")
    ws2.append(["항목", "값"])
    ws2.append(["담당자", "홍길동"])

    path = tmp_path / "sample.xlsx"
    wb.save(str(path))
    return path


def test_convert_xlsx_roundtrip(tmp_path):
    path = _make_xlsx(tmp_path)
    result = converter.convert_with_meta(path)
    assert result.extraction_method == "text"
    assert "## 시트: 매출" in result.body
    assert "## 시트: 메모" in result.body
    assert "매출액" in result.body
    assert "1월" in result.body
    assert "1200" in result.body
    assert "홍길동" in result.body


def test_convert_xlsx_via_convert_to_markdown(tmp_path):
    path = _make_xlsx(tmp_path)
    body = converter.convert_to_markdown(path)
    assert "매출" in body


def test_xlsx_in_supported_suffixes():
    assert ".xlsx" in converter.SUPPORTED_SUFFIXES


def test_legacy_binary_suffixes_defined():
    assert converter.LEGACY_BINARY_SUFFIXES == {".ppt", ".doc", ".xls"}
    # 레거시는 SUPPORTED_SUFFIXES에는 남아 있어야 한다 (기존 intake 호환)
    assert {".ppt", ".doc"} <= converter.SUPPORTED_SUFFIXES


def test_convert_with_meta_enable_ocr_flag_default_true(tmp_path, monkeypatch):
    """enable_ocr 기본값 True — 기존 호출자(folder_load 등) 동작 보존."""
    calls = {}

    def fake_pdf_meta(src, enable_ocr=True):
        calls["enable_ocr"] = enable_ocr
        return converter.ConversionResult(body="x", extraction_method="text", pages=1)

    monkeypatch.setattr(converter, "_convert_pdf_with_meta", fake_pdf_meta)
    fake_pdf = tmp_path / "f.pdf"
    fake_pdf.write_bytes(b"%PDF-1.4\n")
    converter.convert_with_meta(fake_pdf)
    assert calls["enable_ocr"] is True

    converter.convert_with_meta(fake_pdf, enable_ocr=False)
    assert calls["enable_ocr"] is False


# ─── v31 server API 계약 테스트 ────────────────────────────────────────
def test_source_formats_endpoint():
    resp = client.get("/api/ppt/source/formats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert ".xlsx" in data["extensions"]
    assert ".md" in data["extensions"]
    assert data["max_bytes"] == 20 * 1024 * 1024
    assert ".xlsx" in data["accept"]
    assert data["label"]


def test_convert_endpoint_md_roundtrip():
    content = b"# hello\n\nworld"
    resp = client.post(
        "/api/ppt/source/convert",
        files={"file": ("note.md", io.BytesIO(content), "text/markdown")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert "hello" in data["text"]
    assert "world" in data["text"]


def test_convert_endpoint_xlsx_roundtrip(tmp_path):
    path = _make_xlsx(tmp_path)
    with open(path, "rb") as f:
        resp = client.post(
            "/api/ppt/source/convert",
            files={"file": ("sample.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert "매출" in data["text"]
    assert "홍길동" in data["text"]


@pytest.mark.parametrize("ext", [".ppt", ".doc", ".xls"])
def test_convert_endpoint_rejects_legacy_binary(ext):
    resp = client.post(
        "/api/ppt/source/convert",
        files={"file": (f"old{ext}", io.BytesIO(b"binary-ish content"), "application/octet-stream")},
    )
    assert resp.status_code == 415
    data = resp.json()
    assert "error" in data
    assert ext in data["error"]


def test_convert_endpoint_rejects_unknown_extension():
    resp = client.post(
        "/api/ppt/source/convert",
        files={"file": ("weird.zip", io.BytesIO(b"PK\x03\x04"), "application/zip")},
    )
    assert resp.status_code == 415
    assert "error" in resp.json()


def test_convert_endpoint_rejects_oversize(monkeypatch):
    monkeypatch.setattr(server, "PPT_UPLOAD_MAX_BYTES", 10)
    resp = client.post(
        "/api/ppt/source/convert",
        files={"file": ("note.md", io.BytesIO(b"x" * 1000), "text/markdown")},
    )
    assert resp.status_code == 413
    assert "error" in resp.json()


def test_convert_endpoint_rejects_empty_file():
    resp = client.post(
        "/api/ppt/source/convert",
        files={"file": ("note.md", io.BytesIO(b""), "text/markdown")},
    )
    assert resp.status_code == 400
    assert "error" in resp.json()


def test_convert_endpoint_no_file_returns_400():
    resp = client.post("/api/ppt/source/convert")
    assert resp.status_code in (400, 422)  # FastAPI validation may 422 before reaching handler


def test_convert_endpoint_conversion_error_maps_to_422(monkeypatch):
    def boom(src, enable_ocr=True):
        raise converter.ConversionError("모의 파싱 실패")

    monkeypatch.setattr(converter, "convert_with_meta", boom)
    resp = client.post(
        "/api/ppt/source/convert",
        files={"file": ("broken.pdf", io.BytesIO(b"%PDF-1.4 broken"), "application/pdf")},
    )
    assert resp.status_code == 422
    assert "모의 파싱 실패" in resp.json()["error"]
