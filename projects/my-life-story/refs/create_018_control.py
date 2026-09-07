"""Create textless line and flat-color guides for episode 018."""
import json,math,random
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).resolve().parent
cfg=json.loads((ROOT/'config/manga.json').read_text(encoding='utf-8'))['comfy']; W,H=cfg['width'],cfg['height']; S=4
rng=random.Random(20011801); line=Image.new('RGB',(W*S,H*S),'white'); color=Image.new('RGBA',line.size); d=ImageDraw.Draw(line); c=ImageDraw.Draw(color)
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
# Local gray emotional shadow.
for i in range(120):
    x=155+(i*43)%235; y=455+(i*67)%370
    if ((x-275)/128)**2+((y-635)/190)**2<1:
        r=1+(i%3)*.35; c.ellipse([pt((x-r,y-r)),pt((x+r,y+r))],fill=(198,194,190,150))
# Frozen protagonist.
oval(286,698,55,128,.5,(157,202,201,255)); oval(284,514,57,80,.7,(255,255,255,255))
for x in (269,284,299): stroke([(x,447),(x+1,430)],2.5,.1)
stroke([(267,519),(267,524)],3.3,.05); stroke([(300,519),(300,524)],3.3,.05); stroke([(278,552),(289,552)],2,.05)
poly([(275,598),(293,599),(289,632),(281,638),(276,630)],(214,183,80,255),1.7)
# Receiver and gripping arm are outlined shapes, not skeletal limbs.
poly([(221,465),(238,452),(255,474),(249,489),(235,485),(221,512),(207,506),(211,480)],(220,186,70,255),2.5)
stroke([(244,612),(231,580),(233,500)],3); stroke([(250,613),(246,574),(244,500)],2.5)
stroke([(319,616),(329,650),(330,681)],2.5)
# Trembling marks.
for x,y in [(197,532),(208,560),(354,550),(365,585),(202,670),(363,700)]: stroke([(x-7,y-5),(x+5,y),(x-6,y+6)],1.8,.1)
# Desk and one simplified monitor with abstract drawing lines only.
stroke([(400,699),(674,700)],2.6); stroke([(427,700),(427,810)],2.2); stroke([(650,700),(650,810)],2.2)
poly([(442,460),(650,461),(648,626),(443,624)],(232,229,226,255),2.8)
stroke([(545,625),(545,677)],2.3); stroke([(496,678),(592,678)],2.3)
stroke([(472,505),(520,550),(571,490),(621,565)],1.8,.12); stroke([(475,584),(615,584)],1.4,.1); stroke([(500,600),(590,600)],1.4,.1)
line.resize((W,H),Image.Resampling.LANCZOS).save(HERE/'018-control.png'); color.resize((W,H),Image.Resampling.LANCZOS).save(HERE/'018-color.png')
