@echo off
setlocal

REM Build Windows executable for "Mina Al Arabi Salon Manager" exactly like the previous working process.

set APP_NAME=MinaAlArabiSalonManager
set DIST_DIR=dist\%APP_NAME%
set ENTRY_ATTENDANCE=mina_al_arabi\dashboards\attendance.py

echo.
echo [1/6] Checking attendance module exists...
if not exist "%ENTRY_ATTENDANCE%" (
  echo   ERROR: Missing file: %ENTRY_ATTENDANCE%
  echo   Please ensure the dashboards\attendance.py file exists.
  exit /b 1
)

echo.
echo [2/6] Installing requirements...
pip install -r requirements.txt

echo.
echo [3/6] Installing PyInstaller...
pip install pyinstaller

echo.
echo [4/6] Cleaning old outputs (build, dist, __pycache__, .pyc/.pyo)...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
for /d /r %%i in (__pycache__) do rmdir /s /q "%%i"
for /r %%f in (*.pyc) do del /f /q "%%f"
for /r %%f in (*.pyo) do del /f /q "%%f"

echo.
echo [5/6] Building via spec file...
pyinstaller "%APP_NAME%.spec" --clean
if errorlevel 1 (
  echo   ERROR: Build failed via spec file.
  exit /b 1
)

echo.
echo [6/6] Build finished. Final contents of "%DIST_DIR%":
dir /b "%DIST_DIR%"

endlocal