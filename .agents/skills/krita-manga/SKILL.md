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

## Manuscript workflow

1. Require a selected panel before composition.
2. Run `.\manga.ps1 compose -Project <name> -Panel NNN` to place it on `AI素材` and create `pages/NNN.kra`.
3. Treat `.ora` only as interchange. A finished editable manuscript must be `.kra` with Krita mimetype, `maindoc.xml`, and the expected editable layers.
4. Keep source art on `AI素材`. Put manual corrections in `線画`, `効果`, `トーン・色`, `文字`, or `フキダシ` according to their purpose rather than flattening the source.
5. Obey the project's text policy. For `my-life-story`, keep `文字` and `フキダシ` empty; prose belongs in the X.com post text, and the rendered manga must contain no text.
6. Export the finished page from Krita to the project's `export/` directory.
7. Run `.\manga.ps1 validate -Project <name>` before calling the page complete. Report every production-guard failure; never weaken or fabricate a guard or PNG metadata.

For baked-in mistakes, prefer a reversible correction on an upper editable layer. For example, cover unwanted lettering on `効果` while retaining the original `AI素材`, then visually verify the merged result. Regenerate through Comfy when the correction cannot be made cleanly without changing the generated artwork.

## Controlling Krita on this PC

- Prefer an available native-app/UI control surface for interactive editing. If no Krita app surface is exposed, say so; do not claim UI actions occurred.
- The installed application is normally `C:\Program Files\Krita (x64)\bin\krita.exe` and has been observed as Krita 5.3.3.
- Do not use `--new-instance`; this build rejects it with a visible error dialog.
- Do not run probing commands such as `krita.exe --version` for routine checks; they may open a visible process or dialog on this machine.
- Do not start hidden command-line conversion while any Krita GUI process is running. It can hang beyond the 45-second timeout. Interact with the open document instead, or ask the user to save and close Krita first.
- Never terminate a Krita process that predated the current operation or may contain user work. If cleanup is necessary, refresh the process list and stop only the exact transient PID created by the current command.

When Krita is fully closed, repository ORA-to-KRA conversion can use the same argument shape as `manga.ps1 compose`:

```powershell
$arguments = @(
    ('"{0}"' -f $sourceOra),
    '--export',
    '--export-filename',
    ('"{0}"' -f $targetKra)
)
$process = Start-Process -FilePath $krita -ArgumentList $arguments -WindowStyle Hidden -PassThru
if (-not $process.WaitForExit(45000)) {
    throw 'Krita conversion timed out after 45 seconds.'
}
if ($process.ExitCode -ne 0) {
    throw "Krita conversion failed (exit $($process.ExitCode))."
}
```

Create output at a temporary sibling path, validate it, inspect its merged preview, and only then atomically replace the requested manuscript. Back up the previous file before replacement when it contains user work.

## Verification

- Inspect `mergedimage.png` from the KRA archive to verify the actual rendered appearance.
- Run `uv run python scripts/production_guard.py check-krita --source <page.kra>` for focused KRA structure validation.
- Run the full project validation after the final Krita export.
- A structurally valid KRA is not automatically publishable: missing Comfy metadata or a missing final Krita export still blocks completion.
