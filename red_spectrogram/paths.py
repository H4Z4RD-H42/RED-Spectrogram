"""Resolution of application paths and of the SoX/sox_ng executable."""

from __future__ import annotations

import os
import shutil
import sys

from . import APP_NAME

# SoX executable names, in order of preference: sox_ng first (actively
# maintained fork), classic sox as a fallback for backwards compatibility.
SOX_EXECUTABLE_NAMES = ("sox_ng.exe", "sox_ng", "sox.exe", "sox")

# Well-known Windows folders where SoX/sox_ng may be installed.
WINDOWS_SYSTEM_SOX_DIRS = (
    r"C:\Program Files\sox_ng",
    r"C:\Program Files (x86)\sox_ng",
    r"C:\sox_ng",
    r"C:\Program Files\sox-14-4-2",
    r"C:\Program Files (x86)\sox-14-4-2",
    r"C:\sox-14-4-2",
)


def get_application_path() -> str:
    """Return the application folder, both from source and as a PyInstaller bundle."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_assets_path(filename: str) -> str:
    """Return the path of a file bundled in red_spectrogram/assets."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", filename)


def get_user_data_dir() -> str:
    """Per-user data folder for the current platform."""
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Local")
    elif sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    return os.path.join(base, APP_NAME)


def _is_writable_dir(path: str) -> bool:
    # Not tempfile: on Windows it retries "access denied" up to TMP_MAX
    # (~2 billion) times when the folder looks writable, hanging the app.
    probe = os.path.join(path, f".write-test-{os.getpid()}")
    try:
        with open(probe, "w"):
            pass
    except OSError:
        return False
    try:
        os.remove(probe)
    except OSError:
        pass
    return True


def get_data_dir() -> str:
    """Folder for config, log and default output.

    The app is portable: everything lives next to the executable. When that
    folder is read-only (e.g. extracted under Program Files) it falls back to
    the per-user data folder instead of crashing on the first write.
    """
    app_dir = get_application_path()
    if _is_writable_dir(app_dir):
        return app_dir
    data_dir = get_user_data_dir()
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def find_sox_path() -> str:
    """Look for the sox_ng/SoX executable: first next to the app, then in
    well-known system folders, finally in PATH. Returns the path found, or the
    default expected path (even if missing) so the UI can show it as a hint."""
    app_dir = get_application_path()
    default_bundled_dir = os.path.join(app_dir, "sox")

    for name in SOX_EXECUTABLE_NAMES:
        candidate = os.path.join(default_bundled_dir, name)
        if os.path.exists(candidate):
            return candidate

    for system_dir in WINDOWS_SYSTEM_SOX_DIRS:
        for name in SOX_EXECUTABLE_NAMES:
            candidate = os.path.join(system_dir, name)
            if os.path.exists(candidate):
                return candidate

    for name in SOX_EXECUTABLE_NAMES:
        found = shutil.which(name)
        if found:
            return found

    return os.path.join(default_bundled_dir, "sox_ng.exe")
