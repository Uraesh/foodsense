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

$pyArgs = @(
    "-$PythonVersion",
    "-m",
    "uvicorn",
    "app.main:app",
    "--host",
    $BindHost,
    "--port",
    "$Port"
)

if ($Reload) {
    $pyArgs += "--reload"
}

Write-Host "Using PYTHONPATH=$env:PYTHONPATH"
Write-Host "Starting backend on http://$BindHost`:$Port"

& py @pyArgs
