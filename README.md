# RED-Spectrogram

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-2.0-green.svg)

A powerful and user-friendly desktop application for generating high-quality spectrograms from FLAC audio files. The application leverages SoX (Sound eXchange) for audio processing while providing an intuitive graphical interface.

<p align="center">
  <img src="https://github.com/user-attachments/assets/93f25a32-b9c2-4c8f-b4d1-9e55d42ececd"
  alt="Spectrogram Generator Screenshot" />
</p>

## Features

- 📊 Generate full and zoomed spectrograms from FLAC audio files
- 🎛️ Customizable spectrogram parameters (width, height, z-range, window type)
- 🔍 Zoom functionality to analyze specific time segments in detail
- 📁 Batch processing for multiple files
- 📂 Folder scan for FLAC files
- 💾 Save and load configuration settings
- 🖼️ Direct preview of generated spectrograms
- 📱 Portable application - no installation required

## Installation

### Standalone Executable

Simply download the latest release and run the executable. No installation required!

1. Download `SpectrogramGenerator.exe` from the [Releases](https://github.com/yourusername/spectrogram-generator/releases) page
2. Run the application
3. That's it! No dependencies needed as SoX is bundled with the application

### From Source

If you prefer to run from source:

```bash
# Clone the repository
git clone https://github.com/yourusername/spectrogram-generator.git
cd spectrogram-generator

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install pillow configparser

# Run the application
python spectrogram_generator.py
```

**Note**: If running from source, you need to have SoX installed and available in your PATH.

## Usage

1. **Add Files**: Click "Add Files" to select FLAC files or "Add Folder" to scan a directory for FLAC files
2. **Configure Settings**: Switch to the "Settings" tab to customize spectrogram parameters
3. **Generate Spectrograms**: Select the type of spectrogram (Full/Zoom) and click "Generate Spectrograms"
4. **View Results**: Generated spectrograms appear in the Output section and can be opened with a double-click

### Spectrogram Types

- **Full Spectrogram**: Analyzes the entire audio file
- **Zoom Spectrogram**: Focuses on a specific time segment (configurable in the settings)

### Configuration Parameters

| Parameter | Description | Typical Range |
|-----------|-------------|---------------|
| Width | Width of the spectrogram in pixels | 500-5000 |
| Height | Height of the spectrogram in pixels | 500-2000 |
| Z-Range | Dynamic range in dB | 80-120 |
| Window Type | FFT window function | Kaiser, Hamming, Hann, etc. |
| Zoom Start | Starting point for zoom (M:SS) | Depends on audio |
| Zoom Duration | Duration for zoom (M:SS) | 0:01-0:10 |

## Building from Source

To create a standalone executable:

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # On Windows

# Install dependencies
pip install pillow configparser pyinstaller

# Create the executable
pyinstaller --onefile --windowed --add-binary "path\to\sox.exe;." --add-binary "path\to\sox\*.dll;." spectrogram_generator.py
```

The executable will be created in the `dist` folder.

## Requirements

When running from source:

- Python 3.6 or higher
- Pillow
- configparser
- SoX (Sound eXchange)

## Contributing

Contributions are welcome! Feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [SoX - Sound eXchange](https://sourceforge.net/projects/sox/) for the powerful audio processing capabilities
- All contributors and users of this software
