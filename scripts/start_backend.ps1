$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$backendDirectory = Join-Path $projectRoot 'backend'
$venvPython = Join-Path $backendDirectory '.venv\Scripts\python.exe'

if (Test-Path -LiteralPath $venvPython) {
    $pythonExe = $venvPython
} else {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
        throw 'Python was not found. Create backend/.venv before starting the backend.'
    }
    $pythonExe = $pythonCommand.Source
}

Push-Location $backendDirectory
try {
    # Running the module avoids the uvicorn.exe launcher, which some Windows
    # Application Control policies block even when python.exe is permitted.
    & $pythonExe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
} finally {
    Pop-Location
}
