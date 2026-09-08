"""Create textless line and flat-color guides for episode 026."""

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
rng = random.Random(20012601)
line = Image.new("RGB", (W * S, H * S), "white")
color = Image.new("RGBA", line.size)
d = ImageDraw.Draw(line)
c = ImageDraw.Draw(color)


def pt(point):
    return round(point[0] * W / 768 * S), round(point[1] * H / 1024 * S)


def stroke(points, width=2.8, jitter=0.25, closed=False):
    source = points + ([points[0]] if closed else [])
    output = []
    for segment, (start, end) in enumerate(zip(source, source[1:])):
        count = max(2, round(math.dist(start, end) / 5))
        for index in range(count):
            if segment and not index:
                continue
            t = index / count
            ease = math.sin(math.pi * t)
            output.append(
                (
                    start[0] + (end[0] - start[0]) * t + rng.uniform(-jitter, jitter) * ease,
                    start[1] + (end[1] - start[1]) * t + rng.uniform(-jitter, jitter) * ease,
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

# Thin frame and generous upper space reserved for later Krita lettering.
stroke([(42, 43), (724, 44), (722, 980), (44, 981), (42, 43)], 2, 1)

# Sparse local night shadow, kept well away from the empty lettering field.
for index in range(175):
    angle = index * 2.39996
    radius = 7 + 1.34 * index
    x = 365 + math.cos(angle) * radius * 1.05
    y = 742 + math.sin(angle) * radius * 0.52
    if 112 < x < 654 and 566 < y < 910:
        dot = 0.9 + (index % 3) * 0.24
        c.ellipse([pt((x - dot, y - dot)), pt((x + dot, y + dot))], fill=(194, 190, 186, 105))

# Compact car, seen from the side with simplified white windows.
car = [(90, 775), (111, 683), (190, 621), (499, 612), (594, 657), (671, 754), (676, 817), (648, 840), (113, 840), (90, 814)]
poly(car, LIGHT_GRAY, 3.0)
rear_window = [(184, 643), (326, 632), (331, 726), (145, 727), (153, 687)]
front_window = [(344, 631), (488, 630), (558, 672), (595, 728), (352, 726)]
poly(rear_window, WHITE, 2.3)
poly(front_window, WHITE, 2.3)
stroke([(340, 625), (343, 809)], 2.1, 0.12)
stroke([(124, 760), (642, 760)], 1.9, 0.25)
stroke([(577, 790), (635, 790)], 1.7, 0.15)

# Resting protagonist inside the rear window: oval face and horizontal bean body.
oval(223, 683, 38, 46, 0.72, WHITE)
for x, y in ((205, 640), (219, 634), (234, 639)):
    stroke([(x, y), (x + 1, y - 12)], 2.3, 0.08)
stroke([(207, 682), (214, 683)], 1.9, 0.05)
stroke([(230, 681), (237, 680)], 1.9, 0.05)
stroke([(215, 705), (223, 707), (230, 704)], 1.7, 0.05)
oval(326, 699, 88, 37, 0.34, TEAL)
poly([(278, 674), (294, 676), (279, 704), (251, 715), (245, 704), (267, 691)], TEAL, 2.0)

# A single blanket shape over the rounded body; no independent legs are shown.
blanket = [(331, 666), (401, 671), (420, 703), (397, 730), (324, 735), (298, 711)]
poly(blanket, MUSTARD, 2.0)

# Minimal car details and wheels.
oval(211, 837, 47, 47, 0.2, GRAY)
oval(211, 837, 22, 22, 0.5, WHITE)
oval(558, 837, 47, 47, 0.6, GRAY)
oval(558, 837, 22, 22, 0.9, WHITE)
stroke([(113, 840), (164, 840)], 2.0, 0.12)
stroke([(258, 840), (511, 840)], 2.0, 0.12)
stroke([(605, 840), (648, 840)], 2.0, 0.12)

# One unmarked work bag outside the car, hinting at the workweek routine.
poly([(96, 858), (153, 858), (158, 922), (91, 922)], MUSTARD, 2.1)
stroke([(108, 858), (110, 842), (141, 842), (143, 858)], 2.0, 0.12)

# A short ground line anchors the lonely parked car without a detailed street.
stroke([(70, 927), (696, 927)], 1.7, 0.35)

line.resize((W, H), Image.Resampling.LANCZOS).save(HERE / "026-control.png")
color.resize((W, H), Image.Resampling.LANCZOS).save(HERE / "026-color.png")
