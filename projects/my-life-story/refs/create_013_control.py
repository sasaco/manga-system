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
WHITE = (255, 255, 255, 255)
NORI_BLACK = (35, 38, 36, 255)
RICE_WHITE = (250, 250, 248, 255)
ASHTRAY_GRAY = (180, 178, 175, 255)
SMOKE_GRAY = (210, 208, 205, 160)
RNG = random.Random(20011301)

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
    color_draw.rectangle([px((44, 44)), px((723, 979))], fill=(249, 248, 245, 255))

    # ══ Office chair behind character ══
    oval((80, 520, 160, 770), phase=0.2, fill=WARM_GRAY, width=2.8)
    line([(120, 770), (120, 880)], width=4.0, jitter=0.2)

    # ══ Desk surface ══
    polygon([(50, 710), (715, 700), (718, 850), (48, 855)], fill=LIGHT_GRAY, width=3.2)
    # Desk legs
    line([(85, 855), (82, 970)], width=3.5, jitter=0.2)
    line([(665, 850), (668, 970)], width=3.5, jitter=0.2)

    # ══ CRT Monitor on right (indicating desk-bound office work) ══
    polygon([(480, 420), (670, 410), (695, 445), (510, 455)], fill=(215, 212, 209, 255), width=2.2)
    polygon([(670, 410), (695, 445), (685, 700), (660, 670)], fill=(195, 192, 188, 255), width=2.2)
    polygon([(460, 450), (670, 445), (660, 705), (450, 710)], fill=WARM_GRAY, width=3.5)
    polygon([(475, 470), (650, 465), (642, 680), (467, 685)], fill=(40, 45, 42, 255), width=2.5)
    polygon([(520, 708), (600, 706), (610, 735), (510, 737)], fill=WARM_GRAY, width=2.4)

    # Papers / calculation files stacked near monitor
    polygon([(620, 705), (695, 700), (692, 755), (618, 760)], fill=WHITE, width=1.8)
    polygon([(620, 695), (695, 690), (695, 705), (620, 710)], fill=WARM_GRAY, width=1.4)
    line([(630, 725), (680, 720)], width=1.0, jitter=0.1)

    # ══ Ashtray on desk (foreground right of character) ══
    oval((380, 745, 465, 790), phase=0.4, fill=ASHTRAY_GRAY, width=2.8)
    oval((392, 752, 452, 782), phase=0.2, fill=(140, 138, 135, 255), width=1.8)
    polygon([(360, 760), (405, 765), (403, 773), (358, 768)], fill=WHITE, width=1.6)
    polygon([(358, 768), (372, 770), (370, 777), (356, 775)], fill=(210, 155, 90, 255), width=1.2)
    oval((402, 763, 408, 771), phase=0.0, fill=(230, 80, 50, 255), width=1.0)
    oval((415, 760, 435, 775), phase=0.5, fill=(100, 98, 95, 255), width=1.0)

    # Cigarette smoke wisps
    curve((405, 760), (415, 710), (395, 650), (420, 580), width=2.0, jitter=0.3)
    curve((408, 755), (425, 690), (405, 630), (435, 560), width=1.5, jitter=0.3)

    # ══ Food items on desk ══
    oval((485, 755, 560, 805), phase=0.5, fill=(230, 185, 120, 255), width=2.4)
    polygon([(470, 770), (488, 755), (490, 795), (472, 800)], fill=(240, 240, 240, 200), width=1.4)
    polygon([(555, 760), (575, 775), (570, 805), (552, 795)], fill=(240, 240, 240, 200), width=1.4)

    # ══ Character: Protagonist (入社したら太りました) ══
    # Noticeably plump, rounded bean body!
    shape([
        ((140, 560), (190, 520), (330, 530), (390, 590)),
        ((390, 590), (435, 660), (440, 770), (390, 840)),
        ((390, 840), (320, 885), (200, 875), (130, 810)),
        ((130, 810), (105, 720), (115, 620), (140, 560)),
    ], fill=PALE_TEAL, width=4.2)

    # Plump belly curve contour
    curve((180, 780), (250, 810), (330, 805), (380, 760), width=2.2, jitter=0.15)

    # Mustard yellow necktie – tight over plump belly
    polygon([(245, 595), (275, 595), (282, 618), (260, 632), (238, 618)], fill=MUSTARD, width=2.0)
    polygon([(260, 632), (280, 700), (268, 740), (252, 740), (245, 700)], fill=MUSTARD, width=2.2)

    # Left arm (resting on belly)
    shape([
        ((145, 630), (130, 670), (145, 740), (180, 775)),
        ((180, 775), (230, 785), (270, 775), (285, 755)),
        ((285, 755), (265, 740), (220, 745), (185, 730)),
        ((185, 730), (170, 675), (165, 635), (145, 630)),
    ], fill=PALE_TEAL, width=3.2)

    # Right arm (holding an onigiri near mouth)
    shape([
        ((350, 620), (380, 645), (385, 700), (365, 730)),
        ((365, 730), (345, 740), (320, 725), (315, 695)),
        ((315, 695), (330, 655), (340, 625), (350, 620)),
    ], fill=PALE_TEAL, width=3.0)
    oval((295, 605, 335, 640), phase=0.2, fill=WHITE, width=2.0)

    # Big Onigiri
    polygon([(290, 625), (330, 575), (355, 630)], fill=RICE_WHITE, width=2.8)
    polygon([(302, 605), (332, 595), (342, 630), (312, 630)], fill=NORI_BLACK, width=2.0)
    curve((325, 575), (328, 582), (335, 582), (338, 575), width=2.0)

    # Protagonist Head (chubby face)
    oval((185, 380, 365, 575), phase=0.5, fill=WHITE, width=4.0)
    curve((230, 570), (275, 585), (320, 570), (340, 555), width=2.4, jitter=0.15)

    # Hair strokes
    for x_off, dy in [(-12, 3), (8, -6), (28, -9), (48, -4)]:
        bx = 245 + x_off
        by = 398 + dy
        curve((bx, by), (bx+2, by-14), (bx+7, by-24), (bx+10, by-34), width=2.8)

    # Eyebrows (relaxed, enjoying eating)
    curve((220, 450), (240, 442), (255, 446), (265, 455), width=2.6, jitter=0.15)
    curve((285, 455), (295, 446), (310, 442), (330, 450), width=2.6, jitter=0.15)

    # Eyes: happy, chewing (ニコニコ)
    curve((225, 475), (242, 465), (255, 475), (262, 482), width=3.2, jitter=0.15)
    curve((288, 482), (295, 475), (308, 465), (325, 475), width=3.2, jitter=0.15)

    # Cheeks blush
    oval((210, 495, 235, 515), phase=0.3, fill=(255, 210, 200, 180), width=1.0)
    oval((315, 495, 340, 515), phase=0.3, fill=(255, 210, 200, 180), width=1.0)

    # Mouth: chewing happily (もぐもぐ)
    shape([
        ((260, 520), (275, 510), (295, 512), (305, 528)),
        ((305, 528), (295, 545), (275, 545), (260, 535)),
        ((260, 535), (255, 528), (258, 522), (260, 520)),
    ], fill=(220, 110, 100, 255), width=2.2)
    # Rice grain on cheek
    oval((308, 535, 316, 545), phase=0.1, fill=WHITE, width=1.4)

    # Chew motion lines
    line([(325, 525), (338, 522)], width=1.8, jitter=0.1)
    line([(328, 535), (342, 535)], width=1.8, jitter=0.1)

    # Sweat drop (acknowledging getting fat)
    oval((190, 445, 205, 470), phase=0.2, fill=(180, 215, 235, 255), width=1.6)

    # Warm-gray stipple tone behind character
    for _ in range(60):
        sx = RNG.randint(110, 200)
        sy = RNG.randint(580, 750)
        color_draw.ellipse([px((sx-2, sy-2)), px((sx+2, sy+2))], fill=(190, 185, 180, 120))

    out_line = Path('projects/my-life-story/refs/013-control.png')
    out_color = Path('projects/my-life-story/refs/013-color.png')
    line_image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(out_line)
    color_image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(out_color)
    print('Done:', out_line, out_color)

if __name__ == '__main__':
    main()