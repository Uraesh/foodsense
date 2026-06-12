param(
    [string]$PythonVersion = "3.12",
    [string]$PythonExecutable = "",
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 8000,
    [switch]$Reload
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$SitePackages = Join-Path $ProjectRoot ".venv\\Lib\\site-packages"
$BackendRoot = Join-Path $ProjectRoot "backend"
. (Join-Path $PSScriptRoot "Get-PythonRunner.ps1")

if (-not (Test-Path $BackendRoot)) {
    throw "Dossier backend introuvable: $BackendRoot"
}

if (Test-Path $SitePackages) {
    $env:PYTHONPATH = "$SitePackages;$BackendRoot"
}
else {
    $env:PYTHONPATH = $BackendRoot
}

$Python = Resolve-PythonRunner -ProjectRoot $ProjectRoot -PythonVersion $PythonVersion -PythonExecutable $PythonExecutable
$pyArgs = @($Python.Args + @("-m", "uvicorn", "app.main:app", "--host", $BindHost, "--port", "$Port"))

if ($Reload) {
    $pyArgs += "--reload"
}

Write-Host "Using PYTHONPATH=$env:PYTHONPATH"
Write-Host "Using Python runner=$($Python.Runner) $($Python.Args -join ' ')"
Write-Host "Resolved interpreter=$($Python.Executable)"
Write-Host "Starting backend on http://$BindHost`:$Port"

& $Python.Runner @pyArgs
