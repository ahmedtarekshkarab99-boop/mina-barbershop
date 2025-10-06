@echo off
setlocal

REM Build Windows executable for "مدير صالون مينا العربي"

echo.
echo [1/4] Installing app requirements...
pip install -r requirements.txt

echo.
echo [2/4] Installing build tool (PyInstaller)...
pip install pyinstaller

echo.
echo [3/4] Building EXE with PyInstaller...
pyinstaller --noconfirm ^
  --name "MinaAlArabiSalonManager" ^
  --windowed ^
  --collect-all PySide6 ^
  --collect-submodules mina_al_arabi ^
  --hidden-import mina_al_arabi.dashboards.attendance ^
  -p . ^
  mina_al_arabi/main.py

echo.
echo [4/4] Build finished.
echo Executable should be here:
echo   dist\MinaAlArabiSalonManager\MinaAlArabiSalonManager.exe

endlocal