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

- The required production path is **Comfy for image generation, then Krita for lettering and finishing**.
- Do not use Codex built-in image generation, Gemini, or another external generator for a project asset unless the user explicitly changes the repository policy.
- If Comfy is unavailable or has no usable checkpoint, stop and report the blocker. Do not silently fall back to another generator.
- Comfy prompts are visual-only and must explicitly say `no text` or `文字なし`. Add narration, dialogue, and lettering only in Krita.
- A file under `panels/selected/` must retain valid Comfy PNG `prompt` metadata matching `prompts/NNN.txt`.
- A manga is not complete or publishable without an editable `pages/NNN.kra` or `pages/NNN.ora` and a final Krita export under `export/`.
- Before calling any manga artifact complete, run `.\manga.ps1 validate -Project <name>`. Any production-guard finding blocks completion.
- Never bypass, weaken, waive, or fabricate the production guard or Comfy metadata to make a check pass.
