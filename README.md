# 🎬 Video Compressor Tool

A powerful Python-based video compression tool that uses FFmpeg to compress video files with various quality and resolution options. Perfect for reducing large video file sizes while maintaining good quality.

## ✨ Features

- **Multiple compression levels** - Adjustable CRF (Constant Rate Factor) from 18-30
- **Flexible encoding presets** - From ultrafast (quick) to veryslow (best compression)
- **Resolution scaling** - Option to downscale videos for maximum size reduction
- **Audio compression** - Configurable audio codec and bitrate
- **Progress tracking** - Shows compression statistics and file size reduction
- **Cross-platform** - Works on Windows, macOS, and Linux

## 🚀 Installation

### Prerequisites

1. **Install FFmpeg** (Required)
   
   **Windows:**
   - Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
   - Extract to a folder (e.g., `C:\ffmpeg`)
   - Add `C:\ffmpeg\bin` to your system PATH environment variable
   - Restart your terminal/command prompt
   
   **macOS:**
   ```bash
   brew install ffmpeg
   ```
   
   **Linux (Ubuntu/Debian):**
   ```bash
   sudo apt update
   sudo apt install ffmpeg
   ```

2. **Verify FFmpeg installation:**
   ```bash
   ffmpeg -version
   ```

### Install Python Dependencies

1. **Clone or download this repository**
2. **Install required Python packages:**
   ```bash
   pip install -r requirements.txt
   ```

## 📖 Usage

### Basic Usage

```bash
# Simple compression with default settings (CRF=28, preset=fast)
python video_compressor.py input.mp4 output.mp4
```

### Processing Modes

```bash
# 1) Compress the size
python video_compressor.py input.mp4 output.mp4 --mode compress

# 2) Convert video to audio
python video_compressor.py input.mp4 output.mp3 --mode audio --audio-codec mp3

# 3) Convert video to audio and then get transcription
python video_compressor.py input.mp4 output.mp3 --mode audio-transcript --transcript transcript.txt --language en-US
```

### Advanced Usage

```bash
# High compression (larger file size reduction)
python video_compressor.py input.mp4 output.mp4 --crf 30 --preset ultrafast

# Compress and resize to 720p for maximum size reduction
python video_compressor.py input.mp4 output.mp4 --resolution 1280 720

# High quality compression (slower but better quality)
python video_compressor.py input.mp4 output.mp4 --crf 20 --preset slow

# Custom audio settings
python video_compressor.py input.mp4 output.mp4 --audio-codec mp3 --audio-bitrate 96k
```

### Command Line Options

| Option | Description | Default | Range |
|--------|-------------|---------|-------|
| `--crf` | Constant Rate Factor (quality) | 28 | 18-30 |
| `--preset` | Encoding speed preset | fast | ultrafast to veryslow |
| `--resolution` | Target resolution (WIDTH HEIGHT) | Original | Any positive integers |
| `--audio-codec` | Audio codec | aac | Any FFmpeg audio codec |
| `--audio-bitrate` | Audio bitrate | 128k | Any valid bitrate |
| `--mode` | Processing mode | compress | compress, audio, audio-transcript |

## Docker Usage

You can run the CLI fully inside Docker for compression, video-to-audio conversion, and transcription.

### Build the image

```bash
docker build -t video-compressor .
```

### Run with Docker

```powershell
docker run --rm -v ${PWD}:/data -w /data video-compressor input.mp4 output.mp4
```

```powershell
docker run --rm -v ${PWD}:/data -w /data video-compressor input.mp4 output.mp3 --mode audio --audio-codec mp3 --audio-bitrate 128k
```

```powershell
docker run --rm -v ${PWD}:/data -w /data video-compressor input.mp4 output.mp3 --mode audio-transcript --transcript transcript.txt --language en-US
```

### Run with Docker Compose

```bash
docker compose run --rm video-compressor input.mp4 output.mp4
```

```bash
docker compose run --rm video-compressor input.mp4 output.mp3 --mode audio-transcript --transcript transcript.txt --language en-US
```

### SSL Certificate Error During Build

