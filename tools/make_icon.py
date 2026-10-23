"""Generate the application icon (PNG + multi-size ICO) from code.

The icon is a stylised spectrogram: harmonics fading out towards the top,
with a hard cutoff band, drawn in a SoX-like heat palette on a rounded tile.

Usage:  python tools/make_icon.py
Output: red_spectrogram/assets/icon.png, assets/icon.ico
"""

from __future__ import annotations

import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PNG_PATH = os.path.join(REPO_ROOT, "red_spectrogram", "assets", "icon.png")
ICO_PATH = os.path.join(REPO_ROOT, "assets", "icon.ico")

SIZE = 1024  # drawn large, downscaled for crisp edges
ICO_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

# Heat palette similar to SoX's default spectrogram colours.
PALETTE = [
    (0.00, (10, 8, 20)),
    (0.25, (70, 10, 90)),
    (0.45, (175, 20, 60)),
    (0.65, (235, 60, 30)),
    (0.82, (250, 160, 30)),
    (1.00, (255, 245, 200)),
]


def heat(value: float) -> tuple[int, int, int]:
    value = max(0.0, min(1.0, value))
    for (p0, c0), (p1, c1) in zip(PALETTE, PALETTE[1:]):
        if value <= p1:
            t = (value - p0) / (p1 - p0)
            return tuple(round(a + (b - a) * t) for a, b in zip(c0, c1))
    return PALETTE[-1][1]


def draw_spectrogram(size: int) -> Image.Image:
    rng = random.Random(42)
    cols, rows = 48, 48
    img = Image.new("RGB", (cols, rows))
    px = img.load()
    cutoff = 0.78  # fraction of height where the "lowpass" kicks in

    for x in range(cols):
        envelope = 0.75 + 0.25 * math.sin(x / cols * math.pi * 2.2)
        for y in range(rows):
            freq = 1 - y / (rows - 1)  # 0 bottom, 1 top
            level = (1 - freq) ** 0.9 * envelope
            # harmonic lines
            for h in (0.12, 0.27, 0.41, 0.55, 0.68):
                level += 0.55 * math.exp(-((freq - h) ** 2) / 0.0006) * (1 - h * 0.6)
            level += rng.uniform(-0.08, 0.08)
            if freq > cutoff:
                level *= 0.08
            px[x, y] = heat(level)

    return img.resize((size, size), Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(size / 400))


def build_icon() -> Image.Image:
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    margin = SIZE // 16
    inner = SIZE - 2 * margin
    radius = SIZE // 5

    spectro = draw_spectrogram(inner).convert("RGBA")
    mask = Image.new("L", (inner, inner), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, inner - 1, inner - 1), radius=radius, fill=255)
    canvas.paste(spectro, (margin, margin), mask)

    # Thin light border so the tile reads on dark taskbars too.
    border = ImageDraw.Draw(canvas)
    border.rounded_rectangle(
        (margin, margin, SIZE - margin - 1, SIZE - margin - 1),
        radius=radius,
        outline=(255, 255, 255, 60),
        width=SIZE // 128,
    )
    return canvas


def main() -> None:
    icon = build_icon()
    os.makedirs(os.path.dirname(PNG_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(ICO_PATH), exist_ok=True)
    icon.resize((256, 256), Image.Resampling.LANCZOS).save(PNG_PATH, optimize=True)
    icon.save(ICO_PATH, sizes=ICO_SIZES)
    print(f"Wrote {PNG_PATH}\nWrote {ICO_PATH}")


if __name__ == "__main__":
    main()
