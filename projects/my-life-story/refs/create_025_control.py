"""Create textless line and flat-color guides for episode 025."""

import json
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
cfg = json.loads((ROOT / "config/manga.json").read_text(encoding="utf-8"))["comfy"]
W, H = cfg["width"], cfg["height"]
S = 4
rng = random.Random(20012501)
line = Image.new("RGB", (W * S, H * S), "white")
color = Image.new("RGBA", line.size)
d = ImageDraw.Draw(line)
c = ImageDraw.Draw(color)


def pt(point):
    return round(point[0] * W / 768 * S), round(point[1] * H / 1024 * S)


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
    for index in range(96):
        angle = math.tau * index / 96
        wobble = 1 + 0.024 * math.sin(3 * angle + phase) + 0.009 * math.sin(7 * angle)
        points.append((cx + rx * wobble * math.cos(angle), cy + ry * wobble * math.sin(angle)))
    d.polygon([pt(p) for p in points], fill="white")
    c.polygon([pt(p) for p in points], fill=fill)
    stroke(points, 3, 0.32, True)


def poly(points, fill, width=2.3):
    d.polygon([pt(p) for p in points], fill="white")
    c.polygon([pt(p) for p in points], fill=fill)
    stroke(points, width, 0.2, True)


TEAL = (157, 202, 201, 255)
MUSTARD = (216, 188, 105, 255)
GRAY = (190, 186, 181, 255)
LIGHT_GRAY = (229, 226, 222, 255)
WHITE = (255, 255, 255, 255)

# Thin frame and a large empty upper field reserved for later Krita lettering.
stroke([(42, 43), (724, 44), (722, 980), (44, 981), (42, 43)], 2, 1)

# A restrained local shadow behind the protagonist, suggesting despair after closure.
for index in range(155):
    angle = index * 2.39996
    radius = 8 + 1.23 * index
    x = 247 + math.cos(angle) * radius * 0.58
    y = 735 + math.sin(angle) * radius * 0.84
    if 132 < x < 350 and 540 < y < 910:
        dot = 1.0 + (index % 3) * 0.23
        c.ellipse([pt((x - dot, y - dot)), pt((x + dot, y + dot))], fill=(194, 190, 186, 115))

# Dejected protagonist: bowed face, substantial bean body, and short outlined arms.
oval(249, 785, 62, 128, 0.45, TEAL)
oval(235, 583, 55, 73, 0.9, WHITE)
for x, y in ((214, 516), (231, 507), (249, 514)):
    stroke([(x, y), (x + 3, y - 16)], 2.5, 0.1)
stroke([(214, 578), (222, 580)], 2, 0.05)
stroke([(241, 582), (249, 583)], 2, 0.05)
stroke([(218, 614), (228, 609), (238, 613)], 1.9, 0.06)
poly([(231, 690), (247, 692), (246, 720), (238, 728), (231, 717)], MUSTARD, 1.7)
poly([(194, 694), (208, 699), (189, 756), (177, 799), (164, 793), (178, 747)], TEAL, 2.1)
poly([(282, 704), (295, 712), (312, 766), (300, 772), (286, 742)], TEAL, 2.1)

# The remains of the closed business: one unmarked empty box and blank papers.
poly([(91, 813), (177, 804), (201, 835), (108, 846)], LIGHT_GRAY, 2.0)
poly([(108, 846), (201, 835), (199, 911), (106, 922)], WHITE, 2.1)
poly([(91, 813), (108, 846), (106, 922), (88, 892)], LIGHT_GRAY, 2.0)
poly([(99, 800), (143, 778), (177, 804), (132, 825)], WHITE, 1.8)
poly([(177, 804), (214, 785), (221, 812), (201, 835)], WHITE, 1.8)
poly([(286, 906), (371, 898), (382, 918), (294, 928)], WHITE, 1.7)
poly([(314, 891), (383, 885), (389, 900), (306, 908)], LIGHT_GRAY, 1.5)

# Mentor: an older, larger bean silhouette reaching out with a compact open hand.
oval(564, 772, 68, 141, 0.2, GRAY)
oval(570, 560, 60, 78, 0.55, WHITE)
stroke([(545, 543), (558, 539)], 3.1, 0.05)
stroke([(582, 539), (596, 544)], 3.1, 0.05)
stroke([(550, 562), (550, 566)], 3, 0.05)
stroke([(586, 562), (586, 566)], 3, 0.05)
stroke([(553, 597), (566, 600), (581, 596)], 2, 0.06)
stroke([(548, 617), (552, 625)], 1.8, 0.05)
stroke([(581, 617), (578, 625)], 1.8, 0.05)
poly([(515, 683), (529, 691), (489, 719), (444, 737), (432, 726), (476, 699)], GRAY, 2.2)
poly([(432, 726), (443, 720), (454, 727), (446, 738), (433, 742), (423, 736)], WHITE, 1.9)
poly([(611, 699), (624, 706), (642, 766), (630, 773), (617, 742)], GRAY, 2.1)

# A short floor line anchors the quiet meeting without adding background detail.
stroke([(73, 936), (695, 936)], 1.7, 0.35)

line.resize((W, H), Image.Resampling.LANCZOS).save(HERE / "025-control.png")
color.resize((W, H), Image.Resampling.LANCZOS).save(HERE / "025-color.png")
