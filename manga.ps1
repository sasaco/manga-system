[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('doctor', 'new', 'open', 'generate', 'validate', 'help')]
    [string]$Command = 'help',
    [string]$Project,
    [string]$Title,
    [string]$Panel = '001',
    [string]$Model = '',
    [long]$Seed = -1
)

$ErrorActionPreference = 'Stop'
$RepoRoot = $PSScriptRoot
$Config = Get-Content -LiteralPath (Join-Path $RepoRoot 'config\manga.json') -Raw | ConvertFrom-Json

function Resolve-RepoPath([string]$RelativePath) {
    return [System.IO.Path]::GetFullPath((Join-Path $RepoRoot $RelativePath))
}

function Invoke-UvPython([string[]]$PythonArguments) {
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if (-not $uv) { throw 'uv not found. Install uv or add it to PATH.' }
    & $uv.Source run python @PythonArguments
    if ($LASTEXITCODE -ne 0) { throw "uv Python command failed (exit $LASTEXITCODE)" }
}

function Find-Krita {
    $known = @(
        'C:\Program Files\Krita (x64)\bin\krita.exe',
        'C:\Program Files\Krita\bin\krita.exe',
        (Join-Path $env:LOCALAPPDATA 'Programs\Krita\bin\krita.exe')
    )
    foreach ($path in $known) {
        if (Test-Path -LiteralPath $path) { return $path }
    }
    $roots = @(
        'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*'
    )
    $app = Get-ItemProperty $roots -ErrorAction SilentlyContinue |
        Where-Object { $_.DisplayName -like 'Krita*' } | Select-Object -First 1
    if ($app.InstallLocation) {
        $candidate = Join-Path $app.InstallLocation 'bin\krita.exe'
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    return $null
}

function Find-ComfyDesktop {
    $known = Join-Path $env:LOCALAPPDATA 'Programs\Comfy Desktop\Comfy Desktop.exe'
    if (Test-Path -LiteralPath $known) { return $known }
    $app = Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue |
        Where-Object { $_.DisplayName -like 'Comfy Desktop*' } | Select-Object -First 1
    if ($app.DisplayIcon) {
        $candidate = $app.DisplayIcon -replace ',\d+$', ''
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    return $null
}

function Find-ComfyPython {
    $known = Join-Path $env:LOCALAPPDATA 'Comfy-Desktop\ComfyUI-Installs\ComfyUI\ComfyUI\.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $known) { return $known }
    $root = Join-Path $env:LOCALAPPDATA 'Comfy-Desktop\ComfyUI-Installs'
    $candidate = Get-ChildItem -LiteralPath $root -Filter python.exe -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -like '*\.venv\Scripts\python.exe' } | Select-Object -First 1
    if ($candidate) { return $candidate.FullName }
    $repoPython = Join-Path $RepoRoot 'venv_win\Scripts\python.exe'
    if (Test-Path -LiteralPath $repoPython) { return $repoPython }
    return $null
}

function Assert-ProjectName([string]$Name) {
    if (-not $Name -or $Name -notmatch '^[a-z0-9][a-z0-9_-]*$') {
        throw 'Project must use lowercase ASCII letters, digits, hyphens, or underscores (example: first-manga).'
    }
}

function Get-ProjectPath([string]$Name) {
    Assert-ProjectName $Name
    return Resolve-RepoPath (Join-Path $Config.projects_dir $Name)
}

function Show-Doctor {
    $krita = Find-Krita
    $comfy = Find-ComfyDesktop
    $python = Find-ComfyPython
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    Write-Host 'manga-system doctor' -ForegroundColor Cyan
    Write-Host ("Krita:        {0}" -f $(if ($krita) { "OK  $krita" } else { 'NG  Not found' }))
    Write-Host ("Comfy Desktop:{0}" -f $(if ($comfy) { " OK  $comfy" } else { ' NG  Not found' }))
    Write-Host ("Python:       {0}" -f $(if ($python) { "OK  $python" } else { 'NG  Comfy/venv Python not found' }))
    Write-Host ("uv:           {0}" -f $(if ($uv) { "OK  $($uv.Source)" } else { 'NG  Not found' }))

    if ($python) {
        $torch = & $python (Resolve-RepoPath 'scripts\comfy_probe.py') 2>&1
        Write-Host "GPU:          $torch"
    }

    $modelRoot = Join-Path $env:LOCALAPPDATA 'Comfy-Desktop\ComfyUI-Shared\models\checkpoints'
    $models = @(Get-ChildItem -LiteralPath $modelRoot -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -in '.safetensors', '.ckpt' })
    Write-Host ("Models:       {0} checkpoint(s)" -f $models.Count)

    try {
        $null = Invoke-RestMethod -Uri ($Config.comfy.server.TrimEnd('/') + '/system_stats') -TimeoutSec 3
        Write-Host ("Comfy API:    OK  {0}" -f $Config.comfy.server) -ForegroundColor Green
    }
    catch {
        Write-Host ("Comfy API:    NG  {0}" -f $Config.comfy.server) -ForegroundColor Yellow
        Write-Host 'Fully quit and restart Comfy Desktop, wait for ComfyUI, then run doctor again.' -ForegroundColor Yellow
    }
    if ($models.Count -eq 0) {
        Write-Host 'Next: install one checkpoint from Comfy Desktop.' -ForegroundColor Yellow
    }
}

