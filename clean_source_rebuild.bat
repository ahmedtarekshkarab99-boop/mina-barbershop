@echo off
setlocal

REM Clean everything related to build/env, keep only source code, then rebuild fresh.

set APP_NAME=MinaAlArabiSalonManager
set ENTRYPOINT=mina_al_arabi\main.py
set DIST_ROOT=dist
set WORK_ROOT=build
set INSTALL_DIR="%ProgramFiles%\MinaAlArabiSalonManager"
set INSTALL_DIR_X86="%ProgramFiles(x86)%\MinaAlArabiSalonManager"
set SETUP_OUT=installer\windows\output\MinaAlArabiSalonManagerSetup.exe

echo.
echo [0/9] Validating source entrypoint...
if not exist "%ENTRYPOINT%" (
  echo   ERROR: Entry point "%ENTRYPOINT%" not found. Please run from project root.
  exit /b 1
)

echo.
echo [1/9] Uninstall previous installations (silent)...
for %%f in (%INSTALL_DIR%\unins*.exe) do "%%~f" /VERYSILENT /NORESTART
for %%f in (%INSTALL_DIR_X86%\unins*.exe) do "%%~f" /VERYSILENT /NORESTART

echo.
echo [2/9] Remove build outputs and caches...
if exist "%WORK_ROOT%" rmdir /s /q "%WORK_ROOT%"
if exist "%DIST_ROOT%" rmdir /s /q "%DIST_ROOT%"
if exist "%APP_NAME%.spec" del /f /q "%APP_NAME%.spec"
if exist ".venv" rmdir /s /q ".venv"
if exist "installer\windows\output" rmdir /s /q "installer\windows\output"

REM Remove all __pycache__ folders across repo
for /d /r %%i in (__pycache__) do (
  rmdir /s /q "%%i"
)

REM Remove compiled Python leftovers (*.pyc, *.pyo) and build logs
for /r %%f in (*.pyc) do del /f /q "%%f"
for /r %%f in (*.pyo) do del /f /q "%%f"
if exist "%WORK_ROOT%\build_log.txt" del /f /q "%WORK_ROOT%\build_log.txt"

echo.
echo [3/9] Create fresh virtual environment...
python -m venv .venv
if errorlevel 1 (
  echo   ERROR: Failed to create venv.
  exit /b 1
)
call ".venv\Scripts\activate.bat"
if errorlevel 1 (
  echo   ERROR: Failed to activate venv.
  exit /b 1
)

echo.
echo [4/9] Upgrade pip and install requirements...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

echo.
echo [5/9] Build EXE from clean source...
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

echo.
echo [6/9] Verify and prune dist to keep only required runtime files...
set DIST_DIR=%DIST_ROOT%\%APP_NAME%
if not exist "%DIST_DIR%\%APP_NAME%.exe" (
  echo   ERROR: Executable not found: "%DIST_DIR%\%APP_NAME%.exe"
  exit /b 1
)
REM Keep only _internal, mina_al_arabi, and main EXE
for /D %%D in ("%DIST_DIR%\*") do (
  if /I not "%%~nxD"=="_internal" if /I not "%%~nxD"=="mina_al_arabi" (
    echo   Removing folder: %%~nxD
    rmdir /s /q "%%~fD"
  )
)
for %%F in ("%DIST_DIR%\*") do (
  if /I not "%%~nxF"=="%APP_NAME%.exe" (
    if exist "%%~fF" (
      echo   Removing file: %%~nxF
      del /f /q "%%~fF" >nul 2>&1
    )
  )
)

echo.
echo [7/9] (Optional) Build installer if Inno Setup is available...
where iscc >nul 2>&1
if errorlevel 1 (
  echo   Skipping installer build (iscc not in PATH).
) else (
  call build_installer_windows.bat
)

echo.
echo [8/9] List final dist contents:
dir /b "%DIST_DIR%"

echo.
echo [9/9] Fresh rebuild finished.
echo - EXE: %DIST_DIR%\%APP_NAME%.exe
echo - Installer (if built): installer\windows\output\MinaAlArabiSalonManagerSetup.exe

endlocal