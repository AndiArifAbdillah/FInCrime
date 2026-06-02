# ============================================================
#  FinCrime — Universal launcher
# ============================================================
#  Selalu pakai venv Python — tidak perlu Activate.ps1 dulu.
#
#  Usage:
#      .\fc demo                  # end-to-end pipeline
#      .\fc data                  # regenerate sample data
#      .\fc train                 # train all models
#      .\fc api                   # start FastAPI on :8000
#      .\fc dashboard             # start Streamlit on :8501
#      .\fc sanctions             # download OFAC list
#      .\fc import <csv> <acct>   # import a bank CSV
#      .\fc score                 # score imported real data
#      .\fc blockchain            # pull real Etherscan data
#      .\fc test                  # run pytest
#      .\fc shell                 # python REPL with venv
#      .\fc <anything else>       # forwards to venv python
# ============================================================

$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $PSScriptRoot

# Prefer .venv312 (full PyTorch stack) if it exists, else fall back to .venv
$Venv312 = Join-Path $PSScriptRoot ".venv312\Scripts\python.exe"
$Venv    = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (Test-Path $Venv312)   { $VenvPy = $Venv312 }
elseif (Test-Path $Venv)  { $VenvPy = $Venv }
else {
    Write-Host "[!] Tidak ada venv ditemukan: $Venv312 atau $Venv" -ForegroundColor Red
    Write-Host "    Buat venv dulu:  py -m venv .venv  ATAU  py -3.12 -m venv .venv312" -ForegroundColor Yellow
    exit 1
}

# Redirect pip cache to D: (C: drive sering penuh)
$env:TMP = "D:\pip-tmp"
$env:TEMP = "D:\pip-tmp"
$env:PIP_CACHE_DIR = "D:\pip-cache"
$env:PYTHONIOENCODING = "utf-8"
New-Item -ItemType Directory -Force -Path "D:\pip-tmp" | Out-Null
New-Item -ItemType Directory -Force -Path "D:\pip-cache" | Out-Null

$cmd = if ($args.Count -gt 0) { $args[0].ToLower() } else { "help" }
$rest = if ($args.Count -gt 1) { $args[1..($args.Count - 1)] } else { @() }

function Run-Py {
    param([string[]]$Arguments)
    & $VenvPy @Arguments
}

switch ($cmd) {
    "help" {
        Write-Host "`nFinCrime launcher" -ForegroundColor Cyan
        Write-Host "  Using: $VenvPy`n" -ForegroundColor DarkGray
        Write-Host "  .\fc demo                  Run end-to-end pipeline demo"
        Write-Host "  .\fc data                  Regenerate synthetic sample data"
        Write-Host "  .\fc train                 Train all models (Layer 0 + 1 [+ 2 if torch])"
        Write-Host "  .\fc web                   Start web UI + API on http://localhost:8000 (RECOMMENDED)"
        Write-Host "  .\fc api                   Same as 'web' (FastAPI on :8000)"
        Write-Host "  .\fc dashboard             Old Streamlit UI on http://localhost:8501"
        Write-Host "  .\fc sanctions             Download OFAC sanctions list"
        Write-Host "  .\fc import <csv> <acct>   Import a bank statement CSV"
        Write-Host "  .\fc score                 Score imported real-data transactions"
        Write-Host "  .\fc blockchain            Pull real Etherscan data (needs API key)"
        Write-Host "  .\fc test                  Run pytest"
        Write-Host "  .\fc shell                 Open Python REPL with venv"
        Write-Host "  .\fc install               Install/refresh requirements"
        Write-Host "  .\fc python <args>         Run any python command via venv`n"
    }
    "demo"       { Run-Py @("scripts\run_pipeline.py")             + $rest }
    "data"       { Run-Py @("scripts\generate_sample_data.py")     + $rest }
    "train"      { Run-Py @("scripts\train_all_models.py")         + $rest }
    "api"        { Run-Py @("-m", "uvicorn", "src.api.main:app", "--reload", "--port", "8000") }
    "web"        {
        Write-Host "`n  FinCrime Web UI" -ForegroundColor Cyan
        Write-Host "  Open in browser: http://localhost:8000/" -ForegroundColor Green
        Write-Host "  API docs:        http://localhost:8000/docs`n" -ForegroundColor DarkGray
        Run-Py @("-m", "uvicorn", "src.api.main:app", "--reload", "--port", "8000")
    }
    "dashboard"  { Run-Py @("-m", "streamlit", "run", "src\dashboard\app.py") }
    "sanctions"  { Run-Py @("scripts\fetch_sanctions.py")          + $rest }
    "import"     {
        if ($rest.Count -lt 2) {
            Write-Host "Usage: .\fc import <csv-path> <account-id> [--bank bca|mandiri|bri|bni]" -ForegroundColor Yellow
            exit 1
        }
        $csv = $rest[0]; $acct = $rest[1]
        $extra = if ($rest.Count -gt 2) { $rest[2..($rest.Count - 1)] } else { @() }
        Run-Py @("scripts\import_bank_csv.py", $csv, "--account", $acct) + $extra
    }
    "score"      { Run-Py @("scripts\score_real_data.py")          + $rest }
    "blockchain" { Run-Py @("scripts\fetch_real_blockchain.py")    + $rest }
    "test"       { Run-Py @("-m", "pytest", "-m", "not slow", "-v") + $rest }
    "telegram"   { Run-Py @("-m", "src.integrations.telegram_bot") + $rest }
    "etherscan-setup" { Run-Py @("scripts\setup_etherscan_key.py") }
    "elliptic"   { Run-Py @("scripts\import_elliptic.py") + $rest }
    "mlflow"     { Run-Py @("-m", "mlflow", "ui", "--backend-store-uri", "file:./data/mlruns", "--port", "5000") }
    "mlflow-train" { Run-Py @("scripts\train_with_mlflow.py") + $rest }
    "stack"      {
        Write-Host "`n  Starting full FinCrime stack via docker-compose ..." -ForegroundColor Cyan
        Write-Host "  Services: api+UI :8000 · neo4j :7474 · prometheus :9090 · grafana :3000 · mlflow :5000`n" -ForegroundColor DarkGray
        docker-compose up --build
    }
    "shell"      { Run-Py @() }
    "install"    { Run-Py @("-m", "pip", "install", "-r", "requirements-core.txt") }
    "python"     { Run-Py $rest }
    default      { Run-Py @($cmd) + $rest }
}
