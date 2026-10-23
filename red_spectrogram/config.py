"""Loading/saving of the persistent configuration (.ini)."""

from __future__ import annotations

import configparser
import logging
import os
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

CONFIG_FILENAME = "spectrogram_config.ini"

DEFAULT_WIDTH = "3000"
DEFAULT_HEIGHT = "513"
DEFAULT_Z_RANGE = "120"
DEFAULT_WINDOW_TYPE = "Kaiser"
DEFAULT_GAIN = "0"

DEFAULT_ZOOM_WIDTH = "500"
DEFAULT_ZOOM_HEIGHT = "1025"
DEFAULT_ZOOM_START = "1:00"
DEFAULT_ZOOM_DURATION = "0:02"

DEFAULT_THEME = "bootstrap-light"

WINDOW_TYPES = ("Kaiser", "Hamming", "Hann", "Bartlett", "Rectangular")
# ttkbootstrap 2.x themes (not the deprecated pre-2.0 names such as flatly/darkly).
AVAILABLE_THEMES = (
    "bootstrap-light",
    "bootstrap-dark",
    "one-dark",
    "nord-light",
    "dracula-dark",
    "solarized-light",
)


@dataclass
class SpectrogramSettings:
    width: str = DEFAULT_WIDTH
    height: str = DEFAULT_HEIGHT
    z_range: str = DEFAULT_Z_RANGE
    window_type: str = DEFAULT_WINDOW_TYPE
    gain: str = DEFAULT_GAIN


@dataclass
class ZoomSettings(SpectrogramSettings):
    width: str = DEFAULT_ZOOM_WIDTH
    height: str = DEFAULT_ZOOM_HEIGHT
    zoom_start: str = DEFAULT_ZOOM_START
    zoom_duration: str = DEFAULT_ZOOM_DURATION


@dataclass
class AppConfig:
    """Typed application configuration, read from and written to an .ini file.

    The .ini format is kept for compatibility with existing installs; keys
    missing from a file written by an older version (e.g. 'gain' or 'theme')
    get their default value instead of raising an error.
    """

    config_path: str
    output_folder: str
    sox_path: str
    theme: str = DEFAULT_THEME
    full: SpectrogramSettings = field(default_factory=SpectrogramSettings)
    zoom: ZoomSettings = field(default_factory=ZoomSettings)

    @classmethod
    def load(cls, config_path: str, default_output_folder: str, default_sox_path: str) -> AppConfig:
        parser = configparser.ConfigParser()

        if os.path.exists(config_path):
            try:
                parser.read(config_path)
            except configparser.Error as e:
                logger.warning("Config file %s is corrupt (%s); using defaults.", config_path, e)
                parser = configparser.ConfigParser()

        default_section = parser["DEFAULT"] if "DEFAULT" in parser else {}
        zoom_section = parser["ZOOM"] if "ZOOM" in parser else {}
        general_section = parser["GENERAL"] if "GENERAL" in parser else {}

        # If the saved sox_path no longer exists (e.g. after upgrading from
        # classic SoX to sox_ng, where the executable name changes) fall back
        # to the freshly detected path instead of showing "SoX not found"
        # until the user fixes it by hand.
        saved_sox_path = default_section.get("sox_path", "")
        sox_path = saved_sox_path if saved_sox_path and os.path.exists(saved_sox_path) else default_sox_path

        return cls(
            config_path=config_path,
            output_folder=default_section.get("output_folder", default_output_folder),
            sox_path=sox_path,
            theme=general_section.get("theme", DEFAULT_THEME),
            full=SpectrogramSettings(
                width=default_section.get("width", DEFAULT_WIDTH),
                height=default_section.get("height", DEFAULT_HEIGHT),
                z_range=default_section.get("z_range", DEFAULT_Z_RANGE),
                window_type=default_section.get("window_type", DEFAULT_WINDOW_TYPE),
                gain=default_section.get("gain", DEFAULT_GAIN),
            ),
            zoom=ZoomSettings(
                width=zoom_section.get("width", DEFAULT_ZOOM_WIDTH),
                height=zoom_section.get("height", DEFAULT_ZOOM_HEIGHT),
                z_range=zoom_section.get("z_range", DEFAULT_Z_RANGE),
                window_type=zoom_section.get("window_type", DEFAULT_WINDOW_TYPE),
                gain=zoom_section.get("gain", DEFAULT_GAIN),
                zoom_start=zoom_section.get("zoom_start", DEFAULT_ZOOM_START),
                zoom_duration=zoom_section.get("zoom_duration", DEFAULT_ZOOM_DURATION),
            ),
        )

    def save(self) -> None:
        parser = configparser.ConfigParser()

        parser["DEFAULT"] = {
            "width": self.full.width,
            "height": self.full.height,
            "z_range": self.full.z_range,
            "window_type": self.full.window_type,
            "gain": self.full.gain,
            "output_folder": self.output_folder,
            "sox_path": self.sox_path or "",
        }
        parser["ZOOM"] = {
            "width": self.zoom.width,
            "height": self.zoom.height,
            "z_range": self.zoom.z_range,
            "window_type": self.zoom.window_type,
            "gain": self.zoom.gain,
            "zoom_start": self.zoom.zoom_start,
            "zoom_duration": self.zoom.zoom_duration,
        }
        parser["GENERAL"] = {"theme": self.theme}

        with open(self.config_path, "w", encoding="utf-8") as f:
            parser.write(f)

    def reset_spectrogram_defaults(self) -> None:
        """Reset only the spectrogram parameters (not output folder, SoX path or theme)."""
        self.full = SpectrogramSettings()
        self.zoom = ZoomSettings()
