from pathlib import Path

import pytest
from PIL import Image

from stackshot.pipeline import StackshotPipeline, _convert_layout_manifest


class FakeAdapter:
    def __init__(self, frames):
        self.frames = frames
        self.calls = []

    def render(self, input_path, work_dir, options):
        self.calls.append((Path(input_path), options))
        rendered = []
        for index, (size, color) in enumerate(self.frames[input_path.name]):
            frame = Path(work_dir) / f"frame-{index}.png"
            Image.new("RGB", size, color).save(frame)
            rendered.append(frame)
        return rendered


def test_layout_manifest_arranges_document_tiles_in_row_major_order(tmp_path):
    config = tmp_path / "layout.toml"
    config.write_text(
        """
columns = 2
inputs = ["red.html", "green.html", "blue.html"]
width = 100
gap = 10
bg = "#010203"
""".strip(),
        encoding="utf-8",
    )
    for name in ("red.html", "green.html", "blue.html"):
        (tmp_path / name).write_text("source", encoding="utf-8")

    pipeline = StackshotPipeline(
        {
            ".html": FakeAdapter(
                {
                    "red.html": [((100, 20), "red")],
                    "green.html": [((100, 40), "green")],
                    "blue.html": [((100, 20), "blue")],
                }
            )
        }
    )
    output = tmp_path / "output.png"

    _convert_layout_manifest(config, output, pipeline=pipeline)

    with Image.open(output) as image:
        assert image.size == (100, 37)
        assert image.getpixel((0, 0)) == (255, 0, 0)
        assert image.getpixel((55, 0)) == (0, 128, 0)
        assert image.getpixel((0, 12)) == (1, 2, 3)
        assert image.getpixel((0, 28)) == (0, 0, 255)
        assert image.getpixel((55, 28)) == (1, 2, 3)


def test_layout_manifest_keeps_multiframe_source_in_one_document_tile(tmp_path):
    config = tmp_path / "layout.toml"
    config.write_text(
        'columns = 2\ninputs = ["multi.html", "single.html"]\nwidth = 100',
        encoding="utf-8",
    )
    for name in ("multi.html", "single.html"):
        (tmp_path / name).write_text("source", encoding="utf-8")

    pipeline = StackshotPipeline(
        {
            ".html": FakeAdapter(
                {
                    "multi.html": [((100, 20), "red"), ((100, 20), "blue")],
                    "single.html": [((100, 20), "green")],
                }
            )
        }
    )
    output = tmp_path / "output.png"

    _convert_layout_manifest(config, output, pipeline=pipeline)

    with Image.open(output) as image:
        assert image.size == (100, 20)
        assert image.getpixel((0, 5)) == (255, 0, 0)
        assert image.getpixel((0, 15)) == (0, 0, 255)
        assert image.getpixel((50, 15)) == (255, 255, 255)


@pytest.mark.parametrize(
    ("manifest", "message"),
    [
        ('columns = 1\ninputs = ["source.html"]', "`columns`"),
        ("columns = 2\ninputs = []", "non-empty list"),
        ('columns = 2\ninputs = ["missing.html"]', "Input file does not exist"),
        ('columns = 2\ninputs = ["source.html"]\ncss = "missing.css"', "Stylesheet does not exist"),
        ('columns = 2\ninputs = ["source.html"]\nrows = 1', "Unsupported layout manifest option"),
        ("not valid TOML", "Invalid layout manifest"),
    ],
)
def test_invalid_layout_manifest_preserves_existing_output(tmp_path, manifest, message):
    (tmp_path / "source.html").write_text("source", encoding="utf-8")
    config = tmp_path / "layout.toml"
    config.write_text(manifest, encoding="utf-8")
    output = tmp_path / "output.png"
    output.write_bytes(b"existing output")

    with pytest.raises((FileNotFoundError, ValueError), match=message):
        _convert_layout_manifest(config, output)

    assert output.read_bytes() == b"existing output"


def test_render_failure_preserves_existing_output(tmp_path):
    config = tmp_path / "layout.toml"
    config.write_text('columns = 2\ninputs = ["source.html"]', encoding="utf-8")
    (tmp_path / "source.html").write_text("source", encoding="utf-8")
    output = tmp_path / "output.png"
    output.write_bytes(b"existing output")

    class BrokenAdapter:
        def render(self, input_path, work_dir, options):
            raise RuntimeError("render failed")

    pipeline = StackshotPipeline({".html": BrokenAdapter()})

    with pytest.raises(RuntimeError, match="render failed"):
        _convert_layout_manifest(config, output, pipeline=pipeline)

    assert output.read_bytes() == b"existing output"


def test_layout_manifest_resolves_relative_paths_and_allows_repeated_sources(tmp_path):
    manifest_dir = tmp_path / "manifest"
    manifest_dir.mkdir()
    source = tmp_path / "source.html"
    source.write_text("source", encoding="utf-8")
    stylesheet = tmp_path / "shared.css"
    stylesheet.write_text("body { color: red; }", encoding="utf-8")
    config = manifest_dir / "layout.toml"
    config.write_text(
        'columns = 2\ninputs = ["../source.html", "../source.html"]\nwidth = 100\ncss = "../shared.css"',
        encoding="utf-8",
    )
    adapter = FakeAdapter({"source.html": [((100, 20), "red")]})
    output = tmp_path / "output.png"

    _convert_layout_manifest(config, output, pipeline=StackshotPipeline({".html": adapter}))

    with Image.open(output) as image:
        assert image.size == (100, 10)
        assert image.getpixel((0, 0)) == (255, 0, 0)
        assert image.getpixel((50, 0)) == (255, 0, 0)
    assert [call[0] for call in adapter.calls] == [source.resolve(), source.resolve()]
    assert all(call[1].css_path == stylesheet.resolve() for call in adapter.calls)


def test_layout_manifest_applies_stylesheet_only_to_web_sources(tmp_path):
    config = tmp_path / "layout.toml"
    config.write_text(
        'columns = 2\ninputs = ["page.html", "document.pdf"]\ncss = "shared.css"',
        encoding="utf-8",
    )
    for name in ("page.html", "document.pdf"):
        (tmp_path / name).write_text("source", encoding="utf-8")
    stylesheet = tmp_path / "shared.css"
    stylesheet.write_text("body { color: red; }", encoding="utf-8")
    html_adapter = FakeAdapter({"page.html": [((1200, 20), "red")]})
    pdf_adapter = FakeAdapter({"document.pdf": [((1200, 20), "blue")]})

    _convert_layout_manifest(
        config,
        tmp_path / "output.png",
        pipeline=StackshotPipeline({".html": html_adapter, ".pdf": pdf_adapter}),
    )

    assert html_adapter.calls[0][1].css_path == stylesheet.resolve()
    assert pdf_adapter.calls[0][1].css_path is None
