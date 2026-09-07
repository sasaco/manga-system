"""Episode 016's native drawing guide: sparse irregular contours and flat fills."""
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
cfg = json.loads((ROOT / 'config/manga.json').read_text(encoding='utf-8'))['comfy']
W, H = cfg['width'], cfg['height']
S = 3
line = Image.new('RGB', (W*S, H*S), 'white')
color = Image.new('RGBA', line.size)
d, c = ImageDraw.Draw(line), ImageDraw.Draw(color)

def points(ps):
    return [(round(x*W/768*S), round(y*H/1024*S)) for x,y in ps]

def stroke(ps, width=2.7):
    d.line(points(ps), fill=(28,27,26), width=round(width*S), joint='curve')

def oval(cx,cy,rx,ry,phase,fill):
    ps=[]
    for i in range(121):
        a=i/120*math.tau
        k=1+.025*math.sin(3*a+phase)+.012*math.sin(5*a)
        ps.append((cx+rx*k*math.cos(a),cy+ry*k*math.sin(a)))
    d.polygon(points(ps),fill='white')
    c.polygon(points(ps),fill=fill)
    stroke(ps)

stroke([(42,43),(724,44),(722,980),(44,981),(42,43)],2)
# Local emotional tone, never a colored background or a cast shadow.
for i in range(47):
    x=302+((i*29)%69); y=539+((i*43)%153)
    if ((x-335)/37)**2+((y-610)/85)**2<1:
        c.ellipse(points([(x,y),(x+1.4,y+1.4)]),fill=(195,190,187,255))
oval(385,699,37,100,.8,(157,202,201,255))
oval(389,552,45,67,.4,(255,255,255,255))
for x,y in [(373,492),(385,487),(397,490)]:
    stroke([(x,y+6),(x-1,y-7),(x+1,y-15)],2.5)
stroke([(393,559),(393,563)],3)
stroke([(412,558),(412,562)],3)
stroke([(402,586),(408,587)],2)
c.polygon(points([(379,622),(387,623),(389,641),(384,647),(380,641)]),fill=(214,183,80,255))
stroke([(379,622),(387,623),(389,641),(384,647),(380,641),(379,622)],1.7)
# Short attached outlined arms; no separate line legs.
stroke([(355,664),(363,683),(386,695),(389,690),(371,677),(368,662)])
stroke([(418,663),(425,680),(410,694),(405,691),(417,677)])
stroke([(284,704),(342,703),(405,705),(490,704)],2.4)
stroke([(304,705),(305,782)],2.2)
stroke([(471,705),(470,781)],2.2)
line.resize((W,H),Image.Resampling.LANCZOS).save(HERE/'016-control.png')
color.resize((W,H),Image.Resampling.LANCZOS).save(HERE/'016-color.png')
