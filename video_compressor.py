#!/usr/bin/env python3
"""
Video Compressor Tool
A Python script to compress video files using FFmpeg with various quality and resolution options.
Also includes transcript generation functionality using speech recognition.
"""

import os
import sys
import argparse
import json
import urllib.error
import urllib.parse
import urllib.request
import ffmpeg
import speech_recognition as sr
import tempfile


def load_dotenv_file(dotenv_path='.env'):
    """Load simple KEY=VALUE pairs from a .env file into process environment."""
    if not os.path.exists(dotenv_path):
        return

    try:
        with open(dotenv_path, 'r', encoding='utf-8') as file_handle:
            for raw_line in file_handle:
                line = raw_line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue

                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except OSError:
        # The app can still run without .env parsing; environment variables may already exist.
        return


def check_ffmpeg():
    """Check if FFmpeg is available in the system PATH."""
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_file_size_mb(file_path):
    """Get file size in MB."""
    if os.path.exists(file_path):
        size_bytes = os.path.getsize(file_path)
        return round(size_bytes / (1024 * 1024), 2)
    return 0


def compress_video(input_file, output_file, crf=28, preset='fast', 
                   resolution=None, audio_codec='aac', audio_bitrate='128k'):
    """
    Compress video using FFmpeg.
    
    Args:
        input_file (str): Path to input video file
        output_file (str): Path to output compressed video file
        crf (int): Constant Rate Factor (18-30, lower = better quality)
        preset (str): Encoding preset (ultrafast to veryslow)
        resolution (tuple): Target resolution as (width, height) or None to keep original
        audio_codec (str): Audio codec for output
        audio_bitrate (str): Audio bitrate
    """
    
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Build FFmpeg command
    input_stream = ffmpeg.input(input_file)
    
    # Video output options
    output_options = {
        'vcodec': 'libx264',
        'crf': crf,
        'preset': preset,
        'acodec': audio_codec,
        'ab': audio_bitrate
    }
    
    # Add resolution scaling if specified
    if resolution:
        width, height = resolution
        output_options['vf'] = f'scale={width}:{height}'
    
    # Get input file info for progress display
    input_size = get_file_size_mb(input_file)
    print(f"Input file: {input_file} ({input_size} MB)")
    print(f"Output file: {output_file}")
    print(f"Compression settings: CRF={crf}, Preset={preset}")
    if resolution:
        print(f"Resolution: {resolution[0]}x{resolution[1]}")
    print("Starting compression...")
    
    try:
        # Run FFmpeg compression
        (
            input_stream
            .output(output_file, **output_options)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        # Get output file size
        output_size = get_file_size_mb(output_file)
        compression_ratio = round((1 - output_size / input_size) * 100, 1)
        
        print(f"\n✅ Compression completed successfully!")
        print(f"Original size: {input_size} MB")
        print(f"Compressed size: {output_size} MB")
        print(f"Size reduction: {compression_ratio}%")
        
        return True
        
    except ffmpeg.Error as e:
        print(f"❌ FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False


def convert_video_to_audio(input_file, output_file, audio_codec='mp3', audio_bitrate='128k'):
    """
    Convert video to audio-only output using FFmpeg.

    Args:
        input_file (str): Path to input video file
        output_file (str): Path to output audio file
        audio_codec (str): Audio codec for output
        audio_bitrate (str): Audio bitrate
    """

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    input_size = get_file_size_mb(input_file)
    print(f"Input file: {input_file} ({input_size} MB)")
    print(f"Output audio file: {output_file}")
    print(f"Audio settings: codec={audio_codec}, bitrate={audio_bitrate}")
    print("Starting audio conversion...")

    try:
        (
            ffmpeg
            .input(input_file)
            .output(output_file, vn=None, acodec=audio_codec, ab=audio_bitrate)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )

        output_size = get_file_size_mb(output_file)
        print("\n✅ Audio conversion completed successfully!")
        print(f"Output size: {output_size} MB")
        return True

    except ffmpeg.Error as e:
        print(f"❌ FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False


def merge_videos(input_files, output_file):
    """
    Merge multiple video files into one in the given order using FFmpeg concat demuxer.

    Args:
        input_files (list): Ordered list of input video file paths.
        output_file (str): Path to the merged output video file.

    Returns:
        bool: True on success, False on failure.
    """
    if not input_files:
        raise ValueError('No input files provided for merging.')

    for path in input_files:
        if not os.path.exists(path):
            raise FileNotFoundError(f'Input file not found: {path}')

    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.txt', delete=False, encoding='utf-8'
    ) as list_file:
        list_path = list_file.name
        for path in input_files:
            # ffmpeg concat list requires forward slashes; escape embedded single quotes
            safe_path = path.replace('\\', '/').replace("'", r"'\''")
            list_file.write(f"file '{safe_path}'\n")

    print(f"Merging {len(input_files)} files → {output_file}")
    try:
        (
            ffmpeg
            .input(list_path, format='concat', safe=0)
            .output(output_file, c='copy')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        print(f'✅ Merge completed: {output_file}')
        return True
    except ffmpeg.Error as e:
        print(f"❌ FFmpeg merge error: {e.stderr.decode() if e.stderr else str(e)}")
        return False
    except Exception as e:
        print(f'❌ Unexpected error during merge: {str(e)}')
        return False
    finally:
        if os.path.exists(list_path):
            os.unlink(list_path)


def save_text_output(output_file, text):
    """Save text content to a file, creating parent folders when needed."""
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output_file, 'w', encoding='utf-8') as file_handle:
        file_handle.write(text)


def _chunk_text(text, max_chars=12000):
    """Split large text into sentence-friendly chunks for LLM summarization."""
    stripped_text = text.strip()
    if not stripped_text:
        return []

    chunks = []
    current_chunk = []
    current_length = 0

    sentences = stripped_text.replace('\r', '').split('\n')
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        sentence_length = len(sentence) + 1
        if current_chunk and current_length + sentence_length > max_chars:
            chunks.append('\n'.join(current_chunk))
            current_chunk = [sentence]
            current_length = sentence_length
        else:
            current_chunk.append(sentence)
            current_length += sentence_length

    if current_chunk:
        chunks.append('\n'.join(current_chunk))

    return chunks


def _extract_message_content(message_content):
    """Normalize Azure OpenAI response content to plain text."""
    if isinstance(message_content, str):
        return message_content.strip()

    if isinstance(message_content, list):
        text_parts = []
        for item in message_content:
            if isinstance(item, dict) and item.get('type') == 'text':
                text_parts.append(item.get('text', ''))
        return '\n'.join(part for part in text_parts if part).strip()

    return ''


def _azure_chat_completion(messages, endpoint, deployment, api_key,
                           api_version='2024-02-15-preview',
                           temperature=0.2, max_tokens=700):
    """Send one chat completion request to Azure OpenAI."""
    if not endpoint or not deployment or not api_key:
        raise ValueError('Azure endpoint, deployment, and API key are required for AI summarization.')

    endpoint = endpoint.rstrip('/')
    deployment_name = urllib.parse.quote(deployment, safe='')
    api_version_value = urllib.parse.quote(api_version, safe='')
    url = f"{endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version={api_version_value}"

    payload = {
        'messages': messages,
        'temperature': temperature,
        'max_tokens': max_tokens
    }

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'api-key': api_key
        },
        method='POST'
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            response_data = json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode('utf-8', errors='replace')
        raise RuntimeError(f'Azure OpenAI request failed ({exc.code}): {error_body}') from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f'Azure OpenAI connection failed: {exc.reason}') from exc

    try:
        content = response_data['choices'][0]['message']['content']
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f'Unexpected Azure OpenAI response: {response_data}') from exc

    normalized_content = _extract_message_content(content)
    if not normalized_content:
        raise RuntimeError('Azure OpenAI returned an empty summary.')

    return normalized_content


