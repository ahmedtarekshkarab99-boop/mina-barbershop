@echo off
setlocal

REM Fresh rebuild: remove old installs/builds, create clean venv, reinstall deps, rebuild EXE and installer.

set APP_NAME=MinaAlArabiSalonManager
set ENTRYPOINT=mina_al_arabi\main.py
set DIST_ROOT=dist
set WORK_ROOT=build
set INSTALL_DIR="%ProgramFiles%\MinaAlArabiSalonManager"
set INSTALL_DIR_X86="%ProgramFiles(x86)%\MinaAlArabiSalonManager"
set SETUP_OUT=installer\windows\output\MinaAlArabiSalonManagerSetup.exe

echo.
echo [0/9] Validating project structure...
if not exist "%ENTRYPOINT%" (
  echo   ERROR: Entry point "%ENTRYPOINT%" not found. Please run this script from the project root.
  exit /b 1
)

echo.
echo [1/9] Uninstalling any previous installations (silent)...
set FOUND_UNINSTALL=0
for %%f in (%INSTALL_DIR%\unins*.exe) do (
  set FOUND_UNINSTALL=1
  echo   Running uninstaller: %%~f
  "%%~f" /VERYSILENT /NORESTART
)
for %%f in (%INSTALL_DIR_X86%\unins*.exe) do (
  set FOUND_UNINSTALL=1
  echo   Running uninstaller (x86): %%~f
  "%%~f" /VERYSILENT /NORESTART
)
if "%FOUND_UNINSTALL%"=="0" (
  echo   No existing installation found in Program Files.
)

echo.
echo [2/9] Cleaning previous outputs and caches...
if exist "%WORK_ROOT%" rmdir /s /q "%WORK_ROOT%"
if exist "%DIST_ROOT%" rmdir /s /q "%DIST_ROOT%"
if exist "%APP_NAME%.spec" del /f /q "%APP_NAME%.spec"
if exist "installer\windows\output" rmdir /s /q "installer\windows\output"
for /d /r %%i in (__pycache__) do (
  rmdir /s /q "%%i"
)

echo.
echo [3/9] Removing previous virtual environment (.venv) if exists...
if exist ".venv" rmdir /s /q ".venv"

echo.
echo [4/9] Creating fresh virtual environment...
python -m venv .venv
if errorlevel 1 (
  echo   ERROR: Failed to create virtual environment.
  exit /b 1
)
call ".venv\Scripts\activate.bat"
if errorlevel 1 (
  echo   ERROR: Failed to activate virtual environment.
  exit /b 1
)

echo.
echo [5/9] Upgrading pip and installing requirements inside venv...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

echo.
echo [6/9] Building EXE in fresh environment...
pyinstaller --noconfirm ^
  --name "%APP_NAME%" ^
  --windowed ^
  --clean ^
  --distpath "%DIST_ROOT%" ^
  --workpath "%WORK_ROOT%" ^
  --specpath "%WORK_ROOT%" ^
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

if not exist "%DIST_ROOT%\%APP_NAME%\%APP_NAME%.exe" (
  echo   ERROR: Executable not found: "%DIST_ROOT%\%APP_NAME%\%APP_NAME%.exe"
  exit /b 1
)

echo.
echo [7/9] Building installer with Inno Setup...
where iscc >nul 2>&1
if errorlevel 1 (
  echo   ERROR: Inno Setup compiler (iscc) not found in PATH.
  echo   Install Inno Setup from: https://jrsoftware.org/isdl.php
  echo   Then ensure iscc.exe is in PATH (usually "C:\Program Files (x86)\Inno Setup 6\iscc.exe").
  goto :skip_installer
)
call build_installer_windows.bat
if errorlevel 1 (
  echo   ERROR: Installer build failed.
  goto :skip_installer
)
if exist "%SETUP_OUT%" (
  echo   Installer created: %SETUP_OUT%
) else (
  echo   WARN: Installer output not found at "%SETUP_OUT%".
)

:skip_installer

echo.
echo [8/9] Test-running the new EXE (5 seconds)...
start "" /B "%DIST_ROOT%\%APP_NAME%\%APP_NAME%.exe"
timeout /t 5 >nul
tasklist | find /i "%APP_NAME%.exe" >nul
if not errorlevel 1 taskkill /f /im "%APP_NAME%.exe" >nul 2>&1

echo.
echo [9/9] Fresh rebuild completed successfully.
echo - EXE: %DIST_ROOT%\%APP_NAME%\%APP_NAME%.exe
echo - Setup (if built): %SETUP_OUT%

echo.
echo Notes:
echo - Run the EXE from inside the dist folder.
echo - If antivirus blocks output, whitelist the project folder.
echo - Attendance and all dashboards are explicitly included in the build.

endlocal