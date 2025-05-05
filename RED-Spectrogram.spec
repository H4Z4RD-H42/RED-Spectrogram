# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['red-Spectrogram.py'],
    pathex=[],
    binaries=[('sox\\sox.exe', '.'), ('sox\\*.dll', '.'), ('C:\\Users\\DRH\\AppData\\Local\\Programs\\Python\\Python313\\DLLs\\tcl86t.dll', '.')],
    datas=[('C:\\Users\\DRH\\AppData\\Local\\Programs\\Python\\Python313\\tcl\\tcl8.6', 'tcl'), ('C:\\Users\\DRH\\AppData\\Local\\Programs\\Python\\Python313\\Lib\\tkinter', 'tkinter')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=True,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [('v', None, 'OPTION')],
    name='red-Spectrogram',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
