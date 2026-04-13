@echo off
echo ========================================
echo    Video Compressor - Build CLI
echo ========================================
echo.

python build_cli.py
if %errorlevel% neq 0 (
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo    CLI Build Complete!
echo ========================================
echo.
echo Executable created: dist\VideoCompressorCLI.exe
echo Launcher script: dist\run_cli.bat
echo Usage examples: dist\USAGE_EXAMPLES.txt
echo.
pause
