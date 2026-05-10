from pathlib import Path

from PIL import Image, ImageColor


def stitch_frames(
    frames: list[Path],
    output_path: Path,
    *,
    width: int,
    gap: int = 0,
    bg: str = "#ffffff",
) -> None:
    if not frames:
        raise ValueError("No frames were produced for the input file.")

    background = ImageColor.getrgb(bg)
    prepared: list[Image.Image] = []
    try:
        for frame in frames:
            image = Image.open(frame).convert("RGB")
            if image.width != width:
                ratio = width / image.width
                image = image.resize((width, max(1, round(image.height * ratio))), Image.Resampling.LANCZOS)
            prepared.append(image)

        total_height = sum(image.height for image in prepared) + gap * (len(prepared) - 1)
        try:
            output = Image.new("RGB", (width, total_height), background)
        except Exception as exc:
            raise RuntimeError(
                f"Could not allocate one PNG of size {width}x{total_height}. "
                "The input may exceed local image limits; auto-splitting is out of scope for v1."
            ) from exc

        y = 0
        for image in prepared:
            output.paste(image, (0, y))
            y += image.height + gap
        output.save(output_path, format="PNG")
    finally:
        for image in prepared:
            image.close()
