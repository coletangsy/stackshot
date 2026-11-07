# stackshot

`stackshot` converts Markdown, HTML, PDF, and PowerPoint files into one vertical PNG.

## Maintainer Documentation

- [Repository guidance](AGENTS.md)
- [Architecture overview](ARCHITECTURE.md)
- [Changelog](CHANGELOG.md)

## Usage

```sh
uv sync
uv run stackshot input.md -o output.png
uv run stackshot input.pdf -o output.png
uv run stackshot input.pptx -o output.png
uv run stackshot input.html -o output.png
uv run pytest
uv build
```

The default output width is `1200px`.

```sh
uv run stackshot INPUT -o OUTPUT --width 1200 --scale 1 --gap 0 --bg "#ffffff" --css custom.css
```

Markdown uses built-in GitHub-like CSS unless `--css` is provided.

## Layout manifests

Use `--config` to compose local source documents into a two-column PNG:

```sh
uv run stackshot --config layout.toml -o comparison.png
```

```toml
columns = 2
inputs = ["left.md", "right.pdf", "appendix.pptx"]
width = 1200
gap = 16
bg = "#ffffff"
css = "shared.css"
```

`inputs` and `css` paths are relative to the manifest. The optional `width`,
`scale`, `gap`, and `bg` values apply to every source; use the manifest rather
than rendering flags with `--config`. The stylesheet applies only to Markdown
and HTML sources.

## Python API

```python
from stackshot import convert

convert("input.md", "output.png", width=1200)
```

## Runtime Dependencies

HTML and Markdown rendering uses Playwright. Install browser binaries with:

```sh
uv run playwright install chromium
```

PowerPoint conversion requires LibreOffice or `soffice` on `PATH`.

## HTML Slide Decks

For HTML decks that use `.slide` elements and JavaScript navigation, `stackshot` captures each slide state separately and stitches those screenshots vertically. Regular scrolling HTML pages still use a normal full-page screenshot.
