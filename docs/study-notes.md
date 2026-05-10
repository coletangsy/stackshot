# Stackshot Study Notes

## Project Purpose

`stackshot` converts document-like input files into one vertical PNG. It is designed for cases where a user wants a single long image from content that may originally be paged, slide-based, or scrollable.

Supported inputs:

- Markdown: `.md`, `.markdown`
- HTML: `.html`, `.htm`
- PDF: `.pdf`
- PowerPoint: `.ppt`, `.pptx`

Output:

- One stitched PNG file

The default output width is `1200` pixels. Rendering options can change width, scale, frame gap, background color, and optional CSS for Markdown or HTML rendering.

## Tech Stack

- Python 3.11 or newer: runtime language and package baseline.
- `uv`: dependency management, local execution, lockfile updates, tests, and builds.
- Pillow: image loading, resizing, background creation, frame pasting, and final PNG writing.
- Playwright: Chromium-based rendering for HTML and Markdown-derived HTML.
- PyMuPDF: PDF page rasterization.
- `markdown-it-py`: Markdown to HTML conversion with CommonMark and table support.
- pytest: automated test runner.
- LibreOffice or `soffice`: external dependency for PowerPoint-to-PDF conversion.

HTML and Markdown rendering require Playwright Chromium browser binaries:

```sh
uv run playwright install chromium
```

PowerPoint conversion requires either `libreoffice` or `soffice` on `PATH`.

## Repository Structure

```text
stackshot/
├── src/stackshot/
│   ├── __init__.py
│   ├── cli.py
│   ├── options.py
│   ├── pipeline.py
│   ├── stitch.py
│   └── adapters/
│       ├── __init__.py
│       ├── html.py
│       ├── markdown.py
│       ├── pdf.py
│       └── ppt.py
├── tests/
├── README.md
├── AGENTS.md
├── pyproject.toml
└── uv.lock
```

Major modules:

- `src/stackshot/__init__.py`: public Python API. Exposes `convert()` and `ConvertOptions`.
- `src/stackshot/cli.py`: `argparse` command-line interface for the `stackshot` console script.
- `src/stackshot/options.py`: immutable conversion options dataclass and basic option validation.
- `src/stackshot/pipeline.py`: adapter registry, format selection, temporary working directory setup, and final stitching call.
- `src/stackshot/stitch.py`: combines rendered frame images into one vertical PNG.
- `src/stackshot/adapters/html.py`: renders HTML with Playwright and handles regular pages and `.slide` decks.
- `src/stackshot/adapters/markdown.py`: converts Markdown to a styled temporary HTML document, then delegates rendering to the HTML adapter.
- `src/stackshot/adapters/pdf.py`: renders each PDF page into a PNG frame with PyMuPDF.
- `src/stackshot/adapters/ppt.py`: converts PowerPoint to PDF with LibreOffice, then delegates rendering to the PDF adapter.
- `tests/`: focused tests for API behavior, CLI parsing, pipeline selection, stitching, Markdown HTML generation, HTML slide handling, and dependency errors.

## End-to-End Conversion Flow

The conversion path is intentionally simple:

1. A caller invokes either the CLI or the Python API.
2. Input and output paths plus rendering options are normalized into `ConvertOptions`.
3. `StackshotPipeline.default()` creates the default adapter map.
4. The pipeline selects an adapter from the input file suffix.
5. The selected adapter renders one or more temporary frame PNG files.
6. `stitch_frames()` loads the frames, resizes them to the requested output width when needed, inserts optional gaps, and saves one final vertical PNG.

The API entrypoint is `convert()`:

```python
from stackshot import convert

convert("input.md", "output.png", width=1200)
```

The CLI entrypoint calls the same API:

```sh
uv run stackshot input.md -o output.png
```

Full option example:

```sh
uv run stackshot INPUT -o OUTPUT --width 1200 --scale 1 --gap 0 --bg "#ffffff" --css custom.css
```

## Options

`ConvertOptions` currently contains:

