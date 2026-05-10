from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Protocol

from .options import ConvertOptions
from .stitch import stitch_frames


class Adapter(Protocol):
    def render(self, input_path: Path, work_dir: Path, options: ConvertOptions) -> list[Path]:
        ...


class StackshotPipeline:
    def __init__(self, adapters: dict[str, Adapter]):
        self.adapters = {suffix.lower(): adapter for suffix, adapter in adapters.items()}

    @classmethod
    def default(cls) -> "StackshotPipeline":
        from .adapters.html import HtmlAdapter
        from .adapters.markdown import MarkdownAdapter
        from .adapters.pdf import PdfAdapter
        from .adapters.ppt import PowerPointAdapter

        pdf = PdfAdapter()
        html = HtmlAdapter()
        return cls(
            {
                ".html": html,
                ".htm": html,
                ".md": MarkdownAdapter(html),
                ".markdown": MarkdownAdapter(html),
                ".pdf": pdf,
                ".ppt": PowerPointAdapter(pdf),
                ".pptx": PowerPointAdapter(pdf),
            }
        )

    def convert(self, input_path: Path, output_path: Path, options: ConvertOptions) -> None:
        adapter = self.adapters.get(input_path.suffix.lower())
        if adapter is None:
            supported = ", ".join(sorted(self.adapters))
            raise ValueError(f"Unsupported input format '{input_path.suffix}'. Supported formats: {supported}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix="stackshot-") as temp_dir:
            frames = adapter.render(input_path, Path(temp_dir), options)
            stitch_frames(frames, output_path, width=options.width, gap=options.gap, bg=options.bg)
