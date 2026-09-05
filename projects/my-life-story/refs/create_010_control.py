# -*- coding: utf-8 -*-
"""Episode 010 v2 – control image.

Composition:
- Large CRT TV mounted high on the wall (upper half of panel, center-right)
  showing twin-tower silhouettes + explosion cloud
- Character (lower-left) slumped at cluttered desk, face tilted UPWARD
  toward the TV – the "ふと見上げる" (casually glancing up) posture
- Desk covered in papers, a mug, a ruler — all-nighter atmosphere
- Wide shot so the TV + character contrast in size is clear
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
TV_GLOW = (255, 248, 218, 255)
EXPLOSION_ORANGE = (230, 140, 50, 255)
BUILDING_DARK = (70, 55, 48, 255)
WHITE = (255, 255, 255, 255)
RNG = random.Random(20010911)


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

    # ══ Background wall (warm gray wash) ══
    color_draw.rectangle([px((44, 44)), px((723, 979))], fill=(245, 243, 240, 255))

    # ══ TV – high on the wall, right-center, large ══
    # TV screen (glow)
    polygon([(320, 55), (700, 57), (697, 380), (323, 378)], fill=TV_GLOW, width=4.5)
    # TV bezel (thicker frame lines)
    line([(312, 47), (708, 49)], width=5.5, jitter=0.6)   # top
    line([(708, 49), (705, 388)], width=5.5, jitter=0.6)  # right
    line([(705, 388), (314, 386)], width=5.5, jitter=0.6) # bottom
    line([(314, 386), (312, 47)], width=5.5, jitter=0.6)  # left

    # TV stand / bracket
    polygon([(490, 386), (540, 386), (548, 415), (482, 415)], fill=WARM_GRAY, width=2.2)
    line([(470, 415), (560, 415)], width=3.0, jitter=0.3)

    # TV content: twin towers (silhouette)
    polygon([(365, 145), (415, 145), (413, 360), (363, 360)], fill=BUILDING_DARK, width=1.8)
    polygon([(438, 160), (480, 160), (478, 360), (436, 360)], fill=BUILDING_DARK, width=1.8)
    # Antenna on left tower
    line([(388, 145), (390, 110)], width=2.0, jitter=0.2)

    # Explosion cloud (upper right of towers, orange-warm)
    expl = [
        (462, 88), (500, 68), (540, 80), (575, 62),
        (610, 80), (638, 68), (665, 90), (672, 120),
        (655, 148), (635, 140), (615, 162), (590, 148),
        (565, 168), (538, 152), (508, 162), (482, 145),
        (462, 125), (455, 105),
    ]
    color_draw.polygon([px(p) for p in expl], fill=EXPLOSION_ORANGE)
    line(expl, width=2.5, jitter=2.0, closed=True)
    # Inner lighter highlight
    expl_inner = [
        (498, 100), (525, 84), (558, 95), (588, 80),
        (618, 100), (622, 128), (600, 140), (570, 130),
        (540, 148), (510, 135), (490, 115),
    ]
    color_draw.polygon([px(p) for p in expl_inner], fill=(255, 200, 90, 255))

    # Impact flash lines radiating from explosion
    for angle_deg, length in [(300, 28), (318, 24), (338, 32), (352, 25), (368, 22)]:
        angle = math.radians(angle_deg)
        ox, oy = 565, 115
        line([(ox, oy), (ox + math.cos(angle)*length, oy + math.sin(angle)*length)],
             width=2.2, jitter=0.6)

    # TV scan lines (subtle horizontal)
    for row in range(80, 370, 22):
        color_draw.line([px((324, row)), px((696, row))], fill=(0, 0, 0, 18), width=SCALE)

    # ══ Desk surface ══
    polygon([(52, 768), (714, 762), (718, 850), (49, 856)], fill=LIGHT_GRAY, width=3.2)
    # Desk legs
    line([(90, 856), (87, 970)], width=3.5, jitter=0.2)
    line([(660, 854), (664, 970)], width=3.5, jitter=0.2)

    # Desk clutter – papers (scattered, slightly overlapping)
    # Far-left stack
    for off in (10, 5):
        polygon([(55, 770+off), (230, 764+off), (235, 840+off), (58, 846+off)],
                fill=WHITE, width=1.2)
    polygon([(52, 770), (230, 764), (235, 840), (55, 846)], fill=LIGHT_GRAY, width=2.0)
    line([(72, 785), (210, 779)], width=1.1, jitter=0.1)
    line([(72, 800), (195, 794)], width=1.1, jitter=0.1)
    line([(72, 815), (180, 810)], width=1.1, jitter=0.1)

    # Center papers (partly under character arm)
    polygon([(230, 775), (480, 770), (482, 845), (232, 850)], fill=WHITE, width=1.5)
    line([(250, 790), (460, 785)], width=1.0, jitter=0.1)
    line([(250, 808), (440, 803)], width=1.0, jitter=0.1)

    # Coffee mug on right side
    polygon([(580, 770), (628, 770), (620, 845), (588, 845)], fill=WHITE, width=2.2)
    oval((576, 766, 632, 784), phase=0.4, fill=WARM_GRAY, width=1.8)
    # Handle
    curve((628, 790), (652, 790), (655, 820), (628, 820), width=2.0, jitter=0.2)
    # Steam wisps above mug
    curve((598, 766), (592, 748), (605, 734), (598, 718), width=1.8, jitter=0.4)
    curve((610, 766), (618, 744), (605, 728), (612, 712), width=1.8, jitter=0.4)

    # Ruler
    polygon([(430, 778), (575, 774), (577, 790), (432, 794)], fill=LIGHT_GRAY, width=1.5)
    for tick in range(450, 568, 12):
        line([(tick, 778), (tick, 785)], width=1.0, jitter=0.0)

    # ══ Character – lower left, slumped but head tilted UP toward TV ══
    # Body: rounded teal bean, seated, slightly hunched forward
    shape(
        [
            ((60, 580), (45, 640), (50, 810), (85, 870)),
            ((85, 870), (125, 900), (275, 896), (308, 862)),
            ((308, 862), (338, 800), (330, 640), (310, 582)),
            ((310, 582), (260, 550), (110, 548), (60, 580)),
        ],
        fill=PALE_TEAL,
        width=4.2,
    )

    # Face: oval, tilted upward (head raised to look at TV)
    # Positioned slightly upper and angled right
    oval((78, 370, 300, 590), phase=0.8, fill=WHITE, width=3.8)

    # Hair strokes (4 short lines from crown)
    for x_off, dy in [(-5, 0), (14, -9), (34, -12), (52, -6)]:
        bx = 128 + x_off
        by = 395 + dy
        curve((bx, by), (bx-1, by-14), (bx+2, by-28), (bx+4, by-40), width=2.8)

    # Expression: eyes wide open (surprise/alert), mouth slightly open
    # Eyes – large round, looking upward
    oval((100, 440, 158, 490), phase=0.3, fill=WHITE, width=3.0)
    oval((180, 432, 238, 482), phase=0.5, fill=WHITE, width=3.0)
    # Pupils (positioned upward in eye socket – looking up)
    oval((112, 443, 136, 467), phase=0.2, fill=(*INK, 255), width=1.5)
    oval((192, 436, 216, 460), phase=0.4, fill=(*INK, 255), width=1.5)
    # Small highlight dots
    oval((130, 444, 138, 452), phase=0.0, fill=WHITE, width=1.0)
    oval((210, 437, 218, 445), phase=0.0, fill=WHITE, width=1.0)

    # Eyebrows – slightly raised in mild surprise
    line([(100, 430), (155, 422)], width=2.5, jitter=0.15)
    line([(178, 420), (233, 428)], width=2.5, jitter=0.15)

    # Mouth: small open 'o' (mid-surprise, drowsy)
    oval((152, 528, 188, 555), phase=0.6, fill=WHITE, width=2.5)

    # Tired eye-bag lines under eyes (all-nighter detail)
    line([(100, 490), (158, 486)], width=1.5, jitter=0.1)
    line([(180, 484), (238, 488)], width=1.5, jitter=0.1)

    # Tie
    polygon([(165, 600), (193, 600), (202, 624), (180, 644), (157, 624)], fill=MUSTARD, width=2.0)
    polygon([(180, 644), (195, 695), (180, 716), (165, 695)], fill=MUSTARD, width=2.2)

    # Left arm: resting limp on desk papers
    shape(
        [
            ((58, 650), (40, 670), (42, 745), (56, 775)),
            ((56, 775), (76, 790), (118, 786), (134, 772)),
            ((134, 772), (140, 745), (138, 672), (122, 652)),
            ((122, 652), (105, 638), (70, 638), (58, 650)),
        ],
        fill=PALE_TEAL,
        width=3.0,
    )
    oval((45, 768, 98, 794), phase=0.4, fill=PALE_TEAL, width=2.0)

    # Right arm: also on desk, slightly bent
    shape(
        [
            ((300, 648), (328, 668), (334, 744), (318, 772)),
            ((318, 772), (295, 787), (258, 782), (242, 768)),
            ((242, 768), (235, 742), (236, 668), (256, 648)),
            ((256, 648), (272, 636), (292, 637), (300, 648)),
        ],
        fill=PALE_TEAL,
        width=3.0,
    )
    oval((238, 766, 322, 790), phase=0.5, fill=PALE_TEAL, width=2.0)

    # ── Gaze direction line (subtle arc from character eyes toward TV) ──
    # Dashed line is hard to do; instead draw a very faint dotted arc
    for i in range(6):
        t = i / 5
        ox = 220 + t * (510 - 220)
        oy = 455 + t * (215 - 455)
        color_draw.ellipse([px((ox-3, oy-3)), px((ox+3, oy+3))], fill=(180, 160, 140, 120))

    # ── Shock effect lines from face (upper-right direction toward TV) ──
    for angle_deg, r0, r1 in [
        (330, 62, 95), (348, 58, 88), (8, 60, 92), (28, 55, 82),
    ]:
        angle = math.radians(angle_deg)
        cx_h, cy_h = 192, 458
        line(
            [(cx_h + math.cos(angle)*r0, cy_h + math.sin(angle)*r0),
             (cx_h + math.cos(angle)*r1, cy_h + math.sin(angle)*r1)],
            width=2.0, jitter=0.5,
        )

    # ── Extra: distant background shelf/bracket the TV sits on ──
    polygon([(305, 408), (715, 406), (718, 428), (306, 430)], fill=WARM_GRAY, width=2.5)

    output = Path(__file__).with_name('010-control.png')
    color_output = Path(__file__).with_name('010-color.png')
    line_image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(output)
    color_image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(color_output)
    print(output)
    print(color_output)


if __name__ == '__main__':
    main()