def summarize_transcript_with_azure_openai(transcript_text, endpoint, deployment, api_key,
                                           api_version='2024-02-15-preview'):
    """
    Summarize transcript text using Azure OpenAI.

    Large transcripts are summarized in chunks first, then consolidated.
    """
    if not transcript_text or not transcript_text.strip():
        raise ValueError('Transcript text is required for summarization.')

    chunks = _chunk_text(transcript_text)
    if not chunks:
        raise ValueError('Transcript text is empty after cleanup.')

    chunk_summaries = []
    for index, chunk in enumerate(chunks, start=1):
        chunk_summary = _azure_chat_completion(
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'You summarize transcript excerpts accurately. '
                        'Keep names, numbers, and decisions precise. '
                        'Return concise prose with short bullet points when useful.'
                    )
                },
                {
                    'role': 'user',
                    'content': (
                        f'Summarize transcript chunk {index} of {len(chunks)}. '
                        'Capture the main topics, key facts, and action items.\n\n'
                        f'Transcript:\n{chunk}'
                    )
                }
            ],
            endpoint=endpoint,
            deployment=deployment,
            api_key=api_key,
            api_version=api_version,
            temperature=0.1,
            max_tokens=500
        )
        chunk_summaries.append(f'Chunk {index} summary:\n{chunk_summary}')

    if len(chunk_summaries) == 1:
        return chunk_summaries[0].replace('Chunk 1 summary:\n', '', 1).strip()

    combined_summary_input = '\n\n'.join(chunk_summaries)
    return _azure_chat_completion(
        messages=[
            {
                'role': 'system',
                'content': (
                    'You create clean meeting-style summaries from transcript summaries. '
                    'Return exactly these sections: Overview, Key Points, Action Items, Open Questions.'
                )
            },
            {
                'role': 'user',
                'content': (
                    'Combine the chunk summaries below into one final summary. '
                    'Be concise, structured, and factual.\n\n'
                    f'{combined_summary_input}'
                )
            }
        ],
        endpoint=endpoint,
        deployment=deployment,
        api_key=api_key,
        api_version=api_version,
        temperature=0.1,
        max_tokens=700
    )


