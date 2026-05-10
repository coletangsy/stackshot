from pathlib import Path
from typing import Protocol

from .options import ConvertOptions
from .pipeline import StackshotPipeline


class Pipeline(Protocol):
    def convert(self, input_path: Path, output_path: Path, options: ConvertOptions) -> None:
        ...


def convert(
    input_path: str | Path,
    output_path: str | Path,
    *,
    width: int = 1200,
    scale: float = 1,
    gap: int = 0,
    bg: str = "#ffffff",
    css: str | Path | None = None,
    pipeline: Pipeline | None = None,
) -> None:
    source = Path(input_path)
    if not source.exists():
        raise FileNotFoundError(f"Input file does not exist: {source}")

    options = ConvertOptions(
        width=width,
        scale=scale,
        gap=gap,
        bg=bg,
        css_path=Path(css) if css is not None else None,
    )
    active_pipeline = pipeline or StackshotPipeline.default()
    active_pipeline.convert(source, Path(output_path), options)


__all__ = ["convert", "ConvertOptions"]
