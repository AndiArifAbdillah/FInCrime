@echo off
REM ============================================================
REM  FinCrime launcher (cmd-prompt wrapper)
REM  Tidak perlu venv activation. Cukup: fc demo
REM ============================================================
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0fc.ps1" %*
