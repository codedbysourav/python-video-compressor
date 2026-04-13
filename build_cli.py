#!/usr/bin/env python3
"""
Build script for creating CLI executable
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_cli_executable():
    """Build the CLI executable using PyInstaller."""
    
    print("🎬 Building Video Compressor CLI Executable")
    print("=" * 50)
    
    # Clean previous builds
    if os.path.exists("dist"):
        print("🧹 Cleaning previous builds...")
        shutil.rmtree("dist")
    
    if os.path.exists("build"):
        print("🧹 Cleaning build directory...")
        shutil.rmtree("build")
    
    # PyInstaller command for CLI version
    cmd = [
        "python", "-m", "PyInstaller",
        "--onefile",                    # Single executable file
        "--console",                    # Keep console window for CLI
        "--name=VideoCompressorCLI",   # Executable name
        "--add-data=requirements.txt;.", # Include requirements
        "--hidden-import=ffmpeg",       # Ensure ffmpeg-python is included
        "--hidden-import=speech_recognition",
        "--hidden-import=pyaudio",
        "--hidden-import=argparse",
        "--hidden-import=pathlib",
        "--hidden-import=tempfile",
        "--hidden-import=datetime",
        "--clean",                      # Clean cache
        "video_compressor.py"          # Main script
    ]
    
    print("🔨 Running PyInstaller...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ CLI executable built successfully!")
        
        # Check if executable was created
        exe_path = Path("dist/VideoCompressorCLI.exe")
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"📦 Executable created: {exe_path}")
            print(f"📏 Size: {size_mb:.1f} MB")
            return True
        else:
            print("❌ Executable not found!")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def create_usage_examples():
    """Create usage examples and batch files."""
    
    # Create usage examples file
    examples_content = """# Video Compressor CLI - Usage Examples

## Basic Usage
VideoCompressorCLI.exe input.mp4 output.mp4

## High Compression (Maximum Size Reduction)
VideoCompressorCLI.exe input.mp4 output.mp4 --crf 30 --preset ultrafast

## Compress and Resize to 720p
VideoCompressorCLI.exe input.mp4 output.mp4 --resolution 1280 720

## High Quality Compression
VideoCompressorCLI.exe input.mp4 output.mp4 --crf 20 --preset slow

## Compress with Transcript Generation
VideoCompressorCLI.exe input.mp4 output.mp4 --transcript transcript.txt

## Complete Example (Compress + Resize + Transcript)
VideoCompressorCLI.exe large_video.mp4 web_ready.mp4 --crf 28 --resolution 1280 720 --transcript transcript.txt

## Available Options:
--crf: Quality (18-30, default: 28)
--preset: Speed (ultrafast to veryslow, default: fast)
--resolution: Width Height (e.g., 1280 720)
--audio-codec: Audio codec (default: aac)
--audio-bitrate: Audio bitrate (default: 128k)
--transcript: Generate transcript file
--language: Language code (default: en-US)

## Note: FFmpeg must be installed and in PATH for this to work.
"""
    
    with open("dist/USAGE_EXAMPLES.txt", "w") as f:
        f.write(examples_content)
    
    # Create batch file for easy usage
    batch_content = """@echo off
echo Video Compressor CLI
echo ====================
echo.
echo Usage: VideoCompressorCLI.exe input.mp4 output.mp4 [options]
echo.
echo Examples:
echo   VideoCompressorCLI.exe video.mp4 compressed.mp4
echo   VideoCompressorCLI.exe video.mp4 compressed.mp4 --crf 30 --preset ultrafast
echo   VideoCompressorCLI.exe video.mp4 compressed.mp4 --resolution 1280 720
echo.
echo For more examples, see USAGE_EXAMPLES.txt
echo.
pause
"""
    
    with open("dist/run_cli.bat", "w") as f:
        f.write(batch_content)
    
    print("📝 Created usage examples: dist/USAGE_EXAMPLES.txt")
    print("📝 Created launcher script: dist/run_cli.bat")

def main():
    """Main build function."""
    print("🚀 Starting CLI executable build process...")
    
    # Check if PyInstaller is available
    try:
        subprocess.run(["python", "-m", "PyInstaller", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ PyInstaller not found! Please install it first:")
        print("pip install pyinstaller")
        return False
    
    # Build the executable
    success = build_cli_executable()
    
    if success:
        create_usage_examples()
        print("\n🎉 Build completed successfully!")
        print("📁 Executable location: dist/VideoCompressorCLI.exe")
        print("📝 Launcher script: dist/run_cli.bat")
        print("📖 Usage examples: dist/USAGE_EXAMPLES.txt")
        print("\n💡 Note: Users will need FFmpeg installed on their system to use the executable.")
    else:
        print("\n💥 Build failed!")
        return False
    
    return True

if __name__ == "__main__":
    main()
