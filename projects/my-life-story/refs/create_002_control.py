"""Create the textless two-person Scribble ControlNet guide for episode 002."""

from pathlib import Path

from PIL import Image, ImageDraw


WIDTH = 768
HEIGHT = 1024
SCALE = 2
BLACK = (0, 0, 0)


def point(value: tuple[int, int]) -> tuple[int, int]:
    return value[0] * SCALE, value[1] * SCALE


def main() -> None:
    canvas = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), "white")
    draw = ImageDraw.Draw(canvas)

    def line(points: list[tuple[int, int]], width: int = 5) -> None:
        draw.line([point(item) for item in points], fill=BLACK, width=width * SCALE, joint="curve")

    def ellipse(box: tuple[int, int, int, int], width: int = 5) -> None:
        draw.ellipse(tuple(value * SCALE for value in box), outline=BLACK, width=width * SCALE)

    def rectangle(box: tuple[int, int, int, int], width: int = 4) -> None:
        draw.rectangle(tuple(value * SCALE for value in box), outline=BLACK, width=width * SCALE)

    # The upper third stays empty for the later Krita narration layer.
    # Apprentice: seated at the left of the drafting board.
    ellipse((120, 515, 184, 579))
    line([(152, 579), (152, 700)])
    line([(152, 615), (245, 690)])
    line([(152, 620), (112, 690)])
    line([(152, 700), (205, 760), (260, 760)])
    line([(152, 700), (110, 770), (70, 770)])

    # Tilted drafting board, practice sheet, ruler, and pencil hand.
    line([(220, 650), (465, 610), (500, 790), (255, 830), (220, 650)])
    line([(305, 820), (285, 930)])
    line([(445, 800), (485, 930)])
    rectangle((285, 670, 435, 770), width=3)
    rectangle((300, 685, 335, 720), width=2)
    rectangle((345, 685, 380, 720), width=2)
    rectangle((390, 685, 425, 720), width=2)
    line([(307, 700), (325, 700)], width=2)
    line([(352, 700), (370, 700)], width=2)
    line([(397, 700), (415, 700)], width=2)
    line([(330, 785), (430, 768)], width=3)
    line([(244, 688), (322, 707)], width=4)

    # Mentor: taller, standing at right, pointing to the practice sheet.
    ellipse((545, 455, 619, 529))
    line([(582, 529), (582, 735)])
    line([(582, 575), (500, 650), (405, 700)])
    line([(582, 575), (650, 650)])
    line([(582, 735), (540, 890), (505, 945)])
    line([(582, 735), (630, 890), (670, 945)])
    line([(558, 482), (572, 478)], width=3)
    line([(592, 478), (606, 482)], width=3)

    output = Path(__file__).with_name("002-control.png")
    canvas.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(output)
    print(output)


if __name__ == "__main__":
    main()
