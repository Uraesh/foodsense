param(
    [string]$TargetEnvFile = ".env",
    [string]$SummaryModel = "llama3.2:1b",
    [int]$EmbeddingQueryMaxChars = 320,
    [int]$SearchTopK = 5,
    [int]$SearchCandidatePool = 12,
    [string]$OllamaKeepAlive = "45s"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$TemplatePath = Join-Path $ProjectRoot ".env.example"
$TargetPath = if ([System.IO.Path]::IsPathRooted($TargetEnvFile)) {
    $TargetEnvFile
} else {
    Join-Path $ProjectRoot $TargetEnvFile
}

if (-not (Test-Path $TemplatePath)) {
    throw "Fichier modele introuvable: $TemplatePath"
}

function Read-EnvMap([string]$Path) {
    $map = [ordered]@{}
    if (-not (Test-Path $Path)) {
        return $map
    }

    foreach ($line in Get-Content $Path) {
        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }
        if ($line.TrimStart().StartsWith("#")) {
            continue
        }

        $separatorIndex = $line.IndexOf("=")
        if ($separatorIndex -lt 0) {
            continue
        }

        $key = $line.Substring(0, $separatorIndex).Trim()
        $value = $line.Substring($separatorIndex + 1)
        $map[$key] = $value
    }

    return $map
}

$templateMap = Read-EnvMap $TemplatePath
$targetMap = Read-EnvMap $TargetPath

foreach ($entry in $templateMap.GetEnumerator()) {
    if (-not $targetMap.Contains($entry.Key)) {
        $targetMap[$entry.Key] = $entry.Value
    }
}

$overrides = [ordered]@{
    "SUMMARY_STRATEGY" = "extractive"
    "SUMMARY_MODEL" = $SummaryModel
    "OLLAMA_KEEP_ALIVE" = $OllamaKeepAlive
    "EMBEDDING_QUERY_MAX_CHARS" = "$EmbeddingQueryMaxChars"
    "SEARCH_TOP_K" = "$SearchTopK"
    "SEARCH_CANDIDATE_POOL" = "$SearchCandidatePool"
    "QDRANT_TIMEOUT_SECONDS" = "1.0"
    "EMBEDDING_CACHE_TTL_SECONDS" = "600"
    "SEARCH_SEMANTIC_WEIGHT" = "0.70"
    "SEARCH_LEXICAL_WEIGHT" = "0.30"
}

foreach ($entry in $overrides.GetEnumerator()) {
    $targetMap[$entry.Key] = $entry.Value
}

$lines = @(
    "# Auto-generated low-resource profile for FoodSense",
    "# This file is safe to regenerate with scripts\\enable_low_resource_mode.ps1",
    ""
)

foreach ($entry in $targetMap.GetEnumerator()) {
    $lines += "$($entry.Key)=$($entry.Value)"
}

$targetDir = Split-Path $TargetPath -Parent
if ($targetDir -and -not (Test-Path $targetDir)) {
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
}

Set-Content -LiteralPath $TargetPath -Value $lines -Encoding ASCII

Write-Host "Low-resource profile written to $TargetPath"
Write-Host ""
Write-Host "Applied overrides:"
foreach ($entry in $overrides.GetEnumerator()) {
    Write-Host "  $($entry.Key)=$($entry.Value)"
}
Write-Host ""
Write-Host "Recommended startup order:"
Write-Host "  1. .\\scripts\\start_ollama.ps1 -LowMemory"
Write-Host "  2. .\\scripts\\start_docker_stack.ps1 -QdrantOnly"
Write-Host "  3. .\\scripts\\start_backend.ps1"
