from pathlib import Path

from playwright.sync_api import sync_playwright

from ..options import ConvertOptions


class HtmlAdapter:
    def render(self, input_path: Path, work_dir: Path, options: ConvertOptions) -> list[Path]:
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                page = browser.new_page(
                    viewport={"width": options.width, "height": 900},
                    device_scale_factor=options.scale,
                )
                page.goto(input_path.resolve().as_uri(), wait_until="networkidle")
                if options.css_path is not None:
                    page.add_style_tag(path=str(options.css_path))
                page.evaluate("() => document.fonts ? document.fonts.ready : Promise.resolve()")
                frames = self._capture_frames(page, work_dir)
                browser.close()
        except Exception as exc:
            message = str(exc)
            if "Executable doesn't exist" in message or "playwright install" in message.lower():
                raise RuntimeError(
                    "Playwright browser dependencies are missing. "
                    "Run `uv run playwright install chromium` and retry."
                ) from exc
            raise
        return frames

    def _capture_frames(self, page, work_dir: Path) -> list[Path]:
        slide_count = page.locator(".slide").count()
        if slide_count > 1:
            return self._capture_slide_deck(page, work_dir, slide_count)

        output = work_dir / "html.png"
        page.screenshot(path=str(output), full_page=True, omit_background=False)
        return [output]

    def _capture_slide_deck(self, page, work_dir: Path, slide_count: int) -> list[Path]:
        frames: list[Path] = []
        for index in range(slide_count):
            page.evaluate(SHOW_SLIDE_SCRIPT, index)
            page.wait_for_timeout(120)
            frame = work_dir / f"slide-{index + 1:04d}.png"
            page.screenshot(path=str(frame), full_page=False, omit_background=False)
            frames.append(frame)
        return frames


SHOW_SLIDE_SCRIPT = """
(index) => {
  const slides = Array.from(document.querySelectorAll('.slide'));
  const deck = document.getElementById('deck') || slides[0]?.parentElement;
  if (deck) {
    deck.style.transition = 'none';
    deck.style.width = `${slides.length * 100}vw`;
    deck.style.transform = `translateX(${-index * 100}vw)`;
  }
  slides.forEach((slide, i) => slide.classList.toggle('active', i === index));
  document.querySelectorAll('.dot').forEach((dot, i) => dot.classList.toggle('active', i === index));
  const active = slides[index];
  if (active) {
    const theme = active.dataset.theme || (active.classList.contains('light') ? 'light' : 'dark');
    document.body.classList.toggle('light-bg', theme === 'light');
  }
}
"""
