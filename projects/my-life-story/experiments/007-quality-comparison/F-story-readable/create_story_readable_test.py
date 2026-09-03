"""Create an episode-007 test that stays sparse but reads as a specific story.

The Comfy input remains textless.  The balloon and authored dialogue are kept on
separate transparent layers for the later Krita finishing pass.
"""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH = 768
HEIGHT = 1024
SCALE = 4
INK = (31, 30, 29, 255)
PALE_TEAL = (157, 202, 201, 255)
MUSTARD = (244, 204, 72, 255)
WARM_GRAY = (197, 193, 191, 255)
PAPER = (245, 243, 239, 255)
WHITE = (255, 255, 255, 255)
RNG = random.Random(20010913)


def main() -> None:
    size = (WIDTH * SCALE, HEIGHT * SCALE)
    line_layer = Image.new("RGBA", size, (0, 0, 0, 0))
    color_layer = Image.new("RGBA", size, (0, 0, 0, 0))
    balloon_layer = Image.new("RGBA", size, (0, 0, 0, 0))
    lettering_layer = Image.new("RGBA", size, (0, 0, 0, 0))
    line_draw = ImageDraw.Draw(line_layer)
    color_draw = ImageDraw.Draw(color_layer)
    balloon_draw = ImageDraw.Draw(balloon_layer)
    lettering_draw = ImageDraw.Draw(lettering_layer)

    def px(point: tuple[float, float]) -> tuple[int, int]:
        return round(point[0] * SCALE), round(point[1] * SCALE)

    def cubic(
        start: tuple[float, float],
        a: tuple[float, float],
        b: tuple[float, float],
        end: tuple[float, float],
        steps: int = 28,
    ) -> list[tuple[float, float]]:
        result: list[tuple[float, float]] = []
        for step in range(steps + 1):
            t = step / steps
            u = 1 - t
            result.append(
                (
                    u**3 * start[0]
                    + 3 * u**2 * t * a[0]
                    + 3 * u * t**2 * b[0]
                    + t**3 * end[0],
                    u**3 * start[1]
                    + 3 * u**2 * t * a[1]
                    + 3 * u * t**2 * b[1]
                    + t**3 * end[1],
                )
            )
        return result

    def wobble(
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

    def oval_points(
        bounds: tuple[float, float, float, float], phase: float
    ) -> list[tuple[float, float]]:
        left, top, right, bottom = bounds
        cx = (left + right) / 2
        cy = (top + bottom) / 2
        rx = (right - left) / 2
        ry = (bottom - top) / 2
        result: list[tuple[float, float]] = []
        for step in range(72):
            angle = math.tau * step / 72
            uneven = 1 + 0.017 * math.sin(3 * angle + phase)
            result.append(
                (cx + rx * uneven * math.cos(angle), cy + ry * uneven * math.sin(angle))
            )
        return result

    def shape(
        points: list[tuple[float, float]],
        fill: tuple[int, int, int, int],
        *,
        width: float = 4.0,
        jitter: float = 0.7,
    ) -> None:
        color_draw.polygon([px(point) for point in points], fill=fill)
        wobble(points, width=width, jitter=jitter, closed=True)

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
        width: float = 4.0,
    ) -> None:
        points: list[tuple[float, float]] = []
        for index, segment in enumerate(segments):
            sampled = cubic(*segment)
            points.extend(sampled if index == 0 else sampled[1:])
        shape(points, fill, width=width)

    def face(
        bounds: tuple[float, float, float, float],
        *,
        phase: float,
        worried: bool,
    ) -> None:
        points = oval_points(bounds, phase)
        shape(points, WHITE, width=4.1)
        left, top, right, bottom = bounds
        if worried:
            wobble([(left + 25, top + 64), (left + 39, top + 59)], width=2.7)
            wobble([(right - 39, top + 59), (right - 25, top + 65)], width=2.7)
            wobble(
                cubic(
                    (left + 39, bottom - 28),
                    (left + 52, bottom - 45),
                    (right - 52, bottom - 45),
                    (right - 38, bottom - 29),
                ),
                width=2.8,
                jitter=0.25,
            )
        else:
            wobble([(left + 30, top + 63), (left + 45, top + 65)], width=2.7)
            wobble([(right - 45, top + 65), (right - 30, top + 62)], width=2.7)
            wobble(
                cubic(
                    (left + 46, bottom - 30),
                    (left + 58, bottom - 20),
                    (right - 58, bottom - 20),
                    (right - 45, bottom - 32),
                ),
                width=2.7,
                jitter=0.25,
            )

    # Single imperfect frame.
    wobble(
        [(45, 44), (723, 45), (721, 980), (46, 979), (45, 44)],
        width=4.0,
        jitter=1.0,
    )

    # A restrained fingerprint-like anxiety cloud behind the apprentice.
    for ring in range(28):
        inset_x = ring * 1.8
        inset_y = ring * 3.0
        bounds = (
            round((76 + inset_x) * SCALE),
            round((380 + inset_y) * SCALE),
            round((287 - inset_x) * SCALE),
            round((907 - inset_y) * SCALE),
        )
        if bounds[2] <= bounds[0] or bounds[3] <= bounds[1]:
            break
        start = RNG.randint(4, 55)
        for shift in (0, 83, 176, 263):
            color_draw.arc(
                bounds,
                start=start + shift,
                end=start + shift + RNG.randint(24, 43),
                fill=(180, 176, 174, 175),
                width=max(2, round(1.2 * SCALE)),
            )

    # Hundreds of downstream pages, reduced to one unmistakable tall stack.
    for offset in range(74, -1, -7):
        shape(
            [
                (59 + offset * 0.09, 650 + offset),
                (151, 645 + offset),
                (164, 858 + offset),
                (51, 865 + offset),
            ],
            PAPER,
            width=1.35,
            jitter=0.25,
        )

    # Apprentice, pressed between the sample and the page stack.
    bean(
        [
            ((151, 574), (131, 626), (137, 788), (157, 845)),
            ((157, 845), (184, 868), (245, 866), (267, 842)),
            ((267, 842), (285, 781), (281, 635), (262, 580)),
            ((262, 580), (236, 555), (177, 552), (151, 574)),
        ],
        PALE_TEAL,
    )
    face((151, 420, 260, 580), phase=0.6, worried=True)
    for x, lean in ((169, -3), (185, -1), (201, 1), (217, 3)):
        wobble([(x, 432), (x + lean, 407)], width=3.5, jitter=0.3)
    wobble([(137, 498), (129, 510)], width=2.5, jitter=0.25)
    wobble([(133, 482), (124, 488)], width=2.5, jitter=0.25)
    shape([(197, 577), (213, 577), (218, 594), (205, 606), (192, 594)], MUSTARD, width=2.4)

    # Mentor is already turning to the exit while giving only one sample binder.
    bean(
        [
            ((563, 566), (542, 620), (548, 773), (572, 829)),
            ((572, 829), (603, 851), (673, 848), (695, 819)),
            ((695, 819), (715, 756), (708, 626), (685, 573)),
            ((685, 573), (656, 548), (590, 545), (563, 566)),
        ],
        WARM_GRAY,
    )
    face((560, 410, 684, 571), phase=1.2, worried=False)
    # Cap-like hair block from the reference, kept minimal.
    wobble([(569, 461), (575, 424), (665, 424), (677, 460)], width=3.7, jitter=0.4)
    for x in (589, 608, 628, 648):
        wobble([(x, 427), (x + 2, 458)], width=2.2, jitter=0.25)
    for x, y in ((596, 531), (614, 535), (632, 530)):
        wobble([(x, y), (x + 5, y + 8)], width=1.9, jitter=0.2)
    wobble([(711, 553), (711, 861)], width=2.8, jitter=0.5)

    # The one sample binder is physically being passed between them.
    for offset in (14, 8):
        shape(
            [(269, 686 + offset), (438, 665 + offset), (455, 745 + offset), (286, 766 + offset)],
            PAPER,
            width=1.4,
            jitter=0.25,
        )
    shape([(266, 683), (438, 662), (455, 742), (284, 764)], PAPER, width=3.1)
    bean(
        [
            ((562, 658), (528, 652), (489, 661), (449, 684)),
            ((449, 684), (439, 690), (439, 704), (450, 710)),
            ((450, 710), (493, 691), (530, 692), (565, 704)),
            ((565, 704), (575, 694), (574, 668), (562, 658)),
        ],
        WARM_GRAY,
        width=3.1,
    )
    bean(
        [
            ((264, 706), (249, 708), (235, 722), (227, 739)),
            ((227, 739), (222, 748), (228, 758), (239, 758)),
            ((239, 758), (252, 744), (266, 740), (282, 743)),
            ((282, 743), (288, 731), (280, 709), (264, 706)),
        ],
        PALE_TEAL,
        width=3.1,
    )

    # Large dialogue balloon, separate from the textless Comfy source.
    bubble = oval_points((284, 125, 545, 635), phase=0.9)
    balloon_draw.polygon([px(point) for point in bubble], fill=WHITE)
    wobble(
        bubble,
        width=4.2,
        jitter=0.85,
        closed=True,
        target=balloon_draw,
    )
    balloon_draw.polygon([px((507, 579)), px((557, 624)), px((527, 554))], fill=WHITE)
    wobble(
        [(507, 579), (557, 624), (527, 554)],
        width=4.0,
        jitter=0.5,
        closed=True,
        target=balloon_draw,
    )

    # Episode-authored dialogue, vertically arranged right-to-left.
    font_path = "C:/Windows/Fonts/UDDigiKyokashoN-R.ttc"
    comic_font = ImageFont.truetype(font_path, 42 * SCALE, layout_engine=ImageFont.Layout.BASIC)

    def vertical_text(text: str, x: float, y: float, spacing: float = 51) -> None:
        for index, character in enumerate(text):
            lettering_draw.text(
                px((x, y + index * spacing)),
                character,
                font=comic_font,
                fill=INK,
                anchor="mm",
                stroke_width=0,
            )

    vertical_text("サンプルの", 478, 205)
    vertical_text("aを1から2に", 412, 184)
    vertical_text("変えろ", 346, 255)

    base = Image.new("RGBA", size, WHITE)
    source = Image.alpha_composite(Image.alpha_composite(base, color_layer), line_layer)
    story_preview = Image.alpha_composite(
        Image.alpha_composite(source, balloon_layer), lettering_layer
    )

    output_dir = Path(__file__).parent
    krita_line = Image.alpha_composite(Image.new("RGBA", size, WHITE), line_layer)
    outputs = (
        (krita_line, "line.png"),
        (color_layer, "color.png"),
        (source, "source.png"),
        (balloon_layer, "balloon.png"),
        (lettering_layer, "lettering.png"),
        (story_preview, "story-preview.png"),
    )
    for image, filename in outputs:
        image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(output_dir / filename)

    candidate = output_dir / "generated" / "007_2001116_01.png"
    if candidate.exists():
        generated = Image.open(candidate).convert("RGBA").resize(size, Image.Resampling.LANCZOS)
        finished = Image.alpha_composite(
            Image.alpha_composite(generated, balloon_layer), lettering_layer
        )
        finished.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(
            output_dir / "finished-preview.png"
        )


if __name__ == "__main__":
    main()
