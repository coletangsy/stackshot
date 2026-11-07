# stackshot Architecture

## Purpose and boundary

`stackshot` converts Markdown, HTML, PDF, and PowerPoint documents into one vertical PNG. It is a local Python package and CLI; it does not publish documents or retain a remote document store.

## Rendering flow

```text
CLI (`src/stackshot/cli.py`) or Python API
        ↓
options + optional layout manifest
        ↓
format adapter (`src/stackshot/adapters/`)
  ├─ Markdown → styled HTML
  ├─ HTML → page or slide states
  ├─ PDF → rendered page images
  └─ PPT/PPTX → LibreOffice PDF → page images
        ↓
pipeline (`pipeline.py`) → stitch (`stitch.py`)
        ↓
one vertical PNG
```

`options.py` normalizes width, scale, gap, background, CSS, and manifest settings. Markdown and HTML use Playwright Chromium for browser rendering; PDF uses PyMuPDF; PowerPoint depends on `soffice`/LibreOffice. `pipeline.py` resolves the appropriate adapter, captures frames, and sends them to the stitcher. The Python API in `__init__.py` shares this path with the CLI.

For HTML slide decks, the adapter captures each `.slide` state separately; ordinary scrolling pages use a full-page screenshot. Format-specific behavior stays in its adapter so each path remains independently testable.

## Operational boundaries

- Use `uv sync`, `uv run pytest`, `uv run stackshot ...`, and `uv build` for normal checks.
- Install Chromium with `uv run playwright install chromium` when rendering HTML or Markdown. LibreOffice is required for PPT/PPTX.
- Output PNGs are caller-owned artifacts. Keep temporary source documents, browser state, and generated outputs outside the repository unless a fixture or example is intentionally tracked.
