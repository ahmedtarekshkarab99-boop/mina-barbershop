@echo off
setlocal

REM Build Windows executable for "مدير صالون مينا العربي"

set APP_NAME=MinaAlArabiSalonManager
set ENTRYPOINT=mina_al_arabi\main.py
set DIST_DIR=dist\%APP_NAME%
set BUILD_LOG=build\build_log.txt

echo.
echo [1/7] Installing app requirements...
pip install -r requirements.txt

echo.
echo [2/7] Installing build tool (PyInstaller)...
pip install pyinstaller

echo.
echo [3/7] Cleaning old outputs...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo [4/7] Building EXE (CLI)...
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
echo [5/7] Verifying output...
if exist "%DIST_DIR%\%APP_NAME%.exe" (
  echo   Build finished successfully.
  echo   Executable: %DIST_DIR%\%APP_NAME%.exe
) else (
  echo   WARN: Executable not found after CLI build.
  echo   Attempting build via spec file...
  pyinstaller "%APP_NAME%.spec" --clean --distpath dist --workpath build > "%BUILD_LOG%" 2>&1
  if exist "%DIST_DIR%\%APP_NAME%.exe" (
    echo   Build via spec succeeded.
    echo   Executable: %DIST_DIR%\%APP_NAME%.exe
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

echo.
echo [6/7] Cleanup: keep only _internal, mina_al_arabi, and the EXE...
if exist "%DIST_DIR%" (
  REM Remove any extra directories except _internal and mina_al_arabi
  for /D %%D in ("%DIST_DIR%\*") do (
    if /I not "%%~nxD"=="_internal" if /I not "%%~nxD"=="mina_al_arabi" (
      echo   Removing folder: %%~nxD
      rmdir /s /q "%%~fD"
    )
  )
  REM Remove any extra files except the main EXE
  for %%F in ("%DIST_DIR%\*") do (
    if /I not "%%~nxF"=="%APP_NAME%.exe" (
      if exist "%%~fF" (
        echo   Removing file: %%~nxF
        del /f /q "%%~fF" >nul 2>&1
      )
    )
  )
)

echo.
echo [7/7] Done. Final contents of "%DIST_DIR%":
dir /b "%DIST_DIR%"

endlocal