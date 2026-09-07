"""Create textless line and flat-color guides for episode 019."""
import json
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CFG = json.loads((ROOT / "config/manga.json").read_text(encoding="utf-8"))["comfy"]
W, H = CFG["width"], CFG["height"]
S = 4
rng = random.Random(20011901)
line = Image.new("RGB", (W * S, H * S), "white")
color = Image.new("RGBA", line.size)
d = ImageDraw.Draw(line)
c = ImageDraw.Draw(color)


def pt(p):
    return round(p[0] * W / 768 * S), round(p[1] * H / 1024 * S)


def stroke(ps, width=2.8, jitter=0.25, closed=False):
    src = ps + ([ps[0]] if closed else [])
    out = []
    for k, (a, b) in enumerate(zip(src, src[1:])):
        count = max(2, round(math.dist(a, b) / 5))
        for i in range(count):
            if k and not i:
                continue
            t = i / count
            ease = math.sin(math.pi * t)
            out.append(
                (
                    a[0] + (b[0] - a[0]) * t + rng.uniform(-jitter, jitter) * ease,
                    a[1] + (b[1] - a[1]) * t + rng.uniform(-jitter, jitter) * ease,
                )
            )
    out.append(src[-1])
    d.line([pt(p) for p in out], fill=(28, 27, 26), width=round(width * S), joint="curve")


def oval(cx, cy, rx, ry, phase, fill):
    points = []
    for i in range(90):
        angle = math.tau * i / 90
        q = 1 + 0.024 * math.sin(3 * angle + phase) + 0.01 * math.sin(7 * angle)
        points.append((cx + rx * q * math.cos(angle), cy + ry * q * math.sin(angle)))
    d.polygon([pt(p) for p in points], fill="white")
    c.polygon([pt(p) for p in points], fill=fill)
    stroke(points, 3, 0.32, True)


def poly(points, fill, width=2.3):
    d.polygon([pt(p) for p in points], fill="white")
    c.polygon([pt(p) for p in points], fill=fill)
    stroke(points, width, 0.2, True)


stroke([(42, 43), (724, 44), (722, 980), (44, 981), (42, 43)], 2, 1)

# Local warm-gray stipple behind the separate specialist software stations.
for i in range(145):
    x = 390 + (i * 47) % 315
    y = 375 + (i * 71) % 500
    if ((x - 548) / 170) ** 2 + ((y - 625) / 270) ** 2 < 1:
        radius = 1 + (i % 3) * 0.35
        c.ellipse([pt((x - radius, y - radius)), pt((x + radius, y + radius))], fill=(198, 194, 190, 135))

# Curious young designer: uneven oval face plus a rounded bean body.
oval(190, 708, 50, 118, 0.5, (157, 202, 201, 255))
oval(188, 541, 52, 72, 0.7, (255, 255, 255, 255))
for x in (173, 188, 203):
    stroke([(x, 479), (x + 1, 462)], 2.5, 0.1)
stroke([(174, 543), (174, 548)], 3, 0.05)
stroke([(204, 543), (204, 548)], 3, 0.05)
stroke([(181, 574), (192, 571), (201, 575)], 2, 0.05)
poly([(180, 616), (197, 616), (194, 646), (188, 651), (181, 642)], (214, 183, 80, 255), 1.7)

# The reaching arm is a narrow outlined gesture that ends before the software wall.
poly([(223, 632), (248, 609), (286, 592), (293, 603), (255, 625), (231, 650)], (157, 202, 201, 255), 2.2)
stroke([(287, 592), (300, 585)], 2.1, 0.08)
stroke([(290, 600), (304, 601)], 2.1, 0.08)


def station(x, y, tint, diagram):
    poly([(x, y), (x + 190, y + 1), (x + 188, y + 118), (x + 2, y + 117)], tint, 2.6)
    stroke([(x + 95, y + 118), (x + 95, y + 138)], 2.1)
    stroke([(x + 65, y + 138), (x + 126, y + 138)], 2.1)
    # Separate mouse at every station: each step needs manual operation.
    oval(x + 165, y + 143, 14, 10, 0.3, (255, 255, 255, 255))
    stroke([(x + 165, y + 133), (x + 166, y + 140)], 1.4, 0.05)
    if diagram == 0:
        stroke([(x + 28, y + 86), (x + 72, y + 34), (x + 112, y + 82), (x + 158, y + 42)], 2, 0.1)
        for px, py in ((x + 28, y + 86), (x + 72, y + 34), (x + 112, y + 82), (x + 158, y + 42)):
            oval(px, py, 4, 4, 0.2, (255, 255, 255, 255))
    elif diagram == 1:
        stroke([(x + 28, y + 82), (x + 58, y + 55), (x + 94, y + 44), (x + 132, y + 56), (x + 162, y + 84)], 2, 0.1)
        stroke([(x + 28, y + 89), (x + 162, y + 89)], 1.6, 0.08)
    else:
        poly([(x + 34, y + 35), (x + 155, y + 35), (x + 143, y + 54), (x + 46, y + 54)], (255, 255, 255, 255), 1.5)
        poly([(x + 43, y + 66), (x + 146, y + 66), (x + 133, y + 87), (x + 57, y + 87)], (255, 255, 255, 255), 1.5)


station(430, 352, (232, 229, 226, 255), 0)
station(468, 548, (238, 236, 232, 255), 1)
station(410, 744, (232, 229, 226, 255), 2)

# One oversized mustard padlock represents the unaffordable complete software set.
stroke([(604, 731), (604, 696), (618, 676), (645, 676), (658, 697), (658, 731)], 5, 0.15)
poly([(590, 724), (672, 724), (670, 810), (592, 810)], (214, 183, 80, 255), 3)
oval(631, 762, 7, 9, 0.4, (255, 255, 255, 255))
stroke([(631, 771), (631, 785)], 3, 0.05)

line.resize((W, H), Image.Resampling.LANCZOS).save(HERE / "019-control.png")
color.resize((W, H), Image.Resampling.LANCZOS).save(HERE / "019-color.png")
