# AI Talk Practice - Backend Server Startup Script for Windows

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

if (!(Test-Path ".env")) {
    Write-Host "⚠️  No .env file found. Creating from .env.example..."
    Copy-Item ".env.example" ".env"
    Write-Host "📝 Please edit .env and set your API keys, then run this script again."
    exit 1
}

if (!(Test-Path ".venv")) {
    Write-Host "📦 Creating virtual environment..."
    python -m venv .venv
}

& ".\.venv\Scripts\Activate.ps1"

Write-Host "📦 Installing dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt --quiet

Write-Host "🛠️ Checking and applying database migrations..."
alembic upgrade head

Write-Host ""
Write-Host "🚀 Starting AI Talk Practice Backend..."
Write-Host "   Host:      0.0.0.0"
Write-Host "   Port:      8000"
Write-Host ""

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
