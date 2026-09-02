# Agent Context

## Current target

- Treat `projects/my-life-story/` as the default target for the current work in this repository.
- Put new autobiographical story, prompt, panel, and series-setting changes under `projects/my-life-story/` unless the user explicitly names another target.
- Read `projects/my-life-story/SERIES_BIBLE.md` before story writing or image generation.
- Do not modify sibling projects under `projects/` unless the user explicitly requests it.
- Repository-level tooling may still be run from the repository root when required.

## Python environment

- This PC and repository use `uv`.
- Run Python commands as `uv run python ...`; do not assume bare `python` or `py` is available on `PATH`.
- Run Python tools and tests through `uv run`.
- Add or resolve Python packages with `uv add`, `uv sync`, or `uv run --with <package>` as appropriate.

## Mandatory manga production harness

- The required production path is **Comfy for image generation, then Krita for layered finishing**.
- Do not use Codex built-in image generation, Gemini, or another external generator for a project asset unless the user explicitly changes the repository policy.
- If Comfy is unavailable or has no usable checkpoint, stop and report the blocker. Do not silently fall back to another generator.
- Comfy prompts are visual-only and must explicitly say `no text` or `文字なし`.
- The project's `image_text_policy` takes precedence over generic production guidance. If it starts with `none`, `no-text`, or `textless`, never put narration, dialogue, titles, sound effects, or lettering in the image or manuscript; keep the `文字` and `フキダシ` layers empty and publish prose outside the image.
- Only projects whose `image_text_policy` explicitly permits image text may add lettering manually in Krita. The compose helper must never inject lettering automatically.
- For a textless project, visually inspect the selected Comfy PNG, the KRA `mergedimage.png`, and the final export at readable scale; any visible glyph, number, logo, signature, or watermark blocks completion even when the required-empty layer checks pass.
- A file under `panels/selected/` must retain valid Comfy PNG `prompt` metadata matching `prompts/NNN.txt`.
- Editable manuscripts must be `pages/NNN.kra`. `.ora` is only an interchange template and must not be treated as a finished manuscript.
- After selecting a panel, run `.\manga.ps1 compose -Project <name> -Panel NNN` to place it on `AI素材` and create the `.kra` before opening Krita.
- A manga is not complete or publishable without an editable `pages/NNN.kra` and a final Krita export under `export/`.
- Before calling any manga artifact complete, run `.\manga.ps1 validate -Project <name>`. Any production-guard finding blocks completion.
- Never bypass, weaken, waive, or fabricate the production guard or Comfy metadata to make a check pass.
