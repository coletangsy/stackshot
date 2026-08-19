import argparse
import sys

from . import convert
from .pipeline import _convert_layout_manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stackshot",
        description="Convert Markdown, HTML, PDF, and PowerPoint files into one vertical PNG.",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("input", nargs="?", help="Input .md, .html, .pdf, .ppt, or .pptx file")
    source.add_argument("--config", help="TOML layout manifest")
    parser.add_argument("-o", "--output", required=True, help="Output PNG path")
    parser.add_argument("--width", type=int, default=argparse.SUPPRESS, help="Output width in pixels")
    parser.add_argument(
        "--scale", type=float, default=argparse.SUPPRESS, help="Rendering scale multiplier"
    )
    parser.add_argument("--gap", type=int, default=argparse.SUPPRESS, help="Gap between frames in pixels")
    parser.add_argument("--bg", default=argparse.SUPPRESS, help="Background color")
    parser.add_argument(
        "--css", default=argparse.SUPPRESS, help="Optional CSS file for Markdown/HTML rendering"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    rendering_options = {
        name: value for name, value in vars(args).items() if name not in {"input", "config", "output"}
    }
    if args.config and rendering_options:
        overrides = ", ".join(f"--{name}" for name in rendering_options)
        parser.error(f"{overrides} cannot be used with --config")
    try:
        if args.config:
            _convert_layout_manifest(args.config, args.output)
        else:
            convert(args.input, args.output, **rendering_options)
    except Exception as exc:
        print(f"stackshot: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
