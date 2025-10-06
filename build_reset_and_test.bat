@echo off
setlocal

REM Reset, rebuild, create installer, install silently to temp, run app, and uninstall.

set APP_NAME=MinaAlArabiSalonManager
set ENTRYPOINT=mina_al_arabi\main.py
set DIST_DIR=dist\%APP_NAME%
set SETUP_OUT=installer\windows\output\MinaAlArabiSalonManagerSetup.exe
set TEST_DIR=%TEMP%\MinaAlArabiTest

echo.
echo [0/8] Validating project structure...
if not exist "%ENTRYPOINT%" (
  echo   ERROR: Entry point "%ENTRYPOINT%" not found. Please run from project root.
  exit /b 1
)

echo.
echo [1/8] Cleaning old outputs...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "%APP_NAME%.spec" del /f /q "%APP_NAME%.spec"
for /d /r %%i in (__pycache__) do rmdir /s /q "%%i"

echo.
echo [2/8] Installing requirements and PyInstaller...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo [3/8] Building EXE...
pyinstaller --noconfirm ^
  --name "%APP_NAME%" ^
  --windowed ^
  --clean ^
  --collect-all PySide6 ^
  --collect-submodules mina_al_arabi ^
  --hidden-import mina_al_arabi.dashboards.attendance ^
  --hidden-import mina_al_arabi.dashboards.cashier ^
  --hidden-import mina_al_arabi.dashboards.inventory ^
  --hidden-import mina_al_arabi.dashboards.sales ^
  --hidden-import mina_al_arabi.dashboards.expenses ^
  --hidden-import mina_al_arabi.dashboards.reports ^
  --additional-hooks-dir hooks ^
  -p . ^
  "%ENTRYPOINT%"
if errorlevel 1 (
  echo   ERROR: Build failed.
  exit /b 1
)

if not exist "%DIST_DIR%\%APP_NAME%.exe" (
  echo   ERROR: Executable not found: "%DIST_DIR%\%APP_NAME%.exe"
  exit /b 1
)

echo.
echo [4/8] Building installer...
call build_installer_windows.bat
if errorlevel 1 (
  echo   ERROR: Installer build failed.
  exit /b 1
)

echo.
echo [5/8] Installing silently to temp: "%TEST_DIR%"
if exist "%TEST_DIR%" rmdir /s /q "%TEST_DIR%"
mkdir "%TEST_DIR%"
where iscc >nul 2>&1
if errorlevel 1 (
  echo   NOTE: You may need admin rights to install silently.
)
"%SETUP_OUT%" /VERYSILENT /DIR="%TEST_DIR%" /NORESTART
if errorlevel 1 (
  echo   ERROR: Silent install failed.
  exit /b 1
)

echo.
echo [6/8] Running installed app (5 seconds)...
start "" /B "%TEST_DIR%\%APP_NAME%\%APP_NAME%.exe"
timeout /t 5 >nul
tasklist | find /i "%APP_NAME%.exe" >nul
if not errorlevel 1 taskkill /f /im "%APP_NAME%.exe" >nul 2>&1

echo.
echo [7/8] Uninstalling silent...
for %%f in ("%TEST_DIR%\%APP_NAME%\unins*.exe") do (
  "%%~f" /VERYSILENT /NORESTART
)

echo.
echo [8/8] Done. Installer and EXE verified.
echo - EXE: %DIST_DIR%\%APP_NAME%.exe
echo - Setup: %SETUP_OUT%

endlocal