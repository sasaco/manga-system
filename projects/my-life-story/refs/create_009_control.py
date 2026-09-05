# -*- coding: utf-8 -*-
"""Draw the sparse, textless guide and flat colors for episode 009."""

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
RNG = random.Random(20010925)


def main() -> None:
    line_image = Image.new('RGB', (WIDTH * SCALE, HEIGHT * SCALE), 'white')
    line_draw = ImageDraw.Draw(line_image)
    color_image = Image.new('RGBA', (WIDTH * SCALE, HEIGHT * SCALE), (0, 0, 0, 0))
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
        line_draw.polygon([px(point) for point in values], fill='white')
        color_draw.polygon([px(point) for point in values], fill=fill)
        line(values, width=width, jitter=0.36, closed=True)

    def polygon(
        points: list[tuple[float, float]],
        *,
        fill: tuple[int, int, int, int] = WHITE,
        width: float = 2.7,
    ) -> None:
        line_draw.polygon([px(point) for point in points], fill='white')
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
        line_draw.polygon([px(point) for point in points], fill='white')
        color_draw.polygon([px(point) for point in points], fill=fill)
        line(points, width=width, jitter=0.3, closed=True)

    # Single hand-drawn frame
    line([(43, 43), (724, 44), (722, 980), (45, 981), (43, 43)], width=3.2, jitter=0.9)

    # Desk in the foreground
    polygon([(65, 680), (700, 675), (710, 755), (55, 760)], fill=WHITE, width=3.0)
    line([(95, 760), (90, 935)], width=3.0, jitter=0.18)
    line([(680, 755), (688, 935)], width=3.0, jitter=0.18)

    # Large blueprint spread across the desk from left to center
    for offset in (8, 4):
        polygon([(85, 690 + offset), (460, 682 + offset), (475, 742 + offset), (95, 750 + offset)], fill=WHITE, width=1.4)
    polygon([(80, 690), (460, 682), (475, 742), (90, 750)], fill=LIGHT_GRAY, width=2.4)
    line([(115, 705), (420, 698)], width=1.3, jitter=0.1)
    line([(115, 717), (390, 711)], width=1.3, jitter=0.1)
    line([(115, 729), (340, 724)], width=1.3, jitter=0.1)

    # Calculation binder stack on left edge
    for offset in (16, 8):
        polygon([(75, 635 + offset), (165, 630 + offset), (175, 690 + offset), (85, 695 + offset)], fill=WHITE, width=1.2)
    polygon([(70, 635), (165, 630), (175, 690), (80, 695)], fill=LIGHT_GRAY, width=2.2)

    # Apprentice at right-center: leaning forward proactively over the work
    shape(
        [
            ((430, 500), (390, 560), (395, 800), (430, 875)),
            ((430, 875), (480, 910), (630, 905), (670, 870)),
            ((670, 870), (695, 785), (685, 565), (645, 505)),
            ((645, 505), (590, 475), (480, 472), (430, 500)),
        ],
        fill=PALE_TEAL,
        width=4.0,
    )

    # Face: oval, focused & determined expression
    oval((455, 310, 635, 535), phase=0.9, fill=WHITE, width=3.8)

    # Hair strokes
    for x, offset in ((490, 0), (520, -10), (555, -12), (590, -4)):
        curve((x, 335 + offset), (x, 315 + offset), (x + 2, 300 + offset), (x + 4, 288 + offset), width=3.0)

    # Determined face: slightly angled eyebrows, focused eyes, straight mouth
    line([(495, 415), (525, 408)], width=2.8, jitter=0.1)
    line([(565, 408), (595, 415)], width=2.8, jitter=0.1)
    line([(500, 432), (522, 430)], width=2.4, jitter=0.1)
    line([(568, 430), (590, 432)], width=2.4, jitter=0.1)
    line([(530, 482), (560, 482)], width=2.4, jitter=0.1)

    # Tie
    polygon([(530, 520), (558, 520), (568, 545), (544, 565), (520, 545)], fill=MUSTARD, width=2.2)
    polygon([(544, 565), (560, 615), (544, 638), (528, 615)], fill=MUSTARD, width=2.4)

    # Left arm: reaching out to hold the blueprint
    shape(
        [
            ((435, 570), (395, 610), (340, 660), (300, 695)),
            ((300, 695), (305, 712), (325, 715), (350, 698)),
            ((350, 698), (400, 650), (450, 615), (470, 585)),
            ((470, 585), (465, 570), (450, 565), (435, 570)),
        ],
        fill=PALE_TEAL,
        width=3.2,
    )
    oval((290, 688, 330, 718), phase=0.4, fill=PALE_TEAL, width=2.2)

    # Right arm: bent forward, holding pen over drawing
    shape(
        [
            ((640, 575), (665, 615), (680, 660), (650, 695)),
            ((650, 695), (630, 710), (612, 702), (605, 685)),
            ((605, 685), (615, 650), (610, 615), (600, 585)),
            ((600, 585), (615, 570), (630, 570), (640, 575)),
        ],
        fill=PALE_TEAL,
        width=3.2,
    )
    oval((605, 680, 645, 710), phase=0.6, fill=PALE_TEAL, width=2.2)

    # Pen
    polygon([(610, 698), (595, 718), (600, 722), (615, 702)], fill=INK, width=1.5)

    output = Path(__file__).with_name('009-control.png')
    color_output = Path(__file__).with_name('009-color.png')
    line_image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(output)
    color_image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(color_output)
    print(output)
    print(color_output)


if __name__ == '__main__':
    main()
