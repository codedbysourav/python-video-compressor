# 🚀 Building Executables for Video Compressor

This guide explains how to create standalone executable (.exe) files for the Video Compressor tool.

## 📋 Prerequisites

1. **Python 3.7+** installed
2. **PyInstaller** installed: `pip install pyinstaller`
3. **All project dependencies** installed: `pip install -r requirements.txt`
4. **FFmpeg** installed on the target system (users will need this)

## 🛠️ Build Methods

### Method 1: Using Build Scripts (Recommended)

#### Build GUI Executable
```bash
python build_gui.py
```
or
```bash
build_gui.bat
```

#### Build CLI Executable
```bash
python build_cli.py
```
or
```bash
build_cli.bat
```

#### Build Both Executables
```bash
build_all.bat
```

### Method 2: Manual PyInstaller Commands

#### GUI Version
```bash
python -m PyInstaller --onefile --windowed --name=VideoCompressorGUI --add-data=requirements.txt;. --hidden-import=ffmpeg --hidden-import=speech_recognition --hidden-import=pyaudio --hidden-import=tkinter --hidden-import=tkinter.ttk --hidden-import=tkinter.filedialog --hidden-import=tkinter.messagebox --hidden-import=tkinter.scrolledtext --hidden-import=threading --hidden-import=tempfile --hidden-import=pathlib --hidden-import=datetime --clean video_compressor_gui.py
```

#### CLI Version
```bash
python -m PyInstaller --onefile --console --name=VideoCompressorCLI --add-data=requirements.txt;. --hidden-import=ffmpeg --hidden-import=speech_recognition --hidden-import=pyaudio --hidden-import=argparse --hidden-import=pathlib --hidden-import=tempfile --hidden-import=datetime --clean video_compressor.py
```

## 📁 Output Files

After building, you'll find these files in the `dist/` folder:

### GUI Version
- `VideoCompressorGUI.exe` - Main GUI executable (~55 MB)
- `run_gui.bat` - Launcher script

### CLI Version
- `VideoCompressorCLI.exe` - Main CLI executable (~52 MB)
- `run_cli.bat` - Launcher script
- `USAGE_EXAMPLES.txt` - Usage examples and help

## 🎯 Executable Features

### GUI Executable (VideoCompressorGUI.exe)
- **No console window** - Clean GUI experience
- **All GUI features** - File selection, compression settings, progress tracking
- **Transcript generation** - Built-in speech recognition
- **Easy to use** - Just double-click to run

### CLI Executable (VideoCompressorCLI.exe)
- **Console interface** - Full command-line functionality
- **All CLI options** - CRF, presets, resolution, audio settings
- **Transcript support** - Command-line transcript generation
- **Batch processing** - Perfect for automation

## 📦 Distribution

### What Users Need
1. **The executable file** (VideoCompressorGUI.exe or VideoCompressorCLI.exe)
2. **FFmpeg installed** on their system
3. **No Python installation required!**

### FFmpeg Installation for Users
Users need to install FFmpeg separately:

**Windows:**
- Download from https://ffmpeg.org/download.html
- Extract to a folder (e.g., `C:\ffmpeg`)
- Add `C:\ffmpeg\bin` to system PATH
- Restart command prompt/terminal

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

## 🔧 Troubleshooting

### Common Build Issues

1. **"PyInstaller not found"**
   ```bash
   pip install pyinstaller
   ```

2. **"Module not found" errors**
   - Add missing modules to `--hidden-import` list
   - Check all dependencies are installed

3. **Large executable size**
   - This is normal for GUI apps with many dependencies
   - GUI version: ~55 MB, CLI version: ~52 MB

4. **FFmpeg not found at runtime**
   - Users must install FFmpeg separately
   - Add FFmpeg to system PATH

### Build Optimization

To reduce executable size:
```bash
# Exclude unnecessary modules
python -m PyInstaller --onefile --windowed --exclude-module=matplotlib --exclude-module=scipy --name=VideoCompressorGUI video_compressor_gui.py
```

## 📋 Build Scripts Explained

### build_gui.py
- Creates GUI executable with no console window
- Includes all GUI dependencies
- Generates launcher script

### build_cli.py
- Creates CLI executable with console window
- Includes all CLI dependencies
- Generates usage examples

### build_all.bat
- Builds both GUI and CLI versions
- Provides complete distribution package

## 🎉 Success!

After building, you'll have standalone executables that users can run without Python installed. Just make sure they have FFmpeg installed on their system!

## 📝 Notes

- **File sizes**: GUI ~55 MB, CLI ~52 MB (this is normal for Python executables)
- **Dependencies**: All Python dependencies are bundled into the executable
- **FFmpeg**: Must be installed separately on user's system
- **Cross-platform**: These instructions are for Windows; adjust for macOS/Linux
