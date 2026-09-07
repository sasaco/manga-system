"""Finish episode 019 using separate Krita artwork, balloon, and text layers."""
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

P = ROOT / "projects/my-life-story"
HERE = P / "refs"
CFG = json.loads((ROOT / "config/manga.json").read_text(encoding="utf-8"))["comfy"]
W, H = CFG["width"], CFG["height"]
S = 4
INK = (29, 28, 27, 255)
rng = random.Random(20011902)


def png(image):
    out = io.BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()


def fit(image, size):
    fitted = ImageOps.contain(image.convert("RGBA"), size, Image.Resampling.LANCZOS)
    out = Image.new("RGBA", size)
    out.alpha_composite(fitted, ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2))
    return out


def px(point):
    return round(point[0] * S), round(point[1] * S)


def oval(box, phase):
    left, top, right, bottom = box
    cx, cy = (left + right) / 2, (top + bottom) / 2
    rx, ry = (right - left) / 2, (bottom - top) / 2
    points = []
    for i in range(100):
        angle = math.tau * i / 100
        q = 1 + 0.02 * math.sin(3 * angle + phase) + 0.008 * math.sin(7 * angle)
        points.append((cx + rx * q * math.cos(angle), cy + ry * q * math.sin(angle)))
    return points


def wobble(draw, points, width=3.6, closed=False):
    src = points + ([points[0]] if closed else [])
    out = []
    for k, (a, b) in enumerate(zip(src, src[1:])):
        count = max(2, round(math.dist(a, b) / 6))
        for i in range(count):
            if k and not i:
                continue
            t = i / count
            ease = math.sin(math.pi * t)
            out.append(
                (
                    a[0] + (b[0] - a[0]) * t + rng.uniform(-0.65, 0.65) * ease,
                    a[1] + (b[1] - a[1]) * t + rng.uniform(-0.65, 0.65) * ease,
                )
            )
    out.append(src[-1])
    draw.line([px(p) for p in out], fill=INK, width=round(width * S), joint="curve")


balloon = Image.new("RGBA", (W * S, H * S))
balloon_draw = ImageDraw.Draw(balloon)
bubble = oval((62, 70, 704, 337), 0.6)
balloon_draw.polygon([px(p) for p in bubble], fill="white")
wobble(balloon_draw, bubble, 3.7, True)
tail = [(150, 316), (174, 455), (252, 326)]
balloon_draw.polygon([px(p) for p in tail], fill="white")
wobble(balloon_draw, tail, 3.4, True)

lettering = Image.new("RGBA", (W * S, H * S))
lettering_draw = ImageDraw.Draw(lettering)
font = ImageFont.truetype(
    "C:/Windows/Fonts/UDDigiKyokashoN-R.ttc",
    35 * S,
    layout_engine=ImageFont.Layout.BASIC,
)
lettering_draw.text(px((383, 171)), "全部、", font=font, fill=INK, anchor="mm")
lettering_draw.text(px((383, 260)), "つなげられたら……", font=font, fill=INK, anchor="mm")

balloon = balloon.resize((W, H), Image.Resampling.LANCZOS)
lettering = lettering.resize((W, H), Image.Resampling.LANCZOS)
balloon.save(HERE / "019-balloon.png")
lettering.save(HERE / "019-lettering.png")

preview = Image.new("RGBA", (W, H), "white")
preview = Image.alpha_composite(preview, Image.open(HERE / "019-color.png").convert("RGBA"))
gray = ImageOps.grayscale(Image.open(HERE / "019-control.png"))
ink = Image.new("RGBA", (W, H), (0, 0, 0, 255))
ink.putalpha(ImageOps.invert(gray))
preview = Image.alpha_composite(preview, ink)
preview = Image.alpha_composite(preview, balloon)
preview = Image.alpha_composite(preview, lettering)
preview.save(HERE / "019-preview.png")

settings = json.loads((P / "project.json").read_text(encoding="utf-8"))
ora = P / "pages/.019-finished.ora"
prepare_page(
    ROOT / "templates/krita" / settings["page_template"],
    P / "panels/selected/019.png",
    ora,
    line_art=HERE / "019-control.png",
    color_art=HERE / "019-color.png",
)
with zipfile.ZipFile(ora) as archive:
    data = {name: archive.read(name) for name in archive.namelist()}
stack = ET.fromstring(data["stack.xml"])
size = int(stack.get("w")), int(stack.get("h"))
layers = {element.get("name"): element for element in stack.iter("layer") if element.get("src")}
data[layers["文字"].get("src")] = png(fit(lettering, size))
data[layers["フキダシ"].get("src")] = png(fit(balloon, size))
text_layer = layers["文字"]
parent = next(element for element in stack.iter("stack") if text_layer in list(element))
parent.remove(text_layer)
parent.insert(0, text_layer)
data["stack.xml"] = ET.tostring(stack, encoding="utf-8", xml_declaration=True)

fd, name = tempfile.mkstemp(dir=ora.parent, suffix=".ora")
os.close(fd)
temporary = Path(name)
try:
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
        for key, payload in data.items():
            archive.writestr(key, payload)
    temporary.replace(ora)
finally:
    temporary.unlink(missing_ok=True)
print(ora)
