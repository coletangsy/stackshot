from dataclasses import replace
from pathlib import Path

from markdown_it import MarkdownIt

from ..options import ConvertOptions
from .html import HtmlAdapter


BUILTIN_CSS = """
body {
  margin: 0;
  background: #ffffff;
}
.markdown-body {
  box-sizing: border-box;
  max-width: 980px;
  margin: 0 auto;
  padding: 48px;
  color: #24292f;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 16px;
  line-height: 1.55;
}
.markdown-body h1,
.markdown-body h2 {
  border-bottom: 1px solid #d0d7de;
  padding-bottom: 0.3em;
}
.markdown-body pre {
  background: #f6f8fa;
  border-radius: 6px;
  overflow: auto;
  padding: 16px;
}
.markdown-body code {
  background: #f6f8fa;
  border-radius: 4px;
  padding: 0.2em 0.4em;
}
.markdown-body pre code {
  background: transparent;
  padding: 0;
}
.markdown-body table {
  border-collapse: collapse;
  width: 100%;
}
.markdown-body th,
.markdown-body td {
  border: 1px solid #d0d7de;
  padding: 6px 13px;
}
.markdown-body img {
  max-width: 100%;
}
"""


def markdown_to_html_document(markdown_text: str, css_text: str | None) -> str:
    renderer = MarkdownIt("commonmark").enable("table")
    body = renderer.render(markdown_text)
    css = BUILTIN_CSS if css_text is None else f"{BUILTIN_CSS}\n{css_text}"
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<style>{css}</style></head><body><main class=\"markdown-body\">"
        f"{body}</main></body></html>"
    )


class MarkdownAdapter:
    def __init__(self, html_adapter: HtmlAdapter | None = None):
        self.html_adapter = html_adapter or HtmlAdapter()

    def render(self, input_path: Path, work_dir: Path, options: ConvertOptions) -> list[Path]:
        markdown_text = input_path.read_text(encoding="utf-8")
        css_text = options.css_path.read_text(encoding="utf-8") if options.css_path else None
        html = markdown_to_html_document(markdown_text, css_text)
        html_path = work_dir / f"{input_path.stem or 'markdown'}.html"
        html_path.write_text(html, encoding="utf-8")
        html_options = replace(options, css_path=None)
        return self.html_adapter.render(html_path, work_dir, html_options)
