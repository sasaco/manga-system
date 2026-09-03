"""Create an adult-proportion composition guide for the full-manga experiment."""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw


WIDTH = 768
HEIGHT = 1024
SCALE = 4
INK = (18, 18, 18)
RNG = random.Random(20011603)


def main() -> None:
    image = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), "white")
    draw = ImageDraw.Draw(image)

    def p(point: tuple[float, float]) -> tuple[int, int]:
        return round(point[0] * SCALE), round(point[1] * SCALE)

    def line(
        points: list[tuple[float, float]], width: float = 2.3, jitter: float = 0.18
    ) -> None:
        sampled: list[tuple[float, float]] = []
        for segment, (start, end) in enumerate(zip(points, points[1:])):
            steps = max(2, round(math.dist(start, end) / 6))
            for index in range(steps):
                if segment and index == 0:
                    continue
                t = index / steps
                envelope = math.sin(math.pi * t)
                sampled.append(
                    (
                        start[0] + (end[0] - start[0]) * t
                        + RNG.uniform(-jitter, jitter) * envelope,
                        start[1] + (end[1] - start[1]) * t
                        + RNG.uniform(-jitter, jitter) * envelope,
                    )
                )
        sampled.append(points[-1])
        draw.line([p(point) for point in sampled], fill=INK, width=round(width * SCALE), joint="curve")

    def polygon(points: list[tuple[float, float]], width: float = 2.4, fill: str = "white") -> None:
        draw.polygon([p(point) for point in points], fill=fill)
        line(points + [points[0]], width=width)

    def ellipse(box: tuple[float, float, float, float], width: float = 2.4, fill: str = "white") -> None:
        scaled = tuple(round(value * SCALE) for value in box)
        draw.ellipse(scaled, fill=fill, outline=INK, width=round(width * SCALE))

    def arc(box: tuple[float, float, float, float], start: int, end: int, width: float = 2.2) -> None:
        scaled = tuple(round(value * SCALE) for value in box)
        draw.arc(scaled, start=start, end=end, fill=INK, width=round(width * SCALE))

    # Border and office perspective.
    line([(34, 33), (733, 35), (734, 988), (33, 988), (34, 33)], width=3.0, jitter=0.35)
    line([(36, 438), (732, 405)], width=1.4)
    line([(366, 438), (356, 984)], width=1.2)
    line([(36, 987), (208, 438)], width=1.0)
    line([(733, 987), (602, 411)], width=1.0)

    # Background client: adult head, jacket, trousers, and natural stance.
    ellipse((74, 98, 137, 178), width=2.2)
    polygon([(67, 180), (101, 166), (140, 181), (159, 307), (61, 308)], width=2.5)
    polygon([(61, 308), (108, 308), (105, 418), (70, 418)], width=2.2)
    polygon([(108, 308), (158, 307), (151, 417), (116, 417)], width=2.2)
    polygon([(80, 184), (101, 218), (121, 182), (109, 277)], width=1.7)
    line([(88, 128), (98, 122), (112, 123), (126, 132)], width=3.3)
    line([(90, 145), (96, 145)], width=1.5)
    line([(116, 145), (122, 145)], width=1.5)
    line([(99, 161), (113, 162)], width=1.4)

    # Background consultant receiving a rolled plan.
    ellipse((232, 92, 299, 177), width=2.2)
    polygon([(216, 181), (256, 165), (306, 183), (334, 315), (210, 316)], width=2.5)
    polygon([(210, 316), (268, 316), (265, 423), (222, 423)], width=2.2)
    polygon([(268, 316), (334, 315), (327, 422), (282, 423)], width=2.2)
    line([(245, 126), (258, 119), (277, 122), (292, 135)], width=3.2)
    line([(247, 147), (253, 147)], width=1.5)
    line([(277, 147), (284, 148)], width=1.5)
    line([(258, 164), (274, 164)], width=1.4)
    polygon([(126, 214), (248, 205), (256, 251), (134, 259)], width=2.2)
    ellipse((239, 205, 263, 253), width=1.8)
    polygon([(136, 198), (157, 196), (171, 226), (151, 240), (132, 226)], width=1.8)
    polygon([(220, 191), (243, 190), (250, 219), (232, 233), (214, 218)], width=1.8)

    # Consultant relays responsibility toward the foreground engineer.
    polygon([(303, 202), (323, 194), (389, 295), (371, 309)], width=2.0)
    ellipse((365, 294, 390, 319), width=1.8)

    # Survey specialist and tripod, deeper in the office.
    ellipse((576, 112, 624, 174), width=2.0)
    polygon([(565, 177), (597, 166), (629, 180), (642, 281), (558, 282)], width=2.2)
    polygon([(558, 282), (598, 282), (588, 383), (564, 383)], width=2.0)
    polygon([(598, 282), (642, 281), (636, 382), (610, 382)], width=2.0)
    polygon([(624, 194), (638, 189), (670, 217), (660, 231)], width=1.9)
    ellipse((653, 210, 678, 235), width=1.8)
    line([(666, 234), (665, 265)], width=2.0)
    line([(665, 265), (631, 384)], width=2.1)
    line([(665, 265), (666, 388)], width=2.1)
    line([(665, 265), (702, 384)], width=2.1)

    # Foreground structural engineer, adult three-quarter seated pose.
    ellipse((92, 442, 263, 628), width=3.2)
    polygon(
        [
            (91, 501),
            (100, 472),
            (121, 449),
            (151, 436),
            (184, 438),
            (216, 447),
            (241, 463),
            (257, 486),
            (261, 507),
            (239, 486),
            (214, 470),
            (187, 460),
            (160, 458),
            (135, 465),
            (112, 482),
        ],
        width=3.0,
        fill="black",
    )
    line([(164, 457), (181, 443), (205, 446)], width=2.0)
    line([(130, 548), (150, 542)], width=2.1)
    line([(198, 542), (218, 548)], width=2.1)
    line([(164, 570), (181, 575)], width=1.5)
    arc((145, 558, 213, 606), 25, 150, width=1.8)
    polygon([(66, 642), (119, 610), (225, 615), (290, 658), (329, 941), (57, 943)], width=3.0)
    line([(111, 622), (171, 675), (231, 626)], width=2.2)
    polygon([(162, 668), (181, 668), (189, 687), (171, 705), (153, 687)], width=1.8)
    polygon([(171, 705), (188, 790), (171, 815), (153, 789)], width=1.8)

    # Sleeves and hands reaching to keyboard and calculation page.
    polygon([(242, 674), (276, 666), (360, 775), (340, 801), (271, 750)], width=2.4)
    ellipse((329, 780, 357, 807), width=1.8)
    polygon([(111, 700), (139, 693), (186, 817), (160, 830), (126, 770)], width=2.4)
    ellipse((151, 815, 180, 842), width=1.8)

    # Bulky CRT monitor dominates the right foreground.
    polygon([(356, 467), (670, 451), (700, 718), (348, 735)], width=3.3)
    polygon([(386, 493), (643, 484), (661, 682), (376, 693)], width=2.7)
    polygon([(434, 735), (615, 730), (635, 772), (418, 779)], width=2.4)
    polygon([(340, 797), (621, 789), (656, 850), (312, 858)], width=2.6)
    for x in range(350, 610, 43):
        line([(x, 811), (x + 8, 838)], width=0.9, jitter=0.05)
    line([(332, 821), (631, 814)], width=0.9, jitter=0.05)
    line([(323, 841), (642, 833)], width=0.9, jitter=0.05)

    # Empty spreadsheet cells, no glyphs.
    for x in (404, 440, 476, 512):
        line([(x, 515), (x, 604)], width=1.1, jitter=0.05)
    for y in (515, 544, 574, 604):
        line([(404, y), (512, y)], width=1.1, jitter=0.05)

    # Truss bridge analysis wireframe, only geometry.
    line([(531, 625), (632, 625)], width=1.8)
    line([(531, 585), (632, 585)], width=1.6)
    for x in (531, 556, 581, 606, 632):
        line([(x, 585), (x, 625)], width=1.2, jitter=0.04)
    line([(531, 625), (556, 585), (581, 625), (606, 585), (632, 625)], width=1.4, jitter=0.04)
    line([(531, 625), (523, 657)], width=1.5)
    line([(632, 625), (640, 657)], width=1.5)

    # A towering calculation book with dozens of visible blank page edges.
    polygon([(439, 861), (693, 855), (714, 900), (423, 908)], width=2.5)
    for offset in range(7, 76, 5):
        line([(423, 908 + offset), (714, 900 + offset)], width=1.0, jitter=0.06)
    line([(423, 908), (423, 978)], width=2.0)
    line([(714, 900), (714, 975)], width=2.0)
    line([(423, 978), (714, 975)], width=2.2)

    # A few controlled hatching cues encourage true inked manga rendering.
    for offset in range(0, 84, 8):
        line([(66 + offset, 646), (57 + offset, 702)], width=0.8, jitter=0.03)
    for offset in range(0, 70, 7):
        line([(638 + offset, 451), (664 + offset, 515)], width=0.8, jitter=0.03)

    output = Path(__file__).with_name("control.png")
    image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(output)
    print(output)


if __name__ == "__main__":
    main()
