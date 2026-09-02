# Codex Project Guard

- Follow the repository-root `AGENTS.md` as the canonical contract.
- The current target is `projects/my-life-story/` and Python runs through `uv run`.
- Do not use built-in image generation for project assets. Use Comfy, finish in Krita, and require `.\manga.ps1 validate -Project my-life-story` to pass before completion.
- Krita manuscripts must be `pages/NNN.kra`; `.ora` is a template/interchange format only. Use `.\manga.ps1 compose` to create the KRA with the selected panel already placed.
