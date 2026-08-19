from pathlib import Path

import pytest
from PIL import Image

from stackshot.stitch import stitch_frames


def make_frame(path: Path, size, color):
    Image.new("RGB", size, color).save(path)


def test_stitch_frames_resizes_to_width_and_applies_gap_and_background(tmp_path):
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    output = tmp_path / "output.png"
    make_frame(first, (50, 10), "red")
    make_frame(second, (100, 20), "blue")

    stitch_frames([first, second], output, width=100, gap=5, bg="#00ff00")

    with Image.open(output) as image:
        assert image.size == (100, 45)
        assert image.getpixel((99, 0)) == (255, 0, 0)
        assert image.getpixel((50, 22)) == (0, 255, 0)
        assert image.getpixel((50, 30)) == (0, 0, 255)


def test_stitch_frames_requires_at_least_one_frame(tmp_path):
    with pytest.raises(ValueError, match="No frames were produced"):
        stitch_frames([], tmp_path / "output.png", width=100)
