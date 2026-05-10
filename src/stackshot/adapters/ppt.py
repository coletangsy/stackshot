import shutil
import subprocess
from pathlib import Path

from ..options import ConvertOptions
from .pdf import PdfAdapter


class PowerPointAdapter:
    def __init__(self, pdf_adapter: PdfAdapter | None = None):
        self.pdf_adapter = pdf_adapter or PdfAdapter()

    def render(self, input_path: Path, work_dir: Path, options: ConvertOptions) -> list[Path]:
        executable = shutil.which("libreoffice") or shutil.which("soffice")
        if executable is None:
            raise RuntimeError(
                "LibreOffice is required to convert PowerPoint files. "
                "Install LibreOffice and ensure `libreoffice` or `soffice` is on PATH."
            )

        result = subprocess.run(
            [
                executable,
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(work_dir),
                str(input_path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            details = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(f"LibreOffice failed to convert PowerPoint to PDF. {details}")

        pdf_path = work_dir / f"{input_path.stem}.pdf"
        if not pdf_path.exists():
            matches = sorted(work_dir.glob("*.pdf"))
            if not matches:
                raise RuntimeError("LibreOffice conversion completed but did not produce a PDF.")
            pdf_path = matches[0]
        return self.pdf_adapter.render(pdf_path, work_dir, options)
