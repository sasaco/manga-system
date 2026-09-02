"""Create lightweight layered OpenRaster templates that Krita opens natively."""

from __future__ import annotations

import argparse
import struct
import zlib
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


RGBA = tuple[int, int, int, int]


def png(
    width: int, height: int, color: RGBA, *, dpi: int,
    rectangles: list[tuple[int, int, int, int, RGBA]] | None = None,
) -> bytes:
    rectangles = rectangles or []
    compressor = zlib.compressobj(9)
    compressed: list[bytes] = []
    for y in range(height):
        row = bytearray(color * width)
        for left, top, right, bottom, line_color in rectangles:
            if y in (top, bottom):
                for x in range(max(0, left), min(width, right + 1)):
                    row[x * 4 : x * 4 + 4] = bytes(line_color)
            elif top <= y <= bottom:
                for x in (left, right):
                    if 0 <= x < width:
                        row[x * 4 : x * 4 + 4] = bytes(line_color)
        compressed.append(compressor.compress(b"\x00" + row))
    compressed.append(compressor.flush())

    def chunk(kind: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(kind + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc)

    ppm = round(dpi / 0.0254)
    return b"\x89PNG\r\n\x1a\n" + b"".join(
        [
            chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)),
            chunk(b"pHYs", struct.pack(">IIB", ppm, ppm, 1)),
            chunk(b"IDAT", b"".join(compressed)),
            chunk(b"IEND", b""),
        ]
    )


def create_template(
    output: Path, *, name: str, width: int, height: int, dpi: int,
    guide_rectangles: list[tuple[int, int, int, int, RGBA]],
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    transparent = png(width, height, (0, 0, 0, 0), dpi=dpi)
    paper = png(width, height, (255, 255, 255, 255), dpi=dpi)
    guides = png(width, height, (0, 0, 0, 0), dpi=dpi, rectangles=guide_rectangles)
    thumb_height = max(1, round(256 * height / width))
    thumbnail = png(256, thumb_height, (255, 255, 255, 255), dpi=72)

    image = ET.Element("image", {"version": "0.0.1", "w": str(width), "h": str(height), "name": name})
    root = ET.SubElement(image, "stack", {"name": "root"})
    groups = [
        ("文字・フキダシ", ["フキダシ", "文字"]),
        ("仕上げ", ["効果", "トーン・色"]),
        ("作画", ["線画", "AI素材"]),
        ("下描き", ["ラフ"]),
    ]
    layer_number = 0
    layer_files: list[str] = []
    for group_name, layer_names in groups:
        group = ET.SubElement(root, "stack", {"name": group_name})
        for layer_name in layer_names:
            source = f"data/layer-{layer_number:02d}.png"
            ET.SubElement(group, "layer", {"name": layer_name, "src": source, "composite-op": "svg:src-over"})
            layer_files.append(source)
            layer_number += 1
    ET.SubElement(root, "layer", {"name": "用紙", "src": "data/paper.png", "composite-op": "svg:src-over"})
    ET.SubElement(
        root, "layer",
        {"name": "ガイド（必要時に表示）", "src": "data/guides.png", "visibility": "hidden", "composite-op": "svg:src-over"},
    )

    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("mimetype", "image/openraster", compress_type=zipfile.ZIP_STORED)
        archive.writestr("stack.xml", ET.tostring(image, encoding="utf-8", xml_declaration=True))
        archive.writestr("mergedimage.png", paper)
        archive.writestr("Thumbnails/thumbnail.png", thumbnail)
        archive.writestr("data/paper.png", paper)
        archive.writestr("data/guides.png", guides)
        for source in layer_files:
            archive.writestr(source, transparent)


def build_defaults(directory: Path) -> None:
    green = (0, 180, 120, 180)
    magenta = (220, 0, 140, 180)
    create_template(
        directory / "instagram-portrait.ora",
        name="Instagram 4:5 (1080x1350)", width=1080, height=1350, dpi=144,
        guide_rectangles=[(54, 54, 1025, 1295, green)],
    )
    create_template(
        directory / "b5-print-600dpi.ora",
        name="B5 print + 3mm bleed (600dpi)", width=4441, height=6213, dpi=600,
        guide_rectangles=[(71, 71, 4369, 6141, magenta), (189, 189, 4251, 6023, green)],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", nargs="?", default="templates/krita")
    args = parser.parse_args()
    build_defaults(Path(args.output_dir))


if __name__ == "__main__":
    main()
