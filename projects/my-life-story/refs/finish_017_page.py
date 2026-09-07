"""Finish episode 017 in separate Krita artwork, balloon, and text layers."""
import io, json, math, os, random, sys, tempfile, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from prepare_krita_page import prepare_page
P=ROOT/'projects/my-life-story'; HERE=P/'refs'; W,H=768,1024; S=4
INK=(29,28,27,255); rng=random.Random(20011702)

def png_bytes(im):
    out=io.BytesIO(); im.save(out,format='PNG'); return out.getvalue()
def fit(im,size):
    fitted=ImageOps.contain(im.convert('RGBA'),size,Image.Resampling.LANCZOS)
    out=Image.new('RGBA',size); out.alpha_composite(fitted,((size[0]-fitted.width)//2,(size[1]-fitted.height)//2)); return out
def px(p): return round(p[0]*S),round(p[1]*S)
def oval_points(box,phase):
    l,t,r,b=box; cx=(l+r)/2; cy=(t+b)/2; rx=(r-l)/2; ry=(b-t)/2; out=[]
    for i in range(100):
        a=math.tau*i/100; q=1+.018*math.sin(3*a+phase)+.008*math.sin(7*a)
        out.append((cx+rx*q*math.cos(a),cy+ry*q*math.sin(a)))
    return out
def wobble(draw,ps,w=3.4,closed=False):
    src=ps+([ps[0]] if closed else []); out=[]
    for k,(a,b) in enumerate(zip(src,src[1:])):
        n=max(2,round(math.dist(a,b)/6))
        for i in range(n):
            if k and not i: continue
            t=i/n; e=math.sin(math.pi*t)
            out.append((a[0]+(b[0]-a[0])*t+rng.uniform(-.6,.6)*e,a[1]+(b[1]-a[1])*t+rng.uniform(-.6,.6)*e))
    out.append(src[-1]); draw.line([px(p) for p in out],fill=INK,width=round(w*S),joint='curve')

balloon=Image.new('RGBA',(W*S,H*S)); bd=ImageDraw.Draw(balloon)
bubble=oval_points((95,80,665,375),.6); bd.polygon([px(p) for p in bubble],fill='white'); wobble(bd,bubble,3.5,True)
tail=[(205,345),(174,465),(285,353)]; bd.polygon([px(p) for p in tail],fill='white'); wobble(bd,tail,3.3,True)
letter=Image.new('RGBA',(W*S,H*S)); ld=ImageDraw.Draw(letter)
font=ImageFont.truetype('C:/Windows/Fonts/UDDigiKyokashoN-R.ttc',31*S,layout_engine=ImageFont.Layout.BASIC)
for y,text in [(170,'すごいな…'),(235,'でも僕には'),(300,'マネできない。')]:
    ld.text(px((380,y)),text,font=font,fill=INK,anchor='mm')
balloon=balloon.resize((W,H),Image.Resampling.LANCZOS); letter=letter.resize((W,H),Image.Resampling.LANCZOS)
balloon.save(HERE/'017-balloon.png'); letter.save(HERE/'017-lettering.png')
base=Image.new('RGBA',(W,H),'white')
for name in ['017-color.png','017-control.png','017-balloon.png','017-lettering.png']:
    base=Image.alpha_composite(base,Image.open(HERE/name).convert('RGBA'))
base.save(HERE/'017-preview.png')

settings=json.loads((P/'project.json').read_text(encoding='utf-8'))
ora=P/'pages/.017-finished-v2.ora'
prepare_page(ROOT/'templates/krita'/settings['page_template'],P/'panels/selected/017.png',ora,line_art=HERE/'017-control.png',color_art=HERE/'017-color.png')
with zipfile.ZipFile(ora) as z: data={n:z.read(n) for n in z.namelist()}
stack=ET.fromstring(data['stack.xml']); size=(int(stack.get('w')),int(stack.get('h')))
layers={e.get('name'):e for e in stack.iter('layer') if e.get('src')}
data[layers['文字'].get('src')]=png_bytes(fit(letter,size)); data[layers['フキダシ'].get('src')]=png_bytes(fit(balloon,size))
text_layer=layers['文字']; parent=next(e for e in stack.iter('stack') if text_layer in list(e)); parent.remove(text_layer); parent.insert(0,text_layer)
data['stack.xml']=ET.tostring(stack,encoding='utf-8',xml_declaration=True)
fd,tmp_name=tempfile.mkstemp(dir=ora.parent,suffix='.ora'); os.close(fd); tmp=Path(tmp_name)
try:
    with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
        for name,payload in data.items(): z.writestr(name,payload)
    tmp.replace(ora)
finally: tmp.unlink(missing_ok=True)
print(ora)
