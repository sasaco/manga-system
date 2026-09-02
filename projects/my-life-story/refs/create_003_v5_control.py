"""Draw episode 003 as a sparse, warm, textless hand-drawn train scene."""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw


WIDTH = 768
HEIGHT = 1024
SCALE = 4
INK = (24, 24, 23)
RNG = random.Random(20010903)


def main() -> None:
    canvas = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), "white")
    draw = ImageDraw.Draw(canvas)

    def point(value: tuple[float, float]) -> tuple[int, int]:
        return round(value[0] * SCALE), round(value[1] * SCALE)

    def path(
        values: list[tuple[float, float]],
        *,
        width: float = 3.2,
        jitter: float = 0.52,
        closed: bool = False,
    ) -> None:
        source = values + ([values[0]] if closed else [])
        sampled: list[tuple[float, float]] = []
        for segment, (start, end) in enumerate(zip(source, source[1:])):
            steps = max(2, round(math.dist(start, end) / 7))
            for step in range(steps):
                if segment and step == 0:
                    continue
                t = step / steps
                envelope = math.sin(math.pi * t)
                sampled.append(
                    (
                        start[0] + (end[0] - start[0]) * t
                        + RNG.uniform(-jitter, jitter) * envelope,
                        start[1] + (end[1] - start[1]) * t
                        + RNG.uniform(-jitter, jitter) * envelope,
                    )
                )
        sampled.append(source[-1])
        draw.line(
            [point(value) for value in sampled],
            fill=INK,
            width=max(1, round(width * SCALE)),
            joint="curve",
        )

    def curve(
        start: tuple[float, float],
        control_a: tuple[float, float],
        control_b: tuple[float, float],
        end: tuple[float, float],
        *,
        width: float = 3.2,
        jitter: float = 0.48,
    ) -> None:
        values: list[tuple[float, float]] = []
        for step in range(37):
            t = step / 36
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
        path(values, width=width, jitter=jitter)

    def oval(
        bounds: tuple[float, float, float, float],
        *,
        width: float = 3.2,
        phase: float = 0.0,
        wobble: float = 0.012,
    ) -> None:
        left, top, right, bottom = bounds
        cx = (left + right) / 2
        cy = (top + bottom) / 2
        rx = (right - left) / 2
        ry = (bottom - top) / 2
        values: list[tuple[float, float]] = []
        for step in range(72):
            angle = math.tau * step / 72
            radius = 1 + wobble * math.sin(3 * angle + phase)
            values.append(
                (cx + rx * radius * math.cos(angle), cy + ry * radius * math.sin(angle))
            )
        path(values, width=width, jitter=0.36, closed=True)

    def white_polygon(values: list[tuple[float, float]]) -> None:
        draw.polygon([point(value) for value in values], fill="white")

    def white_oval(bounds: tuple[float, float, float, float]) -> None:
        draw.ellipse(tuple(round(value * SCALE) for value in bounds), fill="white")

    def dot(x: float, y: float, radius: float = 2.5) -> None:
        draw.ellipse(
            (
                round((x - radius) * SCALE),
                round((y - radius) * SCALE),
                round((x + radius) * SCALE),
                round((y + radius) * SCALE),
            ),
            fill=INK,
        )

    def strap(cx: float, rail_y: float, loop_y: float, lean: float = 0) -> None:
        path([(cx, rail_y), (cx + lean, loop_y - 39)], width=2.5, jitter=0.34)
        x = cx + lean
        curve((x, loop_y - 40), (x - 17, loop_y - 43), (x - 21, loop_y - 13), (x - 9, loop_y + 1), width=2.8)
        curve((x - 9, loop_y + 1), (x + 4, loop_y + 10), (x + 22, loop_y - 2), (x + 22, loop_y - 22), width=2.8)
        curve((x + 22, loop_y - 22), (x + 22, loop_y - 36), (x + 12, loop_y - 42), (x, loop_y - 40), width=2.8)

    # One open, slightly imperfect frame and only enough train detail to set the place.
    path([(45, 45), (721, 43), (724, 979), (42, 981), (45, 45)], width=3.3, jitter=0.78)
    path([(106, 177), (661, 176)], width=3.0, jitter=0.42)
    path([(112, 246), (656, 244), (656, 896), (111, 894), (112, 246)], width=2.6)
    path([(383, 245), (385, 895)], width=2.2)
    path([(136, 306), (304, 303), (304, 471), (135, 473), (136, 306)], width=2.3)
    path([(465, 301), (632, 304), (632, 470), (465, 468), (465, 301)], width=2.3)
    strap(177, 177, 268, -3)
    strap(321, 177, 252, 2)
    strap(495, 176, 254, -2)
    strap(621, 176, 271, 1)

    # Quiet commuters behind the protagonist: visible, but not detailed.
    white_oval((126, 349, 226, 454))
    oval((126, 349, 226, 454), width=2.9, phase=0.4)
    path([(140, 389), (161, 370), (188, 372), (214, 395)], width=3.5)
    dot(169, 411, 1.8)
    curve((217, 438), (242, 472), (265, 514), (294, 548), width=3.8)
    curve((130, 438), (107, 480), (94, 522), (84, 558), width=3.4)

    white_oval((536, 342, 639, 451))
    oval((536, 342, 639, 451), width=2.9, phase=1.3)
    path([(546, 394), (567, 374), (600, 373), (630, 397)], width=3.5)
    dot(589, 415, 1.8)
    curve((542, 435), (520, 477), (493, 518), (466, 548), width=3.8)
    curve((634, 438), (659, 480), (674, 524), (686, 557), width=3.4)

    # The young employee is deliberately narrow, off-balance, and pressed inward.
    white_polygon([(322, 448), (447, 448), (461, 748), (310, 752), (313, 520)])
    white_oval((311, 293, 463, 486))
    curve((314, 367), (314, 319), (341, 294), (382, 296), width=4.1)
    curve((382, 296), (429, 293), (459, 326), (461, 382), width=3.9)
    curve((461, 382), (463, 442), (438, 479), (395, 484), width=3.7)
    curve((395, 484), (350, 489), (316, 458), (313, 405), width=3.6)
    curve((313, 405), (312, 389), (313, 377), (314, 367), width=3.6)

    # Uneven fringe and the smallest possible tired expression.
    path([(320, 357), (330, 321), (345, 342), (358, 309), (373, 340)], width=3.9)
    path([(373, 340), (387, 305), (402, 340), (420, 311), (438, 353)], width=3.9)
    path([(336, 399), (347, 401)], width=2.3)
    path([(414, 401), (426, 398)], width=2.3)
    curve((363, 450), (375, 439), (393, 439), (406, 450), width=2.5, jitter=0.26)

    # Shirt, tiny tie, and shoulders folded by the crowd.
    curve((330, 470), (313, 526), (309, 639), (316, 748), width=4.0)
    curve((316, 748), (355, 755), (421, 752), (455, 741), width=3.8)
    curve((455, 741), (461, 640), (458, 527), (444, 469), width=4.0)
    path([(337, 477), (382, 514), (427, 477)], width=2.7)
    path([(373, 507), (387, 507), (397, 519), (382, 531), (368, 519), (373, 507)], width=2.5)
    path([(382, 531), (396, 581), (381, 603), (367, 580), (382, 531)], width=2.6)

    # One bent arm reaches for a strap; the other curls protectively around the bag.
    curve((439, 516), (455, 458), (465, 337), (490, 270), width=4.7)
    hand = [(486, 256), (495, 257), (501, 264), (501, 272), (496, 280), (488, 281), (482, 274), (481, 266)]
    white_polygon(hand)
    path(hand, width=2.6, jitter=0.24, closed=True)
    path([(482, 267), (488, 270)], width=1.9, jitter=0.16)
    curve((328, 517), (304, 552), (299, 600), (326, 631), width=4.6)

    # A slightly crooked work bag makes him read as a new office worker at a glance.
    white_polygon([(316, 588), (449, 584), (455, 721), (307, 727)])
    path([(316, 588), (449, 584), (455, 721), (307, 727), (316, 588)], width=3.6)
    path([(346, 587), (346, 558), (415, 556), (418, 585)], width=2.7)
    curve((318, 642), (348, 657), (387, 663), (447, 641), width=2.5)

    # Unsteady feet reinforce that he is being carried by the crush of the carriage.
    curve((342, 752), (344, 805), (333, 861), (303, 914), width=4.2)
    curve((419, 750), (419, 805), (430, 861), (462, 910), width=4.2)
    path([(303, 914), (280, 919)], width=4.0)
    path([(462, 910), (487, 917)], width=4.0)

    # Cropped foreground bodies overlap the central figure at different heights.
    white_polygon([(-34, 508), (77, 487), (179, 552), (268, 621), (240, 824), (137, 800), (-34, 763)])
    white_oval((-45, 378, 118, 548))
    oval((-45, 378, 118, 548), width=3.6, phase=0.2)
    path([(-1, 424), (31, 394), (68, 397), (105, 434)], width=4.0)
    path([(41, 478), (55, 480)], width=2.2)
    curve((102, 515), (149, 530), (205, 572), (321, 625), width=5.0)
    curve((-15, 538), (50, 518), (114, 535), (175, 586), width=3.6)
    curve((175, 586), (202, 657), (205, 742), (240, 824), width=3.6)
    path([(240, 824), (137, 800), (27, 775)], width=3.5)

    white_polygon([(679, 490), (805, 500), (805, 764), (706, 804), (615, 833), (577, 604)])
    white_oval((641, 361, 806, 536))
    oval((641, 361, 806, 536), width=3.6, phase=1.2)
    path([(653, 411), (683, 382), (727, 384), (784, 426)], width=4.0)
    path([(693, 473), (707, 474)], width=2.2)
    curve((655, 510), (606, 527), (550, 566), (446, 628), width=5.0)
    curve((789, 526), (741, 511), (684, 528), (620, 581), width=3.6)
    curve((620, 581), (590, 657), (592, 752), (615, 833), width=3.6)
    path([(615, 833), (706, 804), (790, 770)], width=3.5)

    # A few short pressure marks read as motion without becoming symbols or lettering.
    path([(285, 579), (269, 570)], width=2.4, jitter=0.2)
    path([(477, 575), (493, 565)], width=2.4, jitter=0.2)
    path([(286, 599), (268, 597)], width=2.2, jitter=0.2)

    output = Path(__file__).with_name("003-control.png")
    canvas.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(output)
    print(output)


if __name__ == "__main__":
    main()