If image build fails with `CERTIFICATE_VERIFY_FAILED`, your network likely uses a corporate TLS proxy.

Use one of these approaches:

```powershell
$env:PIP_INDEX_URL="https://your-internal-pypi/simple"
docker compose build
```

```powershell
$env:PIP_TRUSTED_HOST="pypi.org files.pythonhosted.org"
docker compose build
```

```powershell
$env:CA_CERT_B64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\path\to\corp-root-ca.crt"))
docker compose build
```

Use `docker compose run --rm ...` for this project. `docker compose up -d` is not ideal because this container is a one-shot CLI task, not a long-running service.

## 🎯 Compression Settings Guide

### CRF (Constant Rate Factor) Values

- **18-20**: High quality, minimal compression (good for archiving)
- **21-25**: Good quality, moderate compression (recommended for most uses)
- **26-28**: Balanced quality/size (default setting)
- **29-30**: High compression, noticeable quality loss (maximum size reduction)

### Encoding Presets

- **ultrafast**: Fastest encoding, largest file size
- **superfast/veryfast**: Quick encoding, good for testing
- **fast**: Good balance of speed and compression (default)
- **medium**: Better compression, slower encoding
- **slow/slower/veryslow**: Best compression, slowest encoding

### Resolution Examples

- **720p**: `--resolution 1280 720`
- **480p**: `--resolution 854 480`
- **360p**: `--resolution 640 360`

## 📊 Expected Results

Based on your 1.7GB screen recording example:

| Settings | Expected Size | Quality | Compression |
|----------|---------------|---------|-------------|
| CRF=28, 1080p | 400-600 MB | Good | 65-75% |
| CRF=30, 1080p | 300-450 MB | Acceptable | 70-80% |
| CRF=28, 720p | 200-350 MB | Good | 80-85% |
| CRF=30, 720p | 150-250 MB | Acceptable | 85-90% |

## 🔧 Troubleshooting

### Common Issues

1. **"FFmpeg not found" error**
   - Ensure FFmpeg is installed and added to PATH
   - Restart your terminal after adding to PATH
   - Verify with `ffmpeg -version`

2. **Permission errors**
   - Run as administrator (Windows) or use `sudo` (Linux/macOS)
   - Check file permissions and write access to output directory

3. **Large output file size**
   - Increase CRF value (28 → 30)
   - Use faster preset (fast → ultrafast)
   - Consider downscaling resolution

4. **Poor video quality**
   - Decrease CRF value (28 → 20)
   - Use slower preset (fast → slow)
   - Keep original resolution

### Performance Tips

- **For quick compression**: Use `--preset ultrafast --crf 30`
- **For best quality**: Use `--preset slow --crf 20`
- **For maximum size reduction**: Combine high CRF with resolution downscaling
- **For archiving**: Use `--preset medium --crf 18-20`

## 📝 Examples

### Example 1: Compress 4K video to 1080p
```bash
python video_compressor.py 4k_video.mp4 compressed_1080p.mp4 --resolution 1920 1080 --crf 25
```

### Example 2: Maximum compression for web upload
```bash
python video_compressor.py large_video.mp4 web_ready.mp4 --crf 30 --preset ultrafast --resolution 1280 720
```

### Example 3: High quality compression for storage
```bash
python video_compressor.py original.mp4 archived.mp4 --crf 20 --preset slow
```

### Example 4: Compress video and generate transcript
```bash
python video_compressor.py presentation.mp4 compressed.mp4 --transcript transcript.txt --crf 25
```

### Example 5: Multi-language transcript generation
```bash
python video_compressor.py spanish_video.mp4 compressed.mp4 --transcript transcript.txt --language es-ES
```

### Example 6: Complete workflow (compress + resize + transcript)
```bash
python video_compressor.py large_video.mp4 web_ready.mp4 --crf 28 --resolution 1280 720 --transcript transcript.txt
```

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve this tool!

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- Built with [ffmpeg-python](https://github.com/kkroening/ffmpeg-python)
- Powered by [FFmpeg](https://ffmpeg.org/) - the leading multimedia framework
