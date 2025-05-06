# RED-Spectrogram

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-2.0-green.svg)

A powerful desktop application for generating high-quality spectrograms from FLAC audio files. The application provides an intuitive graphical interface for audio analysis while leveraging SoX (Sound eXchange) for processing.

<p align="center">
  <img src="https://github.com/user-attachments/assets/2e73cee1-60e7-417f-942f-d2622e43a861"
  alt="RED-Spectrogram interface" />
  <img src="https://github.com/user-attachments/assets/93f25a32-b9c2-4c8f-b4d1-9e55d42ececd"
  alt="Spectrogram screenshot" />
  
</p>

## Features

- 📊 Generate full and zoomed spectrograms from FLAC audio files
- 🎛️ Customizable spectrogram parameters (width, height, z-range, window type)
- 🔍 Zoom functionality to analyze specific time segments in detail
- 📁 Batch processing for multiple files
- 📂 Folder scan for FLAC files
- 💾 Save and load configuration settings
- 🖼️ Direct preview of generated spectrograms
- 📱 Portable application

## Installation

### Standalone Executable

Download the latest release from the [Releases]([https://github.com/yourusername/spectrogram-generator/](https://github.com/H4Z4RD-H42/RED-Spectrogram/releases) page and run the executable.

### From Source

For running from source:

```bash
# Clone the repository
git clone https://github.com/H4Z4RD-H42/RED-Spectrogram.git
cd RED-Spectrogram

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install pillow configparser

# Run the application
python red-spectrogram.py
```

**Note**: Running from source requires SoX to be installed and available in your PATH.

## Usage

1. **Add Files**: Select FLAC files or scan a directory for FLAC files
2. **Configure Settings**: Customize spectrogram parameters in the Settings tab
3. **Generate Spectrograms**: Select spectrogram type (Full/Zoom) and generate
4. **View Results**: Open generated spectrograms from the Output section

### Spectrogram Types

- **Full Spectrogram**: Analyzes the entire audio file
- **Zoom Spectrogram**: Focuses on a specific time segment (configurable in the settings)

### Configuration Parameters

| Parameter | Description | Typical Range |
|-----------|-------------|---------------|
| Width | Width of the spectrogram in pixels | 500-5000 |
| Height (bins) | Height of the spectrogram in bins | 129, 257, 513, 1025 (2^n+1) |
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
pyinstaller --onefile --windowed red-spectrogram.py
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

- [SoX - Sound eXchange](https://sourceforge.net/projects/sox/) for the audio processing capabilities
- All contributors and users of this software
