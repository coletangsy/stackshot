from pathlib import Path

import fitz

from ..options import ConvertOptions


class PdfAdapter:
    def render(self, input_path: Path, work_dir: Path, options: ConvertOptions) -> list[Path]:
        frames: list[Path] = []
        with fitz.open(input_path) as document:
            for index, page in enumerate(document, start=1):
                page_width = page.rect.width
                zoom = (options.width / page_width) * options.scale
                pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
                frame = work_dir / f"page-{index:04d}.png"
                pixmap.save(frame)
                frames.append(frame)
        return frames
