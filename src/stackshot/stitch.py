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


def stitch_document_tiles(
    tiles: list[Path],
    output_path: Path,
    *,
    width: int,
    gap: int = 0,
    bg: str = "#ffffff",
) -> None:
    if not tiles:
        raise ValueError("No document tiles were produced for the layout manifest.")

    left_width = (width - gap) // 2
    right_width = width - gap - left_width
    if left_width <= 0 or right_width <= 0:
        raise ValueError("`gap` must leave room for two document tiles.")

    background = ImageColor.getrgb(bg)
    prepared: list[Image.Image] = []
    try:
        for index, tile in enumerate(tiles):
            cell_width = left_width if index % 2 == 0 else right_width
            with Image.open(tile) as source:
                image = source.convert("RGB")
            if image.width != cell_width:
                ratio = cell_width / image.width
                resized = image.resize(
                    (cell_width, max(1, round(image.height * ratio))),
                    Image.Resampling.LANCZOS,
                )
                image.close()
                image = resized
            prepared.append(image)

        row_heights = [
            max(image.height for image in prepared[index : index + 2])
            for index in range(0, len(prepared), 2)
        ]
        total_height = sum(row_heights) + gap * (len(row_heights) - 1)
        output = Image.new("RGB", (width, total_height), background)

        y = 0
        for index, row_height in enumerate(row_heights):
            left = prepared[index * 2]
            output.paste(left, (0, y))
            right_index = index * 2 + 1
            if right_index < len(prepared):
                output.paste(prepared[right_index], (left_width + gap, y))
            y += row_height + gap
        output.save(output_path, format="PNG")
    finally:
        for image in prepared:
            image.close()
