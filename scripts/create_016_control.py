from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageOps
import random
import math

def create_016_control_image():
    # 768 x 1024 or 1080 x 1350 Canvas (matching standard 4:5 aspect ratio)
    width, height = 768, 1024
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    black = (20, 20, 20)
    line_w = 4
    
    # 1. 枠線 (Border)
    draw.rectangle([40, 40, width - 40, height - 40], outline=black, width=5)
    
    # 2. 主人公「僕」の線画 (Bean body character sitting at desk in thought)
    # 頭部 (楕円) Center around (384, 450)
    head_box = [310, 360, 458, 510]
    draw.ellipse(head_box, outline=black, width=line_w)
    
    # 髪の毛 (頭頂部に短い縦線4本)
    hair_x = [350, 370, 390, 410]
    for x in hair_x:
        draw.line([(x, 362), (x + 3, 335)], fill=black, width=line_w)
        
    # 目（下を見つめる点/短線）
    draw.ellipse([350, 440, 356, 448], fill=black)
    draw.ellipse([410, 440, 416, 448], fill=black)
    
    # 口（小さな思索の短線）
    draw.line([(378, 475), (390, 477)], fill=black, width=3)
    
    # 胴体 (丸い豆形/カプセル体)
    # (300, 500) から (468, 780) に向けて丸いビーンシルエット
    draw.arc([290, 500, 478, 780], 0, 360, fill=black, width=line_w)
    
    # ネクタイ (胸元)
    knot = [374, 510, 394, 530]
    draw.ellipse(knot, outline=black, width=3)
    tie = [(374, 525), (368, 620), (384, 645), (400, 620), (394, 525)]
    draw.polygon(tie, outline=black, fill=None, width=3)
    
    # 手/腕 (デスクに置かれた丸い手の仕草)
    # 左腕
    draw.arc([270, 560, 340, 680], 90, 270, fill=black, width=line_w)
    # 右腕
    draw.arc([420, 560, 490, 680], 270, 90, fill=black, width=line_w)
    
    # 3. シンプルなデスクの線
    draw.line([(200, 680), (568, 680)], fill=black, width=line_w) # デスク天板
    draw.line([(240, 680), (240, 850)], fill=black, width=line_w) # 脚左
    draw.line([(528, 680), (528, 850)], fill=black, width=line_w) # 脚右
    
    # 保存
    output_path = Path(r"C:\Users\sasai\Documents\manga-system\projects\my-life-story\refs\016-control.png")
    img.save(output_path)
    print(f"Created control line-art: {output_path}")

if __name__ == "__main__":
    create_016_control_image()
