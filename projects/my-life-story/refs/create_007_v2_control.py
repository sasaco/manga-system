"""Draw episode 007 as a sparse, textless calculation-tracing scene."""

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
LIGHT_GRAY = (235, 232, 228, 255)
WHITE = (255, 255, 255, 255)
RNG = random.Random(20010908)


def main() -> None:
    canvas = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), "white")
    draw = ImageDraw.Draw(canvas)
    color_canvas = Image.new("RGBA", (WIDTH * SCALE, HEIGHT * SCALE), (0, 0, 0, 0))
    color_draw = ImageDraw.Draw(color_canvas)

    def px(point: tuple[float, float]) -> tuple[int, int]:
        return round(point[0] * SCALE), round(point[1] * SCALE)

    def line(
        points: list[tuple[float, float]],
        *,
        width: float = 3.0,
        jitter: float = 0.35,
        closed: bool = False,
        ink: tuple[int, int, int] = INK,
        on_color: bool = False,
    ) -> None:
        source = points + ([points[0]] if closed else [])
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
        target = color_draw if on_color else draw
        target.line(
            [px(point) for point in sampled],
            fill=ink if not on_color else (*ink, 255),
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
        width: float = 3.0,
        jitter: float = 0.25,
        ink: tuple[int, int, int] = INK,
        on_color: bool = False,
    ) -> None:
        line(
            cubic_points(start, control_a, control_b, end),
            width=width,
            jitter=jitter,
            ink=ink,
            on_color=on_color,
        )

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
        draw.polygon([px(point) for point in values], fill="white")
        if fill is not None:
            color_draw.polygon([px(point) for point in values], fill=fill)
        line(values, width=width, jitter=0.4, closed=True)

    def polygon(
        points: list[tuple[float, float]],
        *,
        width: float = 2.5,
        fill: tuple[int, int, int, int] | None = None,
    ) -> None:
        draw.polygon([px(point) for point in points], fill="white")
        if fill is not None:
            color_draw.polygon([px(point) for point in points], fill=fill)
        line(points, width=width, jitter=0.22, closed=True)

    def oval(
        bounds: tuple[float, float, float, float],
        *,
        width: float = 3.4,
        phase: float = 0.0,
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
            values.append((cx + rx * radius * math.cos(angle), cy + ry * radius * math.sin(angle)))
        draw.polygon([px(point) for point in values], fill="white")
        color_draw.polygon([px(point) for point in values], fill=fill)
        line(values, width=width, jitter=0.32, closed=True)

    def dot(x: float, y: float, radius: float = 2.0) -> None:
        draw.ellipse(
            (
                round((x - radius) * SCALE),
                round((y - radius) * SCALE),
                round((x + radius) * SCALE),
                round((y + radius) * SCALE),
            ),
            fill=INK,
        )

    def blank_sheet(
        left: float,
        top: float,
        right: float,
        bottom: float,
        *,
        highlight: tuple[int, int] = (1, 1),
        skew: float = 0.0,
    ) -> tuple[float, float]:
        points = [(left + skew, top), (right, top + 3), (right - skew, bottom), (left, bottom - 2)]
        polygon(points, width=2.0, fill=WHITE)
        grid_left = left + 18
        grid_top = top + 19
        cell_w = (right - left - 36) / 3
        cell_h = min(28, (bottom - top - 38) / 3)
        row, column = highlight
        highlight_points = [
            (grid_left + column * cell_w, grid_top + row * cell_h),
            (grid_left + (column + 1) * cell_w, grid_top + row * cell_h),
            (grid_left + (column + 1) * cell_w, grid_top + (row + 1) * cell_h),
            (grid_left + column * cell_w, grid_top + (row + 1) * cell_h),
        ]
        color_draw.polygon([px(point) for point in highlight_points], fill=MUSTARD)
        for column_index in range(4):
            x = grid_left + column_index * cell_w
            line([(x, grid_top), (x, grid_top + 3 * cell_h)], width=1.15, jitter=0.08)
        for row_index in range(4):
            y = grid_top + row_index * cell_h
            line([(grid_left, y), (grid_left + 3 * cell_w, y)], width=1.15, jitter=0.08)
        return (
            grid_left + (column + 0.5) * cell_w,
            grid_top + (row + 0.5) * cell_h,
        )

    # One quiet, undivided frame with generous margins.
    line([(43, 43), (724, 44), (723, 980), (44, 981), (43, 43)], width=3.4, jitter=0.7)

    # The mentor is already turning away while handing over the only clue.
    shape(
        [
            ((67, 180), (50, 214), (54, 352), (72, 414)),
            ((72, 414), (99, 435), (164, 437), (190, 414)),
            ((190, 414), (204, 355), (202, 222), (185, 181)),
            ((185, 181), (157, 162), (96, 161), (67, 180)),
        ],
        fill=WARM_GRAY,
    )
    oval((67, 71, 178, 208), phase=0.6)
    line([(77, 126), (91, 94), (119, 88), (165, 122)], width=3.1)
    # Only one eye is visible because the mentor is facing the exit.
    line([(91, 147), (106, 143)], width=2.3)
    line([(99, 180), (111, 181)], width=1.8)
    line([(122, 185), (133, 184)], width=1.8)
    line([(145, 182), (155, 177)], width=1.8)
    # Backward hand-off, without pointer, explanation, or second gesture.
    shape(
        [
            ((176, 242), (211, 238), (248, 256), (282, 283)),
            ((282, 283), (292, 292), (289, 306), (278, 312)),
            ((278, 312), (244, 290), (211, 278), (174, 279)),
            ((174, 279), (164, 271), (166, 251), (176, 242)),
        ],
        width=2.8,
        fill=WARM_GRAY,
    )

    # The single thick sample binder crosses from mentor to apprentice.
    for offset in (18, 12, 6):
        polygon(
            [(246 + offset * 0.2, 276 + offset), (430, 257 + offset), (454, 345 + offset), (270, 365 + offset)],
            width=1.2,
            fill=WHITE,
        )
    polygon([(245, 276), (430, 257), (454, 345), (269, 365)], width=2.8, fill=LIGHT_GRAY)

    # A wide fan of calculation sheets surrounds the apprentice like a source map.
    source_a = blank_sheet(280, 120, 445, 229, highlight=(0, 1), skew=4)
    source_b = blank_sheet(458, 112, 632, 225, highlight=(1, 2), skew=-3)
    source_c = blank_sheet(536, 256, 697, 369, highlight=(2, 0), skew=3)
    source_d = blank_sheet(526, 404, 698, 520, highlight=(0, 2), skew=-4)
    source_e = blank_sheet(492, 552, 665, 667, highlight=(2, 1), skew=4)

    # Hundreds of downstream pages become a single towering blank volume.
    for offset in range(88, -1, -8):
        polygon(
            [(532 - offset * 0.10, 676 + offset), (685, 667 + offset), (701, 897 + offset), (505, 906 + offset)],
            width=1.2,
            fill=WHITE,
        )

    # The apprentice is now calm and fluent in the web of sources.
    shape(
        [
            ((107, 620), (82, 670), (85, 861), (108, 932)),
            ((108, 932), (151, 958), (361, 957), (399, 927)),
            ((399, 927), (416, 846), (407, 690), (376, 626)),
            ((376, 626), (324, 596), (158, 594), (107, 620)),
        ],
        width=4.0,
        fill=PALE_TEAL,
    )
    oval((139, 366, 380, 642), width=4.0, phase=1.1)
    line([(150, 448), (166, 398), (192, 444), (219, 395), (246, 444)], width=3.8)
    line([(246, 444), (275, 398), (305, 449), (337, 416), (370, 468)], width=3.8)
    line([(185, 519), (208, 514)], width=2.4)
    line([(304, 514), (328, 521)], width=2.4)
    # A small, settled smile replaces the earlier overwhelmed frown.
    curve((215, 579), (237, 595), (276, 595), (299, 577), width=2.6, jitter=0.18)
    line([(152, 622), (257, 689), (368, 624)], width=2.5)
    polygon([(247, 679), (268, 679), (278, 700), (257, 716), (237, 700)], width=2.1, fill=MUSTARD)
    polygon([(257, 716), (274, 764), (257, 787), (240, 764)], width=2.3, fill=MUSTARD)

    # One hand rests on the open sample binder at the desk.
    open_sample = blank_sheet(154, 736, 437, 916, highlight=(1, 0), skew=4)
    shape(
        [
            ((125, 707), (154, 709), (187, 732), (218, 771)),
            ((218, 771), (226, 780), (224, 794), (212, 800)),
            ((212, 800), (181, 765), (153, 750), (122, 748)),
            ((122, 748), (110, 739), (111, 716), (125, 707)),
        ],
        width=3.0,
        fill=PALE_TEAL,
    )
    oval((205, 784, 234, 813), width=2.0, phase=0.4)

    # The other hand gathers every source thread into one understood bundle.
    hand_center = (437, 650)
    shape(
        [
            ((374, 690), (397, 677), (415, 657), (428, 641)),
            ((428, 641), (436, 631), (449, 632), (456, 643)),
            ((456, 643), (446, 670), (421, 706), (390, 730)),
            ((390, 730), (376, 737), (363, 723), (374, 690)),
        ],
        width=3.0,
        fill=PALE_TEAL,
    )
    oval((424, 636, 454, 666), width=2.0, phase=0.8)

    # Each thread runs from a different page's highlighted field into his hand.
    thread_sources = [source_a, source_b, source_c, source_d, source_e, open_sample]
    for index, start in enumerate(thread_sources):
        bend = -36 + index * 15
        curve(
            start,
            (start[0] + bend, (start[1] + hand_center[1]) / 2),
            (hand_center[0] - bend, (start[1] + hand_center[1]) / 2),
            hand_center,
            width=4.2,
            jitter=0.16,
            ink=MUSTARD[:3],
            on_color=True,
        )

    output = Path(__file__).with_name("007-control.png")
    color_output = Path(__file__).with_name("007-color.png")
    canvas.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(output)
    color_canvas.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(color_output)
    print(output)
    print(color_output)


if __name__ == "__main__":
    main()
