from pathlib import Path

import pytest

from stackshot import convert
from stackshot.cli import build_parser, main


class RecordingPipeline:
    def __init__(self):
        self.calls = []

    def convert(self, input_path, output_path, options):
        self.calls.append((Path(input_path), Path(output_path), options))


def test_convert_uses_defaults_and_accepts_paths(tmp_path):
    source = tmp_path / "input.html"
    target = tmp_path / "output.png"
    source.write_text("<h1>Hello</h1>", encoding="utf-8")
    pipeline = RecordingPipeline()

    convert(source, target, pipeline=pipeline)

    assert pipeline.calls[0][0] == source
    assert pipeline.calls[0][1] == target
    assert pipeline.calls[0][2].width == 1200
    assert pipeline.calls[0][2].scale == 1
    assert pipeline.calls[0][2].gap == 0
    assert pipeline.calls[0][2].bg == "#ffffff"
    assert pipeline.calls[0][2].css_path is None


def test_convert_passes_custom_options(tmp_path):
    source = tmp_path / "input.md"
    target = tmp_path / "output.png"
    css = tmp_path / "custom.css"
    source.write_text("# Hello", encoding="utf-8")
    css.write_text("body { color: red; }", encoding="utf-8")
    pipeline = RecordingPipeline()

    convert(source, target, width=800, scale=2, gap=12, bg="#101010", css=css, pipeline=pipeline)

    options = pipeline.calls[0][2]
    assert options.width == 800
    assert options.scale == 2
    assert options.gap == 12
    assert options.bg == "#101010"
    assert options.css_path == css


def test_convert_rejects_missing_input(tmp_path):
    with pytest.raises(FileNotFoundError, match="Input file does not exist"):
        convert(tmp_path / "missing.md", tmp_path / "output.png")


def test_cli_parser_exposes_requested_flags():
    args = build_parser().parse_args(
        [
            "input.md",
            "-o",
            "output.png",
            "--width",
            "900",
            "--scale",
            "2",
            "--gap",
            "8",
            "--bg",
            "#eeeeee",
            "--css",
            "style.css",
        ]
    )

    assert args.input == "input.md"
    assert args.output == "output.png"
    assert args.width == 900
    assert args.scale == 2
    assert args.gap == 8
    assert args.bg == "#eeeeee"
    assert args.css == "style.css"


def test_cli_config_uses_manifest_and_keeps_output_on_the_command_line(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "stackshot.cli._convert_layout_manifest",
        lambda config, output: calls.append((config, output)),
    )

    assert main(["--config", "layout.toml", "-o", "output.png"]) == 0

    assert calls == [("layout.toml", "output.png")]


def test_cli_single_input_still_uses_convert_defaults(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "stackshot.cli.convert",
        lambda input_path, output_path, **options: calls.append((input_path, output_path, options)),
    )

    assert main(["input.md", "-o", "output.png"]) == 0

    assert calls == [
        (
            "input.md",
            "output.png",
            {},
        )
    ]


def test_cli_rejects_rendering_overrides_with_a_layout_manifest():
    with pytest.raises(SystemExit):
        main(["--config", "layout.toml", "-o", "output.png", "--width", "900"])


@pytest.mark.parametrize("source", [[""], ["--config", ""]])
def test_cli_rejects_empty_source(source):
    with pytest.raises(SystemExit):
        main([*source, "-o", "output.png"])
