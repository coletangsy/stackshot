from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ConvertOptions:
    width: int = 1200
    scale: float = 1
    gap: int = 0
    bg: str = "#ffffff"
    css_path: Path | None = None

    def __post_init__(self) -> None:
        if self.width <= 0:
            raise ValueError("--width must be greater than 0")
        if self.scale <= 0:
            raise ValueError("--scale must be greater than 0")
        if self.gap < 0:
            raise ValueError("--gap cannot be negative")
