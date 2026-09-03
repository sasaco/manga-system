"""Build a layered ORA experiment with reversible margin cleanup on 効果."""

from __future__ import annotations

import io
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image, ImageDraw, ImageOps


HERE = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from scripts.prepare_krita_page import prepare_page  # noqa: E402


TEMPLATE = REPO_ROOT / "templates" / "krita" / "instagram-portrait.ora"
SOURCE = HERE / "comfy" / "006_2001166_01.png"
OUTPUT = HERE / "page.ora"


def png_bytes(image: Image.Image) -> bytes:
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(f"refusing to overwrite existing experiment: {OUTPUT}")

    with tempfile.TemporaryDirectory(prefix=".006-full-manga-", dir=HERE) as temporary:
        base_ora = Path(temporary) / "base.ora"
        prepare_page(TEMPLATE, SOURCE, base_ora)

        with zipfile.ZipFile(base_ora) as archive:
            infos = archive.infolist()
            entries = {item.filename: archive.read(item) for item in infos}

        stack = ET.fromstring(entries["stack.xml"])
        width = int(stack.attrib["w"])
        height = int(stack.attrib["h"])
        layers = {
            element.attrib.get("name"): element
            for element in stack.iter("layer")
            if "src" in element.attrib
        }
        effect = layers["効果"]
        ai_source = layers["AI素材"].attrib["src"]

        correction = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        correction_draw = ImageDraw.Draw(correction)
        scale = height / 1024
        left = (width - round(768 * scale)) // 2

        # Remove only the hallucinated footer and the small mark in the right margin.
        bottom_start = round(986 * scale)
        correction_draw.rectangle((0, bottom_start, width, height), fill=(255, 255, 255, 255))
        right_start = left + round(736 * scale)
        correction_draw.rectangle((right_start, 0, width, height), fill=(255, 255, 255, 255))
        border_width = max(3, round(3 * scale))
        correction_draw.line(
            (right_start, 0, right_start, bottom_start),
            fill=(18, 18, 18, 255),
            width=border_width,
        )
        correction_draw.line(
            (left, bottom_start, right_start, bottom_start),
            fill=(18, 18, 18, 255),
            width=border_width,
        )

        with Image.open(io.BytesIO(entries["data/paper.png"])) as paper_source:
            merged = paper_source.convert("RGBA")
        with Image.open(io.BytesIO(entries[ai_source])) as ai_layer:
            merged = Image.alpha_composite(merged, ai_layer.convert("RGBA"))
        merged = Image.alpha_composite(merged, correction)

        with Image.open(io.BytesIO(entries["Thumbnails/thumbnail.png"])) as old_thumbnail:
            thumbnail_size = old_thumbnail.size
        thumbnail = ImageOps.contain(merged, thumbnail_size, Image.Resampling.LANCZOS)
        thumbnail_canvas = Image.new("RGBA", thumbnail_size, (255, 255, 255, 255))
        thumbnail_canvas.alpha_composite(
            thumbnail,
            (
                (thumbnail_size[0] - thumbnail.width) // 2,
                (thumbnail_size[1] - thumbnail.height) // 2,
            ),
        )

        replacements = {
            effect.attrib["src"]: png_bytes(correction),
            "mergedimage.png": png_bytes(merged),
            "Thumbnails/thumbnail.png": png_bytes(thumbnail_canvas),
        }
        with tempfile.NamedTemporaryFile(
            prefix=".page-", suffix=".ora", dir=HERE, delete=False
        ) as temporary_output:
            temporary_path = Path(temporary_output.name)
        try:
            with zipfile.ZipFile(temporary_path, "w") as target:
                for info in infos:
                    target.writestr(info, replacements.get(info.filename, entries[info.filename]))
            temporary_path.replace(OUTPUT)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise

    print(OUTPUT)


if __name__ == "__main__":
    main()
