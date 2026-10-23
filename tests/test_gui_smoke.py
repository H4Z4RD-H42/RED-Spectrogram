"""Smoke tests for the real GUI: open the (hidden) window, drive it through
its callbacks and check that the internal state stays consistent. No visual
checks here: the goal is to catch wiring bugs and crashes between changes
without manual testing.
"""

import os

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
    app_window.selected_files = []
    app_window.file_listbox.delete(0, "end")
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

    app_window._generate_full(sample_wav, file_name)

    output_path = os.path.join(str(tmp_path), f"{file_name}_full.png")
    assert os.path.exists(output_path)


def test_start_generation_warns_when_no_files_selected(app_window, monkeypatch):
    warnings = []
    monkeypatch.setattr("red_spectrogram.app.messagebox.showwarning", lambda title, msg: warnings.append(msg))

    app_window.start_generation()

    assert len(warnings) == 1
    assert "No files selected" in warnings[0]
