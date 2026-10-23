import os

import pytest
from PIL import Image

from red_spectrogram.sox_backend import (
    SoxExecutionError,
    SpectrogramParams,
    build_full_cmd,
    build_zoom_cmd,
    is_supported_audio_file,
    run_sox,
)


@pytest.mark.parametrize(
    "filename,expected",
    [
        ("track.flac", True),
        ("track.FLAC", True),
        ("track.wav", True),
        ("track.aiff", True),
        ("track.aif", True),
        ("track.mp3", False),
        ("track.ape", False),
        ("cover.jpg", False),
    ],
)
def test_is_supported_audio_file(filename, expected):
    assert is_supported_audio_file(filename) is expected


def test_build_full_cmd_contains_expected_arguments():
    params = SpectrogramParams(width="3000", height="513", z_range="120", window_type="Kaiser", gain="-6")
    cmd = build_full_cmd("sox_ng.exe", "in.flac", "out.png", params, "title")

    assert cmd[0] == "sox_ng.exe"
    assert cmd[1] == "in.flac"
    assert "-x" in cmd and cmd[cmd.index("-x") + 1] == "3000"
    assert "-y" in cmd and cmd[cmd.index("-y") + 1] == "513"
    assert "-z" in cmd and cmd[cmd.index("-z") + 1] == "120"
    assert "-Z" in cmd and cmd[cmd.index("-Z") + 1] == "-6"
    assert "-w" in cmd and cmd[cmd.index("-w") + 1] == "Kaiser"
    assert "-o" in cmd and cmd[cmd.index("-o") + 1] == "out.png"
    assert "-S" not in cmd
    assert "-d" not in cmd


def test_build_zoom_cmd_includes_start_and_duration():
    params = SpectrogramParams(width="500", height="1025", z_range="120", window_type="Kaiser")
    cmd = build_zoom_cmd("sox_ng.exe", "in.flac", "out.png", params, "title", "1:00", "0:02")

    assert "-S" in cmd and cmd[cmd.index("-S") + 1] == "1:00"
    assert "-d" in cmd and cmd[cmd.index("-d") + 1] == "0:02"


def test_run_sox_raises_on_missing_executable(tmp_path):
    fake_sox = str(tmp_path / "does_not_exist.exe")
    with pytest.raises(SoxExecutionError):
        run_sox([fake_sox, "--version"], fake_sox)


# ---------- Integration tests: eseguono davvero sox_ng su un WAV generato ----------


def test_full_spectrogram_generates_valid_png(sox_ng_path, sample_wav, tmp_path):
    output_path = str(tmp_path / "full.png")
    params = SpectrogramParams(width="400", height="257", z_range="120", window_type="Kaiser")
    cmd = build_full_cmd(sox_ng_path, sample_wav, output_path, params, "test [FULL]")

    run_sox(cmd, sox_ng_path)

    assert os.path.exists(output_path)
    with Image.open(output_path) as img:
        img.verify()


def test_zoom_spectrogram_generates_valid_png(sox_ng_path, sample_wav, tmp_path):
    output_path = str(tmp_path / "zoom.png")
    params = SpectrogramParams(width="300", height="129", z_range="120", window_type="Kaiser")
    cmd = build_zoom_cmd(sox_ng_path, sample_wav, output_path, params, "test [ZOOM]", "0:00", "0:01")

    run_sox(cmd, sox_ng_path)

    assert os.path.exists(output_path)
    with Image.open(output_path) as img:
        img.verify()


def test_run_sox_raises_on_invalid_arguments(sox_ng_path, sample_wav, tmp_path):
    output_path = str(tmp_path / "bad.png")
    params = SpectrogramParams(width="400", height="257", z_range="120", window_type="NotAWindow")
    cmd = build_full_cmd(sox_ng_path, sample_wav, output_path, params, "test")

    with pytest.raises(SoxExecutionError):
        run_sox(cmd, sox_ng_path)