def generate_transcript(input_file, output_file=None, language='en-US'):
    """
    Generate transcript from video file using speech recognition with robust error handling.
    
    Args:
        input_file (str): Path to input video file
        output_file (str): Path to output transcript file (optional)
        language (str): Language code for speech recognition (default: en-US)
    
    Returns:
        str: Generated transcript text
    """
    
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Initialize recognizer
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
        temp_audio_path = temp_audio.name

    try:
        print("🎵 Extracting audio from media...")
        (
            ffmpeg
            .input(input_file)
            .output(
                temp_audio_path,
                acodec='pcm_s16le',
                ar=16000,
                ac=1,
                f='wav',
                loglevel='error'
            )
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True, quiet=True)
        )

        transcript = _transcribe_wav_in_chunks(temp_audio_path, language, recognizer)
        if not transcript:
            print("❌ No transcript generated")
            return None

        if output_file:
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(transcript)

            print(f"📝 Transcript saved to: {output_file}")

        return transcript

    except Exception as e:
        print(f"❌ Error during transcript generation: {str(e)}")
        return None
    finally:
        if os.path.exists(temp_audio_path):
            os.unlink(temp_audio_path)


def _language_candidates(language):
    """Build ordered language candidates for speech recognition retries."""
    candidates = []
    if language:
        candidates.append(language)
        if '-' in language:
            candidates.append(language.split('-')[0])
    if 'en' not in candidates:
        candidates.append('en')
    candidates.append(None)

    # Keep unique order
    unique_candidates = []
    for item in candidates:
        if item not in unique_candidates:
            unique_candidates.append(item)
    return unique_candidates


def _recognize_chunk(audio_chunk, language, recognizer):
    """
    Attempt speech recognition for one chunk using fallback language candidates.
    
    Args:
        audio_chunk: SpeechRecognition AudioData chunk
        language (str): Language code
        recognizer: Speech recognition recognizer instance
    
    Returns:
        str: Recognized text or None if failed
    """
    for lang in _language_candidates(language):
        try:
            if lang:
                return recognizer.recognize_google(audio_chunk, language=lang)
            return recognizer.recognize_google(audio_chunk)
        except sr.UnknownValueError:
            continue
        except sr.RequestError as e:
            print(f"⚠️ Recognition request failed for language {lang or 'auto'}: {e}")
            continue
    return None


