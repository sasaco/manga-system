"""Draw the loose, expressive, textless composition guide for episode 003."""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw


WIDTH = 768
HEIGHT = 1024
SCALE = 4
INK = (28, 27, 25)
RNG = random.Random(2001)


def main() -> None:
    canvas = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), "white")
    draw = ImageDraw.Draw(canvas)

    def scaled(point: tuple[float, float]) -> tuple[int, int]:
        return round(point[0] * SCALE), round(point[1] * SCALE)

    def hand_line(
        values: list[tuple[float, float]],
        width: float = 3.2,
        jitter: float = 0.65,
        closed: bool = False,
    ) -> None:
        source = values + ([values[0]] if closed else [])
        sampled: list[tuple[float, float]] = []
        for index, (start, end) in enumerate(zip(source, source[1:])):
            distance = math.dist(start, end)
            steps = max(2, round(distance / 8))
            for step in range(steps):
                if index and step == 0:
                    continue
                t = step / steps
                x = start[0] + (end[0] - start[0]) * t
                y = start[1] + (end[1] - start[1]) * t
                envelope = math.sin(math.pi * t)
                x += RNG.uniform(-jitter, jitter) * envelope
                y += RNG.uniform(-jitter, jitter) * envelope
                sampled.append((x, y))
        sampled.append(source[-1])
        draw.line(
            [scaled(point) for point in sampled],
            fill=INK,
            width=max(1, round(width * SCALE)),
            joint="curve",
        )

    def cubic(
        start: tuple[float, float],
        control_a: tuple[float, float],
        control_b: tuple[float, float],
        end: tuple[float, float],
        width: float = 3.2,
        jitter: float = 0.7,
    ) -> None:
        values: list[tuple[float, float]] = []
        for step in range(33):
            t = step / 32
            u = 1 - t
            values.append(
                (
                    u**3 * start[0]
                    + 3 * u**2 * t * control_a[0]
                    + 3 * u * t**2 * control_b[0]
                    + t**3 * end[0],
                    u**3 * start[1]
                    + 3 * u**2 * t * control_a[1]
                    + 3 * u * t**2 * control_b[1]
                    + t**3 * end[1],
                )
            )
        hand_line(values, width=width, jitter=jitter)

    def hand_oval(
        bounds: tuple[float, float, float, float],
        width: float = 3.2,
        irregularity: float = 1.2,
        phase: float = 0.0,
    ) -> None:
        left, top, right, bottom = bounds
        cx = (left + right) / 2
        cy = (top + bottom) / 2
        rx = (right - left) / 2
        ry = (bottom - top) / 2
        values: list[tuple[float, float]] = []
        for step in range(65):
            angle = math.tau * step / 64
            wobble = 1 + irregularity * 0.007 * math.sin(3 * angle + phase)
            values.append((cx + rx * wobble * math.cos(angle), cy + ry * wobble * math.sin(angle)))
        hand_line(values, width=width, jitter=0.45, closed=True)

    def white_oval(bounds: tuple[float, float, float, float]) -> None:
        draw.ellipse(tuple(round(value * SCALE) for value in bounds), fill="white")

    def white_shape(values: list[tuple[float, float]]) -> None:
        draw.polygon([scaled(point) for point in values], fill="white")

    def strap(cx: float, rail_y: float, bottom: float, tilt: float) -> None:
        hand_line([(cx, rail_y), (cx + tilt, bottom - 46)], width=2.8)
        x = cx + tilt
        cubic((x, bottom - 47), (x - 20, bottom - 47), (x - 21, bottom - 12), (x - 9, bottom), width=3)
        cubic((x - 9, bottom), (x + 4, bottom + 7), (x + 22, bottom - 7), (x + 22, bottom - 25), width=3)
        cubic((x + 22, bottom - 25), (x + 22, bottom - 41), (x + 12, bottom - 48), (x, bottom - 47), width=3)

    # The panel and train interior stay sparse and slightly imperfect.
    hand_line([(40, 43), (727, 41), (730, 982), (38, 980), (40, 43)], width=3.4, jitter=0.9)
    hand_line([(92, 177), (677, 176)], width=3.2)
    hand_line([(108, 232), (661, 231), (660, 895), (106, 892), (108, 232)], width=2.8)
    hand_line([(382, 231), (385, 895)], width=2.4)
    hand_line([(129, 292), (316, 290), (315, 469), (127, 472), (129, 292)], width=2.5)
    hand_line([(448, 286), (638, 289), (637, 468), (449, 466), (448, 286)], width=2.5)

    strap(167, 177, 268, -2)
    strap(314, 177, 251, 2)
    strap(494, 176, 258, -3)
    strap(625, 176, 273, 1)

    # Two commuters behind the protagonist. Their different angles break symmetry.
    white_oval((122, 335, 231, 448))
    hand_oval((122, 335, 231, 448), width=3, phase=0.6)
    hand_line([(146, 379), (166, 365), (190, 368), (213, 390)], width=3.6)
    hand_line([(148, 408), (160, 407)], width=2.3)
    cubic((216, 430), (239, 475), (267, 521), (307, 556), width=4.3)
    cubic((126, 432), (96, 486), (83, 545), (70, 593), width=3.8)

    white_oval((536, 329, 646, 447))
    hand_oval((536, 329, 646, 447), width=3, phase=1.4)
    hand_line([(549, 385), (568, 367), (600, 364), (631, 382)], width=3.5)
    hand_line([(589, 405), (601, 407)], width=2.2)
    cubic((543, 425), (522, 476), (497, 515), (460, 552), width=4.1)
    cubic((641, 425), (670, 481), (686, 536), (699, 584), width=3.7)

    # The new employee: hunched, tired, and visibly squeezed.
    white_oval((306, 298, 467, 490))
    white_shape([(326, 464), (446, 464), (465, 728), (306, 740), (303, 526)])
    cubic((309, 366), (310, 321), (339, 298), (383, 301), width=4.3)
    cubic((383, 301), (430, 301), (462, 334), (464, 388), width=4.1)
    cubic((464, 388), (466, 444), (439, 483), (394, 487), width=3.8)
    cubic((394, 487), (348, 491), (311, 458), (309, 401), width=3.7)
    cubic((309, 401), (308, 388), (308, 377), (309, 366), width=3.7)

    # Uneven hair strokes and a tiny resigned face.
    hand_line([(319, 350), (330, 319), (345, 340)], width=4)
    hand_line([(345, 337), (356, 308), (371, 336)], width=4)
    hand_line([(372, 335), (385, 305), (399, 338)], width=4)
    hand_line([(399, 338), (416, 309), (429, 346)], width=4)
    hand_line([(333, 397), (345, 400)], width=2.5)
    hand_line([(415, 400), (426, 397)], width=2.5)
    cubic((363, 454), (376, 443), (392, 442), (406, 452), width=2.6, jitter=0.35)

    # Collar, narrow body, and tie. The shoulders turn inward under pressure.
    cubic((327, 475), (311, 516), (306, 621), (311, 733), width=4.2)
    cubic((311, 733), (349, 742), (422, 738), (459, 725), width=4)
    cubic((459, 725), (461, 628), (459, 529), (445, 471), width=4.2)
    hand_line([(335, 477), (382, 515), (430, 477)], width=2.8)
    hand_line([(372, 506), (386, 506), (397, 520), (381, 531), (368, 519), (372, 506)], width=2.7)
    hand_line([(381, 531), (397, 594), (381, 618), (366, 592), (381, 531)], width=2.8)

    # Raised hand grips a strap; the other arm wraps around the work bag.
    cubic((438, 510), (451, 467), (462, 397), (473, 339), width=5)
    hand_oval((459, 319, 486, 348), width=2.8, irregularity=1.5)
    cubic((329, 510), (302, 541), (294, 594), (325, 633), width=5)

    # Slightly skewed bag, with a simple handle.
    white_shape([(314, 582), (449, 579), (454, 716), (309, 722)])
    hand_line([(314, 582), (449, 579), (454, 716), (309, 722), (314, 582)], width=3.8)
    hand_line([(345, 581), (344, 553), (416, 552), (419, 580)], width=2.9)

    # Tired legs do not quite stand straight.
    cubic((339, 737), (341, 791), (333, 855), (299, 912), width=4.7)
    cubic((422, 736), (421, 795), (432, 858), (468, 908), width=4.7)
    hand_line([(299, 912), (274, 917)], width=4.4)
    hand_line([(468, 908), (495, 916)], width=4.4)

    # Foreground commuters crop hard into the frame and press against him.
    white_shape([(-40, 505), (88, 503), (171, 585), (149, 833), (64, 806), (-40, 773)])
    white_oval((-39, 391, 104, 542))
    hand_oval((-39, 391, 104, 542), width=3.7, phase=0.2)
    hand_line([(6, 420), (33, 397), (66, 401), (96, 430)], width=4.1)
    hand_line([(45, 479), (59, 480)], width=2.4)
    cubic((91, 514), (145, 526), (205, 561), (322, 610), width=5.2)
    cubic((-22, 536), (46, 522), (107, 538), (157, 589), width=3.7)
    cubic((157, 589), (183, 661), (174, 750), (149, 833), width=3.8)
    hand_line([(149, 833), (64, 806), (-19, 777)], width=3.6)

    white_shape([(676, 496), (808, 503), (808, 765), (704, 804), (627, 825), (605, 581)])
    white_oval((658, 374, 806, 532))
    hand_oval((658, 374, 806, 532), width=3.7, phase=1.1)
    hand_line([(668, 421), (697, 395), (735, 397), (786, 430)], width=4.1)
    hand_line([(702, 471), (716, 472)], width=2.4)
    cubic((674, 505), (626, 524), (566, 558), (447, 612), width=5.3)
    cubic((790, 526), (738, 516), (686, 529), (624, 580), width=3.8)
    cubic((624, 580), (594, 651), (602, 742), (627, 825), width=3.8)
    hand_line([(627, 825), (704, 804), (788, 772)], width=3.6)

    output = Path(__file__).with_name("003-control.png")
    canvas.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(output)
    print(output)


if __name__ == "__main__":
    main()
