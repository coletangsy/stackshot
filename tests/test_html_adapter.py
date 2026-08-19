from contextlib import nullcontext
from pathlib import Path
from unittest.mock import Mock

from playwright.sync_api import Browser, BrowserType, Locator, Page, Playwright

from stackshot.adapters.html import HtmlAdapter
from stackshot.options import ConvertOptions


def mock_playwright(slide_count):
    locator = Mock(spec_set=Locator)
    locator.count.return_value = slide_count
    page = Mock(spec_set=Page)
    page.locator.return_value = locator
    page.screenshot.side_effect = lambda **kwargs: Path(kwargs["path"]).write_bytes(b"png")
    browser = Mock(spec_set=Browser)
    browser.new_page.return_value = page
    chromium = Mock(spec_set=BrowserType)
    chromium.launch.return_value = browser
    playwright = Mock(spec_set=Playwright)
    playwright.chromium = chromium
    return nullcontext(playwright), page


def test_html_adapter_captures_each_slide_in_a_deck(monkeypatch, tmp_path):
    page = tmp_path / "deck.html"
    page.write_text("<div id='deck'><section class='slide'></section><section class='slide'></section></div>", encoding="utf-8")
    playwright, page_mock = mock_playwright(slide_count=2)
    monkeypatch.setattr("stackshot.adapters.html.sync_playwright", lambda: playwright)

    frames = HtmlAdapter().render(page, tmp_path, ConvertOptions(width=1200))

    assert frames == [tmp_path / "slide-0001.png", tmp_path / "slide-0002.png"]
    page_mock.locator.assert_called_once_with(".slide")
    assert [call.args[1] for call in page_mock.evaluate.call_args_list if len(call.args) > 1] == [0, 1]
    assert all(call.kwargs["full_page"] is False for call in page_mock.screenshot.call_args_list)


def test_html_adapter_uses_full_page_capture_for_regular_html(monkeypatch, tmp_path):
    page = tmp_path / "page.html"
    page.write_text("<main><h1>Hello</h1></main>", encoding="utf-8")
    playwright, page_mock = mock_playwright(slide_count=0)
    monkeypatch.setattr("stackshot.adapters.html.sync_playwright", lambda: playwright)

    frames = HtmlAdapter().render(page, tmp_path, ConvertOptions(width=1200))

    assert frames == [tmp_path / "html.png"]
    page_mock.locator.assert_called_once_with(".slide")
    assert page_mock.screenshot.call_args.kwargs["full_page"] is True
