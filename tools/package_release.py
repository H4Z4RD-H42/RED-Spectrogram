"""Assemble the portable Windows zip from the PyInstaller build.

Expects dist/RED-Spectrogram.exe (pyinstaller RED-Spectrogram.spec) and ./sox
(python tools/fetch_sox_ng.py). Writes release/RED-Spectrogram-<label>-windows-x64.zip.

Usage: python tools/package_release.py v3.0.0
"""

from __future__ import annotations

import os
import sys
import zipfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE_PATH = os.path.join(REPO_ROOT, "dist", "RED-Spectrogram.exe")
SOX_DIR = os.path.join(REPO_ROOT, "sox")
OUT_DIR = os.path.join(REPO_ROOT, "release")

# (source path relative to the repo, path inside the zip folder)
CONTENTS = [
    ("dist/RED-Spectrogram.exe", "RED-Spectrogram.exe"),
    ("LICENSE", "LICENSE.txt"),
    ("THIRD_PARTY_NOTICES.md", "THIRD_PARTY_NOTICES.md"),
    ("sox/sox_ng.exe", "sox/sox_ng.exe"),
    ("sox/COPYING", "sox/COPYING.txt"),
    ("sox/AUTHORS", "sox/AUTHORS.txt"),
    ("sox/README.md", "sox/README.md"),
]
ZIP_ROOT = "RED-Spectrogram"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    label = sys.argv[1]

    missing = [src for src, _ in CONTENTS if not os.path.exists(os.path.join(REPO_ROOT, src))]
    if missing:
        raise SystemExit("Missing files: " + ", ".join(missing))

    os.makedirs(OUT_DIR, exist_ok=True)
    zip_path = os.path.join(OUT_DIR, f"RED-Spectrogram-{label}-windows-x64.zip")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for src, dest in CONTENTS:
            archive.write(os.path.join(REPO_ROOT, src), f"{ZIP_ROOT}/{dest}")

    print(zip_path)


if __name__ == "__main__":
    main()
