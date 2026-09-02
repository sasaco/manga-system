import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("krita_template", ROOT / "scripts" / "create_krita_template.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class KritaTemplateTests(unittest.TestCase):
    def test_openraster_has_required_files_and_layers(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.ora"
            MODULE.create_template(
                path, name="test", width=64, height=80, dpi=144,
                guide_rectangles=[(4, 4, 59, 75, (0, 255, 0, 128))],
            )
            with zipfile.ZipFile(path) as archive:
                self.assertEqual(archive.namelist()[0], "mimetype")
                self.assertEqual(archive.read("mimetype"), b"image/openraster")
                stack = ET.fromstring(archive.read("stack.xml"))
                self.assertEqual(stack.attrib["w"], "64")
                names = [element.attrib.get("name") for element in stack.iter()]
                self.assertIn("線画", names)
                self.assertIn("文字", names)


if __name__ == "__main__":
    unittest.main()
