"""Draw episode 003 with rounded doodle characters rather than stick figures."""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw


WIDTH = 768
HEIGHT = 1024
SCALE = 4
INK = (25, 24, 23)
PALE_TEAL = (157, 202, 201, 255)
MUSTARD = (244, 204, 72, 255)
WARM_GRAY = (205, 201, 199, 255)
PALE_GRAY = (224, 222, 219, 255)
RNG = random.Random(20010904)


def main() -> None:
    canvas = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), "white")
    draw = ImageDraw.Draw(canvas)
    color_canvas = Image.new("RGBA", (WIDTH * SCALE, HEIGHT * SCALE), (0, 0, 0, 0))
    color_draw = ImageDraw.Draw(color_canvas)

    def px(value: tuple[float, float]) -> tuple[int, int]:
        return round(value[0] * SCALE), round(value[1] * SCALE)

    def line(
        values: list[tuple[float, float]],
        *,
        width: float = 3.3,
        jitter: float = 0.55,
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
            [px(value) for value in sampled],
            fill=INK,
            width=max(1, round(width * SCALE)),
            joint="curve",
        )

    def cubic_points(
        start: tuple[float, float],
        control_a: tuple[float, float],
        control_b: tuple[float, float],
        end: tuple[float, float],
        steps: int = 28,
    ) -> list[tuple[float, float]]:
        values: list[tuple[float, float]] = []
        for step in range(steps + 1):
            t = step / steps
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
        return values

    def curve(
        start: tuple[float, float],
        control_a: tuple[float, float],
        control_b: tuple[float, float],
        end: tuple[float, float],
        *,
        width: float = 3.3,
        jitter: float = 0.5,
    ) -> None:
        line(
            cubic_points(start, control_a, control_b, end, 34),
            width=width,
            jitter=jitter,
        )

    def closed_curves(
        segments: list[
            tuple[
                tuple[float, float],
                tuple[float, float],
                tuple[float, float],
                tuple[float, float],
            ]
        ],
        *,
        width: float = 3.6,
        fill: tuple[int, int, int, int] | None = None,
    ) -> None:
        values: list[tuple[float, float]] = []
        for index, segment in enumerate(segments):
            sampled = cubic_points(*segment)
            values.extend(sampled if index == 0 else sampled[1:])
        draw.polygon([px(value) for value in values], fill="white")
        if fill:
            color_draw.polygon([px(value) for value in values], fill=fill)
        line(values, width=width, jitter=0.42, closed=True)

    def oval(
        bounds: tuple[float, float, float, float],
        *,
        width: float = 3.5,
        phase: float = 0,
    ) -> None:
        left, top, right, bottom = bounds
        cx = (left + right) / 2
        cy = (top + bottom) / 2
        rx = (right - left) / 2
        ry = (bottom - top) / 2
        values: list[tuple[float, float]] = []
        for step in range(72):
            angle = math.tau * step / 72
            radius = 1 + 0.011 * math.sin(3 * angle + phase)
            values.append(
                (cx + rx * radius * math.cos(angle), cy + ry * radius * math.sin(angle))
            )
        draw.polygon([px(value) for value in values], fill="white")
        color_draw.polygon([px(value) for value in values], fill=(255, 255, 255, 255))
        line(values, width=width, jitter=0.35, closed=True)

    def dot(x: float, y: float, radius: float = 2.3) -> None:
        draw.ellipse(
            (
                round((x - radius) * SCALE),
                round((y - radius) * SCALE),
                round((x + radius) * SCALE),
                round((y + radius) * SCALE),
            ),
            fill=INK,
        )

    def strap(cx: float, loop_y: float, lean: float = 0) -> None:
        line([(cx, 174), (cx + lean, loop_y - 39)], width=2.5, jitter=0.3)
        x = cx + lean
        curve((x, loop_y - 40), (x - 18, loop_y - 43), (x - 20, loop_y - 12), (x - 8, loop_y + 1), width=2.8)
        curve((x - 8, loop_y + 1), (x + 5, loop_y + 8), (x + 22, loop_y - 3), (x + 22, loop_y - 23), width=2.8)
        curve((x + 22, loop_y - 23), (x + 21, loop_y - 37), (x + 11, loop_y - 42), (x, loop_y - 40), width=2.8)

    # Sparse carriage: one frame, double doors, rail, and four straps.
    line([(43, 44), (722, 43), (724, 980), (42, 981), (43, 44)], width=3.4, jitter=0.75)
    line([(105, 174), (663, 174)], width=3.0, jitter=0.4)
    line([(109, 244), (658, 244), (658, 897), (109, 897), (109, 244)], width=2.6)
    line([(383, 244), (384, 897)], width=2.2)
    line([(137, 306), (301, 305), (301, 461), (136, 463), (137, 306)], width=2.2)
    line([(469, 304), (632, 306), (632, 462), (468, 460), (469, 304)], width=2.2)
    strap(171, 263, -2)
    strap(318, 249, 2)
    strap(500, 252, -2)
    strap(622, 266, 1)

    # Two background commuters are compact head-and-body figures, not line skeletons.
    closed_curves(
        [
            ((139, 439), (113, 470), (107, 566), (126, 650)),
            ((126, 650), (152, 692), (211, 690), (238, 649)),
            ((238, 649), (257, 567), (247, 480), (218, 440)),
            ((218, 440), (194, 423), (161, 423), (139, 439)),
        ],
        width=3.2,
        fill=PALE_GRAY,
    )
    oval((130, 333, 228, 445), width=3.2, phase=0.5)
    line([(142, 381), (160, 363), (190, 362), (216, 384)], width=3.5)
    dot(160, 405, 1.8)
    dot(197, 405, 1.8)

    closed_curves(
        [
            ((536, 439), (507, 476), (500, 572), (522, 651)),
            ((522, 651), (550, 689), (608, 687), (634, 646)),
            ((634, 646), (654, 560), (644, 478), (617, 439)),
            ((617, 439), (593, 423), (560, 423), (536, 439)),
        ],
        width=3.2,
        fill=PALE_GRAY,
    )
    oval((529, 329, 631, 445), width=3.2, phase=1.4)
    line([(540, 383), (563, 363), (597, 363), (621, 386)], width=3.5)
    dot(559, 407, 1.8)
    dot(598, 407, 1.8)

    # The protagonist's body is one rounded, slightly lopsided mass.
    closed_curves(
        [
            ((330, 430), (295, 455), (286, 543), (294, 647)),
            ((294, 647), (298, 753), (315, 833), (359, 861)),
            ((359, 861), (391, 879), (431, 861), (451, 829)),
            ((451, 829), (477, 789), (480, 705), (478, 614)),
            ((478, 614), (478, 516), (468, 453), (438, 430)),
            ((438, 430), (410, 411), (359, 411), (330, 430)),
        ],
        width=4.1,
        fill=PALE_TEAL,
    )

    # A short, outlined arm grows from the torso and reaches the nearest strap.
    closed_curves(
        [
            ((430, 475), (447, 438), (461, 364), (485, 281)),
            ((485, 281), (491, 270), (502, 274), (502, 286)),
            ((502, 286), (485, 375), (475, 458), (456, 503)),
            ((456, 503), (448, 515), (432, 500), (430, 475)),
        ],
        width=3.4,
        fill=PALE_TEAL,
    )

    # The head overlaps the body, like the simple rounded figures in the reference.
    oval((310, 286, 462, 474), width=4.0, phase=0.8)
    line([(319, 350), (329, 316), (344, 337), (356, 306), (371, 336)], width=3.9)
    line([(371, 336), (385, 302), (401, 337), (417, 308), (438, 350)], width=3.9)
    line([(336, 395), (348, 397)], width=2.3)
    line([(413, 397), (425, 394)], width=2.3)
    curve((362, 443), (376, 431), (394, 431), (408, 443), width=2.6, jitter=0.25)

    # Collar, small tie, and bag sit inside the rounded body instead of on stick limbs.
    line([(329, 463), (382, 511), (434, 462)], width=2.7)
    line([(374, 503), (389, 503), (398, 516), (382, 528), (367, 516), (374, 503)], width=2.5)
    line([(382, 528), (396, 579), (381, 602), (367, 579), (382, 528)], width=2.6)
    closed_curves(
        [
            ((323, 584), (355, 578), (417, 578), (449, 585)),
            ((449, 585), (455, 620), (454, 697), (448, 730)),
            ((448, 730), (413, 739), (351, 739), (316, 728)),
            ((316, 728), (310, 691), (311, 620), (323, 584)),
        ],
        width=3.5,
        fill=MUSTARD,
    )
    line([(348, 582), (349, 554), (415, 554), (417, 581)], width=2.6)
    curve((315, 646), (347, 664), (402, 666), (452, 642), width=2.4, jitter=0.28)
    curve((311, 533), (295, 576), (299, 632), (322, 650), width=3.1)

    # Foreground commuters are broad bean-shaped bodies that visibly squeeze him.
    closed_curves(
        [
            ((-20, 496), (45, 472), (126, 485), (177, 531)),
            ((177, 531), (222, 572), (261, 635), (278, 707)),
            ((278, 707), (289, 766), (271, 839), (237, 892)),
            ((237, 892), (165, 898), (70, 873), (-20, 830)),
            ((-20, 830), (-45, 714), (-44, 574), (-20, 496)),
        ],
        width=4.1,
        fill=WARM_GRAY,
    )
    oval((-37, 350, 137, 539), width=3.9, phase=0.2)
    line([(-2, 406), (28, 377), (70, 380), (113, 423)], width=4.1)
    dot(37, 455, 2.0)
    dot(77, 456, 2.0)
    curve((39, 495), (51, 503), (66, 503), (80, 496), width=2.3, jitter=0.24)
    curve((166, 531), (209, 553), (255, 593), (321, 633), width=4.6)

    closed_curves(
        [
            ((653, 489), (704, 466), (783, 475), (812, 510)),
            ((812, 510), (824, 622), (817, 746), (793, 832)),
            ((793, 832), (713, 873), (620, 897), (548, 891)),
            ((548, 891), (516, 838), (500, 764), (512, 700)),
            ((512, 700), (528, 626), (606, 522), (653, 489)),
        ],
        width=4.1,
        fill=WARM_GRAY,
    )
    oval((627, 338, 806, 533), width=3.9, phase=1.2)
    line([(638, 402), (674, 370), (719, 372), (785, 417)], width=4.1)
    dot(676, 452, 2.0)
    dot(718, 451, 2.0)
    curve((675, 490), (688, 500), (705, 500), (721, 491), width=2.3, jitter=0.24)
    curve((648, 520), (602, 545), (551, 588), (448, 637), width=4.6)

    # Short pressure marks clarify the crowd without resembling writing.
    line([(290, 580), (276, 573)], width=2.3, jitter=0.18)
    line([(291, 600), (275, 599)], width=2.2, jitter=0.18)
    line([(475, 578), (489, 568)], width=2.3, jitter=0.18)

    output = Path(__file__).with_name("003-control.png")
    color_output = Path(__file__).with_name("003-color.png")
    canvas.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(output)
    color_canvas.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(color_output)
    print(output)
    print(color_output)


if __name__ == "__main__":
    main()
