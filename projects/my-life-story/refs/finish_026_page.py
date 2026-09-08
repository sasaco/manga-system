"""Finish episode 026 with separated Krita balloon and lettering layers."""

import io
import json
import math
import os
import random
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from prepare_krita_page import prepare_page


PROJECT = ROOT / "projects" / "my-life-story"
REFS = PROJECT / "refs"
WIDTH, HEIGHT = 768, 1024
SCALE = 4
INK = (29, 28, 27, 255)
RNG = random.Random(20012626)


def as_png(image: Image.Image) -> bytes:
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def fit(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    fitted = ImageOps.contain(image.convert("RGBA"), size, Image.Resampling.LANCZOS)
    output = Image.new("RGBA", size)
    output.alpha_composite(
        fitted,
        ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2),
    )
    return output


def scaled(point: tuple[float, float]) -> tuple[int, int]:
    return round(point[0] * SCALE), round(point[1] * SCALE)


def uneven_oval(box: tuple[float, float, float, float], phase: float) -> list[tuple[float, float]]:
    left, top, right, bottom = box
    center_x, center_y = (left + right) / 2, (top + bottom) / 2
    radius_x, radius_y = (right - left) / 2, (bottom - top) / 2
    points = []
    for index in range(120):
        angle = math.tau * index / 120
        wobble = 1 + 0.018 * math.sin(3 * angle + phase) + 0.009 * math.sin(7 * angle)
        points.append(
            (
                center_x + radius_x * wobble * math.cos(angle),
                center_y + radius_y * wobble * math.sin(angle),
            )
        )
    return points


def wobbly_line(
    draw: ImageDraw.ImageDraw,
    points: list[tuple[float, float]],
    *,
    width: float,
    closed: bool = False,
) -> None:
    source = points + ([points[0]] if closed else [])
    output = []
    for segment, (start, end) in enumerate(zip(source, source[1:])):
        count = max(2, round(math.dist(start, end) / 6))
        for index in range(count):
            if segment and not index:
                continue
            t = index / count
            ease = math.sin(math.pi * t)
            output.append(
                (
                    start[0] + (end[0] - start[0]) * t + RNG.uniform(-0.65, 0.65) * ease,
                    start[1] + (end[1] - start[1]) * t + RNG.uniform(-0.65, 0.65) * ease,
                )
            )
    output.append(source[-1])
    draw.line(
        [scaled(point) for point in output],
        fill=INK,
        width=round(width * SCALE),
        joint="curve",
    )


def main() -> None:
    settings = json.loads((PROJECT / "project.json").read_text(encoding="utf-8"))
    config = json.loads((ROOT / "config" / "manga.json").read_text(encoding="utf-8"))
    policy = config["workflow_policy"]
    if settings["image_text_policy"] != "krita-text":
        raise ValueError("episode lettering requires image_text_policy=krita-text")
    if policy["allow_automated_krita_lettering"] is not True:
        raise ValueError("automated Krita lettering is disabled by config/manga.json")
    text_layer_name, balloon_layer_name = policy["krita_text_layers"]

    lines = [
        line.strip()
        for line in (PROJECT / "lettering" / "026.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if lines != ["日曜には、帰れる。"]:
        raise ValueError("lettering/026.txt does not match the approved dialogue")

    balloon = Image.new("RGBA", (WIDTH * SCALE, HEIGHT * SCALE))
    balloon_draw = ImageDraw.Draw(balloon)
    bubble = uneven_oval((84, 73, 684, 356), 0.55)
    balloon_draw.polygon([scaled(point) for point in bubble], fill="white")
    wobbly_line(balloon_draw, bubble, width=3.7, closed=True)
    tail = [(223, 344), (246, 548), (290, 341)]
    balloon_draw.polygon([scaled(point) for point in tail], fill="white")
    wobbly_line(balloon_draw, tail, width=3.5, closed=True)

    lettering = Image.new("RGBA", (WIDTH * SCALE, HEIGHT * SCALE))
    lettering_draw = ImageDraw.Draw(lettering)
    font = ImageFont.truetype(
        "C:/Windows/Fonts/UDDigiKyokashoN-R.ttc",
        46 * SCALE,
        layout_engine=ImageFont.Layout.BASIC,
    )
    lettering_draw.text(
        scaled((384, 220)),
        lines[0],
        font=font,
        fill=INK,
        anchor="mm",
    )

    balloon = balloon.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    lettering = lettering.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    balloon.save(REFS / "026-balloon.png")
    lettering.save(REFS / "026-lettering.png")

    preview = Image.new("RGBA", (WIDTH, HEIGHT), "white")
    preview = Image.alpha_composite(
        preview, Image.open(REFS / "026-color.png").convert("RGBA")
    )
    gray = ImageOps.grayscale(Image.open(REFS / "026-control.png"))
    line_art = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 255))
    line_art.putalpha(ImageOps.invert(gray))
    preview = Image.alpha_composite(preview, line_art)
    preview = Image.alpha_composite(preview, balloon)
    preview = Image.alpha_composite(preview, lettering)
    preview.save(REFS / "026-preview.png")

    ora = PROJECT / "pages" / ".026-finished.ora"
    prepare_page(
        ROOT / "templates" / "krita" / settings["page_template"],
        PROJECT / "panels" / "selected" / "026.png",
        ora,
        line_art=REFS / "026-control.png",
        color_art=REFS / "026-color.png",
    )
    with zipfile.ZipFile(ora) as archive:
        data = {name: archive.read(name) for name in archive.namelist()}
    stack = ET.fromstring(data["stack.xml"])
    canvas_size = int(stack.get("w")), int(stack.get("h"))
    layers = {
        element.get("name"): element
        for element in stack.iter("layer")
        if element.get("src")
    }
    data[layers[text_layer_name].get("src")] = as_png(fit(lettering, canvas_size))
    data[layers[balloon_layer_name].get("src")] = as_png(fit(balloon, canvas_size))

    text_layer = layers[text_layer_name]
    parent = next(element for element in stack.iter("stack") if text_layer in list(element))
    parent.remove(text_layer)
    parent.insert(0, text_layer)
    data["stack.xml"] = ET.tostring(stack, encoding="utf-8", xml_declaration=True)

    descriptor, temporary_name = tempfile.mkstemp(dir=ora.parent, suffix=".ora")
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, payload in data.items():
                archive.writestr(name, payload)
        temporary.replace(ora)
    finally:
        temporary.unlink(missing_ok=True)
    print(ora)


if __name__ == "__main__":
    main()
