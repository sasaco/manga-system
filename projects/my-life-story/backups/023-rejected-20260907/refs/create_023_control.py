"""Create textless line and flat-color guides for episode 023."""
import json, math, random
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
cfg = json.loads((ROOT / "config/manga.json").read_text(encoding="utf-8"))["comfy"]
W, H = cfg["width"], cfg["height"]
S = 4
rng = random.Random(20012301)
line = Image.new("RGB", (W * S, H * S), "white")
color = Image.new("RGBA", line.size)
d = ImageDraw.Draw(line)
c = ImageDraw.Draw(color)


def pt(p):
    return round(p[0] * W / 768 * S), round(p[1] * H / 1024 * S)


def stroke(points, width=2.8, jitter=0.25, closed=False):
    source = points + ([points[0]] if closed else [])
    output = []
    for segment, (a, b) in enumerate(zip(source, source[1:])):
        count = max(2, round(math.dist(a, b) / 5))
        for index in range(count):
            if segment and not index:
                continue
            t = index / count
            ease = math.sin(math.pi * t)
            output.append(
                (
                    a[0] + (b[0] - a[0]) * t + rng.uniform(-jitter, jitter) * ease,
                    a[1] + (b[1] - a[1]) * t + rng.uniform(-jitter, jitter) * ease,
                )
            )
    output.append(source[-1])
    d.line([pt(p) for p in output], fill=(28, 27, 26), width=round(width * S), joint="curve")


def oval(cx, cy, rx, ry, phase, fill):
    points = []
    for index in range(90):
        angle = math.tau * index / 90
        wobble = 1 + 0.024 * math.sin(3 * angle + phase) + 0.01 * math.sin(7 * angle)
        points.append((cx + rx * wobble * math.cos(angle), cy + ry * wobble * math.sin(angle)))
    d.polygon([pt(p) for p in points], fill="white")
    c.polygon([pt(p) for p in points], fill=fill)
    stroke(points, 3, 0.32, True)


def poly(points, fill, width=2.3):
    d.polygon([pt(p) for p in points], fill="white")
    c.polygon([pt(p) for p in points], fill=fill)
    stroke(points, width, 0.2, True)


stroke([(42, 43), (724, 44), (722, 980), (44, 981), (42, 43)], 2, 1)

# A localized emotional shadow for the father's fear.
for index in range(102):
    x = 326 + (index * 43) % 256
    y = 517 + (index * 71) % 332
    if ((x - 451) / 134) ** 2 + ((y - 680) / 174) ** 2 < 1:
        radius = 1 + (index % 3) * 0.28
        c.ellipse([pt((x - radius, y - radius)), pt((x + radius, y + radius))], fill=(198, 194, 190, 135))

# Simple desk and blank work papers, kept beside the father's free hand.
stroke([(95, 810), (682, 811)], 2.6, 0.26)
stroke([(128, 811), (128, 915)], 2.1, 0.12)
stroke([(650, 811), (650, 915)], 2.1, 0.12)
poly([(542, 729), (669, 723), (690, 759), (529, 766)], (232, 229, 226, 255), 2.3)
poly([(558, 695), (683, 690), (669, 723), (542, 729)], (255, 255, 255, 255), 2.1)
stroke([(573, 719), (647, 716)], 1.5, 0.1)

# Young father: rounded body, worried but determined face.
oval(465, 738, 64, 132, 0.45, (157, 202, 201, 255))
oval(459, 541, 56, 76, 0.7, (255, 255, 255, 255))
for x, y in ((437, 473), (454, 462), (472, 469)):
    stroke([(x, y), (x + 4, y - 17)], 2.5, 0.1)
stroke([(441, 535), (446, 538)], 2.6, 0.05)
stroke([(472, 538), (477, 535)], 2.6, 0.05)
stroke([(449, 571), (459, 568), (469, 572)], 1.9, 0.06)
poly([(445, 638), (461, 639), (459, 668), (452, 674), (446, 666)], (214, 183, 80, 255), 1.7)

# One small sweat drop, kept separate from the face.
poly([(514, 530), (521, 543), (514, 552), (508, 543)], (255, 255, 255, 255), 1.7)

# Sleeping baby with a visible-area swaddle, not a line-limb figure.
oval(371, 691, 33, 42, 0.25, (255, 255, 255, 255))
oval(383, 773, 43, 76, 0.55, (220, 186, 70, 255))
stroke([(358, 690), (363, 690)], 2.2, 0.04)
stroke([(378, 690), (383, 690)], 2.2, 0.04)
stroke([(365, 710), (372, 712), (379, 709)], 1.5, 0.05)

# Two short outlined arms: one cradles the baby, one reaches for work.
poly([(426, 670), (440, 675), (415, 742), (403, 733)], (157, 202, 201, 255), 2.1)
poly([(421, 785), (432, 795), (389, 834), (374, 824)], (157, 202, 201, 255), 2.1)
poly([(493, 674), (507, 679), (558, 724), (548, 737), (498, 711)], (157, 202, 201, 255), 2.1)

line.resize((W, H), Image.Resampling.LANCZOS).save(HERE / "023-control.png")
color.resize((W, H), Image.Resampling.LANCZOS).save(HERE / "023-color.png")