def _transcribe_wav_in_chunks(audio_path, language, recognizer, chunk_seconds=30):
    """
    Transcribe long audio reliably by processing fixed-size chunks.
    
    Args:
        audio_path (str): Path to audio file
        language (str): Language code
        recognizer: Speech recognition recognizer instance
        chunk_seconds (int): Chunk duration in seconds
    
    Returns:
        str: Recognized text or None if failed
    """

    transcript_parts = []

    try:
        print("🎤 Processing audio for speech recognition...")
        with sr.AudioFile(audio_path) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.4)

            chunk_number = 1
            while True:
                audio_chunk = recognizer.record(source, duration=chunk_seconds)
                if not audio_chunk.frame_data:
                    break

                text = _recognize_chunk(audio_chunk, language, recognizer)
                if text:
                    transcript_parts.append(text.strip())
                    print(f"✅ Transcribed chunk {chunk_number}")
                else:
                    print(f"⚠️ No speech detected in chunk {chunk_number}")

                chunk_number += 1

        if not transcript_parts:
            return None

        return " ".join(part for part in transcript_parts if part)

    except Exception as e:
        print(f"❌ Audio chunk transcription failed: {e}")
        return None


def compress_video_with_transcript(input_file, output_file, transcript_file=None, 
                                  crf=28, preset='fast', resolution=None, 
                                  audio_codec='aac', audio_bitrate='128k',
                                  language='en-US'):
    """
    Compress video and optionally generate transcript.
    
    Args:
        input_file (str): Path to input video file
        output_file (str): Path to output compressed video file
        transcript_file (str): Path to output transcript file (optional)
        crf (int): Constant Rate Factor (18-30, lower = better quality)
        preset (str): Encoding preset (ultrafast to veryslow)
        resolution (tuple): Target resolution as (width, height) or None to keep original
        audio_codec (str): Audio codec for output
        audio_bitrate (str): Audio bitrate
        language (str): Language code for transcript generation (default: en-US)
    """
    
    print("🎬 Starting video compression and transcript generation...")
    print("=" * 60)
    
    # First compress the video
    compression_success = compress_video(
        input_file=input_file,
        output_file=output_file,
        crf=crf,
        preset=preset,
        resolution=resolution,
        audio_codec=audio_codec,
        audio_bitrate=audio_bitrate
    )
    
    if not compression_success:
        print("❌ Video compression failed. Skipping transcript generation.")
        return False
    
    # Generate transcript if requested
    if transcript_file:
        print("\n" + "=" * 60)
        print("📝 Starting transcript generation...")
        
        transcript = generate_transcript(input_file, transcript_file, language)
        
        if transcript:
            print(f"✅ Transcript generation completed successfully!")
            print(f"Transcript preview: {transcript[:100]}...")
        else:
            print("❌ Transcript generation failed!")
            return False
    
    return True


def run_processing_mode(mode, input_file, output_file, transcript_file=None,
                        crf=28, preset='fast', resolution=None,
                        audio_codec='aac', audio_bitrate='128k', language='en-US',
                        summary_file=None, azure_endpoint=None,
                        azure_deployment=None, azure_api_key=None,
                        azure_api_version='2024-02-15-preview',
                        azure_model_name=None):
    """Run one of the supported processing modes."""

    if mode == 'audio':
        return convert_video_to_audio(
            input_file=input_file,
            output_file=output_file,
            audio_codec=audio_codec,
            audio_bitrate=audio_bitrate
        )

    if mode == 'transcript':
        transcript = generate_transcript(
            input_file=input_file,
            output_file=output_file,
            language=language
        )
        return transcript is not None

    if mode == 'transcript-summary':
        transcript = generate_transcript(
            input_file=input_file,
            output_file=output_file,
            language=language
        )
        if not transcript:
            return False

        if not summary_file:
            summary_file = f"{os.path.splitext(output_file)[0]}_summary.txt"

        summary_text = summarize_transcript_with_azure_openai(
            transcript_text=transcript,
            endpoint=azure_endpoint,
            deployment=azure_deployment,
            api_key=azure_api_key,
            api_version=azure_api_version
        )
        save_text_output(summary_file, summary_text)
        if azure_model_name:
            print(f"🧠 Summary model reference: {azure_model_name}")
        print(f"🧠 Summary saved to: {summary_file}")
        return True

    print(f"❌ Unsupported mode: {mode}")
    return False


