# Third-party notices

RED-Spectrogram itself is released under the [MIT License](LICENSE).
The Windows download also contains the following third-party software.

## sox_ng

- Website: <https://codeberg.org/sox_ng/sox_ng>
- License: GNU General Public License, version 2 (see `sox/COPYING.txt` in the download)
- Shipped as the separate program `sox/sox_ng.exe`, which RED-Spectrogram runs as an external command.
- The complete corresponding source code of the bundled version is attached to every GitHub release
  (`sox_ng-<version>-source.tar.gz`) and is also available from the sox_ng website.

## Components embedded in RED-Spectrogram.exe

The executable is built with PyInstaller and contains:

| Component | License | Website |
|-----------|---------|---------|
| Python | Python Software Foundation License | <https://www.python.org/> |
| Tcl/Tk | Tcl/Tk License (BSD-style) | <https://www.tcl-lang.org/> |
| ttkbootstrap | MIT License | <https://github.com/israel-dryer/ttkbootstrap> |
| Pillow | MIT-CMU License | <https://python-pillow.org/> |
| PyInstaller bootloader | GPL 2.0 with an exception that allows distributing bundled applications under any license | <https://pyinstaller.org/> |

Pillow in turn bundles libraries such as libjpeg-turbo, libpng, zlib, FreeType and others under
their own permissive licenses; see <https://github.com/python-pillow/Pillow/blob/main/LICENSE>.
