# ============================================================
#  FinCrime — Windows / PowerShell setup script
# ============================================================
#  Usage:
#      powershell -ExecutionPolicy Bypass -File .\setup.ps1
#  Or, if execution policy permits:
#      .\setup.ps1
# ============================================================

$ErrorActionPreference = "Stop"
$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $PSScriptRoot

Write-Host ""
Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host "  FinCrime — Setup"                                          -ForegroundColor Cyan
Write-Host "==============================================================" -ForegroundColor Cyan

# ---------- 1. Find or create venv ----------
$venvPython = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "[1/4] Creating virtual environment in .venv ..." -ForegroundColor Yellow
    py -m venv .venv
} else {
    Write-Host "[1/4] Found existing .venv" -ForegroundColor Green
}

# Verify Python version
$pyVer = & $venvPython --version
Write-Host "      Using: $pyVer"

# Warn if Python 3.14+ (PyTorch wheels may not exist yet)
$is314Plus = $pyVer -match "3\.(1[4-9]|[2-9]\d)"
if ($is314Plus) {
    Write-Host ""
    Write-Host "  !! WARNING: Python 3.14+ detected. Some heavy deps " -ForegroundColor Yellow
    Write-Host "     (PyTorch, torch-geometric, weasyprint, shap) may not"      -ForegroundColor Yellow
    Write-Host "     have wheels yet for this version."                          -ForegroundColor Yellow
    Write-Host "     The setup will use requirements-core.txt (essentials only)." -ForegroundColor Yellow
    Write-Host ""
}

# ---------- 2. Upgrade pip ----------
Write-Host "[2/4] Upgrading pip ..." -ForegroundColor Yellow
& $venvPython -m pip install --upgrade pip setuptools wheel

# ---------- 3. Install dependencies ----------
$reqFile = if ($is314Plus) { "requirements-core.txt" } else { "requirements.txt" }
Write-Host "[3/4] Installing from $reqFile ..." -ForegroundColor Yellow
& $venvPython -m pip install -r $reqFile

# ---------- 4. Generate sample data ----------
Write-Host "[4/4] Generating sample data ..." -ForegroundColor Yellow
& $venvPython scripts\generate_sample_data.py

Write-Host ""
Write-Host "==============================================================" -ForegroundColor Green
Write-Host "  SETUP COMPLETE"                                                -ForegroundColor Green
Write-Host "==============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps (activate venv first):" -ForegroundColor Cyan
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host ""
Write-Host "Then run:" -ForegroundColor Cyan
Write-Host "  python scripts\train_all_models.py    # train all layers"
Write-Host "  python scripts\run_pipeline.py        # end-to-end demo"
Write-Host "  uvicorn src.api.main:app --reload     # API on :8000"
Write-Host "  streamlit run src\dashboard\app.py    # UI on :8501"
Write-Host ""
if ($is314Plus) {
    Write-Host "Optional heavy deps (may need Python 3.11/3.12):" -ForegroundColor Yellow
    Write-Host "  python -m pip install torch shap weasyprint torch-geometric"
    Write-Host ""
}
