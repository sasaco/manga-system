# -*- coding: utf-8 -*-
from __future__ import annotations
import math, random
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
GROUND_BROWN = (235, 228, 218, 255)
WHITE = (255, 255, 255, 255)
SWEAT_BLUE = (180, 215, 235, 255)
LEATHER_BROWN = (195, 140, 75, 255)
RNG = random.Random(20011202)

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
    color_draw.rectangle([px((44, 44)), px((723, 979))], fill=(250, 249, 246, 255))

    # ══ Baseball Ground ══
    polygon([(45, 750), (722, 710), (722, 980), (45, 980)], fill=GROUND_BROWN, width=2.8)
    # Mound slope in distance
    curve((460, 480), (550, 455), (650, 460), (722, 475), width=2.2, jitter=0.2)
    # Home plate near foreground
    polygon([(210, 915), (265, 915), (280, 940), (238, 960), (195, 940)], fill=WHITE, width=2.2)

    # ══ Distant Pitcher (small bean figure on mound, off-balance after throwing wild pitch) ══
    # Mound dirt base
    oval((520, 455, 660, 485), phase=0.2, fill=WARM_GRAY, width=1.8)
    # Pitcher body (rounded bean, no stick legs)
    shape([
        ((570, 385), (585, 375), (615, 380), (620, 405)),
        ((620, 405), (625, 440), (615, 465), (595, 470)),
        ((595, 470), (575, 470), (565, 450), (565, 420)),
        ((565, 420), (565, 395), (568, 388), (570, 385)),
    ], fill=WARM_GRAY, width=2.4)
    # Pitcher head
    oval((575, 330, 612, 372), phase=0.3, fill=WHITE, width=2.2)
    # Pitcher cap (tilted wildly)
    polygon([(570, 338), (610, 330), (626, 335), (600, 348)], fill=MUSTARD, width=1.8)
    # Pitcher throwing arm (short outlined gesture)
    shape([
        ((570, 395), (540, 415), (515, 435), (495, 450)),
        ((495, 450), (495, 442), (515, 420), (548, 390)),
    ], fill=WARM_GRAY, width=1.8)
    # Pitcher other arm
    shape([
        ((615, 395), (635, 385), (648, 380), (655, 385)),
        ((655, 385), (650, 395), (635, 400), (615, 405)),
    ], fill=WARM_GRAY, width=1.8)
    # Pitcher sweat mark
    oval((625, 320, 634, 332), phase=0.1, fill=SWEAT_BLUE, width=1.4)

    # ══ Wild Ball Trajectory (dramatic curving speed lines) ══
    curve((490, 450), (410, 520), (310, 580), (210, 630), width=3.0, jitter=0.3)
    curve((485, 460), (395, 540), (290, 605), (190, 655), width=2.0, jitter=0.2)
    curve((495, 440), (420, 500), (330, 560), (240, 610), width=1.8, jitter=0.2)
    # Wind speed dashes
    line([(370, 520), (330, 550)], width=1.6, jitter=0.1)
    line([(280, 580), (240, 610)], width=1.6, jitter=0.1)

    # ══ The Ball & Giant Mitt Interaction ══
    # The catcher lunges to the left, arm extended, mitt wide open.
    # The ball is right at the lip of the mitt, about to be trapped!

    # Mitt (catcher's glove) - positioned at (105, 620) to (210, 740)
    shape([
        ((115, 635), (145, 610), (195, 620), (210, 665)),
        ((210, 665), (215, 715), (185, 755), (135, 760)),
        ((135, 760), (98, 735), (95, 685), (115, 635)),
    ], fill=LEATHER_BROWN, width=3.8)
    # Mitt inner pocket
    oval((125, 635, 185, 725), phase=0.4, fill=(160, 105, 45, 255), width=2.6)
    # Webbing details
    line([(145, 620), (150, 665)], width=2.0, jitter=0.1)
    line([(168, 625), (170, 670)], width=2.0, jitter=0.1)
    line([(135, 645), (185, 650)], width=2.0, jitter=0.1)

    # The baseball (tucked into top-left of the mitt pocket, motion blur lines)
    oval((140, 625, 180, 665), phase=0.0, fill=WHITE, width=2.8)
    curve((148, 633), (153, 645), (153, 653), (148, 659), width=1.6, jitter=0.1)
    curve((172, 633), (167, 645), (167, 653), (172, 659), width=1.6, jitter=0.1)
    # Impact lines around ball/mitt
    line([(125, 615), (110, 600)], width=2.4, jitter=0.1)
    line([(155, 605), (155, 585)], width=2.4, jitter=0.1)
    line([(190, 610), (205, 595)], width=2.4, jitter=0.1)
    line([(110, 655), (90, 655)], width=2.2, jitter=0.1)

    # ══ Protagonist Body (Catcher diving/lunging left) ══
    # Dust puffs under feet
    oval((450, 875, 530, 915), phase=0.8, fill=LIGHT_GRAY, width=2.0)
    oval((490, 855, 560, 895), phase=0.5, fill=LIGHT_GRAY, width=2.0)
    oval((360, 895, 420, 930), phase=0.3, fill=LIGHT_GRAY, width=1.8)

    # Main bean body (rounded, leaning left)
    shape([
        ((270, 710), (320, 660), (410, 670), (460, 720)),
        ((460, 720), (510, 770), (520, 840), (480, 890)),
        ((480, 890), (420, 920), (340, 900), (290, 840)),
        ((290, 840), (250, 790), (240, 740), (270, 710)),
    ], fill=PALE_TEAL, width=4.2)

    # Chest Protector / Vest (mustard yellow, clean curved straps)
    shape([
        ((295, 715), (340, 705), (410, 710), (445, 740)),
        ((445, 740), (455, 790), (435, 840), (395, 860)),
        ((395, 860), (330, 845), (285, 810), (275, 765)),
        ((275, 765), (275, 735), (285, 720), (295, 715)),
    ], fill=MUSTARD, width=3.0)
    # Center tie-like strap
    polygon([(355, 708), (370, 708), (368, 855), (357, 855)], fill=(225, 175, 40, 255), width=1.8)
    # Protector cushion lines
    curve((305, 755), (350, 760), (390, 758), (430, 750), width=2.0)
    curve((295, 795), (345, 802), (385, 800), (420, 790), width=2.0)

    # Legs: absorbed into body, shin guard on right leg
    curve((470, 850), (530, 880), (550, 920), (510, 935), width=3.2)
    shape([
        ((485, 870), (530, 890), (545, 915), (530, 935)),
        ((530, 935), (490, 925), (475, 900), (485, 870)),
    ], fill=WARM_GRAY, width=2.2)
    # Left foot planted
    curve((300, 880), (280, 915), (260, 940), (230, 945), width=3.0)

    # Right arm (flung back for balance)
    shape([
        ((445, 725), (485, 715), (530, 710), (560, 690)),
        ((560, 690), (565, 705), (530, 735), (485, 750)),
        ((485, 750), (455, 755), (440, 740), (445, 725)),
    ], fill=PALE_TEAL, width=3.2)
    oval((555, 680, 585, 705), phase=0.2, fill=WHITE, width=2.2)

    # Left arm (stretching all the way out to mitt)
    shape([
        ((270, 730), (230, 710), (195, 695), (170, 690)),
        ((170, 690), (165, 715), (200, 730), (245, 755)),
        ((245, 755), (270, 755), (275, 745), (270, 730)),
    ], fill=PALE_TEAL, width=3.6)

    # ══ Protagonist Head ══
    # Large oval face, tilted forward-left
    oval((260, 515, 435, 705), phase=0.6, fill=WHITE, width=4.0)

    # Cap / Helmet
    polygon([(280, 545), (340, 510), (425, 535), (445, 570), (405, 590), (330, 560), (280, 545)], fill=PALE_TEAL, width=2.8)
    polygon([(425, 535), (460, 520), (470, 538), (440, 555)], fill=MUSTARD, width=2.2)

    # Hair strokes under cap
    for x_off, dy in [(-15, 5), (5, -3), (25, -6), (45, 0)]:
        bx = 310 + x_off
        by = 560 + dy
        curve((bx, by), (bx - 5, by + 12), (bx - 12, by + 22), (bx - 18, by + 30), width=2.8)

    # Eyebrows (intense determination / strain)
    line([(305, 605), (345, 595)], width=3.4, jitter=0.15)
    line([(370, 598), (410, 612)], width=3.4, jitter=0.15)

    # Eyes (locked on ball)
    oval((308, 608, 342, 642), phase=0.2, fill=WHITE, width=3.0)
    oval((368, 612, 402, 646), phase=0.4, fill=WHITE, width=3.0)
    oval((310, 616, 326, 634), phase=0.1, fill=(*INK, 255), width=1.6)
    oval((370, 620, 386, 638), phase=0.3, fill=(*INK, 255), width=1.6)
    oval((314, 620, 320, 626), phase=0.0, fill=WHITE, width=1.0)
    oval((374, 624, 380, 630), phase=0.0, fill=WHITE, width=1.0)

    line([(305, 648), (338, 648)], width=1.8, jitter=0.1)
    line([(370, 652), (403, 652)], width=1.8, jitter=0.1)

    # Clenched teeth
    polygon([(335, 665), (385, 668), (380, 686), (340, 683)], fill=WHITE, width=2.4)
    line([(336, 674), (383, 676)], width=1.8, jitter=0.1)
    line([(352, 666), (351, 684)], width=1.4, jitter=0.1)
    line([(367, 667), (366, 685)], width=1.4, jitter=0.1)

    # Flying sweat droplets
    oval((245, 585, 262, 610), phase=0.3, fill=SWEAT_BLUE, width=1.8)
    line([(253, 575), (245, 590)], width=1.6, jitter=0.1)
    line([(253, 575), (262, 590)], width=1.6, jitter=0.1)
    oval((265, 555, 276, 570), phase=0.2, fill=SWEAT_BLUE, width=1.4)
    oval((420, 625, 432, 641), phase=0.4, fill=SWEAT_BLUE, width=1.4)
    oval((435, 650, 444, 663), phase=0.1, fill=SWEAT_BLUE, width=1.2)

    # Motion lines behind lunging dive
    line([(490, 760), (550, 770)], width=2.4, jitter=0.15)
    line([(500, 790), (575, 805)], width=2.6, jitter=0.15)
    line([(475, 830), (560, 845)], width=2.4, jitter=0.15)
    line([(450, 865), (530, 880)], width=2.0, jitter=0.15)

    # Warm-gray emotional stipple
    for _ in range(85):
        sx = RNG.randint(380, 520)
        sy = RNG.randint(620, 820)
        color_draw.ellipse([px((sx-2, sy-2)), px((sx+2, sy+2))], fill=(190, 185, 180, 135))

    out_line = Path('projects/my-life-story/refs/012-control.png')
    out_color = Path('projects/my-life-story/refs/012-color.png')
    line_image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(out_line)
    color_image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(out_color)
    print('Done:', out_line, out_color)

if __name__ == '__main__':
    main()
