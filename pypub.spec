# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

# Diagnóstico: no PowerShell use `$env:PYPUB_PYI_CONSOLE='1'` antes do PyInstaller
# para gerar PyPub_console.exe com console (tracebacks visíveis).
_pyi_console = os.environ.get("PYPUB_PYI_CONSOLE", "").strip().lower() in ("1", "true", "yes")
_app_name = "PyPub_console" if _pyi_console else "PyPub"

# A UI do PySide carrega assets nativos.
# Incluímos hooks escondidos pro markdown e keyring funcionarem no freeze.

a = Analysis(
    ['src/pypub/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/pypub/assets/app_icon.svg', 'pypub/assets'),
        ('src/pypub/assets/app_icon.ico', 'pypub/assets'),
    ],
    hiddenimports=[
        'bs4',
        'keyring.backends.Windows',
        'markdown_it',
        'nh3',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        '_pytest',
        'pytestqt',
        'setuptools',
        'pkg_resources',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Vamos gerar formato DIR para que abra mais rapido (não descompacte na ram/temp)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=_app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # UPX comprime DLLs e frequentemente quebra Qt/Shiboken/WebEngine no Windows.
    upx=False,
    console=_pyi_console,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/pypub/assets/app_icon.ico'
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=_app_name,
)
