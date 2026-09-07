"""Create textless line and flat-color guides for episode 022."""
import json, math, random
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
cfg = json.loads((ROOT / "config/manga.json").read_text(encoding="utf-8"))["comfy"]
W, H = cfg["width"], cfg["height"]
S = 4
rng = random.Random(20012201)
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

# A restrained stippled memory behind the mentor.
for index in range(88):
    x = 488 + (index * 41) % 190
    y = 518 + (index * 67) % 286
    if ((x - 582) / 104) ** 2 + ((y - 658) / 152) ** 2 < 1:
        radius = 1 + (index % 3) * 0.28
        c.ellipse([pt((x - radius, y - radius)), pt((x + radius, y + radius))], fill=(198, 194, 190, 135))

# Desk and blank meeting materials.
stroke([(92, 800), (685, 801)], 2.6, 0.26)
stroke([(125, 801), (125, 906)], 2.1, 0.12)
stroke([(651, 801), (651, 906)], 2.1, 0.12)
poly([(377, 736), (507, 731), (541, 773), (365, 778)], (220, 186, 70, 255), 2.1)
for x, y in ((524, 737), (547, 747), (570, 757)):
    poly([(x, y), (x + 53, y - 2), (x + 55, y + 25), (x + 2, y + 27)], (255, 255, 255, 255), 1.6)

# Young project lead with a rounded body, answering the desk phone.
oval(304, 750, 57, 125, 0.45, (157, 202, 201, 255))
oval(299, 570, 53, 72, 0.7, (255, 255, 255, 255))
for x, y in ((278, 505), (295, 494), (312, 500)):
    stroke([(x, y), (x + 4, y - 17)], 2.5, 0.1)
stroke([(283, 565), (283, 569)], 3, 0.05)
stroke([(312, 563), (312, 567)], 3, 0.05)
stroke([(289, 597), (297, 600), (305, 595)], 1.9, 0.06)
poly([(285, 661), (301, 662), (299, 690), (292, 697), (286, 688)], (214, 183, 80, 255), 1.7)

# Receiver and two short outlined gesture arms; no skeletal line limbs.
poly([(235, 519), (249, 510), (269, 533), (263, 548), (250, 544), (244, 530)], (232, 229, 226, 255), 2.4)
poly([(270, 656), (284, 662), (257, 700), (243, 691)], (157, 202, 201, 255), 2.1)
poly([(328, 682), (342, 686), (387, 739), (376, 748), (331, 715)], (157, 202, 201, 255), 2.1)
stroke([(244, 546), (225, 606), (237, 708), (218, 758), (196, 759)], 1.8, 0.2)

# Simple telephone base and soft ringing arcs without glyphs.
poly([(158, 728), (238, 725), (253, 761), (143, 764)], (232, 229, 226, 255), 2.3)
stroke([(168, 715), (164, 701), (170, 688)], 1.7, 0.12)
stroke([(193, 713), (193, 694), (201, 678)], 1.7, 0.12)

# Older mentor remains slightly behind, quietly offering help.
oval(590, 722, 61, 130, 0.15, (187, 183, 178, 255))
oval(596, 527, 57, 77, 0.35, (255, 255, 255, 255))
stroke([(571, 507), (581, 504)], 3.2, 0.05)
stroke([(607, 504), (619, 508)], 3.2, 0.05)
stroke([(578, 535), (578, 539)], 3, 0.05)
stroke([(610, 536), (610, 540)], 3, 0.05)
stroke([(583, 561), (594, 565), (605, 559)], 2, 0.06)
stroke([(574, 578), (579, 587)], 1.8, 0.06)
stroke([(614, 580), (607, 589)], 1.8, 0.06)
poly([(551, 660), (565, 663), (518, 714), (507, 704)], (187, 183, 178, 255), 2.1)
poly([(490, 690), (537, 687), (539, 715), (492, 719)], (255, 255, 255, 255), 1.7)

line.resize((W, H), Image.Resampling.LANCZOS).save(HERE / "022-control.png")
color.resize((W, H), Image.Resampling.LANCZOS).save(HERE / "022-color.png")
