"""Finish episode 020 using separate Krita artwork, balloon, and text layers."""
import io,json,math,os,random,sys,tempfile,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from PIL import Image,ImageDraw,ImageFont,ImageOps
ROOT=Path(__file__).resolve().parents[3]; sys.path.insert(0,str(ROOT/'scripts'))
from prepare_krita_page import prepare_page
P=ROOT/'projects/my-life-story'; HERE=P/'refs'; W,H=768,1024; S=4; INK=(29,28,27,255); rng=random.Random(20012002)
def png(im): out=io.BytesIO(); im.save(out,format='PNG'); return out.getvalue()
def fit(im,size):
    a=ImageOps.contain(im.convert('RGBA'),size,Image.Resampling.LANCZOS); out=Image.new('RGBA',size); out.alpha_composite(a,((size[0]-a.width)//2,(size[1]-a.height)//2)); return out
def px(p): return round(p[0]*S),round(p[1]*S)
def oval(box,phase):
    l,t,r,b=box; cx=(l+r)/2; cy=(t+b)/2; rx=(r-l)/2; ry=(b-t)/2; out=[]
    for i in range(100):
        a=math.tau*i/100; q=1+.02*math.sin(3*a+phase)+.008*math.sin(7*a); out.append((cx+rx*q*math.cos(a),cy+ry*q*math.sin(a)))
    return out
def wobble(draw,ps,w=3.6,closed=False):
    src=ps+([ps[0]] if closed else []); out=[]
    for k,(a,b) in enumerate(zip(src,src[1:])):
        n=max(2,round(math.dist(a,b)/6))
        for i in range(n):
            if k and not i: continue
            t=i/n; e=math.sin(math.pi*t); out.append((a[0]+(b[0]-a[0])*t+rng.uniform(-.65,.65)*e,a[1]+(b[1]-a[1])*t+rng.uniform(-.65,.65)*e))
    out.append(src[-1]); draw.line([px(p) for p in out],fill=INK,width=round(w*S),joint='curve')
balloon=Image.new('RGBA',(W*S,H*S)); bd=ImageDraw.Draw(balloon); bubble=oval((85,80,615,350),.6)
bd.polygon([px(p) for p in bubble],fill='white'); wobble(bd,bubble,3.7,True)
tail=[(188,325),(203,454),(282,335)]; bd.polygon([px(p) for p in tail],fill='white'); wobble(bd,tail,3.4,True)
letter=Image.new('RGBA',(W*S,H*S)); ld=ImageDraw.Draw(letter); font=ImageFont.truetype('C:/Windows/Fonts/UDDigiKyokashoN-R.ttc',36*S,layout_engine=ImageFont.Layout.BASIC)
ld.text(px((350,185)),'僕は、',font=font,fill=INK,anchor='mm'); ld.text(px((350,270)),'設計要員。',font=font,fill=INK,anchor='mm')
balloon=balloon.resize((W,H),Image.Resampling.LANCZOS); letter=letter.resize((W,H),Image.Resampling.LANCZOS); balloon.save(HERE/'020-balloon.png'); letter.save(HERE/'020-lettering.png')
preview=Image.new('RGBA',(W,H),'white'); preview=Image.alpha_composite(preview,Image.open(HERE/'020-color.png').convert('RGBA'))
gray=ImageOps.grayscale(Image.open(HERE/'020-control.png')); ink=Image.new('RGBA',(W,H),(0,0,0,255)); ink.putalpha(ImageOps.invert(gray)); preview=Image.alpha_composite(preview,ink); preview=Image.alpha_composite(preview,balloon); preview=Image.alpha_composite(preview,letter); preview.save(HERE/'020-preview.png')
settings=json.loads((P/'project.json').read_text(encoding='utf-8')); ora=P/'pages/.020-finished.ora'
prepare_page(ROOT/'templates/krita'/settings['page_template'],P/'panels/selected/020.png',ora,line_art=HERE/'020-control.png',color_art=HERE/'020-color.png')
with zipfile.ZipFile(ora) as z: data={n:z.read(n) for n in z.namelist()}
stack=ET.fromstring(data['stack.xml']); size=int(stack.get('w')),int(stack.get('h')); layers={e.get('name'):e for e in stack.iter('layer') if e.get('src')}
data[layers['文字'].get('src')]=png(fit(letter,size)); data[layers['フキダシ'].get('src')]=png(fit(balloon,size)); text=layers['文字']; parent=next(e for e in stack.iter('stack') if text in list(e)); parent.remove(text); parent.insert(0,text); data['stack.xml']=ET.tostring(stack,encoding='utf-8',xml_declaration=True)
fd,name=tempfile.mkstemp(dir=ora.parent,suffix='.ora'); os.close(fd); tmp=Path(name)
try:
    with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
        for key,payload in data.items(): z.writestr(key,payload)
    tmp.replace(ora)
finally: tmp.unlink(missing_ok=True)
print(ora)
