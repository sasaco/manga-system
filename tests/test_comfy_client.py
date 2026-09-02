import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("comfy_client", ROOT / "scripts" / "comfy_client.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class WorkflowTests(unittest.TestCase):
    def test_build_workflow_replaces_runtime_values(self):
        template = json.loads(
            (ROOT / "templates" / "comfy" / "panel_txt2img_api.json").read_text(encoding="utf-8")
        )
        result = MODULE.build_workflow(
            template,
            checkpoint="manga.safetensors", prompt="hero", negative="text", seed=42,
            width=640, height=896, steps=18, cfg=5.5,
            sampler="euler", scheduler="normal", prefix="manga/test",
        )
        self.assertEqual(result["1"]["inputs"]["ckpt_name"], "manga.safetensors")
        self.assertEqual(result["2"]["inputs"]["text"], "hero")
        self.assertEqual(result["4"]["inputs"]["width"], 640)
        self.assertEqual(result["5"]["inputs"]["seed"], 42)
        self.assertEqual(result["7"]["inputs"]["filename_prefix"], "manga/test")
        self.assertEqual(template["1"]["inputs"]["ckpt_name"], "__CHECKPOINT__")

    def test_build_workflow_replaces_controlnet_values(self):
        template = json.loads(
            (ROOT / "templates" / "comfy" / "panel_controlnet_api.json").read_text(encoding="utf-8")
        )
        result = MODULE.build_workflow(
            template,
            checkpoint="manga.safetensors", prompt="two stick figures, no text",
            negative="extra people", seed=2001, width=768, height=1024,
            steps=24, cfg=6.5, sampler="dpmpp_2m", scheduler="karras",
            prefix="manga/control", control_image="002-control.png",
            controlnet="scribble.safetensors", control_strength=1.15,
        )
        self.assertEqual(result["8"]["inputs"]["image"], "002-control.png")
        self.assertEqual(result["10"]["inputs"]["control_net_name"], "scribble.safetensors")
        self.assertEqual(result["11"]["inputs"]["strength"], 1.15)
        self.assertEqual(result["5"]["inputs"]["positive"], ["11", 0])
        self.assertEqual(result["5"]["inputs"]["negative"], ["11", 1])


if __name__ == "__main__":
    unittest.main()
