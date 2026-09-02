import importlib.util
import json
import struct
import sys
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "production_guard", ROOT / "scripts" / "production_guard.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
TEST_CHECKPOINT = MODULE.load_manga_config()["comfy"]["checkpoint"]


def png_chunk(kind: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(kind + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc)


def test_png(prompt: str | None = None) -> bytes:
    chunks = [
        png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)),
    ]
    if prompt is not None:
        embedded = json.dumps(
            {
                "1": {
                    "class_type": "CheckpointLoaderSimple",
                    "inputs": {"ckpt_name": TEST_CHECKPOINT},
                },
                "2": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt}},
                "3": {"class_type": "CLIPTextEncode", "inputs": {"text": "bad quality"}},
                "4": {"class_type": "EmptyLatentImage", "inputs": {}},
                "5": {"class_type": "KSampler", "inputs": {"seed": 42}},
                "6": {"class_type": "VAEDecode", "inputs": {}},
                "7": {"class_type": "SaveImage", "inputs": {}},
            }
        )
        chunks.append(png_chunk(b"tEXt", b"prompt\x00" + embedded.encode("utf-8")))
    chunks.extend(
        [
            png_chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00\x00")),
            png_chunk(b"IEND", b""),
        ]
    )
    return MODULE.PNG_SIGNATURE + b"".join(chunks)


def paint_layer_data(pixel: bytes, compression: str = "RAW") -> bytes:
    if compression == "RAW":
        encoded = pixel
    elif compression == "LZF":
        encoded = b"\x01" + bytes([len(pixel) - 1]) + pixel
    else:
        raise ValueError(compression)
    return (
        b"VERSION 2\nTILEWIDTH 1\nTILEHEIGHT 1\nPIXELSIZE 4\nDATA 1\n"
        + f"0,0,{compression},{len(encoded)}\n".encode()
        + encoded
    )


def write_krita_source(
    path: Path,
    *,
    text_pixel: bytes | None = None,
    balloon_pixel: bytes | None = None,
    ai_pixel: bytes = b"\x00\x00\x00\xff",
    compression: str = "RAW",
) -> None:
    document = """<DOC><IMAGE>
        <layer name="AI素材" filename="layer1" nodetype="paintlayer"/>
        <layer name="文字" filename="layer2" nodetype="paintlayer"/>
        <layer name="フキダシ" filename="layer3" nodetype="paintlayer"/>
    </IMAGE></DOC>""".encode()
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("mimetype", "application/x-krita")
        archive.writestr("maindoc.xml", document)
        archive.writestr("mergedimage.png", test_png())
        for filename, pixel in (
            ("layer1", ai_pixel),
            ("layer2", text_pixel or b"\x00\x00\x00\x00"),
            ("layer3", balloon_pixel or b"\x00\x00\x00\x00"),
        ):
            archive.writestr(
                f"data/layers/{filename}", paint_layer_data(pixel, compression)
            )
            archive.writestr(f"data/layers/{filename}.defaultpixel", b"\x00\x00\x00\x00")


