param(
    [switch]$Install,
    [string]$PythonVersion = "3.12"
)

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$VenvPath = Join-Path $ProjectRoot ".venv"

$paths = @{
    PIP_CACHE_DIR = Join-Path $ProjectRoot ".cache\\pip"
    UV_CACHE_DIR = Join-Path $ProjectRoot ".cache\\uv"
    NPM_CONFIG_CACHE = Join-Path $ProjectRoot ".cache\\npm"
    MPLCONFIGDIR = Join-Path $ProjectRoot ".cache\\matplotlib"
    HF_HOME = Join-Path $ProjectRoot ".cache\\huggingface"
    TRANSFORMERS_CACHE = Join-Path $ProjectRoot ".cache\\huggingface\\transformers"
    JUPYTER_CONFIG_DIR = Join-Path $ProjectRoot ".jupyter\\config"
    JUPYTER_DATA_DIR = Join-Path $ProjectRoot ".jupyter\\data"
    JUPYTER_RUNTIME_DIR = Join-Path $ProjectRoot ".jupyter\\runtime"
    IPYTHONDIR = Join-Path $ProjectRoot ".ipython"
    OLLAMA_MODELS = Join-Path $ProjectRoot ".ollama\\models"
    TEMP = Join-Path $ProjectRoot ".cache\\tmp"
    TMP = Join-Path $ProjectRoot ".cache\\tmp"
}

foreach ($entry in $paths.GetEnumerator()) {
    New-Item -ItemType Directory -Force -Path $entry.Value | Out-Null
    Set-Item -Path ("Env:" + $entry.Key) -Value $entry.Value
}

if (-not (Test-Path $VenvPath)) {
    & py "-$PythonVersion" -m venv $VenvPath
}

$PythonExe = Join-Path $VenvPath "Scripts\\python.exe"
$PipExe = Join-Path $VenvPath "Scripts\\pip.exe"
$RequirementsPath = Join-Path $ProjectRoot "requirements.txt"

if ($Install) {
    if (Test-Path $PipExe) {
        & $PythonExe -m pip install --upgrade pip
        & $PythonExe -m pip install -r $RequirementsPath
    }
    else {
        & py "-$PythonVersion" -m pip --python $PythonExe install -r $RequirementsPath
    }
}

Write-Host "D-drive local environment prepared."
Write-Host "Project root: $ProjectRoot"
Write-Host "Virtual environment: $VenvPath"
Write-Host "To activate it in the current shell, run:"
Write-Host "  & `"$VenvPath\\Scripts\\Activate.ps1`""
Write-Host "To install dependencies on D:, run:"
Write-Host "  .\\scripts\\bootstrap_local_env.ps1 -Install"
Write-Host "Python version target: $PythonVersion"
