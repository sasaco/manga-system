[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('doctor', 'new', 'open', 'generate', 'compose', 'validate', 'help')]
    [string]$Command = 'help',
    [string]$Project,
    [string]$Title,
    [string]$Panel = '001',
    [string]$Model = '',
    [string]$ControlImage = '',
    [string]$ControlNet = '',
    [double]$ControlStrength = 1.0,
    [long]$Seed = -1
)

$ErrorActionPreference = 'Stop'
$RepoRoot = $PSScriptRoot
$Config = Get-Content -LiteralPath (Join-Path $RepoRoot 'config\manga.json') -Raw | ConvertFrom-Json

function Resolve-RepoPath([string]$RelativePath) {
    return [System.IO.Path]::GetFullPath((Join-Path $RepoRoot $RelativePath))
}

function Invoke-UvPython {
    param(
        [string[]]$PythonArguments,
        [string[]]$WithPackages = @()
    )
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if (-not $uv) { throw 'uv not found. Install uv or add it to PATH.' }
    $uvArguments = @('run')
    foreach ($package in $WithPackages) {
        $uvArguments += @('--with', $package)
    }
    $uvArguments += 'python'
    $uvArguments += $PythonArguments
    & $uv.Source @uvArguments
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

function Find-KritaConsole {
    $gui = Find-Krita
    if (-not $gui) { return $null }
    $console = Join-Path (Split-Path -Parent $gui) 'krita.com'
    if (Test-Path -LiteralPath $console) { return $console }
    return $gui
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

    Write-Host "Created project: $destination" -ForegroundColor Green
    Write-Host "Next: generate/select a panel, then run .\manga.ps1 compose -Project $Name -Panel 001"
}

function Open-MangaProject([string]$Name, [string]$PanelNumber) {
    $projectPath = Get-ProjectPath $Name
    if (-not (Test-Path -LiteralPath $projectPath)) { throw "Project not found: $projectPath" }
    $krita = Find-Krita
    if (-not $krita) { throw 'Krita not found. Run doctor.' }
    if ($PanelNumber -notmatch '^\d{3}$') { throw 'Panel must be three digits (example: 001).' }
    $page = Join-Path $projectPath "pages\$PanelNumber.kra"
    if (-not (Test-Path -LiteralPath $page)) {
        throw "Krita manuscript not found: $page. Run compose first."
    }
    Start-Process -FilePath $krita -ArgumentList @($page)

    if (-not (Get-Process -Name 'Comfy Desktop' -ErrorAction SilentlyContinue)) {
        $comfy = Find-ComfyDesktop
        if ($comfy) { Start-Process -FilePath $comfy }
    }
    Write-Host "Opened in Krita: $page"
}

function New-KritaManuscript([string]$Name, [string]$PanelNumber) {
    $projectPath = Get-ProjectPath $Name
    if (-not (Test-Path -LiteralPath $projectPath)) { throw "Project not found: $projectPath" }
    if ($PanelNumber -notmatch '^\d{3}$') { throw 'Panel must be three digits (example: 001).' }

    $selected = Join-Path $projectPath "panels\selected\$PanelNumber.png"
    if (-not (Test-Path -LiteralPath $selected)) { throw "Selected panel not found: $selected" }
    $settings = Get-Content -LiteralPath (Join-Path $projectPath 'project.json') -Raw | ConvertFrom-Json
    $imageTextPolicy = [string]$settings.image_text_policy
    $requiresTextlessImage = $imageTextPolicy -match '^\s*(none|no-text|textless)\b'
    $templateName = if ($settings.page_template) { [string]$settings.page_template } else { [string]$Config.krita_template }
    $template = if ([System.IO.Path]::IsPathRooted($templateName)) {
        [System.IO.Path]::GetFullPath($templateName)
    }
    elseif ($templateName -match '[/\\]') {
        Resolve-RepoPath $templateName
    }
    else {
        Resolve-RepoPath (Join-Path 'templates\krita' $templateName)
    }
    if (-not (Test-Path -LiteralPath $template)) { throw "Krita template not found: $template" }

    $krita = Find-KritaConsole
    if (-not $krita) { throw 'Krita not found. Run doctor.' }
    $pages = Join-Path $projectPath 'pages'
    $manuscript = Join-Path $pages "$PanelNumber.kra"
    if (Test-Path -LiteralPath $manuscript) {
        throw "Refusing to overwrite an existing Krita manuscript: $manuscript"
    }

    $token = [guid]::NewGuid().ToString('N')
    $preparedOra = Join-Path $pages ".$PanelNumber.compose-$token.ora"
    $temporaryKra = Join-Path $pages ".$PanelNumber.compose-$token.kra"
    try {
        $prepareArguments = @(
            (Resolve-RepoPath 'scripts\prepare_krita_page.py'),
            '--template', $template,
            '--art', $selected,
            '--output', $preparedOra
        )
        $lineArt = Join-Path $projectPath "refs\$PanelNumber-control.png"
        if (Test-Path -LiteralPath $lineArt) {
            $prepareArguments += @('--line-art', $lineArt)
        }
        $narration = Join-Path $projectPath "lettering\$PanelNumber.txt"
        if ($requiresTextlessImage -and (Test-Path -LiteralPath $narration)) {
            throw "Textless image policy forbids lettering input: $narration. Put prose in the post text."
        }
        Invoke-UvPython -WithPackages @('pillow') -PythonArguments $prepareArguments

        $kritaArguments = @(
            ('"{0}"' -f $preparedOra),
            '--nosplash',
            '--export',
            '--export-filename',
            ('"{0}"' -f $temporaryKra)
        )
        $process = Start-Process -FilePath $krita -ArgumentList $kritaArguments -WindowStyle Hidden -PassThru
        if (-not $process.WaitForExit(45000)) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            $null = $process.WaitForExit(5000)
            throw 'Krita conversion timed out after 45 seconds.'
        }
        if ($process.ExitCode -ne 0) { throw "Krita conversion failed (exit $($process.ExitCode))." }
        if (-not (Test-Path -LiteralPath $temporaryKra)) { throw 'Krita did not create the .kra manuscript.' }

        $checkArguments = @(
            (Resolve-RepoPath 'scripts\production_guard.py'),
            'check-krita', '--source', $temporaryKra
        )
        if ($requiresTextlessImage) {
            $textLayerName = [string]([char]0x6587) + [char]0x5B57
            $balloonLayerName = [string]([char]0x30D5) + [char]0x30AD + [char]0x30C0 + [char]0x30B7
            $checkArguments += @('--empty-layer', $textLayerName, '--empty-layer', $balloonLayerName)
        }
        Invoke-UvPython -PythonArguments $checkArguments
        Move-Item -LiteralPath $temporaryKra -Destination $manuscript
        Write-Host "Created editable Krita manuscript: $manuscript" -ForegroundColor Green
    }
    finally {
        Remove-Item -LiteralPath $preparedOra -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $temporaryKra -Force -ErrorAction SilentlyContinue
    }
}

