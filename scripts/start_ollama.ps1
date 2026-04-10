param(
    [string]$ModelsPath = "D:\Ollama\models",
    [switch]$LowMemory,
    [int]$KeepAliveSeconds = 120,
    [int]$MaxLoadedModels = 1,
    [int]$NumParallel = 1,
    [switch]$Serve
)

$ErrorActionPreference = "Stop"

$OllamaExecutable = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"
if (-not (Test-Path $OllamaExecutable)) {
    throw "Executable Ollama introuvable: $OllamaExecutable"
}

if (-not (Test-Path $ModelsPath)) {
    throw "Dossier des modeles introuvable: $ModelsPath"
}

$effectiveKeepAlive = $KeepAliveSeconds
if ($LowMemory -and $PSBoundParameters["KeepAliveSeconds"] -eq $null) {
    $effectiveKeepAlive = 45
}

$env:OLLAMA_MODELS = $ModelsPath
$env:OLLAMA_KEEP_ALIVE = "${effectiveKeepAlive}s"
$env:OLLAMA_MAX_LOADED_MODELS = "$MaxLoadedModels"
$env:OLLAMA_NUM_PARALLEL = "$NumParallel"

Write-Host "Using OLLAMA_MODELS=$env:OLLAMA_MODELS"
Write-Host "Using OLLAMA_KEEP_ALIVE=$env:OLLAMA_KEEP_ALIVE"
Write-Host "Using OLLAMA_MAX_LOADED_MODELS=$env:OLLAMA_MAX_LOADED_MODELS"
Write-Host "Using OLLAMA_NUM_PARALLEL=$env:OLLAMA_NUM_PARALLEL"

if ($Serve) {
    Get-Process ollama -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 2
    & $OllamaExecutable serve
    exit $LASTEXITCODE
}

Start-Process -FilePath $OllamaExecutable -ArgumentList "serve" -WorkingDirectory (Split-Path $OllamaExecutable) -WindowStyle Hidden
Write-Host "Ollama demarre en arriere-plan."
