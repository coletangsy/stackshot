from pathlib import Path

from stackshot.adapters.html import HtmlAdapter
from stackshot.options import ConvertOptions


class FakeLocator:
    def __init__(self, count):
        self._count = count

    def count(self):
        return self._count


class FakePage:
    def __init__(self, slide_count):
        self.slide_count = slide_count
        self.evaluate_calls = []
        self.screenshots = []

    def goto(self, *_args, **_kwargs):
        return None

    def add_style_tag(self, **_kwargs):
        return None

    def locator(self, selector):
        assert selector == ".slide"
        return FakeLocator(self.slide_count)

    def evaluate(self, script, arg=None):
        self.evaluate_calls.append((script, arg))
        if script == "() => document.fonts ? document.fonts.ready : Promise.resolve()":
            return None
        return None

    def wait_for_timeout(self, _milliseconds):
        return None

    def screenshot(self, **kwargs):
        self.screenshots.append(kwargs)
        Path(kwargs["path"]).write_bytes(b"png")


class FakeBrowser:
    def __init__(self, page):
        self.page = page
        self.closed = False

    def new_page(self, **_kwargs):
        return self.page

    def close(self):
        self.closed = True


class FakeChromium:
    def __init__(self, page):
        self.page = page

    def launch(self):
        return FakeBrowser(self.page)


class FakePlaywright:
    def __init__(self, page):
        self.chromium = FakeChromium(page)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def test_html_adapter_captures_each_slide_in_a_deck(monkeypatch, tmp_path):
    page = tmp_path / "deck.html"
    page.write_text("<div id='deck'><section class='slide'></section><section class='slide'></section></div>", encoding="utf-8")
    fake_page = FakePage(slide_count=2)
    monkeypatch.setattr("stackshot.adapters.html.sync_playwright", lambda: FakePlaywright(fake_page))

    frames = HtmlAdapter().render(page, tmp_path, ConvertOptions(width=1200))

    assert frames == [tmp_path / "slide-0001.png", tmp_path / "slide-0002.png"]
    assert [call[1] for call in fake_page.evaluate_calls if call[1] is not None] == [0, 1]
    assert all(screenshot["full_page"] is False for screenshot in fake_page.screenshots)


def test_html_adapter_uses_full_page_capture_for_regular_html(monkeypatch, tmp_path):
    page = tmp_path / "page.html"
    page.write_text("<main><h1>Hello</h1></main>", encoding="utf-8")
    fake_page = FakePage(slide_count=0)
    monkeypatch.setattr("stackshot.adapters.html.sync_playwright", lambda: FakePlaywright(fake_page))

    frames = HtmlAdapter().render(page, tmp_path, ConvertOptions(width=1200))

    assert frames == [tmp_path / "html.png"]
    assert fake_page.screenshots[0]["full_page"] is True
