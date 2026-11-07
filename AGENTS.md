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

## Agent skills

### Issue tracker

GitHub Issues in `coletangsy/stackshot` are the issue tracker. See `docs/agents/issue-tracker.md`.

### Domain docs

This repo uses a single-context domain-doc layout. See `docs/agents/domain.md`.

## Documentation

- [README](README.md) is the command and format support entry point.
- [ARCHITECTURE.md](ARCHITECTURE.md) describes adapters, rendering engines, layout manifests, and stitching.
- [CHANGELOG.md](CHANGELOG.md) records delivered behavior and documentation changes.
- Update `ARCHITECTURE.md` when supported formats, rendering engines, layout semantics, or output contracts change. Update `CHANGELOG.md` for user-visible or operator-visible changes.
