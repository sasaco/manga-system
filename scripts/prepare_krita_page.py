"""Place a selected panel into the AI素材 layer of a Krita OpenRaster template.

The resulting ORA is an interchange file.  ``manga.ps1 compose`` immediately
converts it to the repository's canonical editable manuscript format, ``.kra``.
"""

from __future__ import annotations

import argparse
import io
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image, ImageOps


AI_LAYER_NAME = "AI素材"
LINE_LAYER_NAME = "線画"
TEXT_LAYER_NAME = "文字"


def _png_bytes(image: Image.Image) -> bytes:
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _fit_art(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    fitted = ImageOps.contain(image.convert("RGBA"), size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    left = (size[0] - fitted.width) // 2
    top = (size[1] - fitted.height) // 2
    canvas.alpha_composite(fitted, (left, top))
    return canvas


def _fit_line_art(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    gray = ImageOps.grayscale(image)
    fitted = ImageOps.contain(gray, size, Image.Resampling.LANCZOS)
    alpha = ImageOps.invert(fitted)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    ink = Image.new("RGBA", fitted.size, (0, 0, 0, 255))
    ink.putalpha(alpha)
    canvas.alpha_composite(ink, ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2))
    return canvas


def prepare_page(
    template: Path,
    art: Path,
    output: Path,
    *,
    line_art: Path | None = None,
) -> None:
    """Create a populated ORA suitable for conversion to KRA by Krita."""
    template = template.resolve()
    art = art.resolve()
    output = output.resolve()
    if not template.is_file():
        raise FileNotFoundError(f"Krita template not found: {template}")
    if not art.is_file():
        raise FileNotFoundError(f"selected panel not found: {art}")
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output}")
    if output == template:
        raise ValueError("output must differ from the template")

    with zipfile.ZipFile(template) as source:
        entries = {item.filename: source.read(item) for item in source.infolist()}
        infos = source.infolist()

    stack = ET.fromstring(entries["stack.xml"])
    size = (int(stack.attrib["w"]), int(stack.attrib["h"]))
    layers = {
        element.attrib.get("name"): element
        for element in stack.iter("layer")
        if "src" in element.attrib
    }
    for required in (AI_LAYER_NAME, LINE_LAYER_NAME, TEXT_LAYER_NAME):
        if required not in layers:
            raise ValueError(f"template must contain a {required} paint layer")
    ai_source = layers[AI_LAYER_NAME].attrib["src"]

    with Image.open(art) as selected:
        ai_layer = _fit_art(selected, size)
    line_layer = Image.new("RGBA", size, (0, 0, 0, 0))
    if line_art:
        with Image.open(line_art) as clean_source:
            line_layer = _fit_line_art(clean_source, size)
        layers[AI_LAYER_NAME].set("visibility", "hidden")
    text_layer = Image.new("RGBA", size, (0, 0, 0, 0))
    with Image.open(io.BytesIO(entries["data/paper.png"])) as paper_image:
        paper = paper_image.convert("RGBA")
    merged = Image.alpha_composite(paper, line_layer if line_art else ai_layer)
    merged = Image.alpha_composite(merged, text_layer)

    with Image.open(io.BytesIO(entries["Thumbnails/thumbnail.png"])) as old_thumbnail:
        thumbnail_size = old_thumbnail.size
    thumbnail = ImageOps.contain(merged, thumbnail_size, Image.Resampling.LANCZOS)
    thumbnail_canvas = Image.new("RGBA", thumbnail_size, (255, 255, 255, 255))
    thumbnail_canvas.alpha_composite(
        thumbnail,
        ((thumbnail_size[0] - thumbnail.width) // 2, (thumbnail_size[1] - thumbnail.height) // 2),
    )

    replacements = {
        ai_source: _png_bytes(ai_layer),
        layers[LINE_LAYER_NAME].attrib["src"]: _png_bytes(line_layer),
        layers[TEXT_LAYER_NAME].attrib["src"]: _png_bytes(text_layer),
        "stack.xml": ET.tostring(stack, encoding="utf-8", xml_declaration=True),
        "mergedimage.png": _png_bytes(merged),
        "Thumbnails/thumbnail.png": _png_bytes(thumbnail_canvas),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=f".{output.stem}-", suffix=output.suffix, dir=output.parent, delete=False
    ) as temporary:
        temporary_path = Path(temporary.name)
    try:
        with zipfile.ZipFile(temporary_path, "w") as target:
            for info in infos:
                target.writestr(info, replacements.get(info.filename, entries[info.filename]))
        temporary_path.replace(output)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--art", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--line-art", type=Path)
    args = parser.parse_args()
    prepare_page(
        args.template,
        args.art,
        args.output,
        line_art=args.line_art,
    )


if __name__ == "__main__":
    main()