function New-MangaProject {
    param([string]$Name, [string]$DisplayTitle)
    $destination = Get-ProjectPath $Name
    if (Test-Path -LiteralPath $destination) { throw "Project already exists: $destination" }
    if (-not $DisplayTitle) { $DisplayTitle = $Name }
    $template = Resolve-RepoPath 'projects\_template'
    Copy-Item -LiteralPath $template -Destination $destination -Recurse

    $settingsPath = Join-Path $destination 'project.json'
    $settings = Get-Content -LiteralPath $settingsPath -Raw | ConvertFrom-Json
    $settings.title = $DisplayTitle
    $settings.slug = $Name
    $settings.created = (Get-Date).ToString('yyyy-MM-dd')
    $settings | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $settingsPath -Encoding utf8

    $scriptPath = Join-Path $destination 'script.yaml'
    (Get-Content -LiteralPath $scriptPath -Raw) -replace '(?m)^title:.*$', "title: `"$DisplayTitle`"" |
        Set-Content -LiteralPath $scriptPath -Encoding utf8

    $kritaTemplate = Resolve-RepoPath $Config.krita_template
    if (-not (Test-Path -LiteralPath $kritaTemplate)) { throw "Krita template not found: $kritaTemplate" }
    Copy-Item -LiteralPath $kritaTemplate -Destination (Join-Path $destination 'pages\001.ora')
    Write-Host "Created project: $destination" -ForegroundColor Green
    Write-Host "Next: .\manga.ps1 open -Project $Name"
}

function Open-MangaProject([string]$Name) {
    $projectPath = Get-ProjectPath $Name
    if (-not (Test-Path -LiteralPath $projectPath)) { throw "Project not found: $projectPath" }
    $krita = Find-Krita
    if (-not $krita) { throw 'Krita not found. Run doctor.' }
    $page = Join-Path $projectPath 'pages\001.kra'
    if (-not (Test-Path -LiteralPath $page)) { $page = Join-Path $projectPath 'pages\001.ora' }
    Start-Process -FilePath $krita -ArgumentList @($page)

    if (-not (Get-Process -Name 'Comfy Desktop' -ErrorAction SilentlyContinue)) {
        $comfy = Find-ComfyDesktop
        if ($comfy) { Start-Process -FilePath $comfy }
    }
    Write-Host "Opened in Krita: $page"
}

function Invoke-PanelGeneration([string]$Name, [string]$PanelNumber, [string]$RequestedModel, [long]$RequestedSeed) {
    $projectPath = Get-ProjectPath $Name
    if (-not (Test-Path -LiteralPath $projectPath)) { throw "Project not found: $projectPath" }
    if ($PanelNumber -notmatch '^\d{3}$') { throw 'Panel must be three digits (example: 001).' }
    $prompt = Join-Path $projectPath "prompts\$PanelNumber.txt"
    if (-not (Test-Path -LiteralPath $prompt)) { throw "Prompt not found: $prompt" }
    if (-not $RequestedModel) { $RequestedModel = [string]$Config.comfy.checkpoint }

    Invoke-UvPython -PythonArguments @(
        (Resolve-RepoPath 'scripts\production_guard.py'),
        'check-prompt', '--prompt', $prompt
    )

    $arguments = @(
        (Resolve-RepoPath 'scripts\comfy_client.py'),
        '--server', [string]$Config.comfy.server,
        '--workflow', (Resolve-RepoPath $Config.comfy.workflow),
        '--prompt-file', $prompt,
        '--output-dir', (Join-Path $projectPath 'panels\ai'),
        '--project', $Name,
        '--panel', $PanelNumber,
        '--negative', [string]$Config.comfy.negative_prompt,
        '--seed', [string]$RequestedSeed,
        '--width', [string]$Config.comfy.width,
        '--height', [string]$Config.comfy.height,
        '--steps', [string]$Config.comfy.steps,
        '--cfg', [string]$Config.comfy.cfg,
        '--sampler', [string]$Config.comfy.sampler,
        '--scheduler', [string]$Config.comfy.scheduler
    )
    if ($RequestedModel) { $arguments += @('--model', $RequestedModel) }
    Invoke-UvPython -PythonArguments $arguments
}

function Invoke-ProductionValidation([string]$Name) {
    $projectPath = Get-ProjectPath $Name
    if (-not (Test-Path -LiteralPath $projectPath)) { throw "Project not found: $projectPath" }
    Invoke-UvPython -PythonArguments @(
        (Resolve-RepoPath 'scripts\production_guard.py'),
        'validate', '--project', $projectPath
    )
}

function Show-Help {
    @'
manga-system
  .\manga.ps1 doctor
  .\manga.ps1 new -Project first-manga -Title "My first manga"
  .\manga.ps1 open -Project first-manga
  .\manga.ps1 generate -Project first-manga -Panel 001 [-Model NAME] [-Seed 1234]
  .\manga.ps1 validate -Project first-manga
'@ | Write-Host
}

switch ($Command) {
    'doctor' { Show-Doctor }
    'new' { New-MangaProject -Name $Project -DisplayTitle $Title }
    'open' { Open-MangaProject -Name $Project }
    'generate' { Invoke-PanelGeneration -Name $Project -PanelNumber $Panel -RequestedModel $Model -RequestedSeed $Seed }
    'validate' { Invoke-ProductionValidation -Name $Project }
    default { Show-Help }
}