function Invoke-PanelGeneration(
    [string]$Name,
    [string]$PanelNumber,
    [string]$RequestedModel,
    [string]$RequestedControlImage,
    [string]$RequestedControlNet,
    [double]$RequestedControlStrength,
    [long]$RequestedSeed
) {
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

    $workflow = Resolve-RepoPath $Config.comfy.workflow
    $arguments = @(
        (Resolve-RepoPath 'scripts\comfy_client.py'),
        '--server', [string]$Config.comfy.server,
        '--workflow', $workflow,
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
    if ($RequestedControlImage) {
        $controlImagePath = if ([System.IO.Path]::IsPathRooted($RequestedControlImage)) {
            [System.IO.Path]::GetFullPath($RequestedControlImage)
        }
        else {
            Resolve-RepoPath $RequestedControlImage
        }
        if (-not (Test-Path -LiteralPath $controlImagePath)) {
            throw "Control image not found: $controlImagePath"
        }
        $arguments[4] = Resolve-RepoPath 'templates\comfy\panel_controlnet_api.json'
        $arguments += @(
            '--control-image', $controlImagePath,
            '--control-strength', [string]$RequestedControlStrength
        )
        if ($RequestedControlNet) { $arguments += @('--controlnet', $RequestedControlNet) }
    }
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
  .\manga.ps1 generate -Project first-manga -Panel 001 -ControlImage PATH [-ControlNet NAME]
  .\manga.ps1 compose -Project first-manga -Panel 001
  .\manga.ps1 validate -Project first-manga
'@ | Write-Host
}

switch ($Command) {
    'doctor' { Show-Doctor }
    'new' { New-MangaProject -Name $Project -DisplayTitle $Title }
    'open' { Open-MangaProject -Name $Project -PanelNumber $Panel }
    'generate' {
        Invoke-PanelGeneration -Name $Project -PanelNumber $Panel -RequestedModel $Model `
            -RequestedControlImage $ControlImage -RequestedControlNet $ControlNet `
            -RequestedControlStrength $ControlStrength -RequestedSeed $Seed
    }
    'compose' { New-KritaManuscript -Name $Project -PanelNumber $Panel }
    'validate' { Invoke-ProductionValidation -Name $Project }
    default { Show-Help }
}