def main():
    """Main function to handle command line arguments and run compression."""
    load_dotenv_file()
    
    # Check if FFmpeg is available
    if not check_ffmpeg():
        print("❌ FFmpeg not found! Please install FFmpeg and add it to your system PATH.")
        print("Download from: https://ffmpeg.org/download.html")
        sys.exit(1)
    
    parser = argparse.ArgumentParser(
        description="Video Processor Tool - Convert video to audio, transcribe video, or transcribe and summarize with Azure OpenAI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # 1) Convert video to audio
    python video_compressor.py input.mp4 output.mp3 --mode audio --audio-codec mp3

    # 2) Get transcription from video
    python video_compressor.py input.mp4 transcript.txt --mode transcript --language en-US

    # 3) Get transcription and summarize with Azure OpenAI
    python video_compressor.py input.mp4 transcript.txt --mode transcript-summary --summary-output summary.txt --azure-endpoint https://your-resource.openai.azure.com --azure-deployment gpt-4o --azure-api-key YOUR_KEY
        """
    )
    
    parser.add_argument('input', help='Input video file path')
    parser.add_argument('output', help='Primary output path: audio file for audio mode, transcript file for transcript modes')
    parser.add_argument('--mode', default='audio', choices=['audio', 'transcript', 'transcript-summary'],
                       help='Processing mode: audio, transcript, or transcript-summary (default: audio)')
    parser.add_argument('--crf', type=int, default=28, choices=range(18, 31),
                       help='Constant Rate Factor (18-30, lower = better quality, default: 28)')
    parser.add_argument('--preset', default='fast', 
                       choices=['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow'],
                       help='Encoding preset (default: fast)')
    parser.add_argument('--resolution', nargs=2, type=int, metavar=('WIDTH', 'HEIGHT'),
                       help='Target resolution (e.g., 1280 720 for 720p)')
    parser.add_argument('--audio-codec', default='aac', help='Audio codec (default: aac)')
    parser.add_argument('--audio-bitrate', default='128k', help='Audio bitrate (default: 128k)')
    parser.add_argument('--transcript', metavar='FILE', help='Generate transcript and save to specified file')
    parser.add_argument('--language', default='en-US', help='Language code for transcript generation (default: en-US)')
    parser.add_argument('--summary-output', metavar='FILE', help='Summary output file for transcript-summary mode')
    parser.add_argument('--azure-endpoint', default=os.getenv('AZURE_OPENAI_ENDPOINT'), help='Azure OpenAI endpoint URL')
    parser.add_argument('--azure-deployment', default=os.getenv('AZURE_OPENAI_DEPLOYMENT'), help='Azure OpenAI deployment name')
    parser.add_argument('--azure-api-key', default=os.getenv('AZURE_OPENAI_API_KEY'), help='Azure OpenAI API key')
    parser.add_argument('--azure-api-version', default=os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'), help='Azure OpenAI API version')
    parser.add_argument('--azure-model-name', default=os.getenv('AZURE_OPENAI_MODEL_NAME'), help='Azure OpenAI model name reference')
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.input):
        print(f"❌ Input file not found: {args.input}")
        sys.exit(1)
    
    print("🎬 Video Processor Tool")
    print("=" * 50)

    if args.mode == 'transcript-summary':
        missing_settings = []
        if not args.azure_endpoint:
            missing_settings.append('azure-endpoint')
        if not args.azure_deployment:
            missing_settings.append('azure-deployment')
        if not args.azure_api_key:
            missing_settings.append('azure-api-key')
        if missing_settings:
            print(f"❌ Missing Azure OpenAI settings: {', '.join(missing_settings)}")
            sys.exit(1)

    success = run_processing_mode(
        mode=args.mode,
        input_file=args.input,
        output_file=args.output,
        transcript_file=args.transcript,
        crf=args.crf,
        preset=args.preset,
        resolution=args.resolution,
        audio_codec=args.audio_codec,
        audio_bitrate=args.audio_bitrate,
        language=args.language,
        summary_file=args.summary_output,
        azure_endpoint=args.azure_endpoint,
        azure_deployment=args.azure_deployment,
        azure_api_key=args.azure_api_key,
        azure_api_version=args.azure_api_version,
        azure_model_name=args.azure_model_name
    )
    
    if success:
        if args.mode == 'audio':
            print("\n🎉 Video to audio conversion completed successfully!")
        elif args.mode == 'transcript':
            print("\n🎉 Video transcription completed successfully!")
        else:
            print("\n🎉 Video transcription and AI summary completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Processing failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
