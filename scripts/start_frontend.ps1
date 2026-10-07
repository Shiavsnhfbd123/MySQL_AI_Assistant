$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$frontendDirectory = Join-Path $projectRoot 'frontend'
$packageFile = Join-Path $frontendDirectory 'package.json'
$nodeModules = Join-Path $frontendDirectory 'node_modules'

if (-not (Test-Path -LiteralPath $packageFile)) {
    throw "Frontend package.json was not found at $packageFile"
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw 'npm was not found. Install Node.js 20 or newer.'
}
if (-not (Test-Path -LiteralPath $nodeModules)) {
    throw 'Frontend dependencies are missing. Run npm install inside the frontend directory first.'
}

Push-Location $frontendDirectory
try {
    npm run dev -- --host 127.0.0.1
} finally {
    Pop-Location
}
