"""Smoke tests for the real GUI: open the (hidden) window, drive it through
its callbacks and check that the internal state stays consistent. No visual
checks here: the goal is to catch wiring bugs and crashes between changes
without manual testing.
"""

import os
import shutil

import pytest
import ttkbootstrap as tb

from red_spectrogram.app import SpectrogramApp
from red_spectrogram.config import DEFAULT_THEME, AppConfig


@pytest.fixture(scope="module")
def app_window(tmp_path_factory, sox_ng_path):
    # A single Tk root for the whole module: creating/destroying a tb.Window
    # per test is slow and, on some Windows setups, causes intermittent Tcl
    # initialisation failures when many interpreters are opened and closed
    # in quick succession in the same process.
    tmp_path = tmp_path_factory.mktemp("gui_smoke")
    config_path = str(tmp_path / "spectrogram_config.ini")
    output_folder = str(tmp_path / "Spectrograms")
    cfg = AppConfig.load(config_path, output_folder, sox_ng_path)

    try:
        root = tb.Window(themename=DEFAULT_THEME)
    except Exception as e:
        pytest.skip(f"No Tk display available: {e}")

    root.withdraw()
    app = SpectrogramApp(root, cfg)
    yield app
    root.destroy()


@pytest.fixture(autouse=True)
def _reset_app_state(app_window):
    """Reset the shared state to a clean point before each test."""
    app_window.clear_files()
    app_window.clear_output_list()
    app_window.width_var.set(app_window.config.full.width)
    yield


def test_app_builds_without_error(app_window):
    assert app_window.notebook is not None
    assert app_window.sox_path.endswith("sox_ng.exe")


def test_add_and_clear_files(app_window, sample_wav):
    app_window.selected_files.append(sample_wav)
    app_window.file_listbox.insert("end", os.path.basename(sample_wav))
    assert len(app_window.selected_files) == 1

    app_window.clear_files()
    assert app_window.selected_files == []
    assert app_window.file_listbox.size() == 0


def test_remove_selected_files(app_window, sample_wav):
    app_window.selected_files.append(sample_wav)
    app_window.file_listbox.insert("end", os.path.basename(sample_wav))
    app_window.file_listbox.selection_set(0)

    app_window.remove_selected()

    assert app_window.selected_files == []
    assert app_window.file_listbox.size() == 0


def test_validate_parameters_rejects_bad_width(app_window, monkeypatch):
    app_window.width_var.set("99999")
    monkeypatch.setattr("red_spectrogram.app.messagebox.showwarning", lambda *a, **k: None)
    assert app_window._validate_parameters() is False


def test_validate_parameters_accepts_defaults(app_window, monkeypatch):
    monkeypatch.setattr("red_spectrogram.app.messagebox.askyesno", lambda *a, **k: True)
    assert app_window._validate_parameters() is True


def test_theme_change_applies_to_config(app_window):
    app_window.theme_var.set("one-dark")
    app_window.root.update()
    assert app_window.config.theme == "one-dark"


def test_generate_full_spectrogram_end_to_end(app_window, sample_wav, tmp_path):
    """Run the real generation flow (outside the worker thread, which is just a
    scheduling detail) and check that the PNG gets created."""
    app_window.output_folder = str(tmp_path)
    file_name = os.path.basename(sample_wav)

    output_path = app_window._generate_full(sample_wav, file_name, str(tmp_path))

    assert output_path == os.path.join(str(tmp_path), f"{file_name}_full.png")
    assert os.path.exists(output_path)


def _make_album(root, name, tracks=("01.wav", "02.wav"), source=None):
    folder = root / name
    folder.mkdir(parents=True)
    for track in tracks:
        shutil.copy(source, folder / track)
    (folder / "cover.jpg").write_text("not audio")
    return str(folder)


def test_add_folder_maps_files_to_subfolder_named_after_it(app_window, sample_wav, tmp_path):
    album = _make_album(tmp_path, "My Album", source=sample_wav)

    app_window.add_folder(album)

    assert len(app_window.selected_files) == 2  # cover.jpg ignored
    for path in app_window.selected_files:
        assert app_window.output_dir_for(path) == os.path.join(app_window.output_folder, "My Album")


def test_single_files_go_to_output_root(app_window, sample_wav):
    app_window.add_files([sample_wav])

    assert app_window.output_dir_for(sample_wav) == app_window.output_folder


def test_same_folder_name_from_different_parents_gets_unique_subfolder(app_window, sample_wav, tmp_path):
    first = _make_album(tmp_path / "Album A", "CD1", source=sample_wav)
    second = _make_album(tmp_path / "Album B", "CD1", source=sample_wav)

    app_window.add_folder(first)
    app_window.add_folder(second)
    app_window.add_folder(first)  # adding the same folder again changes nothing

    dirs = {os.path.basename(app_window.output_dir_for(p)) for p in app_window.selected_files}
    assert dirs == {"CD1", "CD1 (2)"}
    assert len(app_window.selected_files) == 4


def test_removing_files_frees_their_subfolder_mapping(app_window, sample_wav, tmp_path):
    app_window.add_folder(_make_album(tmp_path, "Album", source=sample_wav))

    app_window.file_listbox.selection_set(0, "end")
    app_window.remove_selected()

    assert app_window.output_subdirs == {}


def test_generation_writes_folder_inputs_to_subfolder_and_lists_them(app_window, sample_wav, tmp_path, monkeypatch):
    monkeypatch.setattr("red_spectrogram.app.messagebox.showinfo", lambda *a, **k: None)
    app_window.output_folder = str(tmp_path / "out")
    app_window.add_folder(_make_album(tmp_path, "Album", tracks=("01.wav",), source=sample_wav))
    app_window.add_files([sample_wav])
    app_window.add_output("stale result from a previous run.png")

    jobs = [(p, app_window.output_dir_for(p)) for p in app_window.selected_files]
    app_window.clear_output_list()
    app_window.generate_spectrograms(jobs)
    app_window.process_queue()

    assert os.path.exists(tmp_path / "out" / "Album" / "01.wav_full.png")
    assert os.path.exists(tmp_path / "out" / "test_tone.wav_full.png")
    assert list(app_window.output_listbox.get(0, "end")) == ["Album/01.wav_full.png", "test_tone.wav_full.png"]


def test_start_generation_clears_previous_output_list(app_window, sample_wav, monkeypatch):
    started = []
    monkeypatch.setattr("red_spectrogram.app.threading.Thread", lambda **kw: type("T", (), {"start": lambda self: started.append(kw)})())
    monkeypatch.setattr(app_window.root, "after", lambda *a, **k: None)
    app_window.add_files([sample_wav])
    app_window.add_output("old.png")

    app_window.start_generation()

    assert len(started) == 1
    assert app_window.output_listbox.size() == 0
    assert app_window.output_files == []


def test_start_generation_warns_when_no_files_selected(app_window, monkeypatch):
    warnings = []
    monkeypatch.setattr("red_spectrogram.app.messagebox.showwarning", lambda title, msg: warnings.append(msg))

    app_window.start_generation()

    assert len(warnings) == 1
    assert "No files selected" in warnings[0]
