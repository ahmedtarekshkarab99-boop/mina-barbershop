@echo off
setlocal

REM Build Windows installer (Inno Setup) for "Mina Al Arabi Salon Manager"

set SETUP_OUT=installer\windows\output\MinaAlArabiSalonManagerSetup.exe

echo.
echo [1/4] Checking PyInstaller build output...
if not exist "dist\MinaAlArabiSalonManager\MinaAlArabiSalonManager.exe" (
  echo   ERROR: Executable not found.
  echo   Please run build_windows.bat first to generate the EXE.
  exit /b 1
)

echo.
echo [2/4] Cleaning previous installer output...
if exist "installer\windows\output" rmdir /s /q "installer\windows\output"

echo.
echo [3/4] Checking Inno Setup compiler (iscc) availability...
where iscc >nul 2>&1
if errorlevel 1 (
  echo   ERROR: Inno Setup compiler (iscc) not found in PATH.
  echo   Install Inno Setup from: https://jrsoftware.org/isdl.php
  echo   Then ensure iscc.exe is in PATH (usually "C:\Program Files (x86)\Inno Setup 6\iscc.exe").
  exit /b 1
)

echo.
echo [4/4] Building Installer with Inno Setup...
iscc "installer\windows\MinaAlArabiSalonManager.iss"
if errorlevel 1 (
  echo   ERROR: Installer build failed.
  exit /b 1
)

if not exist "%SETUP_OUT%" (
  echo   ERROR: Expected setup not found: "%SETUP_OUT%"
  exit /b 1
)

echo.
echo Installer build finished.
echo You can find the setup here:
echo   %SETUP_OUT%

endlocal