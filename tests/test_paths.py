import os

from red_spectrogram import paths


def test_data_dir_is_app_dir_when_writable(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "get_application_path", lambda: str(tmp_path))

    assert paths.get_data_dir() == str(tmp_path)


def test_data_dir_falls_back_to_user_dir_when_app_dir_is_read_only(tmp_path, monkeypatch):
    """Extracted under e.g. Program Files the app folder is read-only: config
    and log must go to the per-user folder instead of crashing on startup."""
    app_dir = tmp_path / "app"
    user_dir = tmp_path / "user" / "RED-Spectrogram"
    monkeypatch.setattr(paths, "get_application_path", lambda: str(app_dir))
    monkeypatch.setattr(paths, "_is_writable_dir", lambda path: False)
    monkeypatch.setattr(paths, "get_user_data_dir", lambda: str(user_dir))

    assert paths.get_data_dir() == str(user_dir)
    assert user_dir.is_dir()


def test_is_writable_dir_false_for_missing_folder(tmp_path):
    assert paths._is_writable_dir(str(tmp_path / "missing")) is False


def test_find_sox_path_prefers_bundled_sox_ng(tmp_path, monkeypatch):
    sox_dir = tmp_path / "sox"
    sox_dir.mkdir()
    (sox_dir / "sox.exe").write_text("classic")
    (sox_dir / "sox_ng.exe").write_text("ng")
    monkeypatch.setattr(paths, "get_application_path", lambda: str(tmp_path))

    assert paths.find_sox_path() == os.path.join(str(sox_dir), "sox_ng.exe")


def test_bundled_icon_exists():
    assert os.path.exists(paths.get_assets_path("icon.png"))
