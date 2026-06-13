#!/usr/bin/env pwsh
<#
.SYNOPSIS
Reindex Qdrant collection with v2 embeddings and fixed product_name extraction.

.DESCRIPTION
This script rebuilds the Qdrant index using v2 embeddings files with the latest
fixes for product_name extraction from search_text. It prefers v2 files and ensures
product names are properly extracted and indexed in the Qdrant payload.

.PARAMETER EmbeddingsPath
Path to the embeddings parquet file (optional, auto-detects v2 files if not provided)

.PARAMETER Collection
Qdrant collection name (default: foodsense_products_v2)

.PARAMETER Recreate
Force recreate the collection (default: $true)

.PARAMETER BatchSize
Batch size for upserts (default: 100)

.EXAMPLE
./reindex_qdrant_v2.ps1

.EXAMPLE
./reindex_qdrant_v2.ps1 -Collection foodsense_products_v2 -Recreate $true
#>

param(
    [string]$EmbeddingsPath = "",
    [string]$Collection = "foodsense_products_v2",
    [bool]$Recreate = $true,
    [int]$BatchSize = 100
)

# Ensure we're in the project root
$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Write-Host "📁 Project root: $projectRoot"

# Change to project directory
Push-Location $projectRoot

try {
    # Activate Python environment if it exists
    $venvPaths = @(
        ".\.venv\Scripts\Activate.ps1",
        "./venv/Scripts/activate.ps1",
        "env/Scripts/activate.ps1"
    )
    
    foreach ($venvPath in $venvPaths) {
        if (Test-Path $venvPath) {
            Write-Host "✅ Found virtual environment at: $venvPath"
            & $venvPath
            break
        }
    }
    
    # Build command arguments
    $args = @("pipeline/04_index_qdrant.py")
    
    if ($EmbeddingsPath) {
        $args += "--embeddings-path", $EmbeddingsPath
    }
    
    $args += "--collection", $Collection
    
    if ($Recreate) {
        $args += "--recreate"
    }
    
    $args += "--batch-size", $BatchSize
    
    Write-Host "🚀 Starting Qdrant reindexing with v2 embeddings..."
    Write-Host "   Collection: $Collection"
    Write-Host "   Batch size: $BatchSize"
    Write-Host "   Recreate: $Recreate"
    Write-Host ""
    
    # Run the indexing script
    python @args
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Reindexing completed successfully!"
        Write-Host ""
        Write-Host "Next steps:"
        Write-Host "  1. Ensure your backend is running: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
        Write-Host "  2. Test search endpoint: curl 'http://127.0.0.1:8000/search?query=chocolate&top_k=3'"
        Write-Host "  3. Check that product names appear instead of 'Source productid'"
    } else {
        Write-Host ""
        Write-Host "❌ Reindexing failed with exit code: $LASTEXITCODE"
        exit $LASTEXITCODE
    }
} finally {
    Pop-Location
}
