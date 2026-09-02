---
name: krita-manga
description: Edit, finish, convert, and verify Krita manga manuscripts only inside the manga-system repository. Use here for layered KRA/ORA page edits, layer-safe corrections, export, or Krita command-line troubleshooting; do not use outside this repository or as an image generator.
---

# Krita Manga

This is a repository-local skill. Its canonical location is `.agents/skills/krita-manga/`; do not install or copy it into a user-global skills directory. Apply it only when the repository root contains `manga.ps1`, `config/manga.json`, and the matching root `AGENTS.md`.

Use Krita as the editable finishing environment. Preserve the artwork source and make corrections on appropriately named upper layers whenever possible.

## Start with project rules

- Read the nearest `AGENTS.md` and the target project's series bible before changing a manuscript.
- In this repository, default to `projects/my-life-story/` unless the user names another project.
- This repository uses `uv`; run Python as `uv run python ...` or `uv run --with <package> python ...`.
- The required production path is Comfy for generated artwork, then Krita for editing and export. Never substitute Codex image generation or another generator unless the user explicitly changes that policy.
- Comfy prompts and generated artwork must be visual-only and say `no text` or `文字なし`. Preserve authentic Comfy PNG `prompt` metadata in `panels/selected/NNN.png`.
- Read `config/manga.json` instead of assuming workflow settings. A project's `image_text_policy` must be either `textless` or `manual-krita-text`.

## Manuscript workflow

1. Require a selected panel before composition.
2. Run `.\manga.ps1 compose -Project <name> -Panel NNN` to place it on `AI素材` and create `pages/NNN.kra`.
3. Treat `.ora` only as interchange. A finished editable manuscript must be `.kra` with Krita mimetype, `maindoc.xml`, and the expected editable layers.
4. Keep source art on `AI素材`. Put manual corrections in `線画`, `効果`, `トーン・色`, `文字`, or `フキダシ` according to their purpose rather than flattening the source.
5. Obey the project's text policy. Under `textless`, keep `文字` and `フキダシ` empty and keep every visible render free of glyphs, numbers, logos, signatures, and watermarks. Under `manual-krita-text`, add lettering only in Krita.
6. Export the finished page from Krita to the project's `export/` directory.
7. For a textless page, inspect the selected PNG, KRA merged preview, and export at readable scale. Only after inspection, run `.\manga.ps1 review -Project <name> -Panel NNN -Reviewer <name> -ConfirmNoVisibleText`.
8. Run `.\manga.ps1 validate -Project <name>` before calling the page complete. Report every production-guard failure; never weaken or fabricate a guard or PNG metadata.

For baked-in mistakes, prefer a reversible correction on an upper editable layer. For example, cover unwanted lettering on `効果` while retaining the original `AI素材`, then visually verify the merged result. Regenerate through Comfy when the correction cannot be made cleanly without changing the generated artwork.

## Windows/Krita troubleshooting

Read [references/windows-krita.md](references/windows-krita.md) only when controlling Krita, diagnosing its CLI, or changing ORA-to-KRA conversion. The reference contains machine-specific process-safety and conversion rules.

## Verification

- Inspect `mergedimage.png` from the KRA archive to verify the actual rendered appearance.
- Run `uv run python scripts/production_guard.py check-krita --source <page.kra>` for focused KRA structure validation.
- Run the full project validation after the final Krita export.
- Run `.\manga.ps1 check` after changing repository rules, schemas, scripts, templates, or this skill.
- A structurally valid KRA is not automatically publishable: missing Comfy metadata, a missing final export, a stale textless visual-review receipt, or an incomplete ready episode still blocks completion.
