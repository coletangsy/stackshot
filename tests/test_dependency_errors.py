import shutil
from pathlib import Path

import pytest

from stackshot.adapters.html import HtmlAdapter
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
