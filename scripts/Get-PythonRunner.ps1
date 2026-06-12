function Test-PythonRunner {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Runner,
        [string[]]$RunnerArgs = @()
    )

    $output = $null
    try {
        $output = & $Runner @RunnerArgs -c "import sys; print(sys.executable)" 2>&1
        $exitCode = $LASTEXITCODE
    }
    catch {
        return [pscustomobject]@{
            Success = $false
            Message = $_.Exception.Message
        }
    }

    if ($exitCode -eq 0) {
        return [pscustomobject]@{
            Success = $true
            Message = (($output | Out-String).Trim())
        }
    }

    $message = (($output | Out-String).Trim())
    if ([string]::IsNullOrWhiteSpace($message)) {
        $message = "Python runner exited with code $exitCode."
    }

    return [pscustomobject]@{
        Success = $false
        Message = $message
    }
}

function Resolve-PythonRunner {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ProjectRoot,
        [string]$PythonVersion = "3.12",
        [string]$PythonExecutable,
        [switch]$SkipVenv
    )

    $candidates = New-Object System.Collections.Generic.List[object]

    if ($PythonExecutable) {
        $resolvedPath = if (Test-Path $PythonExecutable) {
            (Resolve-Path $PythonExecutable).Path
        } else {
            $PythonExecutable
        }

        $candidates.Add([pscustomobject]@{
                Label = "explicit"
                Runner = $resolvedPath
                Args = @()
            })
    }

    if (-not $SkipVenv) {
        $venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
        if (Test-Path $venvPython) {
            $candidates.Add([pscustomobject]@{
                    Label = "venv"
                    Runner = $venvPython
                    Args = @()
                })
        }
    }

    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        $candidates.Add([pscustomobject]@{
                Label = "python"
                Runner = $pythonCommand.Source
                Args = @()
            })
    }

    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        $candidates.Add([pscustomobject]@{
                Label = "py"
                Runner = $pyLauncher.Source
                Args = @("-$PythonVersion")
            })
    }

    if ($candidates.Count -eq 0) {
        throw "Aucun interpreteur Python n'a ete trouve. Installe Python 3.12+ ou passe -PythonExecutable."
    }

    $failures = New-Object System.Collections.Generic.List[string]
    foreach ($candidate in $candidates) {
        $probe = Test-PythonRunner -Runner $candidate.Runner -RunnerArgs $candidate.Args
        if ($probe.Success) {
            return [pscustomobject]@{
                Runner = $candidate.Runner
                Args = $candidate.Args
                Label = $candidate.Label
                Executable = $probe.Message
            }
        }

        $failures.Add(("- {0}: {1}" -f $candidate.Label, $probe.Message))
    }

    $failureBlock = ($failures -join [Environment]::NewLine)
    throw @"
Aucun interpreteur Python exploitable n'a ete trouve.

Candidats testes :
$failureBlock

Cause probable :
- le venv ou le lanceur py.exe pointe vers un alias Microsoft Store (WindowsApps) devenu inutilisable

Correctif recommande :
1. installer/reparer un vrai Python 3.12+ hors Windows Store, ou fournir -PythonExecutable
2. recreer l'environnement avec .\scripts\bootstrap_local_env.ps1 -RecreateVenv
3. relancer ensuite .\scripts\start_backend.ps1
"@
}