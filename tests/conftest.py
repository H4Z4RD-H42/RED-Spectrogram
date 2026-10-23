import math
import os
import struct
import wave

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUNDLED_SOX_PATH = os.path.join(REPO_ROOT, "sox", "sox_ng.exe")


@pytest.fixture(scope="module")
def sox_ng_path():
    """Path of the sox_ng binary used by the integration tests.
    Skips the test when it is not present."""
    if not os.path.exists(BUNDLED_SOX_PATH):
        pytest.skip(f"sox_ng non trovato in {BUNDLED_SOX_PATH}")
    return BUNDLED_SOX_PATH


@pytest.fixture
def sample_wav(tmp_path):
    """Generate a 2-second mono WAV (440 Hz tone) for end-to-end tests,
    so no audio fixtures need to live in the repository."""
    path = tmp_path / "test_tone.wav"
    sample_rate = 8000
    duration_s = 2
    freq = 440.0

    with wave.open(str(path), "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        frames = bytearray()
        for i in range(sample_rate * duration_s):
            value = int(32767 * 0.5 * math.sin(2 * math.pi * freq * i / sample_rate))
            frames += struct.pack("<h", value)
        wav_file.writeframes(bytes(frames))

    return str(path)
