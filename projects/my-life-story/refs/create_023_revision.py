"""Textless control and color guides: work, sleeping baby, and a worried parent."""
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
def polygon(points, fill, width=2.5):
    d.polygon([pt(p) for p in points], fill='white')
    c.polygon([pt(p) for p in points], fill=fill)
    stroke(points, width, closed=True)


gray = (224,222,218,255)
teal = (157,202,201,255)
yellow = (216,188,105,255)
white = (255,255,255,255)
# Desk, blank monitor and an unmistakable small keyboard.
stroke([(471,757),(700,759),(696,777),(474,776)], 2.7, closed=True)
stroke([(680,777),(679,915)], 2.6)
polygon([(569,569),(683,572),(682,675),(568,672)], gray)
polygon([(579,580),(672,582),(671,661),(578,659)], white, 1.9)
stroke([(624,674),(624,704),(646,704),(603,704)], 2.5)
polygon([(563,716),(664,720),(677,739),(551,735)], gray, 2)
polygon([(491,714),(542,711),(550,744),(495,745)], white, 1.8)
# Father: his hand stays at work while his gaze drops toward the crib.
oval(443,732,61,143,0.6,teal)
oval(424,527,55,71,1.2,white)
for x,y in ((401,463),(418,455),(435,458)):
    stroke([(x,y+5),(x+2,y-13)], 2.5)
stroke([(391,522),(401,518)], 2)
stroke([(419,522),(429,526)], 2)
stroke([(392,538),(393,542)], 2.8)
stroke([(419,542),(420,546)], 2.8)
stroke([(400,567),(409,563),(418,567)], 1.9)
polygon([(475,514),(481,529),(477,537),(470,535),(469,530)], white, 1.8)
polygon([(429,612),(444,613),(441,642),(435,649),(429,640)], yellow, 1.8)
polygon([(476,653),(487,659),(513,709),(529,719),(522,730),(499,719)], teal, 2.4)
stroke([(398,656),(387,698),(390,712),(400,714),(406,667)], 2.5)
# Crib, pillow and swaddled infant. The visible rails identify the relationship.
stroke([(105,777),(105,934),(109,956)], 2.6)
stroke([(334,780),(336,933),(331,956)], 2.6)
stroke([(106,811),(333,813)], 2.3)
oval(166,822,42,29,0.5,white)
oval(173,801,28,31,1.4,white)
oval(246,829,51,35,0.4,yellow)
stroke([(161,800),(168,803),(172,800)], 1.8)
stroke([(180,805),(186,807),(190,804)], 1.8)
stroke([(171,818),(178,820)], 1.6)
stroke([(218,805),(243,822),(218,845)], 1.9)
polygon([(103,865),(337,867),(337,882),(104,880)], gray, 2.7)
stroke([(105,932),(335,934)], 2.5)
for x in (131,175,219,263,307):
    stroke([(x,881),(x+1,932)], 2)

line.resize((W,H),Image.Resampling.LANCZOS).save(HERE/'023-control.png')
color.resize((W,H),Image.Resampling.LANCZOS).save(HERE/'023-color.png')
