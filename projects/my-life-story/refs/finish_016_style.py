"""Preserve existing Krita lettering; no text is rendered or authored here."""
import sys
import zipfile
import json
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'scripts'))
from prepare_krita_page import prepare_page

P = ROOT/'projects/my-life-story'
settings=json.loads((P/'project.json').read_text(encoding='utf-8'))
output=P/'pages/.016-style-finish.ora'
prepare_page(ROOT/'templates/krita'/settings['page_template'], P/'panels/selected/016.png', output,
             line_art=P/'refs/016-control.png',color_art=P/'refs/016-color.png')
with zipfile.ZipFile(output) as z:
    data={n:z.read(n) for n in z.namelist()}
stack=ET.fromstring(data['stack.xml'])
with zipfile.ZipFile(P/'backups/016-before-style-fix-20260907/original.ora') as old:
    oldstack=ET.fromstring(old.read('stack.xml'))
    for name in ['文字','フキダシ']:
        source=next(e for e in oldstack.iter('layer') if e.get('name')==name)
        target=next(e for e in stack.iter('layer') if e.get('name')==name)
        data[target.get('src')]=old.read(source.get('src'))
        target.set('x',str(int(source.get('x','0'))-100))
        target.set('y',str(int(source.get('y','0'))+100))
text_layer=next(e for e in stack.iter('layer') if e.get('name')=='文字')
parent=next(e for e in stack.iter('stack') if text_layer in list(e))
parent.remove(text_layer)
parent.insert(0,text_layer)
data['stack.xml']=ET.tostring(stack,encoding='utf-8',xml_declaration=True)
with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
    for name,payload in data.items(): z.writestr(name,payload)
print(output)
