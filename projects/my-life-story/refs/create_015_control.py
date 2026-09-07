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
DARK_GRAY = (100, 98, 95, 255)
RNG = random.Random(20011501)

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

    # ══ Background: Streetlight on left ══
    polygon([(100, 300), (120, 300), (125, 880), (95, 880)], fill=WARM_GRAY, width=2.5)
    oval((75, 270, 145, 310), phase=0.2, fill=DARK_GRAY, width=2.0)
    # Light beam polygon
    color_draw.polygon([px((110, 300)), px((30, 880)), px((320, 880))], fill=(255, 250, 210, 90))

    # ══ Background: Station Clock (pointing to 23:45 / Late Night) ══
    clock_cx, clock_cy = 600, 320
    clock_r = 75
    oval((clock_cx - clock_r, clock_cy - clock_r, clock_cx + clock_r, clock_cy + clock_r), phase=0.0, fill=WHITE, width=3.0)
    # Clock marks
    for m in range(12):
        ang = m * math.pi / 6
        x1 = clock_cx + (clock_r - 12) * math.cos(ang)
        y1 = clock_cy + (clock_r - 12) * math.sin(ang)
        x2 = clock_cx + (clock_r - 4) * math.cos(ang)
        y2 = clock_cy + (clock_r - 4) * math.sin(ang)
        line([(x1, y1), (x2, y2)], width=1.8, jitter=0.1)
    # Hands: 23:45 (Short hand near 11/12, Long hand at 9)
    line([(clock_cx, clock_cy), (clock_cx - 15, clock_cy - 40)], width=3.2, jitter=0.1) # Hour hand
    line([(clock_cx, clock_cy), (clock_cx - 50, clock_cy - 5)], width=2.5, jitter=0.1)  # Minute hand
    oval((clock_cx - 6, clock_cy - 6, clock_cx + 6, clock_cy + 6), phase=0.0, fill=DARK_GRAY, width=1.5)

    # ══ Character: Exhausted Protagonist Walking ══
    # Slouched, rounded bean body
    shape([
        ((250, 500), (300, 470), (430, 490), (480, 560)),
        ((480, 560), (510, 660), (500, 780), (450, 840)),
        ((450, 840), (370, 880), (270, 860), (220, 780)),
        ((220, 780), (210, 680), (225, 570), (250, 500)),
    ], fill=PALE_TEAL, width=4.2)

    # Slouched posture contour
    curve((280, 750), (350, 780), (420, 770), (460, 730), width=2.0, jitter=0.15)

    # Mustard Tie hanging loosely
    polygon([(350, 540), (380, 540), (385, 565), (365, 580), (345, 565)], fill=MUSTARD, width=2.0)
    polygon([(365, 580), (375, 650), (360, 710), (345, 710), (342, 650)], fill=MUSTARD, width=2.2)

    # Left arm: Hanging limply
    shape([
        ((250, 560), (220, 600), (215, 680), (230, 720)),
        ((230, 720), (255, 725), (265, 690), (255, 620)),
        ((255, 620), (260, 580), (255, 565), (250, 560)),
    ], fill=PALE_TEAL, width=3.0)

    # Right arm: Carrying business bag drooping
    shape([
        ((460, 580), (500, 620), (490, 710), (465, 740)),
        ((465, 740), (440, 740), (430, 700), (440, 640)),
        ((440, 640), (455, 600), (455, 585), (460, 580)),
    ], fill=PALE_TEAL, width=3.0)

    # Business Bag (drooping low)
    polygon([(440, 730), (530, 720), (525, 830), (435, 840)], fill=MUSTARD, width=3.0)
    # Bag handle
    curve((465, 730), (475, 695), (495, 695), (505, 725), width=2.5, jitter=0.1)

    # Protagonist Head (drooping forward, exhausted face)
    oval((290, 330, 470, 520), phase=0.5, fill=WHITE, width=4.0)

    # Hair strokes (drooping)
    for x_off, dy in [(-12, 5), (8, 0), (28, -3), (48, 2)]:
        bx = 355 + x_off
        by = 345 + dy
        curve((bx, by), (bx+2, by-14), (bx+7, by-24), (bx+10, by-34), width=2.8)

    # Eyebrows (drooping exhausted / 疲れた八の字)
    curve((330, 425), (345, 415), (360, 420), (370, 430), width=2.6, jitter=0.15)
    curve((390, 430), (400, 420), (415, 415), (430, 425), width=2.6, jitter=0.15)

    # Eyes: Tired / closed curves (疲労感のある半目)
    curve((335, 450), (350, 442), (365, 452), (370, 458), width=3.0, jitter=0.15)
    curve((395, 458), (400, 452), (415, 442), (430, 450), width=3.0, jitter=0.15)

    # Mouth: Exhausted sigh / line (はぁ…とため息)
    curve((365, 485), (380, 490), (395, 485), (405, 480), width=2.5, jitter=0.15)

    # Exhaustion mark (縦のハッチング線 / 疲労感影)
    for hx in range(355, 415, 12):
        line([(hx, 460), (hx - 4, 475)], width=1.5, jitter=0.1)

    # Warm-gray stipple tone around feet and background
    for _ in range(60):
        sx = RNG.randint(180, 550)
        sy = RNG.randint(750, 870)
        color_draw.ellipse([px((sx-2, sy-2)), px((sx+2, sy+2))], fill=(190, 185, 180, 120))

    out_line = Path('projects/my-life-story/refs/015-control.png')
    out_color = Path('projects/my-life-story/refs/015-color.png')
    line_image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(out_line)
    color_image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(out_color)
    print('Done:', out_line, out_color)

if __name__ == '__main__':
    main()
