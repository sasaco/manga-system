"""Create a readable single-scene Scribble ControlNet guide for episode 003."""

from pathlib import Path

from PIL import Image, ImageDraw


WIDTH = 768
HEIGHT = 1024
SCALE = 2
INK = (0, 0, 0)


def main() -> None:
    canvas = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), "white")
    draw = ImageDraw.Draw(canvas)

    def box(values: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        return tuple(value * SCALE for value in values)

    def pts(values: list[tuple[int, int]]) -> list[tuple[int, int]]:
        return [(x * SCALE, y * SCALE) for x, y in values]

    def line(values: list[tuple[int, int]], width: int = 4) -> None:
        draw.line(pts(values), fill=INK, width=width * SCALE, joint="curve")

    def ellipse(values: tuple[int, int, int, int], width: int = 4) -> None:
        draw.ellipse(box(values), outline=INK, width=width * SCALE)

    def rectangle(values: tuple[int, int, int, int], width: int = 4) -> None:
        draw.rectangle(box(values), outline=INK, width=width * SCALE)

    def polygon(values: list[tuple[int, int]], width: int = 4) -> None:
        draw.polygon(pts(values), outline=INK)
        line(values + [values[0]], width=width)

    # Train interior: plain double doors and overhead rail.
    rectangle((118, 180, 650, 920), width=5)
    line([(384, 180), (384, 920)], width=4)
    rectangle((155, 235, 348, 445), width=4)
    rectangle((420, 235, 613, 445), width=4)
    line([(85, 145), (683, 145)], width=6)

    # Four hanging straps; the central-left one belongs to the protagonist.
    for cx in (190, 318, 474, 600):
        line([(cx, 145), (cx, 220)], width=4)
        draw.rounded_rectangle(box((cx - 30, 215, cx + 30, 285)), radius=18 * SCALE, outline=INK, width=4 * SCALE)

    # Large central protagonist with readable human silhouette and clothing.
    ellipse((302, 270, 454, 430), width=6)
    # Hair contour and simple tired face.
    line([(308, 332), (322, 292), (360, 275), (406, 286), (448, 325)], width=7)
    line([(335, 355), (355, 351)], width=4)
    line([(401, 351), (421, 355)], width=4)
    line([(363, 390), (384, 396), (405, 390)], width=4)
    # Shirt torso, collar, and tie.
    polygon([(321, 430), (435, 430), (478, 700), (286, 700)], width=6)
    line([(342, 435), (378, 478), (414, 435)], width=4)
    polygon([(369, 470), (387, 470), (396, 570), (378, 605), (360, 570)], width=4)
    # Raised arm gripping the strap; lowered arm holds the bag tightly.
    line([(421, 465), (460, 360), (474, 280)], width=14)
    ellipse((458, 270, 490, 308), width=5)
    line([(328, 470), (258, 560), (330, 640)], width=14)
    # Rectangular work bag across the chest.
    rectangle((304, 540, 468, 690), width=6)
    line([(344, 540), (344, 515), (425, 515), (425, 540)], width=5)
    # Trousers and shoes.
    line([(330, 700), (318, 910), (270, 955)], width=16)
    line([(430, 700), (452, 910), (505, 955)], width=16)

    # Cropped commuters press in from both sides; shoulders overlap the hero.
    ellipse((-45, 300, 105, 455), width=6)
    polygon([(-30, 455), (95, 440), (220, 680), (110, 880), (-30, 820)], width=6)
    line([(82, 470), (250, 585)], width=15)

    ellipse((655, 300, 805, 455), width=6)
    polygon([(680, 440), (798, 455), (798, 820), (660, 880), (540, 680)], width=6)
    line([(686, 470), (520, 585)], width=15)

    # Two more heads and shoulders behind, establishing a packed carriage.
    ellipse((120, 360, 235, 480), width=5)
    line([(148, 470), (245, 610)], width=12)
    ellipse((535, 360, 650, 480), width=5)
    line([(620, 470), (520, 610)], width=12)

    output = Path(__file__).with_name("003-v2-guide.png")
    canvas.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(output)
    print(output)


if __name__ == "__main__":
    main()
