param(
    [string]$ModelsPath = "D:\Ollama\models",
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

$env:OLLAMA_MODELS = $ModelsPath
Write-Host "Using OLLAMA_MODELS=$env:OLLAMA_MODELS"

if ($Serve) {
    Get-Process ollama -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 2
    & $OllamaExecutable serve
    exit $LASTEXITCODE
}

Start-Process -FilePath $OllamaExecutable -ArgumentList "serve" -WorkingDirectory (Split-Path $OllamaExecutable) -WindowStyle Hidden
Write-Host "Ollama demarre en arriere-plan."
