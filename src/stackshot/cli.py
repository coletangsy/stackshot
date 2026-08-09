import argparse
import sys

from . import convert
from .pipeline import _convert_layout_manifest


class _StoreRenderingOption(argparse.Action):
    def __call__(self, _parser, namespace, values, option_string=None) -> None:
        setattr(namespace, self.dest, values)
        overrides = getattr(namespace, "_rendering_overrides", [])
        overrides.append(option_string or f"--{self.dest.replace('_', '-')}")
        setattr(namespace, "_rendering_overrides", overrides)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stackshot",
        description="Convert Markdown, HTML, PDF, and PowerPoint files into one vertical PNG.",
    )
    parser.add_argument("input", nargs="?", help="Input .md, .html, .pdf, .ppt, or .pptx file")
    parser.add_argument("--config", help="TOML layout manifest")
    parser.add_argument("-o", "--output", required=True, help="Output PNG path")
    parser.add_argument(
        "--width", type=int, default=1200, action=_StoreRenderingOption, help="Output width in pixels"
    )
    parser.add_argument(
        "--scale", type=float, default=1, action=_StoreRenderingOption, help="Rendering scale multiplier"
    )
    parser.add_argument("--gap", type=int, default=0, action=_StoreRenderingOption, help="Gap between frames in pixels")
    parser.add_argument("--bg", default="#ffffff", action=_StoreRenderingOption, help="Background color")
    parser.add_argument(
        "--css", default=None, action=_StoreRenderingOption, help="Optional CSS file for Markdown/HTML rendering"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if bool(args.input) == bool(args.config):
        parser.error("provide either INPUT or --config")
    if args.config:
        overrides = getattr(args, "_rendering_overrides", [])
        if overrides:
            parser.error(f"{', '.join(overrides)} cannot be used with --config")
    try:
        if args.config:
            _convert_layout_manifest(args.config, args.output)
        else:
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
