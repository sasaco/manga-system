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
        stroke = ink if not on_color else (*ink, 255)
        last_index = max(1, len(sampled) - 2)
        for index, (start, end) in enumerate(zip(sampled, sampled[1:])):
            progress = index / last_index
            pressure = 0.82 + 0.22 * math.sin(math.pi * progress)
            pressure += 0.035 * math.sin(index * 1.71 + len(points))
            target.line(
                [px(start), px(end)],
                fill=stroke,
                width=max(1, round(width * SCALE * pressure)),
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
            radius = (
                1
                + 0.024 * math.sin(3 * angle + phase)
                + 0.011 * math.sin(5 * angle + phase * 0.7)
            )
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

    def tilted_sheet(
        corners: list[tuple[float, float]],
        *,
        highlight: tuple[int, int],
    ) -> tuple[float, float]:
        """Draw a loose perspective sheet with a sparse, completely blank grid."""
        polygon(corners, width=2.25, fill=WHITE)

        def mix(a: tuple[float, float], b: tuple[float, float], amount: float) -> tuple[float, float]:
            return a[0] + (b[0] - a[0]) * amount, a[1] + (b[1] - a[1]) * amount

        def map_point(u: float, v: float) -> tuple[float, float]:
            top = mix(corners[0], corners[1], u)
            bottom = mix(corners[3], corners[2], u)
            return mix(top, bottom, v)

        left = 0.12
        top = 0.18
        width = 0.76
        height = 0.62
        row, column = highlight
        u0 = left + width * column / 3
        u1 = left + width * (column + 1) / 3
        v0 = top + height * row / 3
        v1 = top + height * (row + 1) / 3
        color_draw.polygon(
            [px(map_point(u0, v0)), px(map_point(u1, v0)), px(map_point(u1, v1)), px(map_point(u0, v1))],
            fill=MUSTARD,
        )
        for index in range(4):
            u = left + width * index / 3
            line([map_point(u, top), map_point(u, top + height)], width=1.05, jitter=0.07)
        for index in range(4):
            v = top + height * index / 3
            line([map_point(left, v), map_point(left + width, v)], width=1.05, jitter=0.07)
        return map_point((u0 + u1) / 2, (v0 + v1) / 2)

    # One quiet, undivided frame with generous margins.
    line([(43, 43), (724, 44), (722, 980), (44, 981), (43, 43)], width=3.3, jitter=0.9)

    # Background pages form a loose diagonal flow instead of a rigid grid wall.
    source_a = tilted_sheet(
        [(285, 105), (455, 94), (470, 229), (300, 241)],
        highlight=(0, 1),
    )
    source_b = tilted_sheet(
        [(500, 105), (681, 124), (662, 255), (483, 235)],
        highlight=(1, 2),
    )
    source_c = tilted_sheet(
        [(548, 288), (704, 314), (684, 454), (528, 429)],
        highlight=(2, 0),
    )
    source_d = tilted_sheet(
        [(517, 492), (683, 477), (701, 615), (535, 633)],
        highlight=(0, 2),
    )

    # Hundreds of downstream pages become a slightly leaning volume.
    for offset in range(48, -1, -8):
        left_shift = offset * 0.12
        polygon(
            [
                (559 - left_shift, 682 + offset),
                (688, 670 + offset),
                (705, 912 + offset),
                (531 - left_shift, 923 + offset),
            ],
            width=1.15,
            fill=WHITE,
        )

    # The mentor is already angled toward the exit while reaching back once.
    shape(
        [
            ((67, 177), (48, 221), (53, 369), (78, 425)),
            ((78, 425), (104, 443), (163, 441), (184, 411)),
            ((184, 411), (194, 343), (194, 225), (177, 182)),
            ((177, 182), (149, 159), (96, 158), (67, 177)),
        ],
        width=3.8,
        fill=WARM_GRAY,
    )
    oval((63, 66, 179, 206), width=3.7, phase=0.6)
    # Sparse side-parted hair, one looking-away eye, and a few beard strokes.
    curve((75, 123), (91, 88), (133, 79), (168, 117), width=3.1, jitter=0.22)
    line([(88, 148), (105, 143)], width=2.15, jitter=0.16)
    line([(103, 180), (113, 182)], width=1.75, jitter=0.12)
    line([(126, 185), (136, 184)], width=1.75, jitter=0.12)
    line([(148, 181), (156, 176)], width=1.75, jitter=0.12)
    shape(
        [
            ((166, 245), (204, 237), (246, 252), (279, 278)),
            ((279, 278), (290, 287), (290, 301), (278, 308)),
            ((278, 308), (240, 289), (204, 278), (168, 285)),
            ((168, 285), (156, 276), (156, 257), (166, 245)),
        ],
        width=3.0,
        fill=WARM_GRAY,
    )

    # The sample calculation binder is the entire lesson.
    for offset in (19, 13, 7):
        polygon(
            [
                (231 + offset * 0.18, 247 + offset),
                (421, 220 + offset),
                (459, 322 + offset),
                (257, 356 + offset),
            ],
            width=1.15,
            fill=WHITE,
        )
    polygon([(230, 247), (421, 220), (459, 322), (257, 356)], width=2.9, fill=LIGHT_GRAY)

    # The apprentice's broad rounded body anchors the diagonal composition.
    shape(
        [
            ((111, 636), (82, 685), (86, 866), (111, 932)),
            ((111, 932), (158, 958), (390, 956), (432, 923)),
            ((432, 923), (446, 848), (433, 696), (399, 641)),
            ((399, 641), (340, 605), (169, 602), (111, 636)),
        ],
        width=4.25,
        fill=PALE_TEAL,
    )
    oval((150, 365, 409, 653), width=4.25, phase=1.2)
    # A few separate hair strokes echo the canonical reference.
    curve((192, 407), (194, 391), (198, 380), (201, 367), width=3.3, jitter=0.22)
    curve((224, 392), (225, 377), (226, 364), (229, 352), width=3.3, jitter=0.22)
    curve((259, 387), (259, 371), (260, 358), (263, 346), width=3.3, jitter=0.22)
    curve((294, 391), (295, 375), (299, 361), (304, 350), width=3.3, jitter=0.22)
    # Eyes angle subtly toward the gathered threads.
    line([(209, 510), (231, 506)], width=2.35, jitter=0.14)
    line([(320, 503), (342, 508)], width=2.35, jitter=0.14)
    curve((238, 574), (258, 590), (296, 590), (320, 570), width=2.55, jitter=0.2)
    line([(169, 637), (274, 701), (391, 637)], width=2.55, jitter=0.2)
    polygon([(264, 691), (285, 690), (297, 711), (275, 729), (253, 711)], width=2.15, fill=MUSTARD)
    polygon([(275, 729), (291, 773), (273, 796), (257, 773)], width=2.25, fill=MUSTARD)

    # The open sample rests in front at a slight perspective angle.
    open_sample = tilted_sheet(
        [(146, 748), (469, 727), (489, 911), (165, 936)],
        highlight=(1, 0),
    )

    # Left sleeve and a small mitten-like hand rest on the sample source cell.
    shape(
        [
            ((128, 704), (158, 704), (199, 731), (235, 773)),
            ((235, 773), (242, 783), (238, 797), (226, 802)),
            ((226, 802), (188, 768), (155, 749), (122, 748)),
            ((122, 748), (109, 738), (112, 714), (128, 704)),
        ],
        width=3.25,
        fill=PALE_TEAL,
    )
    shape(
        [
            ((216, 789), (220, 777), (232, 772), (242, 778)),
            ((242, 778), (252, 786), (255, 801), (248, 811)),
            ((248, 811), (240, 820), (225, 820), (216, 811)),
            ((216, 811), (210, 804), (211, 796), (216, 789)),
        ],
        width=2.1,
        fill=WHITE,
    )

    # Right sleeve rises toward the source web; the hand pinches the threads.
    hand_center = (486, 644)
    shape(
        [
            ((400, 686), (426, 677), (451, 658), (472, 632)),
            ((472, 632), (481, 623), (494, 625), (500, 637)),
            ((500, 637), (486, 670), (458, 705), (421, 728)),
            ((421, 728), (406, 734), (393, 719), (400, 686)),
        ],
        width=3.3,
        fill=PALE_TEAL,
    )
    shape(
        [
            ((474, 631), (479, 621), (491, 617), (501, 623)),
            ((501, 623), (511, 630), (514, 644), (507, 655)),
            ((507, 655), (498, 665), (483, 665), (474, 656)),
            ((474, 656), (468, 648), (468, 639), (474, 631)),
        ],
        width=2.1,
        fill=WHITE,
    )

    # Uneven mustard threads converge from every page into the apprentice's hand.
    thread_sources = [source_a, source_b, source_c, source_d, open_sample]
    controls = [
        ((330, 330), (462, 470)),
        ((598, 300), (520, 448)),
        ((610, 445), (522, 510)),
        ((610, 594), (532, 592)),
        ((340, 818), (422, 720)),
    ]
    for start, (control_a, control_b) in zip(thread_sources, controls):
        curve(
            start,
            control_a,
            control_b,
            hand_center,
            width=3.8,
            jitter=0.3,
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
