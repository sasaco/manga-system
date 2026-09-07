"""Create the textless line and flat-color guides for episode 017."""
import json, math, random
from pathlib import Path
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
cfg=json.loads((ROOT/'config/manga.json').read_text(encoding='utf-8'))['comfy']
W,H=cfg['width'],cfg['height']; S=4; rng=random.Random(20011701)
line=Image.new('RGB',(W*S,H*S),'white'); color=Image.new('RGBA',line.size)
d=ImageDraw.Draw(line); c=ImageDraw.Draw(color)
def pt(p): return round(p[0]*W/768*S),round(p[1]*H/1024*S)
def stroke(ps,w=2.8,j=.28,closed=False):
    src=ps+([ps[0]] if closed else []); out=[]
    for k,(a,b) in enumerate(zip(src,src[1:])):
        n=max(2,round(math.dist(a,b)/5))
        for i in range(n):
            if k and not i: continue
            t=i/n; e=math.sin(math.pi*t)
            out.append((a[0]+(b[0]-a[0])*t+rng.uniform(-j,j)*e,a[1]+(b[1]-a[1])*t+rng.uniform(-j,j)*e))
    out.append(src[-1]); d.line([pt(p) for p in out],fill=(28,27,26),width=round(w*S),joint='curve')
def oval(cx,cy,rx,ry,phase,fill):
    ps=[]
    for i in range(90):
        a=math.tau*i/90; q=1+.024*math.sin(3*a+phase)+.01*math.sin(7*a)
        ps.append((cx+rx*q*math.cos(a),cy+ry*q*math.sin(a)))
    d.polygon([pt(p) for p in ps],fill='white'); c.polygon([pt(p) for p in ps],fill=fill); stroke(ps,3,.32,True)
def poly(ps,fill,w=2.3):
    d.polygon([pt(p) for p in ps],fill='white'); c.polygon([pt(p) for p in ps],fill=fill); stroke(ps,w,.2,True)

stroke([(42,43),(724,44),(722,980),(44,981),(42,43)],2,1)
# Warm-gray local tone marks the admired craft, while the rest remains empty.
for i in range(100):
    x=430+(i*47)%238; y=470+(i*71)%310
    if ((x-550)/135)**2+((y-625)/190)**2<1:
        r=1+(i%3)*.35; c.ellipse([pt((x-r,y-r)),pt((x+r,y+r))],fill=(198,194,190,135))
# Observer, deliberately small and separated.
oval(174,665,38,97,.5,(157,202,201,255)); oval(176,536,43,61,.7,(255,255,255,255))
for x in (163,176,189): stroke([(x,483),(x+1,470)],2.4,.1)
stroke([(164,541),(164,544)],3,.05); stroke([(187,541),(187,544)],3,.05); stroke([(170,566),(177,568)],2,.05)
poly([(166,599),(181,600),(177,627),(170,627)],(214,183,80,255),1.7)
poly([(105,641),(145,637),(148,715),(106,717)],(220,186,70,255),2.2)
stroke([(145,650),(157,664),(163,677)],2.5); stroke([(204,652),(211,666),(219,672)],2.5)
# Two disciplined rounded craftspeople.
oval(485,668,48,107,.2,(201,198,193,255)); oval(480,515,49,66,.6,(255,255,255,255))
oval(612,669,48,108,.9,(157,202,201,255)); oval(611,514,49,66,.1,(255,255,255,255))
for cx in (480,611):
    stroke([(cx-23,464),(cx-16,452),(cx-8,463)],2.5,.1); stroke([(cx-12,522),(cx-12,525)],3,.05); stroke([(cx+12,522),(cx+12,525)],3,.05); stroke([(cx-4,547),(cx+4,547)],2,.05)
# Short outlined arm gestures converge on a single blank sheet.
stroke([(451,629),(467,648),(512,674),(518,668),(482,640),(468,621)],2.6)
stroke([(582,624),(570,648),(536,672),(542,678),(580,655),(593,631)],2.6)
stroke([(389,690),(680,689)],2.5,.22); stroke([(415,689),(416,784)],2.2); stroke([(655,689),(654,784)],2.2)
poly([(474,657),(584,655),(601,686),(459,686)],(255,255,255,255),1.8)
stroke([(490,666),(566,665)],1.5,.08); stroke([(510,675),(578,674)],1.5,.08)
poly([(526,649),(534,649),(568,681),(560,683)],(220,186,70,255),1.5)
line.resize((W,H),Image.Resampling.LANCZOS).save(HERE/'017-control.png')
color.resize((W,H),Image.Resampling.LANCZOS).save(HERE/'017-color.png')
