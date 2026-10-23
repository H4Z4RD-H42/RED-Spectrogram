# -*- mode: python ; coding: utf-8 -*-
# Build with:  pyinstaller RED-Spectrogram.spec

import re

from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.win32.versioninfo import (
    FixedFileInfo,
    StringFileInfo,
    StringStruct,
    StringTable,
    VarFileInfo,
    VarStruct,
    VSVersionInfo,
)

with open("red_spectrogram/__init__.py", encoding="utf-8") as f:
    VERSION = re.search(r'__version__ = "([^"]+)"', f.read()).group(1)
VERSION_TUPLE = tuple(int(part) for part in VERSION.split(".")) + (0,)

version_info = VSVersionInfo(
    ffi=FixedFileInfo(filevers=VERSION_TUPLE, prodvers=VERSION_TUPLE),
    kids=[
        StringFileInfo([
            StringTable("040904B0", [
                StringStruct("CompanyName", "H4Z4RD-H42"),
                StringStruct("FileDescription", "RED-Spectrogram"),
                StringStruct("FileVersion", VERSION),
                StringStruct("InternalName", "RED-Spectrogram"),
                StringStruct("LegalCopyright", "MIT License"),
                StringStruct("OriginalFilename", "RED-Spectrogram.exe"),
                StringStruct("ProductName", "RED-Spectrogram"),
                StringStruct("ProductVersion", VERSION),
            ])
        ]),
        VarFileInfo([VarStruct("Translation", [1033, 1200])]),
    ],
)

a = Analysis(
    ['red-spectrogram.py'],
    pathex=[],
    binaries=[],
    datas=collect_data_files('ttkbootstrap') + [('red_spectrogram/assets', 'red_spectrogram/assets')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='RED-Spectrogram',
    icon='assets/icon.ico',
    version=version_info,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # UPX-packed executables are a common source of antivirus false positives.
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
