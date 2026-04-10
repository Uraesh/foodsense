param(
    [switch]$IncludeUI,
    [switch]$IncludeData,
    [switch]$IncludeLLM,
    [switch]$QdrantOnly,
    [switch]$NoBuild,
    [int]$WaitSeconds = 120
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ComposeFile = Join-Path $ProjectRoot "docker-compose.yml"
$DockerConfigDir = Join-Path $ProjectRoot ".docker-client"
$DockerConfigFile = Join-Path $DockerConfigDir "config.json"
$DockerDesktopExe = "C:\Program Files\Docker\Docker\Docker Desktop.exe"

New-Item -ItemType Directory -Force -Path $DockerConfigDir | Out-Null
if (-not (Test-Path $DockerConfigFile)) {
    "{}" | Set-Content -LiteralPath $DockerConfigFile -Encoding ASCII
}

$env:DOCKER_CONFIG = $DockerConfigDir

function Test-DockerReady {
    try {
        docker version --format "{{.Server.Version}}" | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

if (-not (Test-DockerReady)) {
    if (-not (Test-Path $DockerDesktopExe)) {
        throw "Docker Desktop executable not found: $DockerDesktopExe"
    }

    Start-Process -FilePath $DockerDesktopExe
    Write-Host "Starting Docker Desktop..."

    $attempts = [Math]::Max([Math]::Ceiling($WaitSeconds / 5), 1)
    for ($i = 0; $i -lt $attempts; $i++) {
        Start-Sleep -Seconds 5
        if (Test-DockerReady) {
            break
        }
    }
}

if (-not (Test-DockerReady)) {
    throw "Docker daemon did not become ready within $WaitSeconds seconds."
}

$services = @("qdrant")
if (-not $QdrantOnly) {
    $services += "backend"
}
if ($IncludeData) {
    $services += "notebook"
}
if ($IncludeUI) {
    $services += "frontend"
}
if ($IncludeLLM) {
    $services += "ollama"
}

$composeArgs = @("compose", "-f", $ComposeFile)
if ($IncludeData) {
    $composeArgs += @("--profile", "data")
}
if ($IncludeUI) {
    $composeArgs += @("--profile", "ui")
}
if ($IncludeLLM) {
    $composeArgs += @("--profile", "llm")
}
$composeArgs += @("up", "-d")
if (-not $NoBuild) {
    $composeArgs += "--build"
}
$composeArgs += $services

Write-Host "Using DOCKER_CONFIG=$DockerConfigDir"
Write-Host "Launching services: $($services -join ', ')"
& docker @composeArgs

Write-Host ""
Write-Host "Current stack status:"
& docker compose -f $ComposeFile ps

Write-Host ""
Write-Host "Expected endpoints:"
Write-Host "  Qdrant:  http://127.0.0.1:6333/dashboard"
if (-not $QdrantOnly) {
    Write-Host "  Backend: http://127.0.0.1:8000"
    Write-Host "  Swagger: http://127.0.0.1:8000/docs"
}
if ($IncludeUI) {
    Write-Host "  Frontend: http://127.0.0.1:3000"
}
if ($IncludeData) {
    Write-Host "  Jupyter:  http://127.0.0.1:8888"
}
if ($IncludeLLM) {
    Write-Host "  Ollama:   http://127.0.0.1:11434"
}
