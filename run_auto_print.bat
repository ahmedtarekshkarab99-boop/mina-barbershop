@echo off
REM Auto-print receipts watcher
REM Ensure venv or global python has pywin32 installed: pip install pywin32

SET SCRIPT=mina_al_arabi\auto_print.py

IF NOT EXIST "%SCRIPT%" (
  echo Auto print script not found: %SCRIPT%
  exit /b 1
)

echo Starting auto print watcher...
python "%SCRIPT%"