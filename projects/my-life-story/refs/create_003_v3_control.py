"""Create the intentionally loose, textless control/finishing art for episode 003."""

from pathlib import Path

from PIL import Image, ImageDraw


WIDTH = 768
HEIGHT = 1024
SCALE = 3
INK = (24, 24, 24)


def main() -> None:
    canvas = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), "white")
    draw = ImageDraw.Draw(canvas)

    def points(values: list[tuple[int, int]]) -> list[tuple[int, int]]:
        return [(x * SCALE, y * SCALE) for x, y in values]

    def line(values: list[tuple[int, int]], width: int = 3) -> None:
        draw.line(points(values), fill=INK, width=width * SCALE, joint="curve")

    def closed(values: list[tuple[int, int]], width: int = 3) -> None:
        line(values + [values[0]], width=width)

    def ellipse(bounds: tuple[int, int, int, int], width: int = 3) -> None:
        draw.ellipse(tuple(value * SCALE for value in bounds), outline=INK, width=width * SCALE)

    def rounded(bounds: tuple[int, int, int, int], radius: int, width: int = 3) -> None:
        draw.rounded_rectangle(
            tuple(value * SCALE for value in bounds),
            radius=radius * SCALE,
            outline=INK,
            width=width * SCALE,
        )

    def curve(
        start: tuple[int, int],
        control_a: tuple[int, int],
        control_b: tuple[int, int],
        end: tuple[int, int],
        width: int = 3,
    ) -> None:
        values: list[tuple[int, int]] = []
        for step in range(25):
            t = step / 24
            u = 1 - t
            x = round(
                u**3 * start[0]
                + 3 * u**2 * t * control_a[0]
                + 3 * u * t**2 * control_b[0]
                + t**3 * end[0]
            )
            y = round(
                u**3 * start[1]
                + 3 * u**2 * t * control_a[1]
                + 3 * u * t**2 * control_b[1]
                + t**3 * end[1]
            )
            values.append((x, y))
        line(values, width=width)

    # A single quiet panel and only enough train detail to locate the scene.
    rounded((38, 42, 730, 982), radius=7, width=4)
    line([(103, 188), (667, 187)], width=4)
    rounded((111, 225, 658, 885), radius=7, width=3)
    line([(384, 226), (384, 293)], width=3)
    line([(384, 736), (384, 884)], width=3)
    rounded((143, 286, 344, 488), radius=5, width=3)
    rounded((424, 286, 626, 488), radius=5, width=3)

    # A short row of deliberately plain hanging straps.
    for cx, bottom in ((184, 281), (309, 267), (470, 270), (586, 282)):
        line([(cx, 188), (cx - 1, bottom - 54)], width=3)
        rounded((cx - 25, bottom - 57, cx + 25, bottom), radius=15, width=3)

    # Two rear commuters: just heads and shoulders, no costume detail.
    ellipse((151, 330, 244, 427), width=3)
    line([(158, 414), (123, 505), (258, 531)], width=4)
    ellipse((529, 332, 622, 430), width=3)
    line([(614, 416), (650, 508), (513, 532)], width=4)

    # Central new employee: soft, uneven proportions and a small tired face.
    ellipse((296, 300, 467, 474), width=4)
    line([(305, 349), (322, 319), (355, 302), (392, 307), (422, 323), (458, 357)], width=5)
    line([(333, 383), (351, 380)], width=3)
    line([(409, 381), (427, 384)], width=3)
    line([(363, 423), (382, 429), (402, 421)], width=3)

    # Loose shirt/body outline, tiny collar and tie.
    curve((322, 470), (299, 520), (297, 649), (295, 730), width=4)
    curve((295, 730), (342, 739), (426, 734), (472, 728), width=4)
    curve((472, 728), (469, 640), (461, 520), (438, 468), width=4)
    line([(338, 476), (380, 514), (421, 476)], width=3)
    closed([(372, 507), (389, 507), (399, 590), (381, 617), (363, 590)], width=3)

    # One raised arm, one arm hugging the bag.
    curve((426, 495), (445, 451), (459, 382), (469, 331), width=6)
    ellipse((456, 316, 485, 347), width=3)
    curve((328, 500), (306, 524), (282, 570), (314, 634), width=6)

    # A plain rectangular work bag with one handle.
    rounded((310, 566, 455, 717), radius=5, width=4)
    line([(342, 566), (342, 544), (419, 544), (419, 566)], width=3)

    # Legs angle inward a little, conveying fatigue without extra motion marks.
    curve((330, 729), (329, 780), (330, 851), (293, 911), width=6)
    curve((432, 728), (433, 788), (437, 856), (476, 910), width=6)
    line([(292, 912), (268, 918)], width=5)
    line([(476, 910), (502, 918)], width=5)

    # Foreground commuters crop into the panel and gently squeeze the hero.
    ellipse((-29, 365, 111, 508), width=4)
    curve((-16, 503), (36, 480), (76, 482), (91, 493), width=4)
    curve((91, 493), (154, 524), (197, 581), (219, 617), width=4)
    curve((219, 617), (190, 688), (174, 770), (157, 817), width=4)
    curve((157, 817), (101, 800), (40, 779), (-16, 760), width=4)
    curve((87, 514), (132, 544), (190, 587), (236, 612), width=6)

    ellipse((657, 363, 798, 507), width=4)
    curve((680, 492), (703, 482), (750, 481), (785, 503), width=4)
    curve((785, 760), (727, 779), (664, 799), (612, 816), width=4)
    curve((612, 816), (594, 767), (575, 684), (550, 617), width=4)
    curve((550, 617), (573, 579), (620, 523), (680, 492), width=4)
    curve((681, 512), (634, 544), (577, 587), (531, 611), width=6)

    # Tiny hair cues distinguish people while keeping them almost symbolic.
    line([(11, 390), (35, 367), (69, 369), (98, 394)], width=4)
    line([(668, 391), (692, 367), (728, 367), (781, 401)], width=4)

    output = Path(__file__).with_name("003-control.png")
    canvas.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(output)
    print(output)


if __name__ == "__main__":
    main()
