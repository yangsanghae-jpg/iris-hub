"""V2.7.6 — Deck JSON → HTML → Playwright PDF."""
from __future__ import annotations

import tempfile
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from pypdf import PdfReader, PdfWriter

from src.engine.output.deck.schema import Deck, PATTERN_TEMPLATES


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEMPLATES_DIR = REPO_ROOT / "data" / "templates" / "slides"


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_slide_html(slide_pattern: str, slide_data: dict, deck: Deck,
                      *, pageno: int = 1, total_pages: int = 1) -> str:
    tpl_name = PATTERN_TEMPLATES.get(slide_pattern)
    if not tpl_name:
        raise ValueError(f"미지 패턴: {slide_pattern}")
    tpl = _env().get_template(tpl_name)
    ctx = {
        **slide_data,
        "company_name": deck.company_name,
        "deck_title": deck.title,
        "deck_date": deck.date,
        "pageno": pageno,
        "total_pages": total_pages,
    }
    return tpl.render(**ctx)


def render_deck_to_pdf(deck: Deck, out_path: Path | None = None) -> Path:
    if out_path is None:
        out_path = Path(tempfile.mkdtemp(prefix="iris_deck_")) / "deck.pdf"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    from playwright.sync_api import sync_playwright

    total = len(deck.slides)
    tmp_dir = Path(tempfile.mkdtemp(prefix="iris_deck_html_"))
    pdf_paths: list[Path] = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = ctx.new_page()
        for i, slide in enumerate(deck.slides, 1):
            html = render_slide_html(
                slide.pattern, slide.data, deck,
                pageno=i, total_pages=total,
            )
            html_path = tmp_dir / f"slide_{i:03d}.html"
            html_path.write_text(html, encoding="utf-8")
            page.goto(f"file://{html_path.resolve()}")
            pdf_path = tmp_dir / f"slide_{i:03d}.pdf"
            page.pdf(
                path=str(pdf_path),
                width="1920px",
                height="1080px",
                print_background=True,
                margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
            )
            pdf_paths.append(pdf_path)
        browser.close()

    writer = PdfWriter()
    for p_ in pdf_paths:
        reader = PdfReader(str(p_))
        for pg in reader.pages:
            writer.add_page(pg)
    with out_path.open("wb") as f:
        writer.write(f)

    return out_path


__all__ = ["render_slide_html", "render_deck_to_pdf"]
