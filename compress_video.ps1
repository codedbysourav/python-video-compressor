# Video Compressor Tool - PowerShell Script
# Run this script in PowerShell with: .\compress_video.ps1

param(
    [string]$InputFile = "",
    [string]$OutputFile = "",
    [int]$CRF = 28,
    [string]$Preset = "fast",
    [string]$Resolution = ""
)

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Test-FFmpeg {
    try {
        $null = Get-Command ffmpeg -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}

function Test-Python {
    try {
        $null = Get-Command python -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}

function Get-FileSizeMB {
    param([string]$FilePath)
    if (Test-Path $FilePath) {
        $size = (Get-Item $FilePath).Length
        return [math]::Round($size / 1MB, 2)
    }
    return 0
}

function Show-Header {
    Clear-Host
    Write-ColorOutput "🎬 Video Compressor Tool - PowerShell" "Cyan"
    Write-ColorOutput "=====================================" "Cyan"
    Write-Host ""
}

function Show-CompressionOptions {
    Write-ColorOutput "📊 Compression Quality Options:" "Yellow"
    Write-Host "1. High Quality     - CRF: 18-20, Preset: slow      (Best quality, larger files)"
    Write-Host "2. Balanced         - CRF: 21-25, Preset: fast      (Good balance, recommended)"
    Write-Host "3. High Compression - CRF: 26-30, Preset: ultrafast (Smaller files, lower quality)"
    Write-Host "4. Custom Settings  - Choose your own values"
    Write-Host ""
}

function Show-ResolutionOptions {
    Write-ColorOutput "📐 Resolution Options:" "Yellow"
    Write-Host "1. Keep Original    - No resolution change"
    Write-Host "2. 720p (1280x720) - Good balance of quality/size"
    Write-Host "3. 480p (854x480)  - Smaller file size"
    Write-Host "4. 360p (640x360)  - Very small file size"
    Write-Host "5. Custom Resolution"
    Write-Host ""
}

function Get-UserInput {
    param([string]$Prompt, [string]$DefaultValue = "")
    
    if ($DefaultValue) {
        $input = Read-Host "$Prompt [$DefaultValue]"
        if ($input -eq "") { return $DefaultValue }
        return $input
    }
    return Read-Host $Prompt
}

function Get-CompressionSettings {
    Show-CompressionOptions
    
    $choice = Read-Host "Select compression quality (1-4)"
    
    switch ($choice) {
        "1" { 
            $CRF = 20; $Preset = "slow"
            Write-ColorOutput "✅ Selected: High Quality (CRF=20, Preset=slow)" "Green"
        }
        "2" { 
            $CRF = 25; $Preset = "fast"
            Write-ColorOutput "✅ Selected: Balanced (CRF=25, Preset=fast)" "Green"
        }
        "3" { 
            $CRF = 30; $Preset = "ultrafast"
            Write-ColorOutput "✅ Selected: High Compression (CRF=30, Preset=ultrafast)" "Green"
        }
        "4" {
            $CRF = [int](Get-UserInput "Enter CRF value (18-30)" "28")
            if ($CRF -lt 18 -or $CRF -gt 30) {
                Write-ColorOutput "⚠️  Invalid CRF value, using default (28)" "Yellow"
                $CRF = 28
            }
            
            Write-Host "Select preset:"
            Write-Host "1. ultrafast  2. superfast  3. veryfast  4. faster"
            Write-Host "5. fast       6. medium     7. slow      8. slower  9. veryslow"
            $presetChoice = Read-Host "Enter preset choice (1-9)"
            
            $presets = @("ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow")
            if ($presetChoice -ge 1 -and $presetChoice -le 9) {
                $Preset = $presets[$presetChoice - 1]
            } else {
                Write-ColorOutput "⚠️  Invalid preset choice, using default (fast)" "Yellow"
                $Preset = "fast"
            }
            
            Write-ColorOutput "✅ Selected: Custom (CRF=$CRF, Preset=$Preset)" "Green"
        }
        default {
            Write-ColorOutput "⚠️  Invalid choice, using default settings" "Yellow"
            $CRF = 28; $Preset = "fast"
        }
    }
    
    return $CRF, $Preset
}

function Get-ResolutionSettings {
    Show-ResolutionOptions
    
    $choice = Read-Host "Select resolution option (1-5)"
    
    switch ($choice) {
        "1" { 
            $Resolution = ""
            Write-ColorOutput "✅ Keeping original resolution" "Green"
        }
        "2" { 
            $Resolution = "1280:720"
            Write-ColorOutput "✅ Selected: 720p (1280x720)" "Green"
        }
        "3" { 
            $Resolution = "854:480"
            Write-ColorOutput "✅ Selected: 480p (854x480)" "Green"
        }
        "4" { 
            $Resolution = "640:360"
            Write-ColorOutput "✅ Selected: 360p (640x360)" "Green"
        }
        "5" {
            $width = Read-Host "Enter width"
            $height = Read-Host "Enter height"
            $Resolution = "$width`:$height"
            Write-ColorOutput "✅ Selected: Custom ($width x $height)" "Green"
        }
        default {
            Write-ColorOutput "⚠️  Invalid choice, keeping original resolution" "Yellow"
            $Resolution = ""
        }
    }
    
    return $Resolution
}

function Start-Compression {
    param(
        [string]$InputFile,
        [string]$OutputFile,
        [int]$CRF,
        [string]$Preset,
        [string]$Resolution
    )
    
    Write-Host ""
    Write-ColorOutput "🚀 Starting video compression..." "Cyan"
    Write-Host "Input file: $InputFile"
    Write-Host "Output file: $OutputFile"
    Write-Host "CRF: $CRF"
    Write-Host "Preset: $Preset"
    if ($Resolution) {
        Write-Host "Resolution: $Resolution"
    }
    Write-Host ""
    
    # Build command
    $cmd = "python video_compressor.py `"$InputFile`" `"$OutputFile`" --crf $CRF --preset $Preset"
    if ($Resolution) {
        $width, $height = $Resolution.Split(':')
        $cmd += " --resolution $width $height"
    }
    
    Write-Host "Running: $cmd"
    Write-Host ""
    
    # Run compression
    try {
        Invoke-Expression $cmd
        $exitCode = $LASTEXITCODE
        
        if ($exitCode -eq 0) {
            Write-ColorOutput "✅ Compression completed successfully!" "Green"
            
            # Show file size comparison
            $inputSize = Get-FileSizeMB $InputFile
            $outputSize = Get-FileSizeMB $OutputFile
            if ($inputSize -gt 0 -and $outputSize -gt 0) {
                $reduction = [math]::Round((1 - $outputSize / $inputSize) * 100, 1)
                Write-Host ""
                Write-ColorOutput "📊 File Size Comparison:" "Yellow"
                Write-Host "Original:  $inputSize MB"
                Write-Host "Compressed: $outputSize MB"
                Write-Host "Reduction:  $reduction%"
            }
        } else {
            Write-ColorOutput "❌ Compression failed with exit code: $exitCode" "Red"
        }
    }
    catch {
        Write-ColorOutput "❌ Error running compression: $($_.Exception.Message)" "Red"
    }
}

# Main execution
try {
    Show-Header
    
    # Check prerequisites
    Write-ColorOutput "🔍 Checking prerequisites..." "Yellow"
    
    if (-not (Test-Python)) {
        Write-ColorOutput "❌ Python is not installed or not in PATH" "Red"
        Write-Host "Please install Python from https://python.org"
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    if (-not (Test-FFmpeg)) {
        Write-ColorOutput "❌ FFmpeg is not installed or not in PATH" "Red"
        Write-Host "Please install FFmpeg and add it to your system PATH"
        Write-Host "Download from: https://ffmpeg.org/download.html"
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    Write-ColorOutput "✅ Python and FFmpeg are available" "Green"
    Write-Host ""
    
    # Get input file
    if (-not $InputFile) {
        $InputFile = Get-UserInput "Enter input video file path"
    }
    
    if (-not (Test-Path $InputFile)) {
        Write-ColorOutput "❌ Input file not found: $InputFile" "Red"
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    # Get output file
    if (-not $OutputFile) {
        $OutputFile = Get-UserInput "Enter output file path"
    }
    
    # Get compression settings
    $CRF, $Preset = Get-CompressionSettings
    
    # Get resolution settings
    $Resolution = Get-ResolutionSettings
    
    # Confirm settings
    Write-Host ""
    Write-ColorOutput "📋 Compression Settings Summary:" "Yellow"
    Write-Host "Input:      $InputFile"
    Write-Host "Output:     $OutputFile"
    Write-Host "CRF:        $CRF"
    Write-Host "Preset:     $Preset"
    Write-Host "Resolution: $(if ($Resolution) { $Resolution } else { 'Original' })"
    Write-Host ""
    
    $confirm = Read-Host "Proceed with compression? (y/n)"
    if ($confirm -eq "y" -or $confirm -eq "Y") {
        Start-Compression -InputFile $InputFile -OutputFile $OutputFile -CRF $CRF -Preset $Preset -Resolution $Resolution
    } else {
        Write-ColorOutput "❌ Compression cancelled by user" "Yellow"
    }
}
catch {
    Write-ColorOutput "❌ Unexpected error: $($_.Exception.Message)" "Red"
}
finally {
    Write-Host ""
    Read-Host "Press Enter to exit"
}
