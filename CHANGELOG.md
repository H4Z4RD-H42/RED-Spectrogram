# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.0.0] - 2026-10-22

### Added

- **WAV and AIFF/AIF support** in addition to FLAC, both when adding files and when scanning a folder ([#1](https://github.com/H4Z4RD-H42/RED-Spectrogram/issues/1)).
- **Gain (dB) setting** for full and zoomed spectrograms, to brighten or dim the plot ([#3](https://github.com/H4Z4RD-H42/RED-Spectrogram/issues/3)).
- **sox_ng support**: the actively maintained fork of SoX is now the preferred backend, with classic SoX still supported as a fallback ([#2](https://github.com/H4Z4RD-H42/RED-Spectrogram/issues/2)).
- sox_ng is **bundled in the Windows download**: no separate install needed.
- Files added with **Add Folder** are saved in an output subfolder named after their source folder, so albums stay together.
- Modern themeable interface (ttkbootstrap) with light and dark themes, including a dark Windows title bar.
- Application icon and Windows file version information.
- Log file for troubleshooting (**Help → Open Log File**), plus **Help → Project Website** and **Report an Issue**.
- When the application folder is read-only (e.g. under `Program Files`), settings and logs are stored in `%LOCALAPPDATA%\RED-Spectrogram` instead.
- Automated test suite and continuous integration; release builds are produced by GitHub Actions with SHA-256 checksums and build provenance attestations.

### Changed

- Codebase restructured into the `red_spectrogram` package; can also be started with `python -m red_spectrogram`.
- The **Output** list now shows the images from the latest run and is cleared when a new generation starts; the *Refresh List* button was removed (use **Open Output Folder** to browse everything).
- Running from source now requires Python 3.10 or newer.
- The executable is no longer UPX-compressed, which reduces antivirus false positives.

### Fixed

- The interface was updated from the background thread during generation, which could freeze or crash the app; progress is now reported safely to the main thread.
- A saved SoX path that no longer exists (e.g. after switching from SoX to sox_ng) is replaced with the auto-detected one instead of reporting "SoX not found".
- A corrupt settings file no longer prevents the app from starting.
- The *Generate* button and progress bar no longer change size while long track names are processed.
- Heights below 64 bins, which sox_ng rejects, are now caught with a clear message before generating.
- SoX no longer flashes a console window for each generated spectrogram.

## [2.0] - 2025-05-06

First public release.

[Unreleased]: https://github.com/H4Z4RD-H42/RED-Spectrogram/compare/v3.0.0...HEAD
[3.0.0]: https://github.com/H4Z4RD-H42/RED-Spectrogram/compare/v2.0-initial...v3.0.0
[2.0]: https://github.com/H4Z4RD-H42/RED-Spectrogram/releases/tag/v2.0-initial
