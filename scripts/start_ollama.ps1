$ErrorActionPreference = 'Stop'

$portableOllama = 'D:\Codex\Tools\OllamaPortable\ollama.exe'
$installedOllama = Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'
$ollamaCommand = Get-Command ollama -ErrorAction SilentlyContinue

if ($env:OLLAMA_EXE) {
    $ollamaExe = $env:OLLAMA_EXE
} elseif ($ollamaCommand) {
    $ollamaExe = $ollamaCommand.Source
} elseif (Test-Path -LiteralPath $installedOllama) {
    $ollamaExe = $installedOllama
} elseif (Test-Path -LiteralPath $portableOllama) {
    $ollamaExe = $portableOllama
} else {
    throw 'Ollama was not found. Install it from https://ollama.com/download/windows or set OLLAMA_EXE.'
}

$usingPortableFallback = $ollamaExe -eq $portableOllama
$taskProfile = $env:OLLAMA_USER_PROFILE
$modelDirectory = $env:OLLAMA_MODELS

if ($usingPortableFallback) {
    if (-not $taskProfile) { $taskProfile = 'D:\Codex\Tools\OllamaHome' }
    if (-not $modelDirectory) { $modelDirectory = 'D:\Codex\Tools\OllamaModels' }
}

if ($taskProfile) {
    New-Item -ItemType Directory -Path $taskProfile -Force | Out-Null
    # Changed only for this script process so the portable build has a writable
    # location for its local identity and configuration.
    $env:USERPROFILE = $taskProfile
}
if ($modelDirectory) {
    New-Item -ItemType Directory -Path $modelDirectory -Force | Out-Null
    $env:OLLAMA_MODELS = $modelDirectory
}
$env:OLLAMA_HOST = '127.0.0.1:11434'
$env:OLLAMA_KEEP_ALIVE = '10m'
$env:OLLAMA_FLASH_ATTENTION = '1'

Write-Host "Starting Ollama $(& $ollamaExe --version 2>&1 | Select-Object -Last 1)" -ForegroundColor Cyan
Write-Host "API: http://$($env:OLLAMA_HOST)" -ForegroundColor Cyan
Write-Host "Models: $(if ($modelDirectory) { $modelDirectory } else { 'Ollama default' })" -ForegroundColor Cyan
Write-Host 'Leave this terminal open while using QueryPilot.' -ForegroundColor Yellow

& $ollamaExe serve
