"""Spectrogram parameter validation. Pure functions, no Tk dependency."""

from __future__ import annotations

import re

WIDTH_MIN, WIDTH_MAX = 100, 5000
HEIGHT_MIN = 64  # sox_ng rejects smaller values
Z_RANGE_MIN, Z_RANGE_MAX = 20, 180
GAIN_MIN, GAIN_MAX = -20, 20

# Optimal heights for SoX/sox_ng: a power of two plus one (2^n + 1).
OPTIMAL_HEIGHTS = (65, 129, 257, 513, 1025, 2049, 4097)

_TIME_PATTERN = re.compile(r"^\d+:\d{2}$")


class ValidationError(ValueError):
    """Raised when a spectrogram parameter is invalid."""


def validate_width(value: str, *, label: str = "Width") -> int:
    try:
        width = int(value)
    except ValueError:
        raise ValidationError(f"{label} must be an integer.") from None
    if not (WIDTH_MIN <= width <= WIDTH_MAX):
        raise ValidationError(f"{label} must be between {WIDTH_MIN} and {WIDTH_MAX} pixels.")
    return width


def validate_height(value: str, *, label: str = "Height") -> int:
    try:
        height = int(value)
    except ValueError:
        raise ValidationError(f"{label} must be an integer.") from None
    if height < HEIGHT_MIN:
        raise ValidationError(f"{label} must be at least {HEIGHT_MIN} bins.")
    return height


def is_height_optimal(height: int) -> bool:
    """Heights of 2^n+1 are the most efficient for the SoX/sox_ng FFT."""
    return height in OPTIMAL_HEIGHTS


def validate_z_range(value: str, *, label: str = "Z Range") -> int:
    try:
        z_range = int(value)
    except ValueError:
        raise ValidationError(f"{label} must be an integer.") from None
    if not (Z_RANGE_MIN <= z_range <= Z_RANGE_MAX):
        raise ValidationError(f"{label} must be between {Z_RANGE_MIN} and {Z_RANGE_MAX} dB.")
    return z_range


def validate_gain(value: str, *, label: str = "Gain") -> int:
    try:
        gain = int(value)
    except ValueError:
        raise ValidationError(f"{label} must be an integer.") from None
    if not (GAIN_MIN <= gain <= GAIN_MAX):
        raise ValidationError(f"{label} must be between {GAIN_MIN} and {GAIN_MAX} dB.")
    return gain


def validate_time_format(value: str) -> bool:
    """Expected format: M:SS (e.g. '1:00')."""
    return bool(_TIME_PATTERN.match(value))
