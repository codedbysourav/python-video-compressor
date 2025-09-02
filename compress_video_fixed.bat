@echo off
echo 🎬 Video Compressor Tool - Windows Batch File
echo =============================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Check if FFmpeg is available
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo ❌ FFmpeg is not installed or not in PATH
    echo Please install FFmpeg and add it to your system PATH
    echo Download from: https://ffmpeg.org/download.html
    pause
    exit /b 1
)

echo ✅ Python and FFmpeg are available
echo.

REM Get input file
set /p input_file="Enter input video file path: "
if not exist "%input_file%" (
    echo ❌ Input file not found: %input_file%
    pause
    exit /b 1
)

REM Get output file
set /p output_file="Enter output file path: "

REM Get compression quality
echo.
echo Select compression quality:
echo 1. High quality (CRF=20, slower but better)
echo 2. Balanced (CRF=28, default - recommended)
echo 3. High compression (CRF=30, faster but lower quality)
echo 4. Custom settings
set /p choice="Enter choice (1-4): "

if "%choice%"=="1" (
    set crf=20
    set preset=slow
    echo Using: High quality (CRF=20, preset=slow)
) else if "%choice%"=="2" (
    set crf=28
    set preset=fast
    echo Using: Balanced (CRF=28, preset=fast)
) else if "%choice%"=="3" (
    set crf=30
    set preset=ultrafast
    echo Using: High compression (CRF=30, preset=ultrafast)
) else if "%choice%"=="4" (
    set /p crf="Enter CRF value (18-30): "
    echo Select preset:
    echo 1. ultrafast  2. superfast  3. veryfast  4. faster
    echo 5. fast       6. medium     7. slow      8. slower  9. veryslow
    set /p preset_choice="Enter preset choice (1-9): "
    
    if "%preset_choice%"=="1" set preset=ultrafast
    if "%preset_choice%"=="2" set preset=superfast
    if "%preset_choice%"=="3" set preset=veryfast
    if "%preset_choice%"=="4" set preset=faster
    if "%preset_choice%"=="5" set preset=fast
    if "%preset_choice%"=="6" set preset=medium
    if "%preset_choice%"=="7" set preset=slow
    if "%preset_choice%"=="8" set preset=slower
    if "%preset_choice%"=="9" set preset=veryslow
    
    echo Using: Custom (CRF=%crf%, preset=%preset%)
) else (
    echo Invalid choice, using default settings
    set crf=28
    set preset=fast
)

REM Ask about resolution
echo.
set /p resize="Do you want to resize the video? (y/n): "
if /i "%resize%"=="y" (
    echo Common resolutions:
    echo 1. 720p (1280x720) - Good balance
    echo 2. 480p (854x480) - Small file size
    echo 3. 360p (640x360) - Very small file size
    echo 4. Custom resolution
    set /p res_choice="Enter choice (1-4): "
    
    if "%res_choice%"=="1" (
        set resolution=--resolution 1280 720
        echo Using: 720p resolution
    ) else if "%res_choice%"=="2" (
        set resolution=--resolution 854 480
        echo Using: 480p resolution
    ) else if "%res_choice%"=="3" (
        set resolution=--resolution 640 360
        echo Using: 360p resolution
    ) else if "%res_choice%"=="4" (
        set /p width="Enter width: "
        set /p height="Enter height: "
        set resolution=--resolution %width% %height%
        echo Using: Custom resolution %width%x%height%
    ) else (
        set resolution=
        echo Keeping original resolution
    )
) else (
    set resolution=
    echo Keeping original resolution
)

echo.
echo 🚀 Starting compression...
echo Input: %input_file%
echo Output: %output_file%
echo Settings: CRF=%crf%, Preset=%preset%
if defined resolution echo Resolution: %resolution%
echo.

REM Run the compression - FIXED COMMAND
python video_compressor.py "%input_file%" "%output_file%" --crf %crf% --preset %preset% %resolution%

echo.
if errorlevel 1 (
    echo ❌ Compression failed!
) else (
    echo ✅ Compression completed successfully!
)

echo.
echo Press any key to exit...
pause >nul
