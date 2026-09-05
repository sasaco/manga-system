# -*- coding: utf-8 -*-
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

WIDTH = 768
HEIGHT = 1024
SCALE = 4
INK = (31, 30, 29, 255)
WHITE = (255, 255, 255, 255)
RNG = random.Random(20010915)

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
    left, top, right, bottom = bounds
    cx = (left + right) / 2
    cy = (top + bottom) / 2
    rx = (right - left) / 2
    ry = (bottom - top) / 2
    result = []
    for step in range(80):
        angle = math.tau * step / 80
        uneven = 1 + 0.016 * math.sin(3 * angle + phase)
        result.append((cx + rx * uneven * math.cos(angle), cy + ry * uneven * math.sin(angle)))
    return result

# Balloon: upper center, roomy
bubble = oval_points((205, 80, 555, 555), phase=0.7)
balloon_draw.polygon([px(p) for p in bubble], fill=WHITE)
wobble(bubble, width=4.0, jitter=0.75, closed=True, target=balloon_draw)

# Tail towards president at right (pointing to president mouth/gesture)
tail = [(505, 490), (548, 545), (525, 465)]
balloon_draw.polygon([px(p) for p in tail], fill=WHITE)
wobble(tail, width=3.8, jitter=0.5, closed=True, target=balloon_draw)

# Text: 3 vertical columns
font_path = 'C:/Windows/Fonts/UDDigiKyokashoN-R.ttc'
comic_font = ImageFont.truetype(font_path, 33 * SCALE, layout_engine=ImageFont.Layout.BASIC)

def vertical_text(text, x, y, spacing=38):
    for index, char in enumerate(text):
        lettering_draw.text(px((x, y + index * spacing)), char, font=comic_font, fill=INK, anchor='mm')

vertical_text('なんの指示がなくても', 470, 160, spacing=38)
vertical_text('自分で仕事を見つけて', 395, 160, spacing=38)
vertical_text('やれ！', 315, 245, spacing=44)

here = Path('projects/my-life-story/refs')
balloon_layer.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(here / '008-balloon.png')
lettering_layer.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(here / '008-lettering.png')

# Preview with line and color
line_img = Image.open(here / '008-control.png').convert('RGBA')
color_img = Image.open(here / '008-color.png').convert('RGBA')
base = Image.new('RGBA', (WIDTH, HEIGHT), (255, 255, 255, 255))
preview = Image.alpha_composite(base, color_img)
preview = Image.alpha_composite(preview, line_img)
preview = Image.alpha_composite(preview, balloon_layer.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS))
preview = Image.alpha_composite(preview, lettering_layer.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS))
preview.save(here / '008-preview.png')
print('Adjusted preview successfully')
