import importlib.util
import json
import struct
import sys
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "production_guard", ROOT / "scripts" / "production_guard.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def png_chunk(kind: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(kind + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc)


def test_png(prompt: str | None = None) -> bytes:
    chunks = [
        png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)),
    ]
    if prompt is not None:
        embedded = json.dumps({"2": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt}}})
        chunks.append(png_chunk(b"tEXt", b"prompt\x00" + embedded.encode("utf-8")))
    chunks.extend(
        [
            png_chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00\x00")),
            png_chunk(b"IEND", b""),
        ]
    )
    return MODULE.PNG_SIGNATURE + b"".join(chunks)


def write_krita_source(path: Path) -> None:
    document = b'<DOC><IMAGE><layer name="AI\xe7\xb4\xa0\xe6\x9d\x90"/><layer name="\xe6\x96\x87\xe5\xad\x97"/></IMAGE></DOC>'
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("mimetype", "application/x-krita")
        archive.writestr("maindoc.xml", document)


class ProductionGuardTests(unittest.TestCase):
    def make_project(self, root: Path, prompt: str) -> Path:
        project = root / "project"
        for relative in ("prompts", "panels/selected", "pages", "export"):
            (project / relative).mkdir(parents=True, exist_ok=True)
        (project / "project.json").write_text(
            json.dumps(
                {
                    "format": "one-post-one-panel",
                    "workflow": {"generator": "comfy", "finisher": "krita"},
                }
            ),
            encoding="utf-8",
        )
        (project / "prompts" / "001.txt").write_text(prompt, encoding="utf-8")
        return project

    def test_flat_external_png_and_missing_krita_export_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.make_project(Path(directory), "stick figures, no text")
            (project / "panels" / "selected" / "001.png").write_bytes(test_png())
            findings = MODULE.validate_project(project)
            codes = {finding.code for finding in findings}
            self.assertIn("COMFY_METADATA_MISSING", codes)
            self.assertIn("KRITA_SOURCE_MISSING", codes)
            self.assertIn("KRITA_EXPORT_MISSING", codes)

    def test_prompt_that_requests_baked_text_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            prompt = Path(directory) / "001.txt"
            prompt.write_text("Text (verbatim): hello\nTypography: gothic", encoding="utf-8")
            codes = {finding.code for finding in MODULE.validate_visual_prompt(prompt)}
            self.assertIn("PROMPT_BAKES_TEXT", codes)
            self.assertIn("PROMPT_NO_TEXT_RULE_MISSING", codes)

    def test_comfy_prompt_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prompt = root / "001.txt"
            prompt.write_text("expected art, no text", encoding="utf-8")
            image = root / "001.png"
            image.write_bytes(test_png("different art, no text"))
            findings = MODULE.validate_comfy_png(image, prompt)
            self.assertEqual([finding.code for finding in findings], ["COMFY_PROMPT_MISMATCH"])

    def test_valid_comfy_to_krita_project_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            prompt_text = "minimal stick figures on white, no text"
            project = self.make_project(Path(directory), prompt_text)
            (project / "panels" / "selected" / "001.png").write_bytes(test_png(prompt_text))
            write_krita_source(project / "pages" / "001.kra")
            (project / "export" / "001.png").write_bytes(test_png())
            self.assertEqual(MODULE.validate_project(project), [])

    def test_openraster_is_not_accepted_as_the_manuscript(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "001.ora"
            source.write_bytes(b"not relevant")
            findings = MODULE.validate_krita_source(source)
            self.assertEqual([finding.code for finding in findings], ["KRITA_FORMAT_REQUIRED"])


if __name__ == "__main__":
    unittest.main()
