"""Create textless line and flat-color guides for episode 021."""
import json, math, random
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
cfg = json.loads((ROOT / "config/manga.json").read_text(encoding="utf-8"))["comfy"]
W, H = cfg["width"], cfg["height"]
S = 4
rng = random.Random(20012101)
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

# A fading emotional shadow stays with the familiar engineering binders.
for index in range(72):
    x = 92 + (index * 37) % 220
    y = 648 + (index * 59) % 210
    if ((x - 200) / 115) ** 2 + ((y - 755) / 125) ** 2 < 1:
        radius = 1 + (index % 3) * 0.3
        c.ellipse([pt((x - radius, y - radius)), pt((x + radius, y + radius))], fill=(198, 194, 190, 135))

# Closed, blank design binders left behind.
poly([(105, 720), (245, 711), (251, 818), (111, 829)], (232, 229, 226, 255), 2.4)
poly([(125, 685), (266, 677), (270, 784), (251, 818), (245, 711)], (220, 186, 70, 255), 2.4)
stroke([(145, 716), (230, 711)], 1.7, 0.12)

# The young designer leans toward the computer instead of returning to the binders.
oval(430, 754, 55, 119, 0.45, (157, 202, 201, 255))
oval(457, 594, 54, 73, 0.7, (255, 255, 255, 255))
for x, y in ((438, 529), (452, 518), (468, 523)):
    stroke([(x, y), (x + 4, y - 17)], 2.5, 0.1)
stroke([(451, 589), (451, 593)], 3, 0.05)
stroke([(480, 586), (480, 590)], 3, 0.05)
stroke([(462, 616), (471, 619), (480, 613)], 2, 0.06)
poly([(422, 666), (438, 667), (436, 694), (429, 700), (423, 692)], (214, 183, 80, 255), 1.7)

# Short outlined gesture arms reach naturally from the rounded body to the keyboard.
poly([(463, 690), (478, 696), (536, 745), (528, 755), (467, 718)], (157, 202, 201, 255), 2.1)
poly([(425, 699), (438, 702), (493, 753), (484, 762), (428, 728)], (157, 202, 201, 255), 2.1)

# Simple computer with abstract blocks only; no code glyphs.
poly([(540, 500), (690, 502), (688, 666), (542, 664)], (232, 229, 226, 255), 2.8)
for x, y, width in ((560, 535, 55), (625, 535, 40), (560, 571, 91), (560, 607, 42), (613, 607, 57)):
    c.rectangle([pt((x, y)), pt((x + width, y + 10))], fill=(157, 202, 201, 255))
stroke([(615, 666), (615, 708)], 2.2, 0.1)
stroke([(580, 708), (651, 708)], 2.2, 0.1)
poly([(482, 748), (614, 744), (644, 776), (462, 780)], (255, 255, 255, 255), 2)
stroke([(450, 781), (704, 781)], 2.4, 0.2)
stroke([(482, 781), (482, 873)], 2.1, 0.12)
stroke([(680, 781), (680, 873)], 2.1, 0.12)

line.resize((W, H), Image.Resampling.LANCZOS).save(HERE / "021-control.png")
color.resize((W, H), Image.Resampling.LANCZOS).save(HERE / "021-color.png")
