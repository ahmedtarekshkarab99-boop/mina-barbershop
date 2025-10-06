@echo off
setlocal

REM Build Windows executable for "مدير صالون مينا العربي"

set DIST_ROOT=dist
set WORK_ROOT=build
set APP_NAME=MinaAlArabiSalonManager
set ENTRYPOINT=mina_al_arabi\main.py
set DIST_DIR=%DIST_ROOT%\%APP_NAME%
set BUILD_LOG=%WORK_ROOT%\build_log.txt

echo.
echo [0/6] Checking project structure...
if not exist "%ENTRYPOINT%" (
  echo   ERROR: Entry point "%ENTRYPOINT%" not found. Please run this script from the project root.
  exit /b 1
)

echo.
echo [1/6] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [2/6] Installing app requirements...
pip install -r requirements.txt

echo.
echo [3/6] Installing build tool (PyInstaller)...
pip install pyinstaller

echo.
echo [4/6] Cleaning previous outputs...
if exist "%WORK_ROOT%" rmdir /s /q "%WORK_ROOT%"
if exist "%DIST_ROOT%" rmdir /s /q "%DIST_ROOT%"

echo.
echo [5/6] Building EXE with PyInstaller...
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
echo [6/6] Verifying output...
if not exist "%DIST_DIR%\%APP_NAME%.exe" (
  echo   ERROR: Expected executable not found at "%DIST_DIR%\%APP_NAME%.exe".
  echo   Build log follows:
  type "%BUILD_LOG%"
  echo   Possible causes:
  echo     - Antivirus or system protection blocked write to the dist folder.
  echo     - Hidden import missing; ensure modules are included.
  echo     - Build invoked from the wrong directory.
  exit /b 1
)

echo.
echo Build finished successfully.
echo You can find the executable here:
echo   %DIST_DIR%\%APP_NAME%.exe

endlocal