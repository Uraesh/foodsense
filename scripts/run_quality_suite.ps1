param(
    [switch]$Background,
    [switch]$SkipSemanticEval,
    [switch]$SkipKeywordEval,
    [switch]$SkipTests,
    [switch]$SkipRuff,
    [switch]$SkipCompile,
    [string]$RunLabel
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$LogDir = Join-Path $ProjectRoot "evaluation\results"
$PowerShellExe = "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"

if (-not $RunLabel) {
    $RunLabel = Get-Date -Format "yyyyMMdd_HHmmss"
}

$LogFile = Join-Path $LogDir "quality_suite_$RunLabel.log"
$StatusFile = Join-Path $LogDir "quality_suite_$RunLabel.json"
$LatestStatusFile = Join-Path $LogDir "quality_suite_latest.json"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

if ($Background) {
    $argumentList = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $PSCommandPath,
        "-RunLabel", $RunLabel
    )

    foreach ($switchName in @("SkipSemanticEval", "SkipKeywordEval", "SkipTests", "SkipRuff", "SkipCompile")) {
        if (Get-Variable -Name $switchName -ValueOnly) {
            $argumentList += "-$switchName"
        }
    }

    $process = Start-Process `
        -FilePath $PowerShellExe `
        -ArgumentList $argumentList `
        -WorkingDirectory $ProjectRoot `
        -WindowStyle Hidden `
        -PassThru
    Write-Host "Quality suite started in background."
    Write-Host "PID: $($process.Id)"
    Write-Host "Log: $LogFile"
    Write-Host "Status: $LatestStatusFile"
    exit 0
}

Push-Location $ProjectRoot

$status = [ordered]@{
    run_label = $RunLabel
    started_at = (Get-Date).ToString("o")
    finished_at = $null
    overall_status = "running"
    log_file = $LogFile
    project_root = $ProjectRoot
    steps = @()
    semantic_prerequisites = [ordered]@{
        ollama = $false
        qdrant = $false
    }
}

function Save-Status {
    $json = $status | ConvertTo-Json -Depth 8
    Set-Content -LiteralPath $StatusFile -Value $json -Encoding UTF8
    Set-Content -LiteralPath $LatestStatusFile -Value $json -Encoding UTF8
}

function Write-Log {
    param([string]$Message)

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$timestamp] $Message"
    Write-Host $line
    Add-Content -LiteralPath $LogFile -Value $line -Encoding UTF8
}

function Test-HttpEndpoint {
    param([string]$Uri)

    try {
        Invoke-WebRequest -Uri $Uri -UseBasicParsing -TimeoutSec 5 | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Action
    )

    $step = [ordered]@{
        name = $Name
        status = "running"
        started_at = (Get-Date).ToString("o")
        ended_at = $null
        duration_seconds = $null
        error = $null
    }
    $status.steps += $step
    Save-Status

    $startedAt = Get-Date
    Write-Log "Starting: $Name"

    try {
        & $Action 2>&1 | Tee-Object -FilePath $LogFile -Append | Out-Host
        $step.status = "passed"
    }
    catch {
        $step.status = "failed"
        $step.error = $_.Exception.Message
        Write-Log "Failed: $Name :: $($_.Exception.Message)"
    }

    $endedAt = Get-Date
    $step.ended_at = $endedAt.ToString("o")
    $step.duration_seconds = [Math]::Round(($endedAt - $startedAt).TotalSeconds, 2)
    Save-Status
}

try {
    "" | Set-Content -LiteralPath $LogFile -Encoding UTF8
    Write-Log "Quality suite starting from $ProjectRoot"

    if (-not (Test-Path ".venv\Lib\site-packages")) {
        throw "Virtualenv site-packages not found at .venv\Lib\site-packages"
    }

    $env:PYTHONPATH = ".venv\Lib\site-packages;backend"

    $status.semantic_prerequisites.ollama = Test-HttpEndpoint "http://127.0.0.1:11434/api/tags"
    $status.semantic_prerequisites.qdrant = Test-HttpEndpoint "http://127.0.0.1:6333/collections"
    Save-Status

    if (-not $SkipCompile) {
        Invoke-Step "compileall" { py -3.13 -m compileall backend\app evaluation }
    }

    if (-not $SkipRuff) {
        Invoke-Step "ruff" { .\.venv\Scripts\ruff.exe check backend\app backend\tests evaluation }
    }

    if (-not $SkipTests) {
        Invoke-Step "pytest" { py -3.13 -m pytest backend\tests -q }
    }

    if (-not $SkipKeywordEval) {
        Invoke-Step "keyword_eval" { py -3.13 evaluation\eval_keyword_baseline.py }
    }

    if (-not $SkipSemanticEval) {
        if ($status.semantic_prerequisites.ollama -and $status.semantic_prerequisites.qdrant) {
            Invoke-Step "semantic_eval" { py -3.13 evaluation\eval_semantic.py }
        }
        else {
            $step = [ordered]@{
                name = "semantic_eval"
                status = "skipped"
                started_at = (Get-Date).ToString("o")
                ended_at = (Get-Date).ToString("o")
                duration_seconds = 0
                error = "Skipped because Ollama or Qdrant is unavailable."
            }
            $status.steps += $step
            Write-Log "Skipped: semantic_eval because Ollama or Qdrant is unavailable."
            Save-Status
        }
    }

    if ($status.steps.Where({ $_.status -eq "failed" }).Count -gt 0) {
        $status.overall_status = "failed"
    }
    else {
        $status.overall_status = "passed"
    }
}
catch {
    $status.overall_status = "failed"
    $status.steps += [ordered]@{
        name = "quality_suite"
        status = "failed"
        started_at = (Get-Date).ToString("o")
        ended_at = (Get-Date).ToString("o")
        duration_seconds = 0
        error = $_.Exception.Message
    }
    Write-Log "Fatal error: $($_.Exception.Message)"
}
finally {
    $status.finished_at = (Get-Date).ToString("o")
    Save-Status
    Pop-Location
}

Write-Host ""
Write-Host "Quality suite finished with status: $($status.overall_status)"
Write-Host "Log: $LogFile"
Write-Host "Status: $LatestStatusFile"
