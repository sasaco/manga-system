# -*- coding: utf-8 -*-
"""Episode 011 – control and color image.

Scene:
- Character (young engineer, left-center) hunched forward at desk, staring intently at CRT monitor.
- CRT Monitor (center-right) displaying a black/dark terminal screen with error.
- Keyboard, calculation papers on desk.
- Generous white space at upper-left for later balloon & lettering.
"""

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
DARK_SCREEN = (25, 30, 28, 255)
TERMINAL_GREEN = (70, 150, 80, 255)
ERROR_RED = (210, 75, 65, 255)
WHITE = (255, 255, 255, 255)
RNG = random.Random(20011102)


def main() -> None:
    line_image = Image.new('RGB', (WIDTH * SCALE, HEIGHT * SCALE), 'white')
    line_draw = ImageDraw.Draw(line_image)
    color_image = Image.new('RGBA', (WIDTH * SCALE, HEIGHT * SCALE), (0, 0, 0, 0))
    color_draw = ImageDraw.Draw(color_image)

    def px(point):
        return round(point[0] * SCALE), round(point[1] * SCALE)

    def line(points, *, width=3.0, jitter=0.25, closed=False, ink=INK):
        source = points + ([points[0]] if closed else [])
        sampled = []
        for segment, (start, end) in enumerate(zip(source, source[1:])):
            steps = max(2, round(math.dist(start, end) / 6))
            for step in range(steps):
                if segment and step == 0:
                    continue
                t = step / steps
                envelope = math.sin(math.pi * t)
                sampled.append((
                    start[0] + (end[0] - start[0]) * t + RNG.uniform(-jitter, jitter) * envelope,
                    start[1] + (end[1] - start[1]) * t + RNG.uniform(-jitter, jitter) * envelope,
                ))
        sampled.append(source[-1])
        last = max(1, len(sampled) - 2)
        for index, (a, b) in enumerate(zip(sampled, sampled[1:])):
            pressure = 0.86 + 0.18 * math.sin(math.pi * index / last)
            line_draw.line([px(a), px(b)], fill=ink, width=max(1, round(width * SCALE * pressure)))

    def cubic_pts(s, ca, cb, e, steps=36):
        result = []
        for i in range(steps + 1):
            t = i / steps
            u = 1 - t
            result.append((
                u**3*s[0] + 3*u**2*t*ca[0] + 3*u*t**2*cb[0] + t**3*e[0],
                u**3*s[1] + 3*u**2*t*ca[1] + 3*u*t**2*cb[1] + t**3*e[1],
            ))
        return result

    def curve(s, ca, cb, e, *, width=3.0, jitter=0.2):
        line(cubic_pts(s, ca, cb, e), width=width, jitter=jitter)

    def shape(segs, *, fill, width=3.5):
        vals = []
        for i, seg in enumerate(segs):
            part = cubic_pts(*seg)
            vals.extend(part if i == 0 else part[1:])
        line_draw.polygon([px(p) for p in vals], fill='white')
        color_draw.polygon([px(p) for p in vals], fill=fill)
        line(vals, width=width, jitter=0.36, closed=True)

    def polygon(pts, *, fill=WHITE, width=2.7):
        line_draw.polygon([px(p) for p in pts], fill='white')
        color_draw.polygon([px(p) for p in pts], fill=fill)
        line(pts, width=width, jitter=0.2, closed=True)

    def oval(bounds, *, phase, fill=WHITE, width=3.5):
        l, t, r, b = bounds
        cx, cy = (l+r)/2, (t+b)/2
        rx, ry = (r-l)/2, (b-t)/2
        pts = []
        for step in range(80):
            a = math.tau * step / 80
            w = 1 + 0.022*math.sin(3*a+phase) + 0.009*math.sin(7*a)
            pts.append((cx + rx*w*math.cos(a), cy + ry*w*math.sin(a)))
        line_draw.polygon([px(p) for p in pts], fill='white')
        color_draw.polygon([px(p) for p in pts], fill=fill)
        line(pts, width=width, jitter=0.3, closed=True)

    # ══ Panel frame ══
    line([(43, 43), (724, 44), (722, 980), (45, 981), (43, 43)], width=3.5, jitter=1.0)

    # ══ Background wall (warm white/gray wash) ══
    color_draw.rectangle([px((44, 44)), px((723, 979))], fill=(247, 246, 243, 255))

    # ══ Office chair behind character ══
    oval((40, 560, 110, 780), phase=0.2, fill=WARM_GRAY, width=2.8)
    line([(70, 780), (70, 890)], width=4.0, jitter=0.2)

    # ══ Desk surface ══
    polygon([(50, 700), (715, 695), (718, 830), (48, 835)], fill=LIGHT_GRAY, width=3.2)
    # Desk legs
    line([(85, 835), (82, 970)], width=3.5, jitter=0.2)
    line([(665, 830), (668, 970)], width=3.5, jitter=0.2)

    # ══ CRT Monitor (vintage 2001 bulky computer monitor) ══
    # CRT casing top & back perspective
    polygon([(410, 310), (630, 305), (665, 345), (445, 350)], fill=(215, 212, 209, 255), width=2.4)
    polygon([(630, 305), (665, 345), (655, 675), (620, 635)], fill=(195, 192, 188, 255), width=2.4)

    # Outer CRT front bezel
    polygon([(385, 345), (665, 340), (655, 680), (375, 685)], fill=WARM_GRAY, width=4.0)

    # Inner bezel (recessed screen frame)
    polygon([(400, 365), (648, 360), (640, 650), (392, 655)], fill=(175, 172, 168, 255), width=2.5)

    # Screen (curved CRT glass, dark terminal)
    polygon([(412, 380), (636, 375), (628, 635), (404, 640)], fill=DARK_SCREEN, width=3.0)

    # CRT scanlines / subtle screen glare
    for row in range(390, 630, 16):
        color_draw.line([px((410, row)), px((630, row))], fill=(255, 255, 255, 8), width=SCALE)

    # Terminal output lines (green phosphor)
    for y_pos, w_len in [(400, 100), (420, 160), (440, 130), (460, 180), (480, 110), (500, 150)]:
        polygon([(422, y_pos), (422 + w_len, y_pos - 2), (422 + w_len, y_pos + 7), (422, y_pos + 9)],
                fill=TERMINAL_GREEN, width=1.0)

    # Error message highlight block (red banner in terminal indicating ERROR)
    polygon([(420, 545), (615, 540), (615, 575), (420, 580)], fill=ERROR_RED, width=1.8)
    # Inner abstract error line (yellowish/white highlight)
    polygon([(430, 555), (590, 552), (590, 565), (430, 568)], fill=(255, 230, 180, 255), width=1.0)
    # Secondary error detail line below
    polygon([(420, 592), (540, 590), (540, 604), (420, 606)], fill=ERROR_RED, width=1.2)

    # Monitor Stand / Base
    polygon([(465, 684), (575, 682), (590, 715), (450, 717)], fill=WARM_GRAY, width=2.8)

    # Keyboard in front of monitor
    polygon([(360, 725), (590, 720), (578, 775), (348, 780)], fill=(225, 222, 218, 255), width=2.2)
    # Keyboard grid lines
    line([(368, 735), (582, 730)], width=1.2, jitter=0.1)
    line([(363, 750), (576, 745)], width=1.2, jitter=0.1)
    line([(358, 765), (570, 760)], width=1.2, jitter=0.1)

    # Mouse on right
    oval((605, 735, 640, 770), phase=0.5, fill=WHITE, width=1.8)

    # Calculation papers & binders on desk
    # Thick calculation report on far right
    polygon([(630, 705), (710, 700), (706, 760), (626, 765)], fill=WHITE, width=2.0)
    polygon([(630, 695), (710, 690), (710, 705), (630, 710)], fill=WARM_GRAY, width=1.5)
    line([(645, 725), (695, 720)], width=1.0, jitter=0.1)
    line([(645, 740), (690, 735)], width=1.0, jitter=0.1)

    # Loose calculation sheets under keyboard / left desk
    polygon([(220, 720), (335, 715), (330, 780), (215, 785)], fill=WHITE, width=1.8)
    line([(230, 735), (315, 730)], width=1.0, jitter=0.1)
    line([(230, 750), (305, 745)], width=1.0, jitter=0.1)

    # ══ Character – left side, hunched forward, staring at the screen ══
    # Seated bean body (leaning forward toward monitor)
    shape(
        [
            ((95, 570), (130, 545), (230, 560), (280, 620)),
            ((280, 620), (310, 680), (310, 770), (270, 830)),
            ((270, 830), (210, 860), (120, 845), (85, 790)),
            ((85, 790), (65, 710), (75, 620), (95, 570)),
        ],
        fill=PALE_TEAL,
        width=4.0,
    )

    # Tie (mustard yellow)
    polygon([(185, 615), (210, 615), (218, 638), (198, 655), (178, 638)], fill=MUSTARD, width=2.0)
    polygon([(198, 655), (212, 710), (198, 730), (184, 710)], fill=MUSTARD, width=2.2)

    # Left arm (leaning on desk, hand near keyboard)
    shape(
        [
            ((105, 635), (95, 665), (105, 735), (135, 765)),
            ((135, 765), (180, 785), (240, 780), (260, 760)),
            ((260, 760), (240, 740), (190, 745), (155, 725)),
            ((155, 725), (145, 665), (135, 630), (105, 635)),
        ],
        fill=PALE_TEAL,
        width=3.2,
    )

    # Right arm (reaching toward keyboard/desk)
    shape(
        [
            ((260, 640), (290, 660), (320, 715), (340, 745)),
            ((340, 745), (330, 765), (295, 760), (280, 735)),
            ((280, 735), (265, 695), (250, 665), (250, 645)),
            ((250, 645), (255, 640), (258, 640), (260, 640)),
        ],
        fill=PALE_TEAL,
        width=3.0,
    )

    # Head: oval, tilted forward toward monitor
    oval((135, 360, 315, 565), phase=0.7, fill=WHITE, width=3.8)

    # Hair strokes (short, messy lines from crown)
    for x_off, dy in [(-8, 2), (10, -7), (28, -10), (46, -5)]:
        bx = 190 + x_off
        by = 380 + dy
        curve((bx, by), (bx+2, by-14), (bx+8, by-26), (bx+12, by-38), width=2.8)

    # Eyebrows: troubled / drooping in despair / disappointment (八の字)
    line([(185, 435), (225, 442)], width=2.6, jitter=0.15)
    line([(245, 440), (285, 433)], width=2.6, jitter=0.15)

    # Eyes: wide dot eyes staring in shock/exhaustion at the error
    oval((190, 452, 222, 482), phase=0.3, fill=WHITE, width=2.8)
    oval((248, 448, 280, 478), phase=0.5, fill=WHITE, width=2.8)
    # Pupils (staring straight right toward monitor)
    oval((204, 460, 220, 476), phase=0.2, fill=(*INK, 255), width=1.5)
    oval((262, 456, 278, 472), phase=0.4, fill=(*INK, 255), width=1.5)
    # Small pupil highlights
    oval((212, 463, 218, 469), phase=0.0, fill=WHITE, width=1.0)
    oval((270, 459, 276, 465), phase=0.0, fill=WHITE, width=1.0)

    # Eye-bag / exhaustion lines
    line([(188, 492), (224, 490)], width=1.5, jitter=0.1)
    line([(246, 488), (282, 486)], width=1.5, jitter=0.1)

    # Mouth: small open or wavy line of dismay (へたれ口)
    curve((215, 526), (230, 534), (242, 524), (255, 530), width=2.4, jitter=0.2)

    # Cold sweat drop (despair / shock)
    oval((148, 440, 168, 470), phase=0.4, fill=(180, 215, 235, 255), width=1.8)
    line([(158, 430), (148, 450)], width=1.6, jitter=0.1)
    line([(158, 430), (168, 450)], width=1.6, jitter=0.1)

    # Shock / despair stipple behind character (local warm-gray tone)
    # Series bible: "温かい灰色の指紋状・点描状トーンを人物の背後へ小さく置いてよい"
    for _ in range(70):
        sx = RNG.randint(80, 180)
        sy = RNG.randint(480, 680)
        color_draw.ellipse([px((sx-2, sy-2)), px((sx+2, sy+2))], fill=(190, 185, 180, 130))

    output = Path(__file__).with_name('011-control.png')
    color_output = Path(__file__).with_name('011-color.png')
    line_image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(output)
    color_image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(color_output)
    print('Generated:')
    print(output)
    print(color_output)


if __name__ == '__main__':
    main()
