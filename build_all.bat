@echo off
echo ========================================
echo    Video Compressor - Build All
echo ========================================
echo.

echo Building GUI executable...
python build_gui.py
if %errorlevel% neq 0 (
    echo GUI build failed!
    pause
    exit /b 1
)

echo.
echo Building CLI executable...
python build_cli.py
if %errorlevel% neq 0 (
    echo CLI build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo    Build Complete!
echo ========================================
echo.
echo Executables created in 'dist' folder:
echo - VideoCompressorGUI.exe (GUI version)
echo - VideoCompressorCLI.exe (CLI version)
echo.
echo Note: Users need FFmpeg installed to use these executables.
echo.
pause


