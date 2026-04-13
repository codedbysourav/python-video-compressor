@echo off
echo ========================================
echo    Video Compressor - Build GUI
echo ========================================
echo.

python build_gui.py
if %errorlevel% neq 0 (
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo    GUI Build Complete!
echo ========================================
echo.
echo Executable created: dist\VideoCompressorGUI.exe
echo Launcher script: dist\run_gui.bat
echo.
pause
