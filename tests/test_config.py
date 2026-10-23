import os

from red_spectrogram.config import DEFAULT_THEME, DEFAULT_WIDTH, AppConfig


def test_load_creates_defaults_when_missing(tmp_path):
    config_path = str(tmp_path / "spectrogram_config.ini")
    output_folder = str(tmp_path / "Spectrograms")
    sox_path = str(tmp_path / "sox" / "sox_ng.exe")

    cfg = AppConfig.load(config_path, output_folder, sox_path)

    assert cfg.full.width == DEFAULT_WIDTH
    assert cfg.theme == DEFAULT_THEME
    assert cfg.output_folder == output_folder
    assert cfg.sox_path == sox_path


def test_save_then_load_roundtrip(tmp_path):
    config_path = str(tmp_path / "spectrogram_config.ini")
    cfg = AppConfig.load(config_path, str(tmp_path / "out"), str(tmp_path / "sox.exe"))

    cfg.full.width = "4000"
    cfg.full.gain = "-6"
    cfg.zoom.zoom_start = "2:30"
    cfg.theme = "one-dark"
    cfg.save()

    assert os.path.exists(config_path)

    reloaded = AppConfig.load(config_path, str(tmp_path / "out"), str(tmp_path / "sox.exe"))
    assert reloaded.full.width == "4000"
    assert reloaded.full.gain == "-6"
    assert reloaded.zoom.zoom_start == "2:30"
    assert reloaded.theme == "one-dark"


def test_load_fills_missing_keys_from_older_config(tmp_path):
    """An .ini written by an older version (no 'gain'/'theme') must still
    load: missing keys get their default value."""
    config_path = tmp_path / "spectrogram_config.ini"
    config_path.write_text(
        "[DEFAULT]\nwidth = 3000\nheight = 513\nz_range = 120\nwindow_type = Kaiser\n"
        "output_folder = C:\\out\nsox_path = C:\\sox\\sox.exe\n\n"
        "[ZOOM]\nwidth = 500\nheight = 1025\nz_range = 120\nwindow_type = Kaiser\n"
        "zoom_start = 1:00\nzoom_duration = 0:02\n",
        encoding="utf-8",
    )

    cfg = AppConfig.load(str(config_path), "fallback_out", "fallback_sox.exe")

    assert cfg.full.gain == "0"
    assert cfg.zoom.gain == "0"
    assert cfg.theme == DEFAULT_THEME
    assert cfg.output_folder == "C:\\out"


def test_load_falls_back_to_detected_sox_when_saved_path_missing(tmp_path):
    """An .ini from an old install pointing to 'sox.exe' (classic name, now
    replaced by sox_ng.exe) must not leave the user stuck on a dead path:
    it falls back to the auto-detected one."""
    config_path = tmp_path / "spectrogram_config.ini"
    stale_sox_path = str(tmp_path / "sox" / "sox.exe")  # does not exist
    config_path.write_text(
        "[DEFAULT]\nwidth = 3000\nheight = 513\nz_range = 120\nwindow_type = Kaiser\n"
        f"output_folder = out\nsox_path = {stale_sox_path}\n\n[ZOOM]\n",
        encoding="utf-8",
    )

    detected_sox_path = str(tmp_path / "sox" / "sox_ng.exe")
    cfg = AppConfig.load(str(config_path), "fallback_out", detected_sox_path)

    assert cfg.sox_path == detected_sox_path


def test_load_keeps_saved_sox_path_when_it_still_exists(tmp_path):
    config_path = tmp_path / "spectrogram_config.ini"
    real_sox_path = tmp_path / "sox" / "sox_ng.exe"
    real_sox_path.parent.mkdir(parents=True)
    real_sox_path.write_text("fake exe", encoding="utf-8")
    config_path.write_text(
        "[DEFAULT]\nwidth = 3000\nheight = 513\nz_range = 120\nwindow_type = Kaiser\n"
        f"output_folder = out\nsox_path = {real_sox_path}\n\n[ZOOM]\n",
        encoding="utf-8",
    )

    cfg = AppConfig.load(str(config_path), "fallback_out", "should_not_be_used.exe")

    assert cfg.sox_path == str(real_sox_path)


def test_load_recovers_from_corrupt_file(tmp_path):
    config_path = tmp_path / "spectrogram_config.ini"
    config_path.write_text("this is not valid ini [[[", encoding="utf-8")

    cfg = AppConfig.load(str(config_path), "fallback_out", "fallback_sox.exe")

    assert cfg.output_folder == "fallback_out"
    assert cfg.full.width == DEFAULT_WIDTH
