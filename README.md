# 🎬 Video Compressor Tool

A powerful Python-based video compression tool that uses FFmpeg to compress video files with various quality and resolution options. Perfect for reducing large video file sizes while maintaining good quality.

## ✨ Features

- **Multiple compression levels** - Adjustable CRF (Constant Rate Factor) from 18-30
- **Flexible encoding presets** - From ultrafast (quick) to veryslow (best compression)
- **Resolution scaling** - Option to downscale videos for maximum size reduction
- **Audio compression** - Configurable audio codec and bitrate
- **Progress tracking** - Shows compression statistics and file size reduction
- **Cross-platform** - Works on Windows, macOS, and Linux
- **Video to audio export** - Create audio-only output from video files
- **Video transcription** - Generate transcript text directly from uploaded video
- **Pluggable transcription** - Use Google Speech Recognition (default, online), faster-whisper (local Whisper, offline after first download), or Gemma 4 E2B-it (local multimodal LLM)
- **Multi-provider AI summaries** - Summarize transcripts using Azure OpenAI, OpenAI, Ollama (local or cloud), or any OpenAI-compatible endpoint (Groq, Together, OpenRouter, LM Studio, vLLM, etc.)

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

Optional local transcription engines are lazy-loaded, so the default Google path needs no extra packages:

```bash
# Local Whisper transcription
pip install faster-whisper

# Local Gemma 4 E2B-it transcription
pip install "transformers>=4.58" torch accelerate soundfile librosa
```

## 📖 Usage

### GUI Workflows

The desktop app supports these workflows:

1. **Convert Video to Audio**
2. **Transcribe Video**
3. **Transcribe and Summarize with AI**

For transcription workflows, pick an engine in **Transcription Settings**:

- **Google Speech Recognition** — default online path, no new dependencies
- **faster-whisper (local)** — downloads the selected Whisper model from HuggingFace on first run
- **Gemma 4 E2B-it (local)** — downloads the Gemma multimodal model on first run and processes audio in 30-second chunks

For the summary workflow, pick a provider in the **AI Summarization Provider** card:

- **Azure OpenAI** — Endpoint, Deployment, API version, API key
- **OpenAI** — Base URL (default `https://api.openai.com/v1`), Model (default `gpt-4o-mini`), API key
- **OpenAI-compatible (custom)** — any host that speaks `/v1/chat/completions` (Groq, Together, OpenRouter, LM Studio, vLLM, …)
- **Ollama (local)** — requires `ollama serve` running and the model pulled (`ollama pull llama3.1`); API key optional
- **Ollama (cloud)** — Base URL `https://ollama.com/v1`, model from your Ollama account, API key from ollama.com

Defaults auto-fill when you switch presets. You can also set defaults through environment variables (see [example.env](example.env)):

```dotenv
# Pick a provider: azure | openai | openai_compatible | ollama_local | ollama_cloud
AI_PROVIDER=openai

# Generic (used by openai / openai_compatible / ollama_local / ollama_cloud)
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o-mini
AI_API_KEY=sk-...

# Transcription
TRANSCRIPT_PROVIDER=faster_whisper
WHISPER_MODEL=large-v3-turbo
WHISPER_DEVICE=auto
WHISPER_COMPUTE_TYPE=auto

# Or for Azure
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_API_KEY=...
```

### CLI: Transcription Provider Examples

```bash
# Default Google Speech Recognition
python video_compressor.py input.mp4 transcript.txt --mode transcript --language en-US

# Local faster-whisper
python video_compressor.py input.mp4 transcript.txt --mode transcript \
    --transcript-provider faster_whisper \
    --whisper-model large-v3-turbo --whisper-device auto

# Local Gemma 4 E2B-it
python video_compressor.py input.mp4 transcript.txt --mode transcript \
    --transcript-provider gemma4_local \
    --gemma-model google/gemma-4-E2B-it --gemma-device auto
```

### CLI: AI Summary Examples

```bash
# Azure OpenAI
python video_compressor.py input.mp4 transcript.txt --mode transcript-summary \
    --summary-output summary.txt \
    --ai-provider azure \
    --azure-endpoint https://your-resource.openai.azure.com \
    --azure-deployment gpt-4o --azure-api-key YOUR_KEY

# OpenAI
python video_compressor.py input.mp4 transcript.txt --mode transcript-summary \
    --summary-output summary.txt \
    --ai-provider openai --ai-model gpt-4o-mini --ai-api-key sk-...

# Ollama local (no key needed, requires `ollama serve`)
python video_compressor.py input.mp4 transcript.txt --mode transcript-summary \
    --summary-output summary.txt \
    --ai-provider ollama_local --ai-model llama3.1

# Ollama cloud
python video_compressor.py input.mp4 transcript.txt --mode transcript-summary \
    --summary-output summary.txt \
    --ai-provider ollama_cloud --ai-model llama3.1:70b --ai-api-key OLLAMA_KEY

# Any OpenAI-compatible host (Groq in this example)
python video_compressor.py input.mp4 transcript.txt --mode transcript-summary \
    --summary-output summary.txt \
    --ai-provider openai_compatible \
    --ai-base-url https://api.groq.com/openai/v1 \
    --ai-model mixtral-8x7b-instruct --ai-api-key gsk_...
```

### Basic Usage

```bash
# Convert video to audio with the default CLI mode
python video_compressor.py input.mp4 output.mp3 --audio-codec mp3
```

### Processing Modes

```bash
# 1) Convert video to audio
python video_compressor.py input.mp4 output.mp3 --mode audio --audio-codec mp3

# 2) Transcribe video
python video_compressor.py input.mp4 transcript.txt --mode transcript --language en-US

# 3) Transcribe video and summarize it with an AI provider
python video_compressor.py input.mp4 transcript.txt --mode transcript-summary --summary-output summary.txt
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
| `--mode` | Processing mode | audio | audio, transcript, transcript-summary |
| `--language` | Transcript language code | en-US | e.g. en-US, es-ES, fr-FR |
| `--transcript-provider` | Speech-to-text engine | google | google, faster_whisper, gemma4_local |
| `--whisper-model` | faster-whisper model | large-v3-turbo | tiny, base, small, medium, large-v3, large-v3-turbo |
| `--whisper-device` | faster-whisper device | auto | auto, cpu, cuda, mps |
| `--whisper-compute-type` | faster-whisper compute type | auto | auto, int8, float16 |
| `--gemma-model` | Gemma model ID | google/gemma-4-E2B-it | Any compatible HuggingFace model ID |
| `--gemma-device` | Gemma device | auto | auto, cpu, cuda, mps |

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

5. **Local transcription dependency errors**
   - For faster-whisper, install `faster-whisper`
   - For Gemma 4, install `transformers>=4.58`, `torch`, `accelerate`, `soundfile`, and `librosa`

6. **First local transcription run is slow**
   - faster-whisper downloads the selected model before transcribing
   - Gemma 4 local downloads a much larger model before first use
   - Subsequent runs reuse the HuggingFace cache

7. **Device-specific local model issues**
   - Try `--whisper-device cpu` or `--gemma-device cpu` if `auto`, MPS, or CUDA fails
   - Gemma 4 support depends on a recent enough `transformers` release

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
