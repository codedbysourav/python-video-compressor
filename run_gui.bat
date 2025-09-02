@echo off
echo 🎬 Launching Video Compressor GUI...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Check if required packages are installed
python -c "import ffmpeg" >nul 2>&1
if errorlevel 1 (
    echo 📦 Installing required packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Failed to install required packages
        pause
        exit /b 1
    )
)

REM Launch the GUI
echo 🚀 Starting Video Compressor GUI...
python video_compressor_gui.py

echo.
echo GUI closed.
pause
