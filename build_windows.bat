@echo off
setlocal

REM Build Windows executable for "Mina Al Arabi Salon Manager" exactly like the previous working process.

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
echo [4/5] Building via spec file...
pyinstaller "%APP_NAME%.spec" --clean
if errorlevel 1 (
  echo   ERROR: Build failed via spec file.
  exit /b 1
)

echo.
echo [5/5] Pruning output to keep only required items...
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
echo Build finished.
echo Final contents of "%DIST_DIR%":
dir /b "%DIST_DIR%"

endlocal