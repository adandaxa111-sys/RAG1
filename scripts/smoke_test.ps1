# Quick smoke test: ingest a document then query it
$ErrorActionPreference = "Stop"
$base = "http://127.0.0.1:8000"

Write-Host "=== Smoke Test ===" -ForegroundColor Cyan

# Health check
Write-Host "`n[1] Health check..." -ForegroundColor Yellow
$health = Invoke-RestMethod "$base/health"
Write-Host "  Status: $($health.status), Docs: $($health.documents), Chunks: $($health.chunks)"

# Ingest text
Write-Host "`n[2] Ingesting test document..." -ForegroundColor Yellow
$body = @{
    text = "The Eiffel Tower is a wrought-iron lattice tower in Paris, France. It was constructed from 1887 to 1889 as the entrance arch for the 1889 World's Fair. The tower is 330 metres tall and is the tallest structure in Paris."
    document_name = "test_doc.txt"
} | ConvertTo-Json

$ingest = Invoke-RestMethod "$base/ingest_text" -Method Post -ContentType "application/json" -Body $body
Write-Host "  Ingested: $($ingest.document_name) ($($ingest.chunks_added) chunks)"

# Query
Write-Host "`n[3] Querying..." -ForegroundColor Yellow
$query = @{ question = "How tall is the Eiffel Tower?" } | ConvertTo-Json
$result = Invoke-RestMethod "$base/query" -Method Post -ContentType "application/json" -Body $query
Write-Host "  Answer: $($result.answer)"
Write-Host "  Sources: $($result.sources.Count)"

Write-Host "`n=== Done ===" -ForegroundColor Green
