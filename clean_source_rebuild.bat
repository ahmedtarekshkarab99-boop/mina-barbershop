@echo off
setlocal

REM Clean everything related to build/env, keep only source code, then rebuild fresh.

set APP_NAME=MinaAlArabiSalonManager
set ENTRYPOINT=main.py
set DIST_DIR=dist\%APP_NAME%
set BUILD_DIR=build
set VENV_DIR=.venv
set BUILD_LOG=%BUILD_DIR%\build_log.txt

echo.
echo [1/8] Removing previous build outputs and caches...
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
if exist "dist" rmdir /s /q "dist"
if exist "%APP_NAME%.spec" del /f /q "%APP_NAME%.spec"
if exist "%VENV_DIR%" rmdir /s /q "%VENV_DIR%"
for /d /r %%i in (__pycache__) do rmdir /s /q "%%i"
for /r %%f in (*.pyc) do del /f /q "%%f"
for /r %%f in (*.pyo) do del /f /q "%%f"

echo.
echo [2/8] Creating fresh virtual environment...
python -m venv "%VENV_DIR%"
if errorlevel 1 (
  echo   ERROR: Failed to create venv.
  exit /b 1
)
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
  echo   ERROR: Failed to activate venv.
  exit /b 1
)

echo.
echo [3/8] Upgrading pip and installing requirements...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

echo.
echo [4/8] Building fresh EXE with explicit hidden imports...
mkdir "%BUILD_DIR%" >nul 2>&1
pyinstaller --noconfirm ^
  --onefile ^
  --name "%APP_NAME%" ^
  --clean ^
  --distpath "%DIST_DIR%" ^
  --workpath "%BUILD_DIR%" ^
  --specpath "%BUILD_DIR%" ^
  --hidden-import mina_al_arabi.dashboards.attendance ^
  --hidden-import mina_al_arabi.dashboards.cashier ^
  --hidden-import mina_al_arabi.dashboards.inventory ^
  --hidden-import mina_al_arabi.dashboards.sales ^
  --hidden-import mina_al_arabi.dashboards.expenses ^
  --hidden-import mina_al_arabi.dashboards.reports ^
  -p . ^
  "%ENTRYPOINT%" > "%BUILD_LOG%" 2>&1

if errorlevel 1 (
  echo   ERROR: Build failed. See log: "%BUILD_LOG%"
  type "%BUILD_LOG%"
  exit /b 1
)

echo.
echo [5/8] Verifying output...
if not exist "%DIST_DIR%\%APP_NAME%.exe" (
  echo   ERROR: Expected executable not found at "%DIST_DIR%\%APP_NAME%.exe"
  echo   Build log:
  type "%BUILD_LOG%"
  echo   Possible causes:
  echo     - Antivirus blocked write to dist.
  echo     - Script was not run from project root.
  exit /b 1
)

echo.
echo [6/8] Listing dist contents:
dir /b "%DIST_DIR%"

echo.
echo [7/8] Test-run the app (5 seconds)...
start "" /B "%DIST_DIR%\%APP_NAME%.exe"
timeout /t 5 >nul
tasklist | find /i "%APP_NAME%.exe" >nul
if not errorlevel 1 taskkill /f /im "%APP_NAME%.exe" >nul 2>&1

echo.
echo [8/8] Build completed successfully.
echo Executable:
echo   %DIST_DIR%\%APP_NAME%.exe
echo Build log:
echo   %BUILD_LOG%

endlocal