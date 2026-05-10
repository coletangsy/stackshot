import argparse
import sys

from . import convert


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stackshot",
        description="Convert Markdown, HTML, PDF, and PowerPoint files into one vertical PNG.",
    )
    parser.add_argument("input", help="Input .md, .html, .pdf, .ppt, or .pptx file")
    parser.add_argument("-o", "--output", required=True, help="Output PNG path")
    parser.add_argument("--width", type=int, default=1200, help="Output width in pixels")
    parser.add_argument("--scale", type=float, default=1, help="Rendering scale multiplier")
    parser.add_argument("--gap", type=int, default=0, help="Gap between frames in pixels")
    parser.add_argument("--bg", default="#ffffff", help="Background color")
    parser.add_argument("--css", default=None, help="Optional CSS file for Markdown/HTML rendering")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        convert(
            args.input,
            args.output,
            width=args.width,
            scale=args.scale,
            gap=args.gap,
            bg=args.bg,
            css=args.css,
        )
    except Exception as exc:
        print(f"stackshot: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
