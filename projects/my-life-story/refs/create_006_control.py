"""Draw episode 006 as a sparse, textless civil-design team scene."""

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
PALE_TEAL_LIGHT = (225, 241, 239, 255)
MUSTARD = (244, 204, 72, 255)
WARM_GRAY = (205, 201, 199, 255)
LIGHT_WARM_GRAY = (235, 232, 228, 255)
WHITE = (255, 255, 255, 255)
RNG = random.Random(20010907)


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
        jitter: float = 0.45,
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
        jitter: float = 0.35,
    ) -> None:
        line(cubic_points(start, control_a, control_b, end), width=width, jitter=jitter)

    def shape(
        segments: list[
            tuple[
                tuple[float, float],
                tuple[float, float],
                tuple[float, float],
                tuple[float, float],
            ]
        ],
        *,
        width: float = 3.4,
        fill: tuple[int, int, int, int] | None = None,
    ) -> None:
        values: list[tuple[float, float]] = []
        for index, segment in enumerate(segments):
            sampled = cubic_points(*segment)
            values.extend(sampled if index == 0 else sampled[1:])
        draw.polygon([px(value) for value in values], fill="white")
        if fill is not None:
            color_draw.polygon([px(value) for value in values], fill=fill)
        line(values, width=width, jitter=0.4, closed=True)

    def polygon(
        values: list[tuple[float, float]],
        *,
        width: float = 2.7,
        fill: tuple[int, int, int, int] | None = None,
    ) -> None:
        draw.polygon([px(value) for value in values], fill="white")
        if fill is not None:
            color_draw.polygon([px(value) for value in values], fill=fill)
        line(values, width=width, jitter=0.3, closed=True)

    def oval(
        bounds: tuple[float, float, float, float],
        *,
        width: float = 3.5,
        phase: float = 0,
        fill: tuple[int, int, int, int] = WHITE,
    ) -> None:
        left, top, right, bottom = bounds
        cx = (left + right) / 2
        cy = (top + bottom) / 2
        rx = (right - left) / 2
        ry = (bottom - top) / 2
        values: list[tuple[float, float]] = []
        for step in range(72):
            angle = math.tau * step / 72
            radius = 1 + 0.013 * math.sin(3 * angle + phase)
            values.append(
                (cx + rx * radius * math.cos(angle), cy + ry * radius * math.sin(angle))
            )
        draw.polygon([px(value) for value in values], fill="white")
        color_draw.polygon([px(value) for value in values], fill=fill)
        line(values, width=width, jitter=0.34, closed=True)

    def dot(x: float, y: float, radius: float = 2.1) -> None:
        draw.ellipse(
            (
                round((x - radius) * SCALE),
                round((y - radius) * SCALE),
                round((x + radius) * SCALE),
                round((y + radius) * SCALE),
            ),
            fill=INK,
        )

    # One undivided panel with broad white margins.
    line([(44, 44), (722, 43), (724, 980), (43, 981), (44, 44)], width=3.4, jitter=0.75)

    # The commissioning client passes a completely blank plan to the consultant.
    shape(
        [
            ((76, 194), (61, 223), (62, 308), (72, 359)),
            ((72, 359), (98, 376), (150, 378), (174, 359)),
            ((174, 359), (182, 314), (181, 229), (165, 195)),
            ((165, 195), (141, 179), (99, 179), (76, 194)),
        ],
        fill=MUSTARD,
    )
    oval((84, 91, 170, 210), phase=0.4)
    line([(93, 139), (107, 112), (131, 107), (160, 131)], width=3.0)
    dot(109, 158, 1.8)
    dot(145, 158, 1.8)
    curve((116, 183), (125, 187), (135, 187), (143, 181), width=2.0, jitter=0.18)

    # Two short outlined arms support the hand-off rather than forming a line skeleton.
    shape(
        [
            ((155, 224), (177, 224), (195, 232), (213, 248)),
            ((213, 248), (219, 255), (218, 266), (210, 271)),
            ((210, 271), (190, 258), (171, 249), (153, 247)),
            ((153, 247), (145, 241), (146, 229), (155, 224)),
        ],
        width=2.5,
        fill=MUSTARD,
    )

    # Consultant in the middle receives the plan and connects the team by gesture.
    shape(
        [
            ((233, 192), (216, 225), (218, 311), (229, 365)),
            ((229, 365), (260, 383), (319, 383), (347, 362)),
            ((347, 362), (356, 308), (352, 225), (335, 194)),
            ((335, 194), (306, 177), (259, 177), (233, 192)),
        ],
        fill=WARM_GRAY,
    )
    oval((244, 88, 337, 210), phase=1.1)
    line([(252, 139), (265, 111), (289, 105), (328, 133)], width=3.0)
    line([(266, 156), (277, 153)], width=2.0)
    line([(306, 153), (318, 157)], width=2.0)
    curve((275, 181), (285, 187), (297, 187), (307, 180), width=2.0, jitter=0.18)

    # The blank rolled plan is shared by client and consultant, with no labels or marks.
    polygon([(190, 225), (274, 218), (285, 266), (201, 274)], width=2.5, fill=WHITE)
    oval((269, 218, 291, 268), width=2.1, phase=0.6)
    shape(
        [
            ((224, 229), (232, 217), (245, 216), (253, 226)),
            ((253, 226), (259, 235), (258, 250), (249, 255)),
            ((249, 255), (240, 261), (229, 258), (224, 247)),
            ((224, 247), (221, 240), (221, 235), (224, 229)),
        ],
        width=2.2,
        fill=WARM_GRAY,
    )

    # Consultant's second arm gestures toward the structural specialist below.
    shape(
        [
            ((330, 235), (350, 243), (371, 268), (388, 298)),
            ((388, 298), (393, 309), (388, 319), (378, 319)),
            ((378, 319), (360, 292), (342, 275), (324, 264)),
            ((324, 264), (316, 255), (319, 240), (330, 235)),
        ],
        width=2.5,
        fill=WARM_GRAY,
    )
    oval((374, 303, 399, 328), width=2.0, phase=1.0)

    # Another specialist quietly holds a small surveying instrument.
    shape(
        [
            ((522, 209), (509, 237), (510, 307), (520, 349)),
            ((520, 349), (544, 365), (588, 365), (609, 348)),
            ((609, 348), (617, 304), (615, 239), (600, 210)),
            ((600, 210), (578, 196), (543, 195), (522, 209)),
        ],
        fill=PALE_TEAL,
    )
    oval((531, 112, 605, 218), phase=0.2)
    line([(540, 154), (551, 129), (574, 125), (598, 149)], width=2.8)
    dot(552, 173, 1.7)
    dot(582, 173, 1.7)
    curve((556, 195), (565, 200), (573, 200), (581, 194), width=1.9, jitter=0.16)
    shape(
        [
            ((602, 247), (622, 242), (637, 238), (648, 236)),
            ((648, 236), (657, 236), (663, 244), (660, 252)),
            ((660, 252), (640, 256), (620, 263), (602, 271)),
            ((602, 271), (594, 266), (594, 253), (602, 247)),
        ],
        width=2.3,
        fill=PALE_TEAL,
    )
    oval((644, 229, 675, 260), width=2.2, phase=0.8, fill=MUSTARD)
    line([(659, 260), (659, 292)], width=2.7)
    line([(659, 292), (626, 357)], width=2.7)
    line([(659, 292), (660, 361)], width=2.7)
    line([(659, 292), (694, 357)], width=2.7)

    # The young protagonist works in front as the structural-design specialist.
    shape(
        [
            ((88, 632), (68, 674), (72, 831), (91, 914)),
            ((91, 914), (128, 941), (263, 941), (306, 911)),
            ((306, 911), (321, 823), (317, 680), (292, 632)),
            ((292, 632), (250, 606), (132, 608), (88, 632)),
        ],
        width=4.0,
        fill=PALE_TEAL,
    )
    oval((111, 416, 299, 644), width=4.0, phase=0.9)
    line([(122, 486), (137, 444), (158, 480), (179, 440), (201, 481)], width=3.8)
    line([(201, 481), (225, 442), (247, 481), (268, 455), (290, 500)], width=3.8)
    line([(150, 537), (170, 531)], width=2.4)
    line([(237, 531), (256, 537)], width=2.4)
    curve((176, 586), (191, 596), (214, 597), (231, 583), width=2.6, jitter=0.2)
    line([(124, 639), (202, 690), (285, 638)], width=2.6)
    polygon([(193, 681), (211, 681), (220, 699), (202, 713), (184, 699)], width=2.2, fill=MUSTARD)
    polygon([(202, 713), (217, 755), (202, 775), (187, 755)], width=2.3, fill=MUSTARD)

    # Bulky CRT computer, screen kept entirely free of glyphs and labels.
    shape(
        [
            ((361, 480), (349, 515), (350, 704), (366, 745)),
            ((366, 745), (420, 766), (617, 764), (654, 741)),
            ((654, 741), (667, 696), (663, 521), (647, 484)),
            ((647, 484), (581, 465), (424, 465), (361, 480)),
        ],
        width=3.7,
        fill=WARM_GRAY,
    )
    polygon([(386, 505), (624, 502), (631, 689), (379, 692)], width=3.0, fill=PALE_TEAL_LIGHT)

    # Empty spreadsheet cells on the left side of the screen.
    for x in (401, 438, 475, 512):
        line([(x, 526), (x, 603)], width=1.3, jitter=0.12)
    for y in (526, 551, 577, 603):
        line([(401, y), (512, y)], width=1.3, jitter=0.12)

    # A simple bridge analysis outline occupies the other half of the screen.
    line([(526, 619), (605, 619)], width=2.2, jitter=0.15)
    line([(537, 619), (537, 657)], width=2.0, jitter=0.15)
    line([(594, 619), (594, 657)], width=2.0, jitter=0.15)
    curve((537, 619), (550, 573), (580, 573), (594, 619), width=2.2, jitter=0.15)
    line([(537, 657), (525, 670)], width=1.8, jitter=0.12)
    line([(594, 657), (606, 670)], width=1.8, jitter=0.12)

    # Plain keyboard and two short working arm shapes.
    polygon([(350, 787), (603, 785), (631, 843), (329, 847)], width=3.0, fill=LIGHT_WARM_GRAY)
    for x in (366, 405, 444, 483, 522, 561):
        line([(x, 803), (x + 7, 826)], width=1.0, jitter=0.08)
    line([(354, 812), (595, 810)], width=1.0, jitter=0.08)
    line([(348, 829), (604, 827)], width=1.0, jitter=0.08)
    shape(
        [
            ((292, 707), (323, 712), (353, 748), (382, 797)),
            ((382, 797), (388, 808), (383, 819), (372, 820)),
            ((372, 820), (340, 777), (314, 758), (287, 748)),
            ((287, 748), (277, 739), (279, 715), (292, 707)),
        ],
        width=3.0,
        fill=PALE_TEAL,
    )
    oval((369, 798, 395, 824), width=2.0, phase=0.4)

    # A calculation book hundreds of pages thick, expressed only by blank edges.
    for offset in range(48, -1, -8):
        polygon(
            [(424 - offset * 0.18, 879 + offset), (679, 873 + offset), (696, 915 + offset), (404, 923 + offset)],
            width=1.4,
            fill=WHITE,
        )
    polygon([(415, 879), (679, 873), (696, 915), (404, 923)], width=2.7, fill=WHITE)

    output = Path(__file__).with_name("006-control.png")
    color_output = Path(__file__).with_name("006-color.png")
    canvas.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(output)
    color_canvas.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(color_output)
    print(output)
    print(color_output)


if __name__ == "__main__":
    main()
