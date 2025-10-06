@echo off
setlocal

REM Build Windows executable for "مدير صالون مينا العربي"

set APP_NAME=MinaAlArabiSalonManager
set ENTRYPOINT=mina_al_arabi\main.py
set DIST_DIR=dist\%APP_NAME%
set BUILD_LOG=build\build_log.txt

echo.
echo [1/6] Installing app requirements...
pip install -r requirements.txt

echo.
echo [2/6] Installing build tool (PyInstaller)...
pip install pyinstaller

echo.
echo [3/6] Cleaning old outputs...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo [4/6] Building EXE (CLI)...
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
  "%ENTRYPOINT%" > "%BUILD_LOG%" 2>&1

echo.
echo [5/6] Verifying output...
if exist "%DIST_DIR%\%APP_NAME%.exe" (
  echo   Build finished successfully.
  echo   Executable: %DIST_DIR%\%APP_NAME%.exe
  goto :done
) else (
  echo   WARN: Executable not found after CLI build.
  echo   Attempting build via spec file...
  pyinstaller "%APP_NAME%.spec" --clean --distpath dist --workpath build > "%BUILD_LOG%" 2>&1
  if exist "%DIST_DIR%\%APP_NAME%.exe" (
    echo   Build via spec succeeded.
    echo   Executable: %DIST_DIR%\%APP_NAME%.exe
    goto :done
  ) else (
    echo   ERROR: Build failed. No executable at "%DIST_DIR%\%APP_NAME%.exe".
    echo   Build log:
    type "%BUILD_LOG%"
    echo   Tips:
    echo     - Run this script from the project root.
    echo     - Ensure antivirus is not blocking the dist folder.
    echo     - Confirm entrypoint "%ENTRYPOINT%" exists.
    exit /b 1
  )
)

:done
endlocal