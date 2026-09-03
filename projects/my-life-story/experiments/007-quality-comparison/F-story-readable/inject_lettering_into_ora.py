"""Add the episode-specific balloon and lettering layers to a comparison ORA.

This is a one-page finishing script for the experiment.  It does not modify the
repository compose helper and never puts lettering into the Comfy source.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from PIL import Image


HERE = Path(__file__).parent
SOURCE = HERE / "page.base.ora"
OUTPUT = HERE / "page.compose.ora"
BALLOON = HERE / "balloon.png"
LETTERING = HERE / "lettering.png"


def png_bytes(image: Image.Image) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def place_on_page(source: Path, page_size: tuple[int, int]) -> Image.Image:
    image = Image.open(source).convert("RGBA")
    page_width, page_height = page_size
    scale = min(page_width / image.width, page_height / image.height)
    target_size = (round(image.width * scale), round(image.height * scale))
    resized = image.resize(target_size, Image.Resampling.LANCZOS)
    layer = Image.new("RGBA", page_size, (0, 0, 0, 0))
    layer.alpha_composite(
        resized,
        ((page_width - target_size[0]) // 2, (page_height - target_size[1]) // 2),
    )
    return layer


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite {OUTPUT}")

    with ZipFile(SOURCE, "r") as source_zip:
        stack = ET.fromstring(source_zip.read("stack.xml"))
        for group in stack.iter("stack"):
            text_layer = next(
                (child for child in group if child.attrib.get("name") == "文字"), None
            )
            balloon_layer = next(
                (child for child in group if child.attrib.get("name") == "フキダシ"), None
            )
            if text_layer is not None and balloon_layer is not None:
                group.remove(text_layer)
                group.remove(balloon_layer)
                group.insert(0, text_layer)
                group.insert(1, balloon_layer)
                break

        merged = Image.open(BytesIO(source_zip.read("mergedimage.png"))).convert("RGBA")
        page_size = merged.size
        balloon = place_on_page(BALLOON, page_size)
        lettering = place_on_page(LETTERING, page_size)
        finished = Image.alpha_composite(Image.alpha_composite(merged, balloon), lettering)

        thumbnail_name = "Thumbnails/thumbnail.png"
        thumbnail = Image.open(BytesIO(source_zip.read(thumbnail_name))).convert("RGBA")
        finished_thumbnail = finished.copy()
        finished_thumbnail.thumbnail(thumbnail.size, Image.Resampling.LANCZOS)

        replacements = {
            "data/layer-00.png": png_bytes(balloon),
            "data/layer-01.png": png_bytes(lettering),
            "stack.xml": ET.tostring(stack, encoding="utf-8", xml_declaration=True),
            "mergedimage.png": png_bytes(finished),
            thumbnail_name: png_bytes(finished_thumbnail),
        }

        with ZipFile(OUTPUT, "w") as output_zip:
            for info in source_zip.infolist():
                output_zip.writestr(info, replacements.get(info.filename, source_zip.read(info)))


if __name__ == "__main__":
    main()
