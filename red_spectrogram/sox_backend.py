"""Building and running SoX/sox_ng commands. No Tk dependency."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Accepted lossless formats. ALAC/APE are not decoded by SoX/sox_ng without
# external libraries, so they are intentionally left out.
SUPPORTED_EXTENSIONS = (".flac", ".wav", ".aif", ".aiff")

# Keep the windowed build from flashing a console window for every SoX run.
_CREATION_FLAGS = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


class SoxExecutionError(RuntimeError):
    """Raised when SoX/sox_ng exits with an error."""

    def __init__(self, message: str, stderr: str = ""):
        super().__init__(message)
        self.stderr = stderr


@dataclass(frozen=True)
class SpectrogramParams:
    """Parameters shared by full and zoomed spectrograms."""

    width: str
    height: str
    z_range: str
    window_type: str
    gain: str = "0"  # -Z: Z-axis maximum in dBFS, exposed as "Gain (dB)"


def is_supported_audio_file(filename: str) -> bool:
    return filename.lower().endswith(SUPPORTED_EXTENSIONS)


def build_full_cmd(
    sox_path: str,
    file_path: str,
    output_path: str,
    params: SpectrogramParams,
    title: str,
) -> list[str]:
    """Build the command for a full spectrogram, as an argument list (no shell
    involved, so file names cannot inject commands)."""
    return [
        sox_path, file_path, "-n", "remix", "1", "spectrogram",
        "-x", params.width,
        "-y", params.height,
        "-z", params.z_range,
        "-Z", params.gain,
        "-w", params.window_type,
        "-t", title,
        "-o", output_path,
    ]


def build_zoom_cmd(
    sox_path: str,
    file_path: str,
    output_path: str,
    params: SpectrogramParams,
    title: str,
    start: str,
    duration: str,
) -> list[str]:
    """Build the command for a spectrogram zoomed on a time range."""
    return [
        sox_path, file_path, "-n", "remix", "1", "spectrogram",
        "-x", params.width,
        "-y", params.height,
        "-z", params.z_range,
        "-Z", params.gain,
        "-w", params.window_type,
        "-t", title,
        "-S", start,
        "-d", duration,
        "-o", output_path,
    ]


def run_sox(cmd: list[str], sox_path: str) -> subprocess.CompletedProcess:
    """Run a SoX/sox_ng command. The working directory is the executable's
    folder so it can find its DLLs. Raises SoxExecutionError on failure."""
    sox_dir = os.path.dirname(sox_path)
    logger.info("Executing command: %s", cmd)

    try:
        result = subprocess.run(
            cmd,
            cwd=sox_dir if os.path.isdir(sox_dir) else None,
            check=True,
            capture_output=True,
            text=True,
            creationflags=_CREATION_FLAGS,
        )
    except subprocess.CalledProcessError as e:
        stderr = e.stderr or ""
        logger.error("SoX execution failed: %s\n%s", e, stderr)
        raise SoxExecutionError(f"SoX exited with code {e.returncode}", stderr) from e
    except FileNotFoundError as e:
        raise SoxExecutionError(f"SoX executable not found: {sox_path}") from e

    if result.stderr:
        logger.warning("SoX stderr output: %s", result.stderr)

    return result
