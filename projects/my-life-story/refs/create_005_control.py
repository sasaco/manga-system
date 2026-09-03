"""Draw episode 005 as a sparse, textless copier-efficiency scene."""

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
LIGHT_WARM_GRAY = (235, 232, 228, 255)
WHITE = (255, 255, 255, 255)
RNG = random.Random(20010906)


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

    # One undivided panel with generous white space.
    line([(44, 44), (722, 43), (724, 980), (43, 981), (44, 44)], width=3.4, jitter=0.75)

    # Coworkers remain small and quiet in the background, relieved to put pencils down.
    shape(
        [
            ((73, 351), (55, 385), (57, 468), (69, 522)),
            ((69, 522), (102, 544), (172, 544), (201, 520)),
            ((201, 520), (209, 462), (207, 389), (189, 351)),
            ((189, 351), (158, 334), (102, 333), (73, 351)),
        ],
        fill=WARM_GRAY,
    )
    oval((87, 222, 193, 365), phase=0.3)
    line([(96, 276), (112, 246), (142, 239), (176, 255), (188, 282)], width=3.3)
    line([(109, 301), (123, 297)], width=2.2)
    line([(154, 297), (170, 301)], width=2.2)
    curve((125, 333), (136, 340), (148, 340), (158, 332), width=2.2, jitter=0.2)
    line([(129, 347), (134, 352)], width=1.7)
    line([(150, 351), (155, 346)], width=1.7)
    shape(
        [
            ((182, 386), (204, 374), (218, 384), (224, 402)),
            ((224, 402), (219, 414), (209, 416), (201, 407)),
            ((201, 407), (195, 399), (188, 394), (182, 386)),
            ((182, 386), (179, 383), (179, 385), (182, 386)),
        ],
        width=2.4,
        fill=WARM_GRAY,
    )

    shape(
        [
            ((208, 349), (195, 384), (197, 466), (208, 516)),
            ((208, 516), (239, 538), (304, 539), (330, 514)),
            ((330, 514), (339, 458), (334, 385), (320, 349)),
            ((320, 349), (290, 331), (236, 331), (208, 349)),
        ],
        fill=MUSTARD,
    )
    oval((220, 219, 324, 361), phase=1.2)
    line([(230, 275), (247, 244), (274, 237), (307, 252), (319, 280)], width=3.2)
    dot(249, 301, 2.0)
    dot(294, 301, 2.0)
    curve((254, 330), (265, 340), (281, 340), (292, 329), width=2.2, jitter=0.18)
    shape(
        [
            ((213, 393), (196, 381), (181, 388), (176, 404)),
            ((176, 404), (181, 417), (193, 419), (202, 410)),
            ((202, 410), (208, 403), (212, 398), (213, 393)),
            ((213, 393), (215, 390), (215, 391), (213, 393)),
        ],
        width=2.4,
        fill=MUSTARD,
    )

    # A simplified copier dominates the right half. Its surfaces stay completely unmarked.
    shape(
        [
            ((367, 303), (354, 350), (353, 752), (365, 872)),
            ((365, 872), (424, 897), (628, 895), (675, 870)),
            ((675, 870), (688, 752), (685, 365), (669, 307)),
            ((669, 307), (595, 288), (435, 288), (367, 303)),
        ],
        width=3.8,
        fill=WARM_GRAY,
    )

    # Extremely thick edited manuscript entering the automatic feeder.
    for offset in (30, 24, 18, 12, 6):
        polygon(
            [(405 - offset * 0.18, 126 + offset), (613, 119 + offset), (639, 232 + offset), (425, 241 + offset)],
            width=1.7,
            fill=WHITE,
        )
    polygon([(401, 126), (608, 119), (635, 231), (421, 240)], width=2.8, fill=WHITE)
    polygon([(387, 239), (647, 230), (670, 302), (373, 310)], width=3.0, fill=LIGHT_WARM_GRAY)

    # Plain, deliberately featureless controls: one physical button only.
    polygon([(387, 330), (520, 327), (534, 382), (379, 384)], width=2.5, fill=WHITE)
    color_draw.ellipse((405 * SCALE, 342 * SCALE, 438 * SCALE, 375 * SCALE), fill=MUSTARD)
    oval((405, 342, 438, 375), width=2.4, phase=0.7, fill=MUSTARD)

    # Finished copied pages fill the output bay.
    polygon([(414, 444), (645, 440), (616, 583), (431, 586)], width=3.0, fill=WHITE)
    for offset in (32, 24, 16, 8):
        polygon(
            [(430, 488 + offset), (617, 485 + offset), (602, 546 + offset), (440, 549 + offset)],
            width=1.5,
            fill=WHITE,
        )
    polygon([(430, 488), (617, 485), (602, 546), (440, 549)], width=2.3, fill=WHITE)

    # Lower drawer is open toward the viewer, holding another thick blank ream.
    polygon([(389, 679), (659, 675), (680, 782), (373, 789)], width=3.0, fill=LIGHT_WARM_GRAY)
    for offset in (24, 18, 12, 6):
        polygon(
            [(415, 685 + offset), (620, 681 + offset), (638, 751 + offset), (399, 756 + offset)],
            width=1.5,
            fill=WHITE,
        )
    polygon([(411, 685), (618, 681), (635, 750), (396, 756)], width=2.6, fill=WHITE)
    polygon([(373, 789), (680, 782), (652, 867), (395, 875)], width=3.0, fill=MUSTARD)

    # The young protagonist works in front, using two short outlined arm gestures.
    shape(
        [
            ((101, 574), (77, 620), (74, 777), (91, 889)),
            ((91, 889), (133, 918), (268, 920), (316, 886)),
            ((316, 886), (327, 772), (323, 626), (296, 574)),
            ((296, 574), (252, 548), (147, 548), (101, 574)),
        ],
        width=4.0,
        fill=PALE_TEAL,
    )
    oval((113, 366, 303, 589), width=4.0, phase=0.8)
    line([(124, 438), (136, 395), (154, 425), (174, 390), (195, 427)], width=3.8)
    line([(195, 427), (218, 388), (239, 428), (258, 400), (293, 445)], width=3.8)
    line([(150, 485), (169, 478)], width=2.4)
    line([(236, 478), (255, 484)], width=2.4)
    curve((176, 538), (192, 552), (216, 552), (232, 535), width=2.7, jitter=0.2)
    line([(132, 580), (203, 630), (287, 579)], width=2.7)
    polygon([(193, 622), (211, 622), (220, 638), (202, 652), (184, 638)], width=2.3, fill=MUSTARD)
    polygon([(202, 652), (218, 697), (202, 717), (186, 697)], width=2.4, fill=MUSTARD)

    # Upper arm presses the one blank button.
    shape(
        [
            ((287, 619), (324, 585), (362, 511), (404, 377)),
            ((404, 377), (411, 365), (424, 368), (426, 380)),
            ((426, 380), (389, 527), (347, 620), (313, 661)),
            ((313, 661), (302, 668), (288, 655), (287, 619)),
        ],
        width=3.1,
        fill=PALE_TEAL,
    )
    oval((408, 358, 435, 386), width=2.2, phase=0.1)

    # Lower arm supports the ream in the open tray.
    shape(
        [
            ((285, 724), (321, 731), (359, 742), (397, 751)),
            ((397, 751), (411, 754), (416, 768), (407, 777)),
            ((407, 777), (366, 774), (326, 768), (290, 761)),
            ((290, 761), (277, 755), (275, 738), (285, 724)),
        ],
        width=3.0,
        fill=PALE_TEAL,
    )
    oval((397, 748, 426, 779), width=2.2, phase=1.3)

    # Copier feet and a spare blank ream make the busy process legible without labels.
    line([(399, 895), (399, 921), (447, 921)], width=3.0)
    line([(624, 894), (624, 920), (670, 920)], width=3.0)
    polygon([(85, 927), (280, 925), (294, 952), (75, 954)], width=2.3, fill=WHITE)

    output = Path(__file__).with_name("005-control.png")
    color_output = Path(__file__).with_name("005-color.png")
    canvas.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(output)
    color_canvas.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(color_output)
    print(output)
    print(color_output)


if __name__ == "__main__":
    main()
