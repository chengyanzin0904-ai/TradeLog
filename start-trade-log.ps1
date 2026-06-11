$ErrorActionPreference = "Stop"

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir

$Python = Join-Path $ProjectDir ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    Write-Host "Python virtual environment not found." -ForegroundColor Red
    Write-Host "Please run:"
    Write-Host "  python -m venv .venv"
    Write-Host "  .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
    Read-Host "Press Enter to exit"
    exit 1
}

Start-Process "http://localhost:8501"
& $Python -m streamlit run app.py --server.port 8501

