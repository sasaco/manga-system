"""Draw episode 004 as a sparse, textless late-night office scene."""

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
DARK_WARM_GRAY = (112, 107, 104, 255)
RNG = random.Random(20010905)


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
        width: float = 3.2,
        jitter: float = 0.5,
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
        steps: int = 32,
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
        width: float = 3.2,
        jitter: float = 0.45,
    ) -> None:
        line(
            cubic_points(start, control_a, control_b, end),
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
        width: float = 3.5,
        fill: tuple[int, int, int, int] | None = None,
    ) -> None:
        values: list[tuple[float, float]] = []
        for index, segment in enumerate(segments):
            sampled = cubic_points(*segment)
            values.extend(sampled if index == 0 else sampled[1:])
        draw.polygon([px(value) for value in values], fill="white")
        if fill:
            color_draw.polygon([px(value) for value in values], fill=fill)
        line(values, width=width, jitter=0.4, closed=True)

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
            radius = 1 + 0.012 * math.sin(3 * angle + phase)
            values.append(
                (cx + rx * radius * math.cos(angle), cy + ry * radius * math.sin(angle))
            )
        draw.polygon([px(value) for value in values], fill="white")
        line(values, width=width, jitter=0.34, closed=True)

    def dot(x: float, y: float, radius: float = 2.2) -> None:
        draw.ellipse(
            (
                round((x - radius) * SCALE),
                round((y - radius) * SCALE),
                round((x + radius) * SCALE),
                round((y + radius) * SCALE),
            ),
            fill=INK,
        )

    def paper(points: list[tuple[float, float]], *, width: float = 2.2) -> None:
        draw.polygon([px(value) for value in points], fill="white")
        line(points, width=width, jitter=0.25, closed=True)

    def cup(x: float, y: float) -> None:
        line([(x, y), (x + 37, y), (x + 32, y + 42), (x + 5, y + 42), (x, y)], width=2.4)
        curve((x + 35, y + 9), (x + 53, y + 7), (x + 53, y + 31), (x + 33, y + 31), width=2.2)

    # One sparse frame and a single dark window establish the late hour.
    line([(44, 44), (722, 43), (724, 980), (43, 981), (44, 44)], width=3.4, jitter=0.75)
    color_draw.rounded_rectangle(
        (86 * SCALE, 92 * SCALE, 344 * SCALE, 302 * SCALE),
        radius=10 * SCALE,
        fill=DARK_WARM_GRAY,
    )
    line([(87, 93), (344, 92), (344, 303), (86, 303), (87, 93)], width=2.8)
    color_draw.ellipse((266 * SCALE, 126 * SCALE, 303 * SCALE, 163 * SCALE), fill=(255, 255, 255, 255))
    oval((266, 126, 303, 163), width=2.0, phase=0.6)
    line([(215, 93), (215, 303)], width=2.0, jitter=0.25)

    # Small desk lamp: the only bright office prop besides the blank paper.
    line([(606, 207), (606, 332)], width=3.0)
    line([(606, 207), (649, 170)], width=3.0)
    closed_curves(
        [
            ((624, 157), (637, 145), (664, 145), (677, 157)),
            ((677, 157), (682, 174), (677, 190), (672, 198)),
            ((672, 198), (651, 200), (625, 198), (609, 192)),
            ((609, 192), (612, 177), (617, 164), (624, 157)),
        ],
        width=2.8,
        fill=MUSTARD,
    )
    line([(580, 333), (633, 333)], width=3.0)

    # Rounded bodies sit behind the desk; legs are absorbed into the silhouettes.
    closed_curves(
        [
            ((104, 486), (82, 520), (76, 626), (91, 725)),
            ((91, 725), (122, 752), (225, 754), (270, 724)),
            ((270, 724), (283, 621), (270, 526), (247, 487)),
            ((247, 487), (208, 465), (142, 465), (104, 486)),
        ],
        width=3.7,
        fill=WARM_GRAY,
    )
    closed_curves(
        [
            ((302, 476), (280, 515), (278, 627), (291, 742)),
            ((291, 742), (326, 773), (435, 773), (473, 741)),
            ((473, 741), (484, 625), (480, 518), (457, 476)),
            ((457, 476), (421, 452), (338, 452), (302, 476)),
        ],
        width=4.0,
        fill=PALE_TEAL,
    )
    closed_curves(
        [
            ((501, 490), (481, 530), (478, 629), (492, 724)),
            ((492, 724), (529, 751), (629, 751), (674, 721)),
            ((674, 721), (686, 620), (675, 527), (650, 489)),
            ((650, 489), (616, 467), (537, 467), (501, 490)),
        ],
        width=3.7,
        fill=MUSTARD,
    )

    # Faces overlap their broad bodies and use only a few marks.
    oval((112, 334, 257, 509), width=3.8, phase=0.4)
    line([(123, 394), (145, 362), (181, 352), (220, 373), (249, 406)], width=4.0)
    line([(142, 425), (158, 421)], width=2.4)
    line([(207, 421), (223, 425)], width=2.4)
    line([(170, 464), (181, 468)], width=2.1)
    line([(191, 467), (202, 463)], width=2.1)
    line([(177, 482), (181, 487)], width=1.8)
    line([(194, 486), (198, 481)], width=1.8)

    oval((306, 314, 459, 498), width=4.0, phase=1.0)
    line([(316, 375), (328, 339), (345, 366), (361, 332), (378, 365)], width=3.8)
    line([(378, 365), (395, 329), (411, 365), (428, 338), (451, 382)], width=3.8)
    dot(344, 418, 2.5)
    dot(417, 418, 2.5)
    curve((361, 467), (373, 455), (393, 455), (405, 468), width=2.5, jitter=0.22)
    line([(325, 490), (382, 539), (440, 490)], width=2.7)
    line([(373, 531), (390, 531), (398, 545), (381, 557), (365, 545), (373, 531)], width=2.4)
    line([(381, 557), (394, 604), (381, 622), (368, 604), (381, 557)], width=2.5)

    oval((505, 347, 649, 514), width=3.7, phase=1.5)
    line([(516, 405), (536, 371), (569, 360), (607, 371), (640, 409)], width=3.7)
    line([(534, 439), (551, 441)], width=2.3)
    line([(599, 441), (616, 438)], width=2.3)
    curve((558, 480), (569, 486), (582, 486), (593, 479), width=2.2, jitter=0.2)

    # Long desk and blank calculation sheets. No marks appear on any paper.
    color_draw.polygon([px((72, 642)), px((697, 642)), px((722, 910)), px((46, 910))], fill=(235, 232, 228, 255))
    line([(72, 642), (697, 642), (722, 910), (46, 910), (72, 642)], width=3.5, jitter=0.55)
    line([(46, 910), (722, 910)], width=3.0)

    # Paper stacks are slightly offset, but every surface remains blank.
    paper([(91, 690), (265, 684), (279, 803), (102, 813)])
    paper([(86, 681), (261, 675), (275, 794), (98, 804)])
    paper([(80, 672), (256, 667), (270, 785), (93, 796)], width=2.6)
    paper([(299, 678), (486, 675), (492, 831), (303, 835)])
    paper([(294, 669), (482, 667), (488, 823), (298, 827)], width=2.6)
    paper([(514, 688), (678, 682), (687, 799), (522, 807)])
    paper([(509, 679), (673, 674), (682, 791), (517, 799)], width=2.6)
    paper([(112, 827), (251, 821), (258, 864), (117, 871)], width=2.0)
    paper([(529, 822), (670, 817), (675, 858), (534, 865)], width=2.0)

    # Three short outlined arm gestures guide pencils to each upper-right corner.
    closed_curves(
        [
            ((229, 555), (245, 581), (248, 627), (248, 672)),
            ((248, 672), (246, 684), (235, 686), (229, 676)),
            ((229, 676), (218, 625), (210, 586), (207, 565)),
            ((207, 565), (209, 553), (219, 548), (229, 555)),
        ],
        width=2.9,
        fill=WARM_GRAY,
    )
    line([(238, 677), (252, 654), (256, 674)], width=3.1, jitter=0.2)

    closed_curves(
        [
            ((430, 548), (449, 572), (464, 627), (472, 675)),
            ((472, 675), (470, 687), (458, 690), (451, 680)),
            ((451, 680), (435, 632), (417, 587), (409, 563)),
            ((409, 563), (410, 550), (420, 543), (430, 548)),
        ],
        width=3.1,
        fill=PALE_TEAL,
    )
    line([(461, 684), (479, 655), (484, 680)], width=3.2, jitter=0.2)

    closed_curves(
        [
            ((620, 557), (636, 582), (648, 627), (661, 678)),
            ((661, 678), (660, 690), (648, 694), (641, 684)),
            ((641, 684), (627, 639), (608, 593), (599, 568)),
            ((599, 568), (600, 556), (611, 550), (620, 557)),
        ],
        width=2.9,
        fill=MUSTARD,
    )
    line([(650, 688), (670, 659), (674, 683)], width=3.1, jitter=0.2)

    cup(107, 594)
    cup(599, 594)

    output = Path(__file__).with_name("004-control.png")
    color_output = Path(__file__).with_name("004-color.png")
    canvas.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(output)
    color_canvas.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(color_output)
    print(output)
    print(color_output)


if __name__ == "__main__":
    main()
