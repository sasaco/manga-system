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

## Mandatory character style for the current series

- For `projects/my-life-story/`, treat `projects/my-life-story/refs/character-style-reference.webp`, `projects/my-life-story/refs/dialogue-style-reference.webp`, and the `固定画風` section of `SERIES_BIBLE.md` as the canonical visual-style references. Inspect them before writing a prompt, drawing a control image, or finishing a page.
- **Do not draw stick figures.** Do not use stickman, pictogram, circle-head-with-line-body, single-line torso, or independent single-line legs as character construction.
- Build each person from an uneven oval face plus a rounded vertical bean/capsule body with visible area. Add only a few short hair strokes, dot or dash facial features, and the minimum clothing or prop shapes needed to identify the scene.
- Arms may be simple, but they must read as short gestures attached to the body or as narrow outlined shapes, not as a skeletal network of line limbs. Legs should normally be absorbed into or omitted by the rounded body silhouette.
- Use loose, slightly wobbly black outlines, generous white space, and a very small muted flat-color palette such as pale teal, mustard yellow, and warm gray. A sparse warm-gray fingerprint-like stipple may be used locally as an emotional shadow. Do not use gradients, realistic lighting, dense hatching, detailed textures, or polished vector symmetry.
- `my-life-story` uses `manual-krita-text`: Comfy prompts and generated PNGs stay completely textless, while original episode dialogue, speech balloons, and sound effects may be added only during the Krita finishing pass on the `文字` and `フキダシ` layers. Never copy the words visible in either style reference.
- Existing production descriptions that request stick figures are obsolete and must be rewritten before generating or revising that episode.

## Mandatory manga production harness

- Treat `config/manga.json` as the machine-readable production policy. Do not
  duplicate its values in scripts or documentation when they can be read from
  the config.
- The required production path is **Comfy for image generation, then Krita for layered finishing**.
- Do not use Codex built-in image generation, Gemini, or another external generator for a project asset unless the user explicitly changes the repository policy.
- If Comfy is unavailable or has no usable checkpoint, stop and report the blocker. Do not silently fall back to another generator.
- Comfy prompts are visual-only and must explicitly say `no text` or `文字なし`.
- Every project must declare exactly one `image_text_policy`: `textless` or `manual-krita-text`.
- Under `textless`, never put narration, dialogue, titles, sound effects, or lettering in the image or manuscript; keep the `文字` and `フキダシ` layers empty and publish prose outside the image.
- Only `manual-krita-text` projects may add lettering manually in Krita. The compose helper must never inject lettering automatically.
- For a textless project, visually inspect the selected Comfy PNG, the KRA `mergedimage.png`, and the final export at readable scale; any visible glyph, number, logo, signature, or watermark blocks completion even when the required-empty layer checks pass.
- After that three-artifact inspection, record it with `./manga.ps1 review -Project <name> -Panel NNN -Reviewer <name> -ConfirmNoVisibleText`. Never record a review based only on automated checks.
- A file under `panels/selected/` must retain valid Comfy PNG `prompt` metadata matching `prompts/NNN.txt`.
- Editable manuscripts must be `pages/NNN.kra`. `.ora` is only an interchange template and must not be treated as a finished manuscript.
- After selecting a panel, run `.\manga.ps1 compose -Project <name> -Panel NNN` to place it on `AI素材` and create the `.kra` before opening Krita.
- A manga is not complete or publishable without an editable `pages/NNN.kra` and a final Krita export under `export/`.
- An episode whose YAML status is `ready`, `complete`, or `published` must have matching `prompts/NNN.txt`, `panels/selected/NNN.png`, `pages/NNN.kra`, and `export/NNN.png` or JPEG.
- Before calling any manga artifact complete, run `.\manga.ps1 validate -Project <name>`. Before merging infrastructure changes, run `.\manga.ps1 check`. Any finding blocks completion.
- Never bypass, weaken, waive, or fabricate the production guard or Comfy metadata to make a check pass.
