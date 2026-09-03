"""Build a sparse episode-007 control drawing from the canonical comic references.

The Comfy source deliberately contains no balloon and no lettering.  A separate
balloon guide is emitted for the later manual Krita finishing pass.
"""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw


WIDTH = 768
HEIGHT = 1024
SCALE = 4
INK = (30, 29, 28, 255)
PALE_TEAL = (157, 202, 201, 255)
MUSTARD = (244, 204, 72, 255)
WARM_GRAY = (198, 194, 192, 255)
PAPER = (244, 242, 239, 255)
WHITE = (255, 255, 255, 255)
RNG = random.Random(20010912)


def main() -> None:
    line_image = Image.new("RGBA", (WIDTH * SCALE, HEIGHT * SCALE), WHITE)
    color_image = Image.new("RGBA", line_image.size, (0, 0, 0, 0))
    balloon_image = Image.new("RGBA", line_image.size, (0, 0, 0, 0))
    line_draw = ImageDraw.Draw(line_image)
    color_draw = ImageDraw.Draw(color_image)
    balloon_draw = ImageDraw.Draw(balloon_image)

    def px(point: tuple[float, float]) -> tuple[int, int]:
        return round(point[0] * SCALE), round(point[1] * SCALE)

    def cubic_points(
        start: tuple[float, float],
        control_a: tuple[float, float],
        control_b: tuple[float, float],
        end: tuple[float, float],
        steps: int = 28,
    ) -> list[tuple[float, float]]:
        points: list[tuple[float, float]] = []
        for step in range(steps + 1):
            t = step / steps
            u = 1 - t
            points.append(
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
        return points

    def wobble_line(
        points: list[tuple[float, float]],
        *,
        width: float = 3.6,
        jitter: float = 0.7,
        closed: bool = False,
        target: ImageDraw.ImageDraw = line_draw,
        fill: tuple[int, int, int, int] = INK,
    ) -> None:
        source = points + ([points[0]] if closed else [])
        sampled: list[tuple[float, float]] = []
        for index, (start, end) in enumerate(zip(source, source[1:])):
            steps = max(2, round(math.dist(start, end) / 6))
            for step in range(steps):
                if index and step == 0:
                    continue
                t = step / steps
                envelope = math.sin(math.pi * t)
                sampled.append(
                    (
                        start[0]
                        + (end[0] - start[0]) * t
                        + RNG.uniform(-jitter, jitter) * envelope,
                        start[1]
                        + (end[1] - start[1]) * t
                        + RNG.uniform(-jitter, jitter) * envelope,
                    )
                )
        sampled.append(source[-1])
        target.line(
            [px(point) for point in sampled],
            fill=fill,
            width=max(1, round(width * SCALE)),
            joint="curve",
        )

    def curve(
        start: tuple[float, float],
        control_a: tuple[float, float],
        control_b: tuple[float, float],
        end: tuple[float, float],
        *,
        width: float = 3.4,
        jitter: float = 0.55,
        target: ImageDraw.ImageDraw = line_draw,
    ) -> None:
        wobble_line(
            cubic_points(start, control_a, control_b, end),
            width=width,
            jitter=jitter,
            target=target,
        )

    def oval_points(
        bounds: tuple[float, float, float, float], phase: float
    ) -> list[tuple[float, float]]:
        left, top, right, bottom = bounds
        cx = (left + right) / 2
        cy = (top + bottom) / 2
        rx = (right - left) / 2
        ry = (bottom - top) / 2
        points: list[tuple[float, float]] = []
        for step in range(72):
            angle = math.tau * step / 72
            uneven = 1 + 0.016 * math.sin(3 * angle + phase)
            points.append(
                (cx + rx * uneven * math.cos(angle), cy + ry * uneven * math.sin(angle))
            )
        return points

    def filled_shape(
        points: list[tuple[float, float]],
        fill: tuple[int, int, int, int],
        *,
        width: float = 4.0,
        jitter: float = 0.75,
    ) -> None:
        line_draw.polygon([px(point) for point in points], fill=WHITE)
        color_draw.polygon([px(point) for point in points], fill=fill)
        wobble_line(points, width=width, jitter=jitter, closed=True)

    def bean(
        segments: list[
            tuple[
                tuple[float, float],
                tuple[float, float],
                tuple[float, float],
                tuple[float, float],
            ]
        ],
        fill: tuple[int, int, int, int],
        *,
        width: float = 4.2,
    ) -> None:
        points: list[tuple[float, float]] = []
        for index, segment in enumerate(segments):
            sampled = cubic_points(*segment)
            points.extend(sampled if index == 0 else sampled[1:])
        filled_shape(points, fill, width=width)

    def face(
        bounds: tuple[float, float, float, float],
        *,
        phase: float,
        worried: bool = False,
    ) -> None:
        points = oval_points(bounds, phase)
        filled_shape(points, WHITE, width=4.2, jitter=0.65)
        left, top, right, bottom = bounds
        if worried:
            wobble_line([(left + 27, top + 67), (left + 42, top + 61)], width=2.7)
            wobble_line([(right - 44, top + 61), (right - 28, top + 67)], width=2.7)
            curve(
                (left + 45, bottom - 32),
                (left + 58, bottom - 45),
                (right - 57, bottom - 45),
                (right - 43, bottom - 31),
                width=2.8,
                jitter=0.25,
            )
        else:
            wobble_line([(left + 31, top + 65), (left + 45, top + 67)], width=2.7)
            wobble_line([(right - 45, top + 67), (right - 31, top + 64)], width=2.7)
            curve(
                (left + 48, bottom - 31),
                (left + 60, bottom - 22),
                (right - 60, bottom - 22),
                (right - 48, bottom - 34),
                width=2.8,
                jitter=0.25,
            )

    def stipple_shadow() -> None:
        # Broken elliptical arcs evoke the reference's fingerprint-like gray cloud.
        for ring in range(30):
            inset_x = ring * 2.0
            inset_y = ring * 3.0
            bounds = (
                round((64 + inset_x) * SCALE),
                round((330 + inset_y) * SCALE),
                round((273 - inset_x) * SCALE),
                round((885 - inset_y) * SCALE),
            )
            if bounds[2] <= bounds[0] or bounds[3] <= bounds[1]:
                break
            start = RNG.randint(5, 80)
            for shift in (0, 72, 151, 236):
                span = RNG.randint(24, 47)
                color_draw.arc(
                    bounds,
                    start=start + shift,
                    end=start + shift + span,
                    fill=(184, 180, 178, 185),
                    width=max(2, round(1.25 * SCALE)),
                )

    # A slightly imperfect single panel frame.
    wobble_line(
        [(46, 45), (722, 44), (721, 979), (45, 980), (46, 45)],
        width=4.0,
        jitter=1.0,
    )

    stipple_shadow()

    # Young worker: deliberately small, anxious, and carrying only one binder.
    bean(
        [
            ((105, 548), (78, 604), (82, 785), (106, 846)),
            ((106, 846), (134, 870), (205, 868), (231, 845)),
            ((231, 845), (253, 777), (249, 622), (226, 557)),
            ((226, 557), (198, 532), (134, 529), (105, 548)),
        ],
        PALE_TEAL,
    )
    face((109, 395, 224, 557), phase=0.4, worried=True)
    for x, lean in ((129, -2), (145, 0), (162, 1), (179, 2)):
        wobble_line([(x, 409), (x + lean, 384)], width=3.6, jitter=0.3)
    # Two tiny sweat strokes.
    wobble_line([(93, 478), (87, 492)], width=2.6, jitter=0.25)
    wobble_line([(88, 462), (79, 469)], width=2.6, jitter=0.25)
    # Minimal necktie.
    filled_shape([(159, 555), (175, 555), (180, 572), (166, 584), (153, 571)], MUSTARD, width=2.5)

    # Thick blank sample binder hugged at the chest.
    for offset in (14, 8):
        filled_shape(
            [(107, 645 + offset), (235, 635 + offset), (247, 731 + offset), (116, 742 + offset)],
            PAPER,
            width=1.6,
            jitter=0.35,
        )
    filled_shape([(104, 643), (235, 632), (247, 729), (114, 741)], PAPER, width=3.3)
    # Short outlined gestures wrap around the binder; no skeletal line limbs.
    bean(
        [
            ((111, 625), (133, 627), (152, 650), (166, 674)),
            ((166, 674), (172, 684), (168, 695), (157, 698)),
            ((157, 698), (139, 673), (122, 662), (104, 661)),
            ((104, 661), (96, 651), (100, 631), (111, 625)),
        ],
        PALE_TEAL,
        width=3.2,
    )
    bean(
        [
            ((222, 706), (208, 708), (192, 721), (181, 738)),
            ((181, 738), (176, 747), (181, 758), (192, 759)),
            ((192, 759), (208, 744), (223, 740), (239, 743)),
            ((239, 743), (247, 733), (240, 710), (222, 706)),
        ],
        PALE_TEAL,
        width=3.2,
    )

    # Older mentor: another small bean figure, already leaning toward the exit.
    bean(
        [
            ((555, 548), (532, 605), (539, 770), (565, 824)),
            ((565, 824), (596, 850), (672, 846), (695, 816)),
            ((695, 816), (715, 749), (709, 614), (683, 558)),
            ((683, 558), (653, 532), (584, 528), (555, 548)),
        ],
        WARM_GRAY,
    )
    face((555, 400, 681, 558), phase=1.3)
    # Thick eyebrows and a few beard dashes identify the mentor.
    wobble_line([(580, 462), (600, 457)], width=4.0, jitter=0.3)
    wobble_line([(632, 458), (653, 463)], width=4.0, jitter=0.3)
    for x, y in ((594, 519), (612, 523), (630, 518)):
        wobble_line([(x, y), (x + 5, y + 8)], width=2.0, jitter=0.2)
    # One brief hand-off gesture toward the binder.
    bean(
        [
            ((562, 623), (529, 616), (496, 626), (465, 646)),
            ((465, 646), (455, 652), (455, 666), (466, 672)),
            ((466, 672), (500, 657), (531, 655), (562, 665)),
            ((562, 665), (574, 657), (574, 633), (562, 623)),
        ],
        WARM_GRAY,
        width=3.2,
    )
    # Bare suggestion of an exit at the far right.
    wobble_line([(709, 532), (710, 857)], width=2.8, jitter=0.5)

    # A guide only: it is not merged into the textless Comfy input.
    bubble_points = oval_points((260, 214, 515, 767), phase=0.9)
    balloon_draw.polygon([px(point) for point in bubble_points], fill=WHITE)
    wobble_line(
        bubble_points,
        width=4.2,
        jitter=0.85,
        closed=True,
        target=balloon_draw,
    )
    # Short tail points toward the mentor without touching the character.
    wobble_line(
        [(493, 665), (529, 649), (552, 622)],
        width=4.0,
        jitter=0.55,
        target=balloon_draw,
    )

    colored_base = Image.alpha_composite(
        Image.new("RGBA", line_image.size, WHITE), color_image
    )
    composite = ImageChops.multiply(colored_base, line_image)
    output_dir = Path(__file__).parent
    for image, name in (
        (line_image, "line.png"),
        (color_image, "color.png"),
        (composite, "source.png"),
        (balloon_image, "balloon-guide.png"),
    ):
        image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(output_dir / name)


if __name__ == "__main__":
    main()
