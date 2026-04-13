#!/usr/bin/env python3
"""
Build script for creating GUI executable
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_gui_executable():
    """Build the GUI executable using PyInstaller."""
    
    print("🎬 Building Video Compressor GUI Executable")
    print("=" * 50)
    
    # Clean previous builds
    if os.path.exists("dist"):
        print("🧹 Cleaning previous builds...")
        shutil.rmtree("dist")
    
    if os.path.exists("build"):
        print("🧹 Cleaning build directory...")
        shutil.rmtree("build")
    
    # PyInstaller command for GUI version
    cmd = [
        "python", "-m", "PyInstaller",
        "--onefile",                    # Single executable file
        "--windowed",                   # No console window for GUI
        "--name=VideoCompressorGUI",    # Executable name
        # "--icon=icon.ico",             # Icon (if available)
        "--add-data=requirements.txt;.", # Include requirements
        "--hidden-import=ffmpeg",       # Ensure ffmpeg-python is included
        "--hidden-import=speech_recognition",
        "--hidden-import=pyaudio",
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.ttk",
        "--hidden-import=tkinter.filedialog",
        "--hidden-import=tkinter.messagebox",
        "--hidden-import=tkinter.scrolledtext",
        "--hidden-import=threading",
        "--hidden-import=tempfile",
        "--hidden-import=pathlib",
        "--hidden-import=datetime",
        "--clean",                      # Clean cache
        "video_compressor_gui.py"      # Main script
    ]
    
    print("🔨 Running PyInstaller...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ GUI executable built successfully!")
        
        # Check if executable was created
        exe_path = Path("dist/VideoCompressorGUI.exe")
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

def create_launcher_script():
    """Create a simple launcher script."""
    launcher_content = """@echo off
echo Starting Video Compressor GUI...
VideoCompressorGUI.exe
pause
"""
    
    with open("dist/run_gui.bat", "w") as f:
        f.write(launcher_content)
    
    print("📝 Created launcher script: dist/run_gui.bat")

def main():
    """Main build function."""
    print("🚀 Starting GUI executable build process...")
    
    # Check if PyInstaller is available
    try:
        subprocess.run(["python", "-m", "PyInstaller", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ PyInstaller not found! Please install it first:")
        print("pip install pyinstaller")
        return False
    
    # Build the executable
    success = build_gui_executable()
    
    if success:
        create_launcher_script()
        print("\n🎉 Build completed successfully!")
        print("📁 Executable location: dist/VideoCompressorGUI.exe")
        print("📝 Launcher script: dist/run_gui.bat")
        print("\n💡 Note: Users will need FFmpeg installed on their system to use the executable.")
    else:
        print("\n💥 Build failed!")
        return False
    
    return True

if __name__ == "__main__":
    main()
