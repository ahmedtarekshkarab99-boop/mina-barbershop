@echo off
setlocal

REM Full clean rebuild for "مدير صالون مينا العربي"

set APP_NAME=MinaAlArabiSalonManager
set DIST_ROOT=dist
set WORK_ROOT=build
set ENTRYPOINT=mina_al_arabi\main.py
set BUILD_LOG=%WORK_ROOT%\build_log.txt

echo.
echo [0/8] Validating project structure...
if not exist "%ENTRYPOINT%" (
  echo   ERROR: Entry point "%ENTRYPOINT%" not found. Please run this script from the project root.
  exit /b 1
)

echo.
echo [1/8] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [2/8] Installing app requirements...
pip install -r requirements.txt

echo.
echo [3/8] Installing build tool (PyInstaller)...
pip install pyinstaller

echo.
echo [4/8] Cleaning old outputs and caches...
if exist "%WORK_ROOT%" rmdir /s /q "%WORK_ROOT%"
if exist "%DIST_ROOT%" rmdir /s /q "%DIST_ROOT%"
if exist "%APP_NAME%.spec" del /f /q "%APP_NAME%.spec"

REM Remove __pycache__ folders across the repo
for /d /r %%i in (__pycache__) do (
  echo   Removing cache folder: %%i
  rmdir /s /q "%%i"
)

echo.
echo [5/8] Building EXE with PyInstaller (fresh spec)...
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
  -p . ^
  "%ENTRYPOINT%" > "%BUILD_LOG%" 2>&1

if errorlevel 1 (
  echo   ERROR: Build failed. See log: "%BUILD_LOG%"
  type "%BUILD_LOG%"
  exit /b 1
)

echo.
echo [6/8] Verifying output paths...
if not exist "%DIST_ROOT%\%APP_NAME%\%APP_NAME%.exe" (
  echo   ERROR: Expected executable not found at "%DIST_ROOT%\%APP_NAME%\%APP_NAME%.exe".
  echo   Build log follows:
  type "%BUILD_LOG%"
  echo   Possible causes:
  echo     - Antivirus or system protection blocked write to the dist folder.
  echo     - Hidden import missing; ensure modules are included.
  echo     - Build invoked from the wrong directory.
  exit /b 1
)

echo.
echo [7/8] Sanity check: listing dist content
dir /b "%DIST_ROOT%\%APP_NAME%"

echo.
echo [8/8] Done.
echo Executable path:
echo   %DIST_ROOT%\%APP_NAME%\%APP_NAME%.exe

echo.
echo Tip:
echo - Run the EXE from its dist folder. Do NOT move the EXE alone outside dist.
echo - If you need a single installer, run: build_installer_windows.bat
echo - If antivirus blocks build, whitelist the project folder.

endlocal