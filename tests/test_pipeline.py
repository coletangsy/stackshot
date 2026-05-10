from pathlib import Path

import pytest
from PIL import Image

from stackshot.options import ConvertOptions
from stackshot.pipeline import StackshotPipeline


class FakeAdapter:
    def __init__(self, color):
        self.color = color
        self.calls = []

    def render(self, input_path, work_dir, options):
        self.calls.append((Path(input_path), Path(work_dir), options))
        frame = Path(work_dir) / "frame.png"
        Image.new("RGB", (options.width, 10), self.color).save(frame)
        return [frame]


def test_pipeline_selects_adapter_by_extension_and_stitches(tmp_path):
    adapter = FakeAdapter("red")
    pipeline = StackshotPipeline(adapters={".html": adapter})
    source = tmp_path / "page.html"
    target = tmp_path / "out.png"
    source.write_text("<p>Hello</p>", encoding="utf-8")

    pipeline.convert(source, target, ConvertOptions(width=120))

    assert adapter.calls[0][0] == source
    with Image.open(target) as image:
        assert image.size == (120, 10)


def test_pipeline_rejects_unsupported_extension(tmp_path):
    source = tmp_path / "input.txt"
    source.write_text("hello", encoding="utf-8")
    pipeline = StackshotPipeline(adapters={})

    with pytest.raises(ValueError, match="Unsupported input format"):
        pipeline.convert(source, tmp_path / "out.png", ConvertOptions())
