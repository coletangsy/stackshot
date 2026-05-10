# Agent Notes

## Project Workflow

Use `uv` for dependency management, local execution, tests, locking, and builds.

Common commands:

```sh
uv sync
uv run pytest
uv run stackshot input.html -o output.png
uv build
```

HTML and Markdown rendering require Playwright Chromium:

```sh
uv run playwright install chromium
```

PowerPoint conversion requires LibreOffice or `soffice` on `PATH`.

## Implementation Notes

`stackshot` renders input files into frame images and stitches them into one vertical PNG.

- Markdown is converted to styled HTML, then rendered by Playwright.
- HTML is rendered by Playwright. Multi-slide HTML decks using `.slide` elements are captured one slide state at a time.
- PDF pages are rendered with PyMuPDF.
- PPT/PPTX files are converted to PDF with LibreOffice, then rendered as PDF pages.

Keep format-specific behavior in `src/stackshot/adapters/` so adapters remain independently testable.
