"""Create textless line and flat-color guides for episode 024."""

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
rng = random.Random(20012401)
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


INK = (28, 27, 26, 255)
TEAL = (157, 202, 201, 255)
MUSTARD = (216, 188, 105, 255)
GRAY = (190, 186, 181, 255)
LIGHT_GRAY = (229, 226, 222, 255)
WHITE = (255, 255, 255, 255)

# Thin frame and generous empty upper space for a later Krita balloon.
stroke([(42, 43), (724, 44), (722, 980), (44, 981), (42, 43)], 2, 1)

# A restrained fingerprint-like patch local to the anxious speaker.
for index in range(135):
    angle = index * 2.39996
    radius = 8 + 1.27 * index
    x = 231 + math.cos(angle) * radius * 0.58
    y = 699 + math.sin(angle) * radius * 0.82
    if 130 < x < 330 and 535 < y < 875:
        dot = 1.0 + (index % 3) * 0.23
        c.ellipse([pt((x - dot, y - dot)), pt((x + dot, y + dot))], fill=(194, 190, 186, 115))

# Nervous protagonist: a bowed face and substantial rounded body, never a stick figure.
oval(244, 748, 58, 132, 0.45, TEAL)
oval(230, 548, 54, 73, 0.9, WHITE)
for x, y in ((209, 482), (226, 472), (244, 479)):
    stroke([(x, y), (x + 3, y - 16)], 2.5, 0.1)
stroke([(211, 539), (220, 536)], 2, 0.05)
stroke([(239, 541), (248, 544)], 2, 0.05)
stroke([(218, 578), (228, 574), (238, 579)], 1.9, 0.06)
poly([(259, 530), (267, 545), (262, 555), (255, 551), (254, 543)], WHITE, 1.7)
poly([(226, 662), (242, 663), (241, 691), (233, 698), (227, 688)], MUSTARD, 1.7)

# Receiver and outlined arm held close to the body.
poly([(171, 516), (183, 507), (203, 531), (198, 546), (185, 543), (178, 529)], LIGHT_GRAY, 2.3)
poly([(199, 631), (212, 636), (188, 587), (181, 547), (193, 543), (205, 582), (222, 618)], TEAL, 2.1)
poly([(269, 688), (281, 693), (301, 750), (291, 757), (272, 721)], TEAL, 2.1)

# Client: serious but listening, with a larger warm-gray bean silhouette.
oval(567, 744, 63, 137, 0.2, GRAY)
oval(575, 543, 57, 76, 0.55, WHITE)
stroke([(550, 527), (562, 524)], 3.1, 0.05)
stroke([(587, 524), (600, 528)], 3.1, 0.05)
stroke([(556, 547), (556, 551)], 3, 0.05)
stroke([(590, 548), (590, 552)], 3, 0.05)
stroke([(560, 581), (573, 582), (586, 581)], 2, 0.06)
poly([(625, 518), (637, 510), (655, 536), (648, 550), (636, 545), (630, 531)], LIGHT_GRAY, 2.3)
poly([(601, 632), (614, 638), (638, 586), (637, 549), (649, 548), (650, 590), (624, 649)], GRAY, 2.1)
poly([(520, 691), (533, 695), (498, 744), (486, 735)], GRAY, 2.1)

# Blank papers beside the client's free hand.
poly([(476, 763), (555, 758), (566, 786), (466, 790)], WHITE, 1.9)
poly([(483, 749), (551, 745), (557, 761), (477, 765)], LIGHT_GRAY, 1.7)

# Two small plain phone bases and a single visual connection between them.
poly([(115, 865), (218, 862), (230, 891), (103, 894)], LIGHT_GRAY, 2.2)
poly([(548, 864), (652, 862), (665, 891), (536, 894)], LIGHT_GRAY, 2.2)
stroke([(218, 886), (305, 896), (380, 879), (465, 897), (548, 885)], 1.8, 0.35)
stroke([(178, 548), (153, 626), (160, 862)], 1.7, 0.22)
stroke([(649, 548), (671, 630), (650, 861)], 1.7, 0.22)

line.resize((W, H), Image.Resampling.LANCZOS).save(HERE / "024-control.png")
color.resize((W, H), Image.Resampling.LANCZOS).save(HERE / "024-color.png")
