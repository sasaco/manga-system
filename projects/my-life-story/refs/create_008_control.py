"""Draw the sparse, textless guide and flat colors for episode 008."""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw


WIDTH = 768
HEIGHT = 1024
SCALE = 4
INK = (27, 26, 24)
PALE_TEAL = (157, 202, 201, 255)
MUSTARD = (244, 204, 72, 255)
WARM_GRAY = (202, 198, 196, 255)
LIGHT_GRAY = (232, 229, 226, 255)
WHITE = (255, 255, 255, 255)
RNG = random.Random(20010909)


def main() -> None:
    line_image = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), "white")
    line_draw = ImageDraw.Draw(line_image)
    color_image = Image.new("RGBA", (WIDTH * SCALE, HEIGHT * SCALE), (0, 0, 0, 0))
    color_draw = ImageDraw.Draw(color_image)

    def px(point: tuple[float, float]) -> tuple[int, int]:
        return round(point[0] * SCALE), round(point[1] * SCALE)

    def line(
        points: list[tuple[float, float]],
        *,
        width: float = 3.0,
        jitter: float = 0.25,
        closed: bool = False,
        ink: tuple[int, int, int] = INK,
    ) -> None:
        source = points + ([points[0]] if closed else [])
        sampled: list[tuple[float, float]] = []
        for segment, (start, end) in enumerate(zip(source, source[1:])):
            steps = max(2, round(math.dist(start, end) / 6))
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
        last = max(1, len(sampled) - 2)
        for index, (start, end) in enumerate(zip(sampled, sampled[1:])):
            pressure = 0.86 + 0.18 * math.sin(math.pi * index / last)
            line_draw.line(
                [px(start), px(end)],
                fill=ink,
                width=max(1, round(width * SCALE * pressure)),
            )

    def cubic_points(
        start: tuple[float, float],
        control_a: tuple[float, float],
        control_b: tuple[float, float],
        end: tuple[float, float],
        steps: int = 36,
    ) -> list[tuple[float, float]]:
        result: list[tuple[float, float]] = []
        for step in range(steps + 1):
            t = step / steps
            u = 1 - t
            result.append(
                (
                    u**3 * start[0] + 3 * u**2 * t * control_a[0]
                    + 3 * u * t**2 * control_b[0] + t**3 * end[0],
                    u**3 * start[1] + 3 * u**2 * t * control_a[1]
                    + 3 * u * t**2 * control_b[1] + t**3 * end[1],
                )
            )
        return result

    def curve(
        start: tuple[float, float],
        control_a: tuple[float, float],
        control_b: tuple[float, float],
        end: tuple[float, float],
        *,
        width: float = 3.0,
        jitter: float = 0.2,
    ) -> None:
        line(cubic_points(start, control_a, control_b, end), width=width, jitter=jitter)

    def shape(
        segments: list[
            tuple[
                tuple[float, float], tuple[float, float],
                tuple[float, float], tuple[float, float]
            ]
        ],
        *,
        fill: tuple[int, int, int, int],
        width: float = 3.5,
    ) -> None:
        values: list[tuple[float, float]] = []
        for index, segment in enumerate(segments):
            part = cubic_points(*segment)
            values.extend(part if index == 0 else part[1:])
        line_draw.polygon([px(point) for point in values], fill="white")
        color_draw.polygon([px(point) for point in values], fill=fill)
        line(values, width=width, jitter=0.36, closed=True)

    def polygon(
        points: list[tuple[float, float]],
        *,
        fill: tuple[int, int, int, int] = WHITE,
        width: float = 2.7,
    ) -> None:
        line_draw.polygon([px(point) for point in points], fill="white")
        color_draw.polygon([px(point) for point in points], fill=fill)
        line(points, width=width, jitter=0.2, closed=True)

    def oval(
        bounds: tuple[float, float, float, float],
        *,
        phase: float,
        fill: tuple[int, int, int, int] = WHITE,
        width: float = 3.5,
    ) -> None:
        left, top, right, bottom = bounds
        cx = (left + right) / 2
        cy = (top + bottom) / 2
        rx = (right - left) / 2
        ry = (bottom - top) / 2
        points = []
        for step in range(80):
            angle = math.tau * step / 80
            wobble = 1 + 0.022 * math.sin(3 * angle + phase) + 0.009 * math.sin(7 * angle)
            points.append((cx + rx * wobble * math.cos(angle), cy + ry * wobble * math.sin(angle)))
        line_draw.polygon([px(point) for point in points], fill="white")
        color_draw.polygon([px(point) for point in points], fill=fill)
        line(points, width=width, jitter=0.3, closed=True)

    # Single hand-drawn frame; the upper center stays open for manual lettering.
    line([(43, 43), (724, 44), (722, 980), (45, 981), (43, 43)], width=3.2, jitter=0.9)

    # A numeral-free clock: two full rotations of its hands hint at hours passing.
    oval((76, 108, 174, 207), phase=0.5, fill=WHITE, width=2.5)
    line([(125, 157), (125, 126)], width=2.2, jitter=0.12)
    line([(125, 157), (149, 169)], width=2.2, jitter=0.12)
    line([(125, 157), (105, 178)], width=1.4, jitter=0.1, ink=MUSTARD[:3])
    color_draw.ellipse((489, 621, 511, 643), fill=MUSTARD)

    # Exactly two empty chairs, kept small and quiet in the far background.
    for left, top, lean in ((76, 272, -4), (185, 290, 4)):
        shape(
            [
                ((left, top), (left - 6, top + 30), (left - 2, top + 78), (left + 8, top + 93)),
                ((left + 8, top + 93), (left + 30, top + 104), (left + 69, top + 101), (left + 82, top + 88)),
                ((left + 82, top + 88), (left + 89, top + 49), (left + 85, top + 15), (left + 72, top + 3)),
                ((left + 72, top + 3), (left + 53, top - 5), (left + 18, top - 4), (left, top)),
            ],
            fill=LIGHT_GRAY,
            width=2.1,
        )
        line([(left + 10, top + 94), (left + 4 + lean, top + 128)], width=2.0, jitter=0.14)
        line([(left + 71, top + 96), (left + 78 + lean, top + 129)], width=2.0, jitter=0.14)

    # Warm-gray fingerprint-like hesitation shadow behind the apprentice.
    for index in range(8):
        inset = index * 7
        color_draw.arc(
            (
                round((71 + inset) * SCALE), round((454 + inset * 0.7) * SCALE),
                round((325 - inset * 0.4) * SCALE), round((892 - inset * 0.9) * SCALE),
            ),
            92,
            270,
            fill=(*WARM_GRAY[:3], 145),
            width=max(2, round(1.5 * SCALE)),
        )

    # Apprentice: an oval face and a broad bean body, not a stick figure.
    shape(
        [
            ((105, 599), (80, 654), (91, 852), (117, 914)),
            ((117, 914), (160, 941), (254, 938), (287, 910)),
            ((287, 910), (309, 834), (308, 663), (276, 606)),
            ((276, 606), (235, 578), (142, 575), (105, 599)),
        ],
        fill=PALE_TEAL,
        width=3.9,
    )
    oval((112, 385, 286, 619), phase=1.1, fill=WHITE, width=3.7)
    for x, offset in ((151, 0), (174, -9), (199, -11), (224, -4)):
        curve((x, 411 + offset), (x, 393 + offset), (x + 2, 380 + offset), (x + 4, 369 + offset), width=2.9)
    line([(150, 503), (171, 501)], width=2.0, jitter=0.12)
    line([(225, 501), (246, 504)], width=2.0, jitter=0.12)
    curve((178, 559), (190, 552), (205, 552), (216, 560), width=2.0, jitter=0.14)
    polygon([(184, 601), (207, 601), (218, 622), (196, 641), (174, 621)], fill=MUSTARD, width=2.0)

    # Bare desk and two mitten-like resting gestures.
    polygon([(63, 720), (354, 715), (363, 783), (59, 789)], fill=WHITE, width=3.0)
    line([(82, 789), (78, 917)], width=3.0, jitter=0.18)
    line([(340, 783), (348, 917)], width=3.0, jitter=0.18)
    shape(
        [
            ((121, 678), (142, 673), (165, 691), (181, 719)),
            ((181, 719), (185, 732), (176, 744), (161, 744)),
            ((161, 744), (139, 730), (118, 718), (111, 701)),
            ((111, 701), (108, 690), (113, 681), (121, 678)),
        ],
        fill=PALE_TEAL,
        width=2.8,
    )
    shape(
        [
            ((265, 680), (284, 681), (303, 696), (313, 718)),
            ((313, 718), (316, 731), (306, 742), (292, 741)),
            ((292, 741), (273, 729), (257, 712), (255, 697)),
            ((255, 697), (255, 688), (260, 682), (265, 680)),
        ],
        fill=PALE_TEAL,
        width=2.8,
    )

    # Older company president, with one firm outlined instructive gesture.
    shape(
        [
            ((520, 610), (494, 664), (499, 852), (525, 916)),
            ((525, 916), (560, 943), (645, 941), (676, 911)),
            ((676, 911), (697, 838), (694, 667), (667, 613)),
            ((667, 613), (634, 583), (553, 582), (520, 610)),
        ],
        fill=WARM_GRAY,
        width=3.9,
    )
    oval((520, 405, 681, 621), phase=0.35, fill=WHITE, width=3.7)
    curve((536, 462), (556, 427), (627, 423), (665, 460), width=3.0, jitter=0.2)
    for x in (554, 578, 603, 629, 650):
        line([(x, 446), (x + 1, 474)], width=2.1, jitter=0.12)
    line([(548, 488), (576, 481)], width=3.0, jitter=0.12)
    line([(624, 481), (652, 489)], width=3.0, jitter=0.12)
    line([(552, 514), (574, 511)], width=2.1, jitter=0.12)
    line([(626, 511), (648, 514)], width=2.1, jitter=0.12)
    curve((575, 576), (592, 565), (613, 565), (630, 577), width=2.1, jitter=0.14)
    for x, y in ((580, 587), (593, 592), (617, 591), (630, 584)):
        line([(x, y), (x + 6, y + 7)], width=1.6, jitter=0.1)
    shape(
        [
            ((523, 672), (492, 674), (455, 690), (421, 710)),
            ((421, 710), (411, 718), (412, 733), (424, 740)),
            ((424, 740), (465, 727), (500, 721), (531, 724)),
            ((531, 724), (545, 713), (544, 687), (523, 672)),
        ],
        fill=WARM_GRAY,
        width=3.1,
    )

    output = Path(__file__).with_name("008-control.png")
    color_output = Path(__file__).with_name("008-color.png")
    line_image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(output)
    color_image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(color_output)
    print(output)
    print(color_output)


if __name__ == "__main__":
    main()
