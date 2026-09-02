# Windows and Krita operational notes

Use these rules only when controlling Krita, troubleshooting its command line, or changing the repository's ORA-to-KRA conversion.

- Prefer an available native-app/UI control surface for interactive editing. If no Krita app surface is exposed, say so; do not claim UI actions occurred.
- The installed application is normally `C:\Program Files\Krita (x64)\bin\krita.exe` and has been observed as Krita 5.3.3. Use `manga.ps1 doctor` as the current source of truth.
- Do not use `--new-instance`; this build rejects it with a visible error dialog.
- Do not run probing commands such as `krita.exe --version` for routine checks; they may open a visible process or dialog.
- Do not start hidden command-line conversion while any Krita GUI process is running. It can hang beyond the 45-second timeout. Interact with the open document instead, or ask the user to save and close Krita first.
- Never terminate a Krita process that predated the current operation or may contain user work. If cleanup is necessary, refresh the process list and stop only the exact transient PID created by the current command.

When Krita is fully closed, repository ORA-to-KRA conversion uses the same argument shape as `manga.ps1 compose`:

```powershell
$arguments = @(
    ('"{0}"' -f $sourceOra),
    '--nosplash',
    '--export',
    '--export-filename',
    ('"{0}"' -f $targetKra)
)
$process = Start-Process -FilePath $krita -ArgumentList $arguments -WindowStyle Hidden -PassThru
if (-not $process.WaitForExit(45000)) {
    Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    $null = $process.WaitForExit(5000)
    throw 'Krita conversion timed out after 45 seconds.'
}
if ($process.ExitCode -ne 0) {
    throw "Krita conversion failed (exit $($process.ExitCode))."
}
```

Create output at a temporary sibling path, validate it, and only then atomically replace the requested manuscript. Never overwrite an existing manuscript implicitly; preserve user work. Inspect `mergedimage.png` before treating the conversion as visually correct.
