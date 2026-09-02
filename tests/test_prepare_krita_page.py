import importlib.util
import io
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


TEMPLATE = load_module("krita_template_for_page", ROOT / "scripts" / "create_krita_template.py")
PAGE = load_module("prepare_krita_page", ROOT / "scripts" / "prepare_krita_page.py")


class PrepareKritaPageTests(unittest.TestCase):
    def test_selected_art_is_visible_on_ai_layer_and_merged_preview(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            template = root / "template.ora"
            art = root / "001.png"
            output = root / "prepared.ora"
            TEMPLATE.create_template(
                template,
                name="test",
                width=80,
                height=100,
                dpi=144,
                guide_rectangles=[],
            )
            Image.new("RGBA", (20, 40), (0, 0, 0, 255)).save(art)

            PAGE.prepare_page(template, art, output)

            with zipfile.ZipFile(output) as archive:
                ai_layer = Image.open(io.BytesIO(archive.read("data/layer-05.png"))).convert("RGBA")
                merged = Image.open(io.BytesIO(archive.read("mergedimage.png"))).convert("RGBA")
                untouched = Image.open(io.BytesIO(archive.read("data/layer-01.png"))).convert("RGBA")
            self.assertIsNotNone(ai_layer.getbbox())
            self.assertEqual(ai_layer.getchannel("A").getextrema(), (0, 255))
            self.assertNotEqual(merged.getpixel((40, 50)), (255, 255, 255, 255))
            self.assertIsNone(untouched.getbbox())

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            template = root / "template.ora"
            art = root / "001.png"
            output = root / "prepared.ora"
            TEMPLATE.create_template(
                template,
                name="test",
                width=32,
                height=40,
                dpi=144,
                guide_rectangles=[],
            )
            Image.new("RGBA", (8, 8), (0, 0, 0, 255)).save(art)
            output.write_bytes(b"keep")

            with self.assertRaises(FileExistsError):
                PAGE.prepare_page(template, art, output)
            self.assertEqual(output.read_bytes(), b"keep")

    def test_line_art_is_separate_and_text_layer_stays_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            template = root / "template.ora"
            art = root / "002.png"
            line_art = root / "002-control.png"
            output = root / "prepared.ora"
            TEMPLATE.create_template(
                template,
                name="test",
                width=240,
                height=300,
                dpi=144,
                guide_rectangles=[],
            )
            Image.new("RGB", (120, 160), (150, 145, 140)).save(art)
            guide = Image.new("RGB", (120, 160), "white")
            for offset in range(3):
                guide.putpixel((60 + offset, 100), (0, 0, 0))
            guide.save(line_art)
            PAGE.prepare_page(template, art, output, line_art=line_art)

            with zipfile.ZipFile(output) as archive:
                line_layer = Image.open(io.BytesIO(archive.read("data/layer-04.png"))).convert("RGBA")
                text_layer = Image.open(io.BytesIO(archive.read("data/layer-01.png"))).convert("RGBA")
                stack = archive.read("stack.xml").decode("utf-8")
            self.assertIsNotNone(line_layer.getbbox())
            self.assertIsNone(text_layer.getbbox())
            self.assertIn('name="AI素材"', stack)
            self.assertIn('visibility="hidden"', stack)

    def test_flat_color_art_is_separate_below_visible_line_art(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            template = root / "template.ora"
            art = root / "003.png"
            line_art = root / "003-control.png"
            color_art = root / "003-color.png"
            output = root / "prepared.ora"
            TEMPLATE.create_template(
                template,
                name="test",
                width=120,
                height=150,
                dpi=144,
                guide_rectangles=[],
            )
            Image.new("RGB", (80, 100), (170, 165, 160)).save(art)
            guide = Image.new("RGB", (80, 100), "white")
            for offset in range(3):
                guide.putpixel((40 + offset, 50), (0, 0, 0))
            guide.save(line_art)
            colors = Image.new("RGBA", (80, 100), (0, 0, 0, 0))
            for x in range(20, 60):
                for y in range(30, 70):
                    colors.putpixel((x, y), (153, 198, 198, 255))
            colors.save(color_art)

            PAGE.prepare_page(
                template,
                art,
                output,
                line_art=line_art,
                color_art=color_art,
            )

            with zipfile.ZipFile(output) as archive:
                color_layer = Image.open(io.BytesIO(archive.read("data/layer-03.png"))).convert("RGBA")
                line_layer = Image.open(io.BytesIO(archive.read("data/layer-04.png"))).convert("RGBA")
                merged = Image.open(io.BytesIO(archive.read("mergedimage.png"))).convert("RGBA")
                text_layer = Image.open(io.BytesIO(archive.read("data/layer-01.png"))).convert("RGBA")
                stack = archive.read("stack.xml").decode("utf-8")
            self.assertIsNotNone(color_layer.getbbox())
            self.assertIsNotNone(line_layer.getbbox())
            self.assertIsNone(text_layer.getbbox())
            self.assertIn('name="トーン・色"', stack)
            self.assertLess(stack.index('name="線画"'), stack.index('name="トーン・色"'))
            self.assertLess(stack.index('name="トーン・色"'), stack.index('name="AI素材"'))
            self.assertNotEqual(merged.getpixel((60, 75)), (255, 255, 255, 255))


if __name__ == "__main__":
    unittest.main()
