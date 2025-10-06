@echo off
setlocal

REM Build Windows executable for "مدير صالون مينا العربي"

echo.
echo [1/4] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [2/4] Installing app requirements...
pip install -r requirements.txt

echo.
echo [3/4] Installing build tool (PyInstaller)...
pip install pyinstaller

echo.
echo [4/4] Building EXE with PyInstaller...
pyinstaller --noconfirm ^
  --name "MinaAlArabiSalonManager" ^
  --windowed ^
  --collect-all PySide6 ^
  --collect-submodules mina_al_arabi ^
  -p . ^
  mina_al_arabi/main.py

echo.
echo Build finished.
echo You can find the executable here:
echo   dist\MinaAlArabiSalonManager\MinaAlArabiSalonManager.exe

endlocal