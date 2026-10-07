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
    throw 'Ollama was not found. Install it or set OLLAMA_EXE.'
}

$env:OLLAMA_HOST = '127.0.0.1:11434'
& $ollamaExe pull qwen2.5:3b
