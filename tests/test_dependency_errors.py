import shutil
from pathlib import Path

import fitz
import pytest

from stackshot.adapters.html import HtmlAdapter
from stackshot.adapters.pdf import PdfAdapter
from stackshot.adapters.ppt import PowerPointAdapter
from stackshot.options import ConvertOptions


def test_ppt_adapter_reports_missing_libreoffice(monkeypatch, tmp_path):
    monkeypatch.setattr(shutil, "which", lambda _name: None)

    with pytest.raises(RuntimeError, match="LibreOffice is required"):
        PowerPointAdapter().render(tmp_path / "deck.pptx", tmp_path, ConvertOptions())


def test_html_adapter_reports_missing_playwright_browser(monkeypatch, tmp_path):
    page = tmp_path / "page.html"
    page.write_text("<h1>Hello</h1>", encoding="utf-8")

    def broken_sync_playwright():
        raise RuntimeError("Executable doesn't exist at /browser/chromium")

    monkeypatch.setattr("stackshot.adapters.html.sync_playwright", broken_sync_playwright)

    with pytest.raises(RuntimeError, match="Playwright browser dependencies are missing"):
        HtmlAdapter().render(page, tmp_path, ConvertOptions(width=100))


def test_pdf_adapter_ignores_optional_stylesheet(tmp_path):
    source = tmp_path / "document.pdf"
    document = fitz.open()
    document.new_page(width=100, height=100)
    document.save(source)
    document.close()

    frames = PdfAdapter().render(
        source,
        tmp_path,
        ConvertOptions(width=100, css_path=tmp_path / "missing.css"),
    )

    assert frames == [tmp_path / "page-0001.png"]
