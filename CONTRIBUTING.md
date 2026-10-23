# Contributing to RED-Spectrogram

Thanks for taking the time to contribute! Bug reports, feature ideas and pull requests are all welcome.

## Reporting bugs and requesting features

Please use the [issue templates](https://github.com/H4Z4RD-H42/RED-Spectrogram/issues/new/choose).
For bugs, the log file (**Help → Open Log File** in the app) is usually the most useful thing to attach.

## Development setup

You need Python 3.10 or newer and Git.

```bash
git clone https://github.com/H4Z4RD-H42/RED-Spectrogram.git
cd RED-Spectrogram

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -e ".[dev]"
python tools/fetch_sox_ng.py    # Windows: downloads the pinned sox_ng build into ./sox

python -m red_spectrogram       # run the app
```

On macOS/Linux, install SoX from your package manager instead (`brew install sox`, `apt install sox`):
the app finds it in `PATH`.

## Before opening a pull request

```bash
ruff check .     # lint
pytest -q        # tests (the sox_ng integration tests are skipped if ./sox is missing)
```

- Keep pull requests focused on one change.
- Add or update tests for behaviour changes; GUI-independent logic belongs in the pure modules
  (`validation.py`, `config.py`, `sox_backend.py`, `paths.py`).
- Add a line to the `Unreleased` section of [CHANGELOG.md](CHANGELOG.md).

## Project layout

| Path | Purpose |
|------|---------|
| `red_spectrogram/app.py` | Tkinter/ttkbootstrap user interface |
| `red_spectrogram/sox_backend.py` | Builds and runs the SoX commands |
| `red_spectrogram/config.py` | Settings file (`spectrogram_config.ini`) |
| `red_spectrogram/validation.py` | Parameter validation |
| `red_spectrogram/paths.py` | App, data and sox_ng locations |
| `tests/` | pytest suite, including GUI smoke tests |
| `tools/` | Icon generator, sox_ng download, release packaging |
| `RED-Spectrogram.spec` | PyInstaller build definition |

## Building the Windows executable

```bash
pyinstaller RED-Spectrogram.spec            # -> dist/RED-Spectrogram.exe
python tools/package_release.py dev         # -> release/RED-Spectrogram-dev-windows-x64.zip
```

## Releasing (maintainers)

1. Update `__version__` in `red_spectrogram/__init__.py`.
2. Move the `Unreleased` entries in `CHANGELOG.md` under a new version heading.
3. Commit, then tag and push: `git tag v3.1.0 && git push origin main v3.1.0`.

The [Release workflow](.github/workflows/release.yml) then tests, builds and publishes the GitHub release automatically.
