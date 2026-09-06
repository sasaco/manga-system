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
RNG = random.Random(20011401)

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

    # ══ Background: Faint Ship Steering Wheel (船長の象徴) ══
    wheel_cx, wheel_cy = 540, 500
    wheel_r = 130
    oval((wheel_cx - wheel_r, wheel_cy - wheel_r, wheel_cx + wheel_r, wheel_cy + wheel_r), phase=0.0, fill=LIGHT_GRAY, width=2.0)
    oval((wheel_cx - wheel_r*0.65, wheel_cy - wheel_r*0.65, wheel_cx + wheel_r*0.65, wheel_cy + wheel_r*0.65), phase=0.1, fill=WHITE, width=1.5)
    oval((wheel_cx - 20, wheel_cy - 20, wheel_cx + 20, wheel_cy + 20), phase=0.0, fill=WARM_GRAY, width=2.0)
    # Spokes of ship wheel
    for spk in range(8):
        ang = spk * math.pi / 4
        x1 = wheel_cx + 20 * math.cos(ang)
        y1 = wheel_cy + 20 * math.sin(ang)
        x2 = wheel_cx + (wheel_r + 30) * math.cos(ang)
        y2 = wheel_cy + (wheel_r + 30) * math.sin(ang)
        line([(x1, y1), (x2, y2)], width=2.2, jitter=0.1)

    # ══ Character: Protagonist ══
    # Plump rounded bean body
    shape([
        ((220, 520), (270, 480), (400, 490), (460, 550)),
        ((460, 550), (490, 640), (495, 750), (450, 830)),
        ((450, 830), (380, 880), (270, 870), (200, 800)),
        ((200, 800), (180, 700), (195, 580), (220, 520)),
    ], fill=PALE_TEAL, width=4.2)

    # Belly contour curve
    curve((250, 770), (330, 800), (400, 790), (440, 750), width=2.0, jitter=0.15)

    # Mustard tie
    polygon([(325, 550), (355, 550), (362, 575), (340, 590), (318, 575)], fill=MUSTARD, width=2.0)
    polygon([(340, 590), (360, 660), (348, 700), (332, 700), (325, 660)], fill=MUSTARD, width=2.2)

    # Left arm: Scratching back of head embarrassedly
    shape([
        ((220, 580), (170, 550), (160, 460), (200, 410)),
        ((200, 410), (230, 400), (240, 440), (210, 470)),
        ((210, 470), (195, 520), (225, 560), (240, 590)),
    ], fill=PALE_TEAL, width=3.2)

    # Right arm: Holding thick calculation binders
    shape([
        ((440, 600), (490, 630), (480, 710), (450, 740)),
        ((450, 740), (410, 750), (390, 720), (400, 680)),
        ((400, 680), (430, 650), (420, 620), (440, 600)),
    ], fill=PALE_TEAL, width=3.0)

    # ══ Thick Calculation Books / Binders in arm ══
    polygon([(340, 620), (490, 600), (510, 760), (360, 785)], fill=WHITE, width=3.2)
    polygon([(340, 620), (360, 625), (380, 790), (360, 785)], fill=WARM_GRAY, width=2.5)
    polygon([(490, 600), (515, 595), (535, 755), (510, 760)], fill=MUSTARD, width=2.2)
    # Binder spine details & lines (標題: 構造計算書)
    line([(370, 650), (470, 635)], width=2.0, jitter=0.1)
    line([(370, 680), (460, 665)], width=1.5, jitter=0.1)
    line([(370, 710), (450, 695)], width=1.5, jitter=0.1)

    # ══ Protagonist Head (embarrassed / bashful face) ══
    oval((265, 330, 445, 525), phase=0.5, fill=WHITE, width=4.0)

    # Hair strokes
    for x_off, dy in [(-12, 3), (8, -6), (28, -9), (48, -4)]:
        bx = 325 + x_off
        by = 348 + dy
        curve((bx, by), (bx+2, by-14), (bx+7, by-24), (bx+10, by-34), width=2.8)

    # Eyebrows (embarrassed / slanting downward)
    curve((305, 410), (320, 400), (335, 405), (345, 415), width=2.6, jitter=0.15)
    curve((365, 415), (375, 405), (390, 400), (405, 410), width=2.6, jitter=0.15)

    # Eyes: Embarrassed / awkward grin (>< or dot with sweat drop)
    curve((308, 435), (325, 428), (340, 438), (345, 442), width=3.0, jitter=0.15)
    curve((368, 442), (375, 438), (390, 428), (408, 435), width=3.0, jitter=0.15)

    # Awkward smile mouth
    curve((330, 475), (355, 485), (380, 480), (395, 468), width=2.8, jitter=0.15)

    # Sweat drop (acknowledging past embarrassment "カンチガイヤローでした")
    oval((270, 395, 288, 425), phase=0.2, fill=(180, 215, 235, 255), width=1.6)

    # Warm-gray stipple tone behind character
    for _ in range(50):
        sx = RNG.randint(160, 250)
        sy = RNG.randint(550, 720)
        color_draw.ellipse([px((sx-2, sy-2)), px((sx+2, sy+2))], fill=(190, 185, 180, 120))

    out_line = Path('projects/my-life-story/refs/014-control.png')
    out_color = Path('projects/my-life-story/refs/014-color.png')
    line_image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(out_line)
    color_image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(out_color)
    print('Done:', out_line, out_color)

if __name__ == '__main__':
    main()
