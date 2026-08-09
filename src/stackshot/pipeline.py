import tomllib
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Protocol

from .options import ConvertOptions
from .stitch import stitch_document_tiles, stitch_frames


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
        adapter = self._adapter_for(input_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix="stackshot-") as temp_dir:
            frames = adapter.render(input_path, Path(temp_dir), options)
            stitch_frames(frames, output_path, width=options.width, gap=options.gap, bg=options.bg)

    def _adapter_for(self, input_path: Path) -> Adapter:
        adapter = self.adapters.get(input_path.suffix.lower())
        if adapter is None:
            supported = ", ".join(sorted(self.adapters))
            raise ValueError(f"Unsupported input format '{input_path.suffix}'. Supported formats: {supported}")
        return adapter

    def _convert_layout(self, sources: list[Path], output_path: Path, options: ConvertOptions) -> None:
        adapters = [self._adapter_for(source) for source in sources]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix="stackshot-", dir=output_path.parent) as temp_dir:
            work_root = Path(temp_dir)
            tiles: list[Path] = []
            for index, (source, adapter) in enumerate(zip(sources, adapters, strict=True)):
                work_dir = work_root / f"source-{index}"
                work_dir.mkdir()
                render_options = options
                if source.suffix.lower() not in {".html", ".htm", ".md", ".markdown"}:
                    render_options = replace(options, css_path=None)
                frames = adapter.render(source, work_dir, render_options)
                tile = work_root / f"tile-{index}.png"
                stitch_frames(frames, tile, width=options.width, gap=options.gap, bg=options.bg)
                tiles.append(tile)
            rendered_output = work_root / "output.png"
            stitch_document_tiles(tiles, rendered_output, width=options.width, gap=options.gap, bg=options.bg)
            rendered_output.replace(output_path)


_MANIFEST_FIELDS = {"columns", "inputs", "width", "scale", "gap", "bg", "css"}


def _convert_layout_manifest(
    config_path: str | Path,
    output_path: str | Path,
    *,
    pipeline: StackshotPipeline | None = None,
) -> None:
    sources, options = _read_layout_manifest(Path(config_path))
    active_pipeline = pipeline or StackshotPipeline.default()
    active_pipeline._convert_layout(sources, Path(output_path), options)


def _read_layout_manifest(config_path: Path) -> tuple[list[Path], ConvertOptions]:
    if not config_path.is_file():
        raise FileNotFoundError(f"Layout manifest does not exist: {config_path}")

    try:
        manifest = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"Invalid layout manifest: {exc}") from exc

    unsupported = sorted(set(manifest) - _MANIFEST_FIELDS)
    if unsupported:
        raise ValueError(f"Unsupported layout manifest option(s): {', '.join(unsupported)}")

    columns = manifest.get("columns")
    if not _is_int(columns) or columns != 2:
        raise ValueError("Layout manifest `columns` must be the integer 2.")

    inputs = manifest.get("inputs")
    if not isinstance(inputs, list) or not inputs:
        raise ValueError("Layout manifest `inputs` must be a non-empty list.")
    if not all(isinstance(item, str) and item for item in inputs):
        raise ValueError("Layout manifest `inputs` must contain file paths.")

    width = manifest.get("width", 1200)
    scale = manifest.get("scale", 1)
    gap = manifest.get("gap", 0)
    bg = manifest.get("bg", "#ffffff")
    css = manifest.get("css")
    if not _is_int(width) or not _is_number(scale) or not _is_int(gap) or not isinstance(bg, str):
        raise ValueError("Layout manifest rendering options have invalid types.")
    if css is not None and not isinstance(css, str):
        raise ValueError("Layout manifest `css` must be a file path.")

    base_dir = config_path.resolve().parent
    sources = [(base_dir / item).resolve() for item in inputs]
    for source in sources:
        if not source.is_file():
            raise FileNotFoundError(f"Input file does not exist: {source}")

    css_path = (base_dir / css).resolve() if css is not None else None
    if css_path is not None and not css_path.is_file():
        raise FileNotFoundError(f"Stylesheet does not exist: {css_path}")

    return sources, ConvertOptions(width=width, scale=scale, gap=gap, bg=bg, css_path=css_path)


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)
