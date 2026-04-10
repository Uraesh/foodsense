param(
    [string]$PythonVersion = "3.13",
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 8000,
    [switch]$Reload
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$SitePackages = Join-Path $ProjectRoot ".venv\\Lib\\site-packages"
$BackendRoot = Join-Path $ProjectRoot "backend"

if (-not (Test-Path $SitePackages)) {
    throw "Site-packages introuvable: $SitePackages"
}

if (-not (Test-Path $BackendRoot)) {
    throw "Dossier backend introuvable: $BackendRoot"
}

$env:PYTHONPATH = "$SitePackages;$BackendRoot"

$Runner = $null
$RunnerArgs = @()
$PyLauncher = Get-Command py -ErrorAction SilentlyContinue
$ProjectPython = Join-Path $ProjectRoot ".venv\\Scripts\\python.exe"

if ($PyLauncher) {
    $Runner = $PyLauncher.Source
    $RunnerArgs = @("-$PythonVersion")
} elseif (Test-Path $ProjectPython) {
    $Runner = $ProjectPython
} else {
    throw "Aucun interpreteur Python exploitable n'a ete trouve."
}

$pyArgs = @($RunnerArgs + @("-m", "uvicorn", "app.main:app", "--host", $BindHost, "--port", "$Port"))

if ($Reload) {
    $pyArgs += "--reload"
}

Write-Host "Using PYTHONPATH=$env:PYTHONPATH"
Write-Host "Using Python runner=$Runner $($RunnerArgs -join ' ')"
Write-Host "Starting backend on http://$BindHost`:$Port"

& $Runner @pyArgs
