# Menú para correr el proyecto.  Uso:  .\iniciar.ps1
Set-Location $PSScriptRoot
$env:PYTHONUTF8 = "1"
$env:HF_HUB_DISABLE_PROGRESS_BARS = "1"

if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }

function Falta-Clave($nombre) {
    $linea = Select-String -Path ".env" -Pattern "^$nombre\s*=\s*(.+)$" -ErrorAction SilentlyContinue
    return -not $linea
}

if (Falta-Clave "ANTHROPIC_API_KEY") {
    Write-Host "Falta ANTHROPIC_API_KEY. Se abre .env para que la pegue (guarde y cierre)." -ForegroundColor Yellow
    notepad ".env" | Out-Null
}
if (Falta-Clave "LANGSMITH_API_KEY") {
    Write-Host "Aviso: sin LANGSMITH_API_KEY no se verá el coste en LangSmith." -ForegroundColor Yellow
}

Write-Host "Preparando entorno (la primera vez tarda unos minutos)..." -ForegroundColor Cyan
uv sync --quiet

while ($true) {
    Write-Host ""
    Write-Host "=== Chat con PDF: RAG + ChromaDB + RAGAS + LangSmith ===" -ForegroundColor Green
    Write-Host "1) Indexar el PDF en ChromaDB"
    Write-Host "2) Chatear con el PDF"
    Write-Host "3) Evaluar precision con RAGAS"
    Write-Host "4) Salir"
    $op = Read-Host "Opcion"
    switch ($op) {
        "1" { uv run python -W ignore -m app.ingesta pdfs/GUIA_Mininet_OpenFlow.pdf }
        "2" { uv run python -W ignore -m app.chat }
        "3" { uv run python -W ignore -m app.evaluar }
        "4" { break }
    }
    if ($op -eq "4") { break }
}
