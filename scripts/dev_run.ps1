# Start the RAG service in development mode
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $projectRoot

Write-Host "Starting RAG service..." -ForegroundColor Cyan
Write-Host "  API docs: http://127.0.0.1:8000/docs" -ForegroundColor Gray
Write-Host "  Frontend: http://127.0.0.1:8000" -ForegroundColor Gray
Write-Host ""

python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
