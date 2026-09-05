# -*- coding: utf-8 -*-
import io
import subprocess
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from PIL import Image, ImageOps

REPO_ROOT = Path('.').resolve()
PROJECT_DIR = REPO_ROOT / 'projects' / 'my-life-story'
TEMPLATE_ORA = REPO_ROOT / 'templates' / 'krita' / 'instagram-portrait.ora'
KRITA_EXE = Path('C:/Program Files/Krita (x64)/bin/krita.com')

SELECTED_ART = PROJECT_DIR / 'panels' / 'selected' / '009.png'
LINE_ART = PROJECT_DIR / 'refs' / '009-control.png'
COLOR_ART = PROJECT_DIR / 'refs' / '009-color.png'
BALLOON_ART = PROJECT_DIR / 'refs' / '009-balloon.png'
LETTERING_ART = PROJECT_DIR / 'refs' / '009-lettering.png'

KRA_OUTPUT = PROJECT_DIR / 'pages' / '009.kra'
EXPORT_OUTPUT = PROJECT_DIR / 'export' / '009.png'

def png_bytes(image: Image.Image) -> bytes:
    output = io.BytesIO()
    image.save(output, format='PNG')
    return output.getvalue()

def fit_art(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    fitted = ImageOps.contain(image.convert('RGBA'), size, Image.Resampling.LANCZOS)
    canvas = Image.new('RGBA', size, (0, 0, 0, 0))
    left = (size[0] - fitted.width) // 2
    top = (size[1] - fitted.height) // 2
    canvas.alpha_composite(fitted, (left, top))
    return canvas

def fit_line_art(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    gray = ImageOps.grayscale(image)
    fitted = ImageOps.contain(gray, size, Image.Resampling.LANCZOS)
    alpha = ImageOps.invert(fitted)
    canvas = Image.new('RGBA', size, (0, 0, 0, 0))
    ink = Image.new('RGBA', fitted.size, (0, 0, 0, 255))
    ink.putalpha(alpha)
    canvas.alpha_composite(ink, ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2))
    return canvas

def main():
    with zipfile.ZipFile(TEMPLATE_ORA) as source:
        entries = {item.filename: source.read(item) for item in source.infolist()}
        infos = source.infolist()

    stack = ET.fromstring(entries['stack.xml'])
    size = (int(stack.attrib['w']), int(stack.attrib['h']))
    layers = {
        element.attrib.get('name'): element
        for element in stack.iter('layer')
        if 'src' in element.attrib
    }

    ai_layer = fit_art(Image.open(SELECTED_ART), size)
    line_layer = fit_line_art(Image.open(LINE_ART), size)
    color_layer = fit_art(Image.open(COLOR_ART), size)
    balloon_layer = fit_art(Image.open(BALLOON_ART), size)
    lettering_layer = fit_art(Image.open(LETTERING_ART), size)

    layers['AI素材'].set('visibility', 'hidden')

    color_element = layers['トーン・色']
    line_element = layers['線画']
    color_parent = next(parent for parent in stack.iter('stack') if color_element in list(parent))
    line_parent = next(parent for parent in stack.iter('stack') if line_element in list(parent))
    color_parent.remove(color_element)
    line_index = list(line_parent).index(line_element)
    line_parent.insert(line_index + 1, color_element)
    color_element.set('composite-op', 'svg:src-over')

    # Reorder text & balloon
    text_element = layers['文字']
    balloon_element = layers['フキダシ']
    text_parent = next(parent for parent in stack.iter('stack') if text_element in list(parent))
    if text_element in list(text_parent) and balloon_element in list(text_parent):
        text_parent.remove(text_element)
        text_parent.remove(balloon_element)
        text_parent.insert(0, text_element)
        text_parent.insert(1, balloon_element)

    paper = Image.open(io.BytesIO(entries['data/paper.png'])).convert('RGBA')
    merged = paper
    merged = Image.alpha_composite(merged, color_layer)
    merged = Image.alpha_composite(merged, line_layer)
    merged = Image.alpha_composite(merged, balloon_layer)
    merged = Image.alpha_composite(merged, lettering_layer)

    thumbnail_size = Image.open(io.BytesIO(entries['Thumbnails/thumbnail.png'])).size
    thumbnail = ImageOps.contain(merged, thumbnail_size, Image.Resampling.LANCZOS)
    thumbnail_canvas = Image.new('RGBA', thumbnail_size, (255, 255, 255, 255))
    thumbnail_canvas.alpha_composite(
        thumbnail,
        ((thumbnail_size[0] - thumbnail.width) // 2, (thumbnail_size[1] - thumbnail.height) // 2),
    )

    replacements = {
        layers['AI素材'].attrib['src']: png_bytes(ai_layer),
        layers['線画'].attrib['src']: png_bytes(line_layer),
        layers['トーン・色'].attrib['src']: png_bytes(color_layer),
        layers['フキダシ'].attrib['src']: png_bytes(balloon_layer),
        layers['文字'].attrib['src']: png_bytes(lettering_layer),
        'stack.xml': ET.tostring(stack, encoding='utf-8', xml_declaration=True),
        'mergedimage.png': png_bytes(merged),
        'Thumbnails/thumbnail.png': png_bytes(thumbnail_canvas),
    }

    temp_ora = PROJECT_DIR / 'pages' / '.009.final.ora'
    temp_kra = PROJECT_DIR / 'pages' / '.009.final.kra'

    with zipfile.ZipFile(temp_ora, 'w') as target:
        for info in infos:
            target.writestr(info, replacements.get(info.filename, entries[info.filename]))

    print('Converting ORA to KRA via Krita...')
    subprocess.run([
        str(KRITA_EXE), str(temp_ora), '--nosplash', '--export', '--export-filename', str(temp_kra)
    ], check=True)

    if temp_kra.exists():
        if KRA_OUTPUT.exists():
            KRA_OUTPUT.unlink()
        temp_kra.replace(KRA_OUTPUT)
        temp_ora.unlink(missing_ok=True)
        print(f'Created KRA manuscript: {KRA_OUTPUT}')

    print('Exporting final image via Krita...')
    EXPORT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        str(KRITA_EXE), str(KRA_OUTPUT), '--nosplash', '--export', '--export-filename', str(EXPORT_OUTPUT)
    ], check=True)
    print(f'Exported: {EXPORT_OUTPUT}')

if __name__ == '__main__':
    main()
