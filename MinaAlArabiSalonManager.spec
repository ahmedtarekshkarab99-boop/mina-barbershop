# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Ensure PySide6 and our app package submodules are collected
hiddenimports = collect_submodules('PySide6') + collect_submodules('mina_al_arabi')
# Explicitly include dashboards to avoid analysis misses
hiddenimports += [
    'mina_al_arabi.dashboards.attendance',
    'mina_al_arabi.dashboards.cashier',
    'mina_al_arabi.dashboards.inventory',
    'mina_al_arabi.dashboards.sales',
    'mina_al_arabi.dashboards.expenses',
    'mina_al_arabi.dashboards.reports',
]

block_cipher = None

# Collect PySide6 data files (plugins, Qt configs like qt.conf, etc.)
pyside6_datas = collect_data_files('PySide6', include_py_files=False)

a = Analysis(
    ['mina_al_arabi/main.py'],
    pathex=['.'],
    binaries=[],
    datas=pyside6_datas,
    hiddenimports=hiddenimports,
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MinaAlArabiSalonManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # windowed
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MinaAlArabiSalonManager'
)