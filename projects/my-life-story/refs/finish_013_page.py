# -*- coding: utf-8 -*-
import math, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

WIDTH = 768
HEIGHT = 1024
SCALE = 4
INK = (31, 30, 29, 255)
WHITE = (255, 255, 255, 255)
RNG = random.Random(20011306)

size = (WIDTH * SCALE, HEIGHT * SCALE)
balloon_layer = Image.new('RGBA', size, (0, 0, 0, 0))
lettering_layer = Image.new('RGBA', size, (0, 0, 0, 0))
balloon_draw = ImageDraw.Draw(balloon_layer)
lettering_draw = ImageDraw.Draw(lettering_layer)

def px(point):
    return round(point[0] * SCALE), round(point[1] * SCALE)

def wobble(points, width=4.0, jitter=0.7, closed=False, target=balloon_draw, fill=INK):
    source = points + ([points[0]] if closed else [])
    sampled = []
    for index, (start, end) in enumerate(zip(source, source[1:])):
        steps = max(2, round(math.dist(start, end) / 6))
        for step in range(steps):
            if index and step == 0:
                continue
            t = step / steps
            envelope = math.sin(math.pi * t)
            sampled.append((
                start[0] + (end[0] - start[0]) * t + RNG.uniform(-jitter, jitter) * envelope,
                start[1] + (end[1] - start[1]) * t + RNG.uniform(-jitter, jitter) * envelope,
            ))
    sampled.append(source[-1])
    target.line([px(p) for p in sampled], fill=fill, width=max(1, round(width * SCALE)), joint='curve')

def oval_points(bounds, phase):
    l, t, r, b = bounds
    cx, cy = (l + r) / 2, (t + b) / 2
    rx, ry = (r - l) / 2, (b - t) / 2
    result = []
    for step in range(80):
        angle = math.tau * step / 80
        uneven = 1 + 0.022 * math.sin(3 * angle + phase)
        result.append((cx + rx * uneven * math.cos(angle), cy + ry * uneven * math.sin(angle)))
    return result

# ── Balloon: slightly higher and broader ──
bubble = oval_points((105, 50, 525, 355), phase=0.8)
balloon_draw.polygon([px(p) for p in bubble], fill=WHITE)
wobble(bubble, width=4.2, jitter=0.75, closed=True, target=balloon_draw)

# Tail: pointing naturally toward protagonist's head
tail = [(250, 340), (285, 405), (315, 335)]
balloon_draw.polygon([px(p) for p in tail], fill=WHITE)
wobble(tail, width=3.8, jitter=0.50, closed=True, target=balloon_draw)

# ── Lettering ──
font_path = 'C:/Windows/Fonts/UDDigiKyokashoN-R.ttc'
bold_path = 'C:/Windows/Fonts/UDDigiKyokashoN-B.ttc'
reg_font  = ImageFont.truetype(font_path, 25 * SCALE, layout_engine=ImageFont.Layout.BASIC)
bold_font = ImageFont.truetype(bold_path, 28 * SCALE, layout_engine=ImageFont.Layout.BASIC)

def vertical_text(text, x, y, spacing=34, font=reg_font):
    for index, char in enumerate(text):
        lettering_draw.text(px((x, y + index * spacing)), char, font=font, fill=INK, anchor='mm')

# 3 columns, right-to-left
vertical_text('一日中座りっぱなし…', 420, 95, spacing=31, font=reg_font)
vertical_text('食べるのだけが', 315, 105, spacing=35, font=bold_font)
vertical_text('唯一の楽しみ…！', 210, 100, spacing=35, font=bold_font)

here = Path('projects/my-life-story/refs')
balloon_layer.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(here / '013-balloon.png')
lettering_layer.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(here / '013-lettering.png')

line_img = Image.open(here / '013-control.png').convert('RGBA')
color_img = Image.open(here / '013-color.png').convert('RGBA')
base = Image.new('RGBA', (WIDTH, HEIGHT), (255, 255, 255, 255))
preview = Image.alpha_composite(base, color_img)
preview = Image.alpha_composite(preview, line_img)
preview = Image.alpha_composite(preview, balloon_layer.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS))
preview = Image.alpha_composite(preview, lettering_layer.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS))
preview.save(here / '013-preview.png')
print('Updated 013-preview.png')