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

Write-Host 'Ollama version:' -ForegroundColor Cyan
& $ollamaExe --version

Write-Host "`nInstalled model:" -ForegroundColor Cyan
& $ollamaExe list | Select-String -Pattern 'qwen2.5:3b|NAME'

Write-Host "`nLoading qwen2.5:3b..." -ForegroundColor Cyan
$body = @{
    model = 'qwen2.5:3b'
    messages = @(@{ role = 'user'; content = 'Reply with exactly: ready' })
    stream = $false
    keep_alive = '10m'
    options = @{ num_ctx = 4096; num_gpu = -1; temperature = 0 }
} | ConvertTo-Json -Depth 5
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:11434/api/chat' -ContentType 'application/json' -Body $body | Out-Null

Write-Host "`nOllama processor allocation:" -ForegroundColor Cyan
& $ollamaExe ps

Write-Host "`nNVIDIA GPU process and memory usage:" -ForegroundColor Cyan
nvidia-smi

Write-Host "`nPASS when ollama ps shows 100% GPU (or GPU-dominant mixed allocation)." -ForegroundColor Green
