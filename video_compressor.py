#!/usr/bin/env python3
"""
Video Compressor Tool
A Python script to compress video files using FFmpeg with various quality and resolution options.
Also includes transcript generation functionality using speech recognition.
"""

import os
import sys
import argparse
import ffmpeg
import speech_recognition as sr
import tempfile


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
                        audio_codec='aac', audio_bitrate='128k', language='en-US'):
    """Run one of the supported processing modes."""

    if mode == 'compress':
        return compress_video(
            input_file=input_file,
            output_file=output_file,
            crf=crf,
            preset=preset,
            resolution=resolution,
            audio_codec=audio_codec,
            audio_bitrate=audio_bitrate
        )

    if mode == 'audio':
        return convert_video_to_audio(
            input_file=input_file,
            output_file=output_file,
            audio_codec=audio_codec,
            audio_bitrate=audio_bitrate
        )

    if mode == 'audio-transcript':
        print("🎧 Converting video to audio...")
        audio_success = convert_video_to_audio(
            input_file=input_file,
            output_file=output_file,
            audio_codec=audio_codec,
            audio_bitrate=audio_bitrate
        )
        if not audio_success:
            return False

        if not transcript_file:
            transcript_file = f"{os.path.splitext(output_file)[0]}_transcript.txt"

        print("\n📝 Generating transcript from converted audio...")
        transcript = generate_transcript(
            input_file=output_file,
            output_file=transcript_file,
            language=language
        )
        return transcript is not None

    print(f"❌ Unsupported mode: {mode}")
    return False


def main():
    """Main function to handle command line arguments and run compression."""
    
    # Check if FFmpeg is available
    if not check_ffmpeg():
        print("❌ FFmpeg not found! Please install FFmpeg and add it to your system PATH.")
        print("Download from: https://ffmpeg.org/download.html")
        sys.exit(1)
    
    parser = argparse.ArgumentParser(
        description="Video Processor Tool - Compress video, convert to audio, or convert to audio and transcribe",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # 1) Compress video with default settings
  python video_compressor.py input.mp4 output.mp4
  
  # High compression (larger file size reduction)
  python video_compressor.py input.mp4 output.mp4 --crf 30 --preset ultrafast
  
  # Compress and resize to 720p
  python video_compressor.py input.mp4 output.mp4 --resolution 1280 720
  
  # High quality compression
  python video_compressor.py input.mp4 output.mp4 --crf 20 --preset slow
  
    # 2) Convert video to audio
    python video_compressor.py input.mp4 output.mp3 --mode audio --audio-codec mp3
  
    # 3) Convert video to audio and then generate transcript
    python video_compressor.py input.mp4 output.mp3 --mode audio-transcript --transcript transcript.txt

    # Audio + transcript in Spanish
    python video_compressor.py input.mp4 output.mp3 --mode audio-transcript --transcript transcript.txt --language es-ES
        """
    )
    
    parser.add_argument('input', help='Input video file path')
    parser.add_argument('output', help='Output compressed video file path')
    parser.add_argument('--mode', default='compress', choices=['compress', 'audio', 'audio-transcript'],
                       help='Processing mode: compress, audio, or audio-transcript (default: compress)')
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
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.input):
        print(f"❌ Input file not found: {args.input}")
        sys.exit(1)
    
    # Validate CRF range
    if args.crf < 18 or args.crf > 30:
        print("❌ CRF must be between 18 and 30")
        sys.exit(1)
    
    # Validate resolution if provided
    if args.resolution:
        width, height = args.resolution
        if width <= 0 or height <= 0:
            print("❌ Resolution dimensions must be positive integers")
            sys.exit(1)
    
    print("🎬 Video Processor Tool")
    print("=" * 50)

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
        language=args.language
    )
    
    if success:
        if args.mode == 'compress':
            print("\n🎉 Video compression completed successfully!")
        elif args.mode == 'audio':
            print("\n🎉 Video to audio conversion completed successfully!")
        else:
            print("\n🎉 Video to audio conversion and transcription completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Processing failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
