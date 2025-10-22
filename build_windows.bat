@echo off
setlocal

REM Build Windows executable for "Mina Al Arabi Salon Manager" (full one-folder like the previous working release).

set APP_NAME=MinaAlArabiSalonManager
set DIST_DIR=dist\%APP_NAME%
set BUILD_DIR=build\%APP_NAME%

echo.
echo [1/5] Installing requirements...
pip install -r requirements.txt

echo.
echo [2/5] Installing PyInstaller...
pip install pyinstaller

echo.
echo [3/5] Cleaning old outputs (build, dist, __pycache__, .pyc/.pyo)...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
for /d /r %%i in (__pycache__) do rmdir /s /q "%%i"
for /r %%f in (*.pyc) do del /f /q "%%f"
for /r %%f in (*.pyo) do del /f /q "%%f"

echo.
echo [4/5] Building via spec file (includes PySide6 data: qt.conf, plugins, DLLs)...
pyinstaller "%APP_NAME%.spec" --clean

REM If spec build fails OR build exe missing (often due to AV), try CLI fallback.
if errorlevel 1 (
  echo   WARNING: Spec build failed. Trying CLI fallback without UPX...
) else (
  if not exist "%BUILD_DIR%\%APP_NAME%.exe" (
    echo   WARNING: Spec build produced no bootloader EXE (likely AV lock). Trying CLI fallback...
  ) else (
    goto :SUCCESS
  )
)

echo.
echo [4b/5] Fallback build via CLI (no UPX)...
pyinstaller --noconfirm --clean --noupx --windowed ^
  --name "%APP_NAME%" ^
  --distpath "dist" ^
  --workpath "build" ^
  --specpath "." ^
  mina_al_arabi\main.py

if errorlevel 1 (
  echo   ERROR: Fallback CLI build failed.
  exit /b 1
)

:SUCCESS
echo.
echo [5/5] Build finished. Launch from inside:
echo   %DIST_DIR%\%APP_NAME%.exe
echo Final contents of "%DIST_DIR%":
dir /b "%DIST_DIR%"

echo.
echo Hints:
echo  - If the EXE is still missing, whitelist this folder in your antivirus/Defender and re-run.
echo  - You can also build to a neutral path, e.g. C:\temp\dist, by editing this script.

endlocal