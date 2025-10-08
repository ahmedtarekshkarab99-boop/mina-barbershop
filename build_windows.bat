@echo off
setlocal

REM Build Windows executable for "Mina Al Arabi Salon Manager" (full one-folder like the previous working release).

set APP_NAME=MinaAlArabiSalonManager
set DIST_DIR=dist\%APP_NAME%

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
if errorlevel 1 (
  echo   ERROR: Build failed via spec file.
  exit /b 1
)

echo.
echo [5/5] Build finished. Launch from inside:
echo   %DIST_DIR%\MinaAlArabiSalonManager.exe
echo Final contents of "%DIST_DIR%":
dir /b "%DIST_DIR%"

endlocal