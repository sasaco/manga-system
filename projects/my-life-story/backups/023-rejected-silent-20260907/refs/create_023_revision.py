"""Textless control and flat-color guides: present-day parent and grown child."""
import json
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
cfg = json.loads((ROOT / 'config/manga.json').read_text(encoding='utf-8'))['comfy']
W, H = cfg['width'], cfg['height']
S = 4
rng = random.Random(2001232)
line = Image.new('RGB', (W*S, H*S), 'white')
color = Image.new('RGBA', line.size)
d, c = ImageDraw.Draw(line), ImageDraw.Draw(color)


def pt(p):
    return round(p[0]*W/768*S), round(p[1]*H/1024*S)


def stroke(points, width=2.8, closed=False):
    source = points + ([points[0]] if closed else [])
    out = []
    for a, b in zip(source, source[1:]):
        count = max(2, round(math.dist(a, b)/5))
        for i in range(count):
            t = i/count
            jitter = math.sin(math.pi*t)*rng.uniform(-0.35, 0.35)
            out.append(pt((a[0]+(b[0]-a[0])*t+jitter, a[1]+(b[1]-a[1])*t+jitter)))
    out.append(pt(source[-1]))
    d.line(out, fill=(28,27,26), width=round(width*S), joint='curve')


def oval(cx, cy, rx, ry, phase, fill):
    points = []
    for i in range(96):
        a = math.tau*i/96
        wobble = 1+0.024*math.sin(3*a+phase)+0.009*math.sin(7*a)
        points.append((cx+rx*wobble*math.cos(a), cy+ry*wobble*math.sin(a)))
    d.polygon([pt(p) for p in points], fill='white')
    c.polygon([pt(p) for p in points], fill=fill)
    stroke(points, 3, closed=True)


stroke([(42,43),(724,44),(722,980),(44,981),(42,43)], 2)
# Grown child: neutral clothing and features, no invented milestone props.
oval(287,641,57,171,0.4,(216,188,105,255))
oval(280,411,53,70,0.8,(255,255,255,255))
for x,y in ((257,351),(273,343),(289,344),(305,353)):
    stroke([(x,y+4),(x+2,y-13)], 2.6)
stroke([(285,412),(286,417)], 2.7)
stroke([(311,410),(312,415)], 2.7)
stroke([(290,438),(298,441),(306,438)], 1.8)
stroke([(248,520),(245,581),(253,594),(262,587),(265,533)], 2.4)
stroke([(327,518),(334,572),(329,585)], 2.2)
# Parent: gaze slightly upward, shoulders lowered, small quiet smile.
oval(491,674,64,140,0.6,(157,202,201,255))
oval(473,476,57,66,1.8,(255,255,255,255))
for x,y in ((451,417),(467,410),(484,413)):
    stroke([(x,y+3),(x+3,y-14)], 2.5)
stroke([(434,465),(435,470)], 2.7)
stroke([(459,460),(460,465)], 2.7)
stroke([(439,493),(446,499),(456,498),(462,492)], 1.9)
stroke([(434,576),(437,622),(445,633),(454,629),(451,589)], 2.4)
stroke([(532,586),(542,627),(538,639)], 2.2)

line.resize((W,H),Image.Resampling.LANCZOS).save(HERE/'023-control.png')
color.resize((W,H),Image.Resampling.LANCZOS).save(HERE/'023-color.png')
