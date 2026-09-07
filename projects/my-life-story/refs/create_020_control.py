"""Create textless line and flat-color guides for episode 020."""
import json,math,random
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).resolve().parent; cfg=json.loads((ROOT/'config/manga.json').read_text(encoding='utf-8'))['comfy']
W,H=cfg['width'],cfg['height']; S=4; rng=random.Random(20012001); line=Image.new('RGB',(W*S,H*S),'white'); color=Image.new('RGBA',line.size); d=ImageDraw.Draw(line); c=ImageDraw.Draw(color)
def pt(p): return round(p[0]*W/768*S),round(p[1]*H/1024*S)
def stroke(ps,w=2.8,j=.25,closed=False):
    src=ps+([ps[0]] if closed else []); out=[]
    for k,(a,b) in enumerate(zip(src,src[1:])):
        n=max(2,round(math.dist(a,b)/5))
        for i in range(n):
            if k and not i: continue
            t=i/n; e=math.sin(math.pi*t); out.append((a[0]+(b[0]-a[0])*t+rng.uniform(-j,j)*e,a[1]+(b[1]-a[1])*t+rng.uniform(-j,j)*e))
    out.append(src[-1]); d.line([pt(p) for p in out],fill=(28,27,26),width=round(w*S),joint='curve')
def oval(cx,cy,rx,ry,phase,fill):
    ps=[]
    for i in range(90):
        a=math.tau*i/90; q=1+.024*math.sin(3*a+phase)+.01*math.sin(7*a); ps.append((cx+rx*q*math.cos(a),cy+ry*q*math.sin(a)))
    d.polygon([pt(p) for p in ps],fill='white'); c.polygon([pt(p) for p in ps],fill=fill); stroke(ps,3,.32,True)
def poly(ps,fill,w=2.3): d.polygon([pt(p) for p in ps],fill='white'); c.polygon([pt(p) for p in ps],fill=fill); stroke(ps,w,.2,True)
stroke([(42,43),(724,44),(722,980),(44,981),(42,43)],2,1)
# Workload shadow behind the young designer.
for i in range(90):
    x=110+(i*41)%250; y=500+(i*61)%300
    if ((x-225)/125)**2+((y-645)/175)**2<1:
        r=1+(i%3)*.35; c.ellipse([pt((x-r,y-r)),pt((x+r,y+r))],fill=(198,194,190,140))
# Young designer holding blank binders.
oval(207,698,49,113,.5,(157,202,201,255)); oval(205,536,51,71,.7,(255,255,255,255))
for x in (191,205,219): stroke([(x,475),(x+1,460)],2.5,.1)
stroke([(190,540),(190,544)],3,.05); stroke([(220,540),(220,544)],3,.05); stroke([(198,568),(207,570)],2,.05)
poly([(196,610),(211,611),(209,638),(202,644),(197,636)],(214,183,80,255),1.7)
poly([(126,603),(232,593),(240,753),(136,762)],(232,229,226,255),2.4); poly([(145,580),(250,571),(258,733),(240,753),(232,593)],(220,186,70,255),2.4)
stroke([(177,636),(190,671),(226,686)],2.7); stroke([(235,636),(224,671),(197,689)],2.7)
# Older president happily programming.
oval(500,704,58,119,.2,(201,198,193,255)); oval(500,531,57,73,.4,(255,255,255,255))
stroke([(472,515),(483,510)],3.2,.08); stroke([(512,510),(524,515)],3.2,.08); stroke([(477,537),(477,541)],3,.05); stroke([(522,537),(522,541)],3,.05); stroke([(487,564),(500,570),(515,562)],2.4,.08)
# Computer and keyboard; display has abstract blocks only.
poly([(580,410),(700,411),(699,548),(581,547)],(232,229,226,255),2.8); stroke([(640,548),(640,613)],2.2); stroke([(606,613),(675,613)],2.2)
for x,y,w in [(596,442,36),(640,442,45),(596,470,72),(596,498,45),(650,498,34)]: c.rectangle([pt((x,y)),pt((x+w,y+9))],fill=(157,202,201,255))
poly([(426,652),(576,652),(597,681),(409,681)],(255,255,255,255),2.0)
stroke([(466,635),(452,652),(436,664)],2.7); stroke([(535,635),(548,650),(568,662)],2.7); stroke([(402,682),(710,683)],2.5); stroke([(428,683),(428,802)],2.2); stroke([(682,683),(682,802)],2.2)
line.resize((W,H),Image.Resampling.LANCZOS).save(HERE/'020-control.png'); color.resize((W,H),Image.Resampling.LANCZOS).save(HERE/'020-color.png')