class ProductionGuardTests(unittest.TestCase):
    def make_project(self, root: Path, prompt: str, *, textless: bool = False) -> Path:
        project = root / "project"
        for relative in ("prompts", "panels/selected", "pages", "export"):
            (project / relative).mkdir(parents=True, exist_ok=True)
        settings = {
            "title": "Test manga",
            "slug": "test-manga",
            "page_template": "instagram-portrait.ora",
            "manuscript_format": "kra",
            "image_text_policy": "textless" if textless else "manual-krita-text",
            "format": "one-post-one-panel",
            "workflow": {"generator": "comfy", "finisher": "krita"},
            "status": "draft",
        }
        (project / "project.json").write_text(
            json.dumps(settings),
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

    def test_affirmative_text_request_is_rejected_even_with_no_text_clause(self):
        with tempfile.TemporaryDirectory() as directory:
            prompt = Path(directory) / "001.txt"
            prompt.write_text(
                "Draw the exact word HELLO on a sign; no text elsewhere.", encoding="utf-8"
            )
            codes = {finding.code for finding in MODULE.validate_visual_prompt(prompt)}
            self.assertIn("PROMPT_BAKES_TEXT", codes)

    def test_comfy_prompt_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prompt = root / "001.txt"
            prompt.write_text("expected art, no text", encoding="utf-8")
            image = root / "001.png"
            image.write_bytes(test_png("different art, no text"))
            findings = MODULE.validate_comfy_png(image, prompt)
            self.assertEqual([finding.code for finding in findings], ["COMFY_PROMPT_MISMATCH"])

    def test_comfy_workflow_shape_is_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prompt = root / "001.txt"
            prompt.write_text("expected art, no text", encoding="utf-8")
            image = root / "001.png"
            embedded = json.dumps(
                {"2": {"class_type": "CLIPTextEncode", "inputs": {"text": "expected art, no text"}}}
            )
            image.write_bytes(
                MODULE.PNG_SIGNATURE
                + png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
                + png_chunk(b"tEXt", b"prompt\x00" + embedded.encode("utf-8"))
                + png_chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00\x00"))
                + png_chunk(b"IEND", b"")
            )
            findings = MODULE.validate_comfy_png(
                image,
                prompt,
                required_node_types={"CheckpointLoaderSimple", "KSampler", "SaveImage"},
            )
            self.assertIn("COMFY_WORKFLOW_INCOMPLETE", {item.code for item in findings})

    def test_comfy_checkpoint_must_match_configured_model(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prompt = root / "001.txt"
            prompt.write_text("expected art, no text", encoding="utf-8")
            image = root / "001.png"
            image.write_bytes(test_png("expected art, no text"))
            findings = MODULE.validate_comfy_png(
                image,
                prompt,
                expected_checkpoint="different-model.safetensors",
            )
            self.assertIn(
                "COMFY_CHECKPOINT_MISMATCH", {item.code for item in findings}
            )

    def test_valid_comfy_to_krita_project_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            prompt_text = "minimal stick figures on white, no text"
            project = self.make_project(Path(directory), prompt_text)
            (project / "panels" / "selected" / "001.png").write_bytes(test_png(prompt_text))
            write_krita_source(project / "pages" / "001.kra")
            (project / "export" / "001.png").write_bytes(test_png())
            self.assertEqual(MODULE.validate_project(project), [])

    def test_each_selected_panel_requires_its_own_export(self):
        with tempfile.TemporaryDirectory() as directory:
            prompt_text = "minimal stick figures on white, no text"
            project = self.make_project(Path(directory), prompt_text)
            (project / "panels" / "selected" / "001.png").write_bytes(test_png(prompt_text))
            write_krita_source(project / "pages" / "001.kra")
            codes = {finding.code for finding in MODULE.validate_project(project)}
            self.assertIn("KRITA_EXPORT_MISSING", codes)

    def test_ready_episode_requires_a_selected_panel(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.make_project(Path(directory), "minimal art, no text")
            episodes = project / "episodes"
            episodes.mkdir()
            (episodes / "002.yaml").write_text(
                """series: Test manga
episode: 2
status: ready
format: one-post-one-panel
panels:
  - number: 1
    purpose: Test
    visual: Test art
    narration: ''
    dialogue: ''
    sfx: ''
""",
                encoding="utf-8",
            )
            codes = {finding.code for finding in MODULE.validate_project(project)}
            self.assertIn("SELECTED_PANEL_MISSING", codes)

    def test_episode_number_must_match_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            episode = Path(directory) / "002.yaml"
            episode.write_text(
                """series: Test manga
episode: 3
status: draft
format: one-post-one-panel
panels:
  - number: 1
    purpose: Test
    visual: Test art
    narration: ''
    dialogue: ''
    sfx: ''
""",
                encoding="utf-8",
            )
            _, findings = MODULE.load_and_validate_episode(episode)
            self.assertIn(
                "EPISODE_NUMBER_MISMATCH", {finding.code for finding in findings}
            )

    def test_openraster_is_not_accepted_as_the_manuscript(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "001.ora"
            source.write_bytes(b"not relevant")
            findings = MODULE.validate_krita_source(source)
            self.assertEqual([finding.code for finding in findings], ["KRITA_FORMAT_REQUIRED"])

    def test_textless_project_rejects_lettering_input(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.make_project(
                Path(directory), "minimal stick figures, no text", textless=True
            )
            lettering = project / "lettering" / "001.txt"
            lettering.parent.mkdir()
            lettering.write_text("This belongs in the post", encoding="utf-8")
            codes = {finding.code for finding in MODULE.validate_project(project)}
            self.assertIn("TEXT_INPUT_FORBIDDEN", codes)

    def test_textless_project_rejects_nonempty_text_layer(self):
        with tempfile.TemporaryDirectory() as directory:
            prompt_text = "minimal stick figures, no text"
            project = self.make_project(Path(directory), prompt_text, textless=True)
            (project / "panels" / "selected" / "001.png").write_bytes(test_png(prompt_text))
            write_krita_source(
                project / "pages" / "001.kra", text_pixel=b"\x00\x00\x00\xff"
            )
            (project / "export" / "001.png").write_bytes(test_png())
            codes = {finding.code for finding in MODULE.validate_project(project)}
            self.assertIn("KRITA_TEXT_LAYER_NOT_EMPTY", codes)

    def test_textless_project_rejects_nonempty_balloon_layer(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "001.kra"
            write_krita_source(source, balloon_pixel=b"\x00\x00\x00\xff")
            findings = MODULE.validate_krita_source(
                source, empty_layers=MODULE.TEXTLESS_KRITA_LAYERS
            )
            self.assertTrue(
                any("'フキダシ'" in finding.message for finding in findings)
            )

    def test_textless_project_accepts_empty_text_and_balloon_layers(self):
        with tempfile.TemporaryDirectory() as directory:
            prompt_text = "minimal stick figures, no text"
            project = self.make_project(Path(directory), prompt_text, textless=True)
            (project / "panels" / "selected" / "001.png").write_bytes(test_png(prompt_text))
            write_krita_source(project / "pages" / "001.kra")
            (project / "export" / "001.png").write_bytes(test_png())
            MODULE.create_visual_review_receipt(project, "001", "unit-test")
            self.assertEqual(MODULE.validate_project(project), [])

    def test_textless_review_receipt_is_invalidated_by_artifact_change(self):
        with tempfile.TemporaryDirectory() as directory:
            prompt_text = "minimal stick figures, no text"
            project = self.make_project(Path(directory), prompt_text, textless=True)
            selected = project / "panels" / "selected" / "001.png"
            selected.write_bytes(test_png(prompt_text))
            write_krita_source(project / "pages" / "001.kra")
            (project / "export" / "001.png").write_bytes(test_png())
            MODULE.create_visual_review_receipt(project, "001", "unit-test")
            selected.write_bytes(test_png(prompt_text) + b"changed")
            codes = {finding.code for finding in MODULE.validate_project(project)}
            self.assertIn("VISUAL_REVIEW_STALE", codes)

    def test_visual_review_receipt_is_only_for_textless_projects(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.make_project(
                Path(directory), "minimal stick figures, no text", textless=False
            )
            with self.assertRaisesRegex(ValueError, "only to textless projects"):
                MODULE.create_visual_review_receipt(project, "001", "unit-test")

    def test_textless_project_accepts_empty_lzf_layers(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "001.kra"
            write_krita_source(source, compression="LZF")
            self.assertEqual(
                MODULE.validate_krita_source(
                    source, empty_layers=MODULE.TEXTLESS_KRITA_LAYERS
                ),
                [],
            )

    def test_krita_source_requires_nonempty_ai_artwork(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "001.kra"
            write_krita_source(source, ai_pixel=b"\x00\x00\x00\x00")
            codes = {finding.code for finding in MODULE.validate_krita_source(source)}
            self.assertIn("KRITA_AI_LAYER_EMPTY", codes)

    def test_export_must_match_krita_preview_size(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "001.kra"
            exported = root / "001.png"
            write_krita_source(source)
            exported.write_bytes(
                MODULE.PNG_SIGNATURE
                + png_chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 1, 8, 6, 0, 0, 0))
                + png_chunk(b"IDAT", zlib.compress(b"\x00" + b"\x00" * 8))
                + png_chunk(b"IEND", b"")
            )
            codes = {
                finding.code
                for finding in MODULE.validate_export_image(exported, source)
            }
            self.assertIn("KRITA_EXPORT_SIZE_MISMATCH", codes)

    def test_invalid_config_schema_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            invalid_schema = Path(directory) / "invalid.schema.json"
            invalid_schema.write_text('{"type": 7}', encoding="utf-8")
            with mock.patch.object(MODULE, "CONFIG_SCHEMA_PATH", invalid_schema):
                with self.assertRaisesRegex(ValueError, "cannot load workflow policy"):
                    MODULE.load_workflow_policy()


if __name__ == "__main__":
    unittest.main()
