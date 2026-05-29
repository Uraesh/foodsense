param(
    [switch]$Install,
    [switch]$SkipPython,
    [switch]$SkipFrontend,
    [switch]$Force,
    [string]$PythonVersion = "3.12",
    [string]$PythonExecutable = "",
    [switch]$RecreateVenv
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$FrontendRoot = Join-Path $ProjectRoot "frontend"
$BackendRoot = Join-Path $ProjectRoot "backend"
$EnvTemplatePath = Join-Path $ProjectRoot ".env.example"
$EnvTargetPath = Join-Path $ProjectRoot ".env"
$VenvRoot = Join-Path $ProjectRoot ".venv"
$VenvPython = Join-Path $VenvRoot "Scripts\python.exe"
$PipCacheDir = Join-Path $ProjectRoot ".cache\pip"
$NpmCacheDir = Join-Path $ProjectRoot ".cache\npm"
. (Join-Path $PSScriptRoot "Get-PythonRunner.ps1")

function Ensure-Directory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
        Write-Host "Created directory: $Path"
        return
    }

    Write-Host "Directory already exists: $Path"
}

function Ensure-EnvFile {
    if (-not (Test-Path -LiteralPath $EnvTemplatePath)) {
        throw "Template introuvable: $EnvTemplatePath"
    }

    if ((Test-Path -LiteralPath $EnvTargetPath) -and -not $Force) {
        Write-Host "Keeping existing env file: $EnvTargetPath"
        return
    }

    Copy-Item -LiteralPath $EnvTemplatePath -Destination $EnvTargetPath -Force
    if ($Force) {
        Write-Host "Refreshed env file from template: $EnvTargetPath"
    } else {
        Write-Host "Created env file from template: $EnvTargetPath"
    }
}

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Action
    )

    Write-Host ""
    Write-Host "==> $Label"
    & $Action
}

if (-not $ProjectRoot.StartsWith("D:", [System.StringComparison]::OrdinalIgnoreCase)) {
    Write-Warning "Le projet n'est pas sur D:. Le bootstrap reste possible, mais l'avantage disque sera moindre."
} else {
    Write-Host "Workspace detected on D:: $ProjectRoot"
}

$requiredDirectories = @(
    (Join-Path $ProjectRoot ".cache"),
    $PipCacheDir,
    $NpmCacheDir,
    (Join-Path $ProjectRoot ".docker-client"),
    (Join-Path $ProjectRoot ".ipython"),
    (Join-Path $ProjectRoot ".jupyter"),
    (Join-Path $ProjectRoot ".ollama"),
    (Join-Path $ProjectRoot ".qdrant"),
    (Join-Path $ProjectRoot ".qdrant\storage"),
    (Join-Path $ProjectRoot "data\raw"),
    (Join-Path $ProjectRoot "data\processed"),
    (Join-Path $ProjectRoot "data\samples")
)

Invoke-Step "Preparing local directories" {
    foreach ($directory in $requiredDirectories) {
        Ensure-Directory -Path $directory
    }
}

Invoke-Step "Preparing .env" {
    Ensure-EnvFile
}

if (-not $Install) {
    Write-Host ""
    Write-Host "Bootstrap scaffold prepared."
    Write-Host "Run .\scripts\bootstrap_local_env.ps1 -Install to create the venv and install dependencies."
    exit 0
}

if (-not $SkipPython) {
    Invoke-Step "Installing backend Python environment" {
        $Python = Resolve-PythonRunner `
            -ProjectRoot $ProjectRoot `
            -PythonVersion $PythonVersion `
            -PythonExecutable $PythonExecutable `
            -SkipVenv

        if ($RecreateVenv -and (Test-Path -LiteralPath $VenvRoot)) {
            Remove-Item -LiteralPath $VenvRoot -Recurse -Force
        }

        if (-not (Test-Path -LiteralPath $VenvPython)) {
            Write-Host "Creating virtual environment in $VenvRoot"
            & $Python.Runner @($Python.Args + @("-m", "venv", $VenvRoot))
            if ($LASTEXITCODE -ne 0) {
                throw "Echec lors de la creation du virtualenv avec l'interpreteur selectionne."
            }
        } else {
            Write-Host "Virtual environment already exists: $VenvRoot"
        }

        $env:PIP_CACHE_DIR = $PipCacheDir
        Write-Host "Using PIP_CACHE_DIR=$env:PIP_CACHE_DIR"
        Write-Host "Using Python runner=$($Python.Runner) $($Python.Args -join ' ')"

        & $VenvPython -m pip install --upgrade pip setuptools wheel
        if ($LASTEXITCODE -ne 0) {
            throw "Echec lors de la mise a jour de pip/setuptools/wheel."
        }

        & $VenvPython -m pip install -r (Join-Path $BackendRoot "requirements.txt")
        if ($LASTEXITCODE -ne 0) {
            throw "Echec lors de l'installation des dependances backend."
        }
    }
}

if (-not $SkipFrontend) {
    Invoke-Step "Installing frontend npm dependencies" {
        if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
            throw "npm est introuvable. Installe Node.js 20.9+ avant de lancer le bootstrap."
        }

        $env:NPM_CONFIG_CACHE = $NpmCacheDir
        Write-Host "Using NPM_CONFIG_CACHE=$env:NPM_CONFIG_CACHE"

        Push-Location $FrontendRoot
        try {
            & npm install
            if ($LASTEXITCODE -ne 0) {
                throw "Echec lors de l'installation des dependances frontend."
            }
        }
        finally {
            Pop-Location
        }
    }
}

Write-Host ""
Write-Host "Bootstrap completed successfully."
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. .\scripts\start_ollama.ps1"
Write-Host "  2. .\scripts\start_docker_stack.ps1 -QdrantOnly"
Write-Host "  3. .\scripts\start_backend.ps1"
Write-Host "  4. cd frontend ; npm run dev"
