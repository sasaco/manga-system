from pathlib import Path
import io
import zipfile
from xml.etree import ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(r"C:\Users\sasai\Documents\manga-system")
PROJECT_DIR = REPO_ROOT / "projects" / "my-life-story"

def create_lettering_images(canvas_size=(1080, 1350)):
    w, h = canvas_size
    text_img = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    bubble_img = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    
    draw_text = ImageDraw.Draw(text_img)
    draw_bubble = ImageDraw.Draw(bubble_img)
    
    # 吹き出しの配置位置 (右上余白: X: 450~950, Y: 120~380)
    box = [450, 120, 950, 380]
    
    # 吹き出し（白ベタ＋太い輪郭）
    draw_bubble.ellipse(box, fill=(255, 255, 255, 250), outline=(35, 35, 35, 255), width=6)
    
    # 吹き出しのしっぽ（左下・主人公に向かう）
    tail_points = [(580, 350), (520, 460), (660, 370)]
    draw_bubble.polygon(tail_points, fill=(255, 255, 255, 250))
    draw_bubble.line([(580, 350), (520, 460)], fill=(35, 35, 35, 255), width=6)
    draw_bubble.line([(520, 460), (660, 370)], fill=(35, 35, 35, 255), width=6)
    
    # テキスト描画 (Meiryo / Yu Gothic)
    font_path = "C:\\Windows\\Fonts\\meiryo.ttc"
    try:
        font = ImageFont.truetype(font_path, 36)
    except Exception:
        font = ImageFont.load_default()
        
    lines = ["意味を付け直すのは、", "自分なんだ。"]
    
    y_offset = 200
    for line in lines:
        bbox = draw_text.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x_pos = 700 - text_w // 2
        draw_text.text((x_pos, y_offset), line, fill=(35, 35, 35, 255), font=font)
        y_offset += 60

    return text_img, bubble_img

def update_ora_and_kra():
    text_img, bubble_img = create_lettering_images()
    
    template_ora_path = PROJECT_DIR / "pages" / ".016_interchange.ora"
    
    selected_png = PROJECT_DIR / "panels" / "selected" / "016.png"
    art_img = Image.open(selected_png).convert("RGBA")
    
    fitted_art = Image.new("RGBA", (1080, 1350), (255, 255, 255, 255))
    left = (1080 - art_img.width) // 2
    top = (1350 - art_img.height) // 2
    fitted_art.paste(art_img, (left, top))
    
    paper_img = Image.new("RGBA", (1080, 1350), (255, 255, 255, 255))
    
    merged = Image.alpha_composite(paper_img, fitted_art)
    merged = Image.alpha_composite(merged, bubble_img)
    merged = Image.alpha_composite(merged, text_img)
    
    stack_xml = """<?xml version="1.0" encoding="UTF-8"?>
<image w="1080" h="1350" version="0.0.3" xmlns="http://openraster.org/ns/layout">
 <stack composite-op="svg:src-over">
  <stack name="文字・フキダシ" composite-op="svg:src-over">
   <layer name="文字" src="data/text.png" composite-op="svg:src-over" x="0" y="0" opacity="1.0" visibility="visible"/>
   <layer name="フキダシ" src="data/bubble.png" composite-op="svg:src-over" x="0" y="0" opacity="1.0" visibility="visible"/>
  </stack>
  <stack name="仕上げ" composite-op="svg:src-over">
   <layer name="効果" src="data/effect.png" composite-op="svg:src-over" x="0" y="0" opacity="1.0" visibility="visible"/>
  </stack>
  <stack name="作画" composite-op="svg:src-over">
   <layer name="線画" src="data/line.png" composite-op="svg:src-over" x="0" y="0" opacity="1.0" visibility="visible"/>
   <layer name="トーン・色" src="data/color.png" composite-op="svg:src-over" x="0" y="0" opacity="1.0" visibility="visible"/>
   <layer name="AI素材" src="data/ai.png" composite-op="svg:src-over" x="0" y="0" opacity="1.0" visibility="visible"/>
  </stack>
  <stack name="下描き" composite-op="svg:src-over">
   <layer name="ラフ" src="data/rough.png" composite-op="svg:src-over" x="0" y="0" opacity="1.0" visibility="visible"/>
  </stack>
  <layer name="用紙" src="data/paper.png" composite-op="svg:src-over" x="0" y="0" opacity="1.0" visibility="visible"/>
 </stack>
</image>
"""

    empty_img = Image.new("RGBA", (1080, 1350), (0, 0, 0, 0))
    
    def png_bytes(img):
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
        
    ora_files = {
        "mimetype": b"image/openraster",
        "stack.xml": stack_xml.encode("utf-8"),
        "mergedimage.png": png_bytes(merged),
        "Thumbnails/thumbnail.png": png_bytes(merged.resize((200, 250))),
        "data/paper.png": png_bytes(paper_img),
        "data/ai.png": png_bytes(fitted_art),
        "data/line.png": png_bytes(empty_img),
        "data/color.png": png_bytes(empty_img),
        "data/effect.png": png_bytes(empty_img),
        "data/rough.png": png_bytes(empty_img),
        "data/bubble.png": png_bytes(bubble_img),
        "data/text.png": png_bytes(text_img),
    }
    
    with zipfile.ZipFile(template_ora_path, "w") as z:
        for name, data in ora_files.items():
            z.writestr(name, data)
            
    print(f"Created interchange ORA: {template_ora_path}")

if __name__ == "__main__":
    update_ora_and_kra()
