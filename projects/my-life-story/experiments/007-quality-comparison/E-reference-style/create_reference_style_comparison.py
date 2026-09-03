"""Render a side-by-side audit of the episode-007 reference-style redesign."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).parent
CELL_WIDTH = 640
CELL_HEIGHT = 880
HEADER_HEIGHT = 72
GUTTER = 28


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def place(
    canvas: Image.Image,
    source: Path,
    label: str,
    column: int,
    row: int,
) -> None:
    x = GUTTER + column * (CELL_WIDTH + GUTTER)
    y = GUTTER + row * (CELL_HEIGHT + HEADER_HEIGHT + GUTTER)
    draw = ImageDraw.Draw(canvas)
    draw.text((x, y), label, fill=(28, 27, 26), font=font(30))
    image = Image.open(source).convert("RGB")
    fitted = ImageOps.contain(image, (CELL_WIDTH, CELL_HEIGHT), Image.Resampling.LANCZOS)
    tile = Image.new("RGB", (CELL_WIDTH, CELL_HEIGHT), "white")
    tile.paste(
        fitted,
        ((CELL_WIDTH - fitted.width) // 2, (CELL_HEIGHT - fitted.height) // 2),
    )
    canvas.paste(tile, (x, y + HEADER_HEIGHT))


def main() -> None:
    canvas = Image.new(
        "RGB",
        (
            GUTTER * 3 + CELL_WIDTH * 2,
            GUTTER * 3 + (CELL_HEIGHT + HEADER_HEIGHT) * 2,
        ),
        (238, 236, 232),
    )
    place(
        canvas,
        ROOT / "export" / "007.v3.png.bak",
        "Before: dense diagram",
        0,
        0,
    )
    place(canvas, HERE / "source.png", "New sparse control", 1, 0)
    place(
        canvas,
        HERE / "generated-base" / "007_2001115_01.png",
        "SD1.5 img2img (production)",
        0,
        1,
    )
    place(
        canvas,
        HERE / "generated" / "007_2001114_01.png",
        "DreamShaper img2img (test)",
        1,
        1,
    )
    canvas.save(HERE / "reference-style-comparison.png")


if __name__ == "__main__":
    main()
