# Start Fashion AI API locally (zero-card defaults)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    python -m venv .venv
    .\.venv\Scripts\pip install -r requirements.txt
}

if (-not (Test-Path ".env")) {
    Copy-Item .env.example .env
    Write-Host "Created .env — add GROQ_API_KEY and HUGGINGFACE_API_KEY (free, no card)"
}

$env:PYTHONPATH = $Root
$env:DATABASE_URL = "sqlite+aiosqlite:///./fashionai.db"
$env:STORAGE_BACKEND = "local"
$env:STORAGE_LOCAL_PATH = "./storage"

Write-Host "API: http://127.0.0.1:8000/docs"
.\.venv\Scripts\python -m uvicorn services.api.main:app --reload --host 127.0.0.1 --port 8000