- `width`: target output width in pixels. Must be greater than `0`.
- `scale`: rendering scale multiplier. Must be greater than `0`.
- `gap`: vertical space between rendered frames in pixels. Cannot be negative.
- `bg`: background color passed to Pillow when creating the final image.
- `css_path`: optional CSS path for Markdown and HTML rendering.

Validation happens in `ConvertOptions.__post_init__()`. Missing input files are rejected in the public `convert()` function before the pipeline runs.

## Adapter Selection

`StackshotPipeline.default()` wires suffixes to adapter instances:

- `.html`, `.htm` -> `HtmlAdapter`
- `.md`, `.markdown` -> `MarkdownAdapter`
- `.pdf` -> `PdfAdapter`
- `.ppt`, `.pptx` -> `PowerPointAdapter`

If the suffix is unsupported, the pipeline raises a `ValueError` listing supported formats.

The pipeline creates a `TemporaryDirectory` with a `stackshot-` prefix. Adapters write intermediate HTML, PDF, or PNG files there. The final output directory is created before rendering.

## Markdown Adapter

Markdown conversion is a two-step process:

1. `markdown_to_html_document()` renders Markdown using `MarkdownIt("commonmark").enable("table")`.
2. The adapter writes the generated HTML into the temporary work directory and delegates to `HtmlAdapter`.

The generated HTML wraps content in:

```html
<main class="markdown-body">
```

The built-in CSS gives Markdown GitHub-like defaults for typography, headings, code blocks, tables, and images. If `--css` or `css=` is provided, that CSS is appended to the built-in CSS.

The Markdown adapter clears `css_path` before delegating to HTML because it already inlined the custom CSS into the generated document.

## HTML Adapter

HTML rendering uses Playwright Chromium:

1. Launch Chromium.
2. Open a new page with viewport width from `options.width` and a fixed `900` pixel viewport height.
3. Navigate to the local file URI and wait for `networkidle`.
4. Add optional CSS with `page.add_style_tag()`.
5. Wait for document fonts when the browser supports `document.fonts.ready`.
6. Capture frames.
7. Close the browser.

For ordinary HTML pages, the adapter captures one full-page screenshot.

For HTML decks with more than one `.slide` element, the adapter captures each slide state separately. The helper script:

- Finds `.slide` elements.
- Uses `#deck` or the first slide's parent as the deck container.
- Disables transitions.
- Sets deck width based on slide count.
- Translates the deck to the requested slide.
- Toggles `active` classes on slides and `.dot` elements.
- Toggles `body.light-bg` based on slide theme data or classes.

This lets JavaScript-style slide decks become a vertical stack of slide screenshots instead of one wide or hidden deck state.

If Playwright browser binaries are missing, the adapter raises a clearer runtime error telling the user to run:

```sh
uv run playwright install chromium
```

## PDF Adapter

PDF rendering uses PyMuPDF:

1. Open the document with `fitz.open()`.
2. Iterate pages in order.
3. Compute zoom from requested output width and page width.
4. Render each page with `page.get_pixmap()`.
5. Save each page frame as `page-0001.png`, `page-0002.png`, and so on.
6. Close the document in a `finally` block.

The adapter renders with `alpha=False`, so frames are RGB-like images without transparent backgrounds.

## PowerPoint Adapter

PowerPoint rendering is implemented by delegation:

1. Locate `libreoffice` or `soffice` on `PATH`.
2. Run LibreOffice headlessly with `--convert-to pdf`.
3. Find the produced PDF in the temporary work directory.
4. Delegate the PDF to `PdfAdapter`.

If LibreOffice is not available, the adapter raises a runtime error explaining the dependency. If LibreOffice exits nonzero, stderr or stdout is included in the raised error. If conversion reports success but no PDF appears, the adapter raises a specific error for that case.

## Stitching Logic

`stitch_frames()` turns adapter frames into the final PNG:

1. Reject an empty frame list.
2. Parse the background color with `ImageColor.getrgb()`.
3. Open each frame and convert it to RGB.
4. Resize any frame whose width does not match the target width.
5. Compute final image height from frame heights and requested gaps.
6. Allocate one RGB output image.
7. Paste each frame from top to bottom.
8. Save the result as PNG.
9. Close all opened image objects.

If Pillow cannot allocate the final image, the function raises a runtime error with the attempted image size and notes that automatic splitting is out of scope for v1.

## CLI Examples

Markdown:

```sh
uv run stackshot notes.md -o notes.png
```

HTML:

```sh
uv run stackshot page.html -o page.png --width 1200
```

PDF:

```sh
uv run stackshot report.pdf -o report-long.png --gap 16 --bg "#ffffff"
```

PowerPoint:

```sh
uv run stackshot deck.pptx -o deck-long.png --width 1600
```

Custom CSS for Markdown or HTML:

```sh
uv run stackshot input.md -o output.png --css custom.css
```

## Python API Examples

Basic conversion:

```python
from stackshot import convert

convert("input.pdf", "output.png")
```

Custom size and spacing:

```python
from stackshot import convert

convert(
    "slides.pptx",
    "slides-long.png",
    width=1600,
    scale=1.5,
    gap=24,
    bg="#ffffff",
)
```

Custom CSS:

```python
from stackshot import convert

convert("notes.md", "notes.png", css="custom.css")
```

Injecting a custom pipeline for tests or advanced integration:

```python
from stackshot import convert

convert("input.html", "output.png", pipeline=my_pipeline)
```

## Error Handling

Important error paths:

- Missing input file: `convert()` raises `FileNotFoundError`.
- Invalid options: `ConvertOptions` raises `ValueError`.
- Unsupported suffix: `StackshotPipeline.convert()` raises `ValueError`.
- No frames from an adapter: `stitch_frames()` raises `ValueError`.
- Missing Playwright browser binaries: `HtmlAdapter` raises a runtime error with the install command.
- Missing LibreOffice: `PowerPointAdapter` raises a runtime error.
- LibreOffice conversion failure: `PowerPointAdapter` raises a runtime error with command output details.
- Final image allocation failure: `stitch_frames()` raises a runtime error that includes the attempted dimensions.

## Test Suite Overview

The tests are small and module-focused:

- `tests/test_api_and_cli.py`: public API defaults, custom options, missing input behavior, and CLI parser flags.
- `tests/test_pipeline.py`: adapter selection, output stitching through a fake adapter, and unsupported format errors.
- `tests/test_markdown.py`: Markdown HTML output, built-in CSS inclusion, and custom CSS appending.
- `tests/test_html_adapter.py`: deck capture behavior for multiple `.slide` elements and full-page capture for ordinary HTML.
- `tests/test_stitch.py`: frame stacking, resizing, gaps, backgrounds, and empty-frame errors.
- `tests/test_dependency_errors.py`: clearer dependency errors for Playwright and LibreOffice cases.

The suite avoids full browser and office integration where possible by using fakes and monkeypatching. This keeps most tests fast and deterministic.

## Development Commands

Install dependencies:

```sh
uv sync
```

Install Playwright Chromium for local HTML and Markdown rendering:

```sh
uv run playwright install chromium
```

Run tests:

```sh
uv run pytest
```

Run the CLI locally:

```sh
uv run stackshot input.html -o output.png
```

Build the package:

```sh
uv build
```

## Design Notes For Contributors

- Keep format-specific behavior in `src/stackshot/adapters/`.
- Prefer delegating common rendering paths instead of duplicating logic. Markdown delegates to HTML, and PowerPoint delegates to PDF.
- Keep adapter outputs as frame PNGs; let `stitch_frames()` own final image composition.
- When adding a new input format, add an adapter, register its suffixes in `StackshotPipeline.default()`, and cover adapter selection plus format-specific behavior in tests.
- Keep dependency errors actionable. The CLI catches exceptions and prints `stackshot: ...` to stderr, so exception messages should be clear on their own.
