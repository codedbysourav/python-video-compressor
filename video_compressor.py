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
from pathlib import Path


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
    
    # Create temporary audio file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
        temp_audio_path = temp_audio.name
    
    try:
        print(f"🎵 Extracting audio from video...")
        
        # Extract audio using FFmpeg with multiple format attempts
        audio_formats = [
            # Format 1: Standard WAV with optimal speech recognition parameters
            {
                'acodec': 'pcm_s16le',
                'ar': 16000,
                'ac': 1,
                'f': 'wav',
                'loglevel': 'error'
            },
            # Format 2: Alternative WAV with different parameters
            {
                'acodec': 'pcm_s16le',
                'ar': 22050,
                'ac': 1,
                'f': 'wav',
                'loglevel': 'error'
            },
            # Format 3: FLAC format (lossless, often better for recognition)
            {
                'acodec': 'flac',
                'ar': 16000,
                'ac': 1,
                'f': 'flac',
                'loglevel': 'error'
            }
        ]
        
        transcript = None
        successful_format = None
        
        for i, format_params in enumerate(audio_formats):
            try:
                print(f"🎵 Trying audio format {i+1}...")
                
                # Extract audio with current format
                (
                    ffmpeg.input(input_file)
                    .output(temp_audio_path, **format_params)
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True, quiet=True)
                )
                
                # Try to recognize speech with this audio format
                transcript = _recognize_speech(temp_audio_path, language, recognizer)
                
                if transcript:
                    successful_format = i + 1
                    print(f"✅ Success with audio format {successful_format}")
                    break
                else:
                    print(f"⚠️ Audio format {i+1} failed, trying next...")
                    
            except Exception as e:
                print(f"⚠️ Audio format {i+1} extraction failed: {e}")
                continue
        
        if not transcript:
            print("❌ All audio formats failed")
            return None
        
        # Save transcript to file if output_file is specified
        if output_file:
            # Create output directory if it doesn't exist
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
        # Clean up temporary audio file
        if os.path.exists(temp_audio_path):
            os.unlink(temp_audio_path)


def _recognize_speech(audio_path, language, recognizer):
    """
    Attempt speech recognition with multiple strategies.
    
    Args:
        audio_path (str): Path to audio file
        language (str): Language code
        recognizer: Speech recognition recognizer instance
    
    Returns:
        str: Recognized text or None if failed
    """
    
    try:
        print(f"🎤 Processing audio for speech recognition...")
        
        # Load audio file
        with sr.AudioFile(audio_path) as source:
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            # Record audio
            audio = recognizer.record(source)
        
        print(f"🔍 Converting speech to text...")
        
        # Strategy 1: Try with original language code
        try:
            transcript = recognizer.recognize_google(audio, language=language)
            print("✅ Speech recognition successful with original language code")
            return transcript
        except sr.RequestError as e:
            print(f"⚠️ First attempt failed: {e}")
        
        # Strategy 2: Try with simplified language code
        try:
            if language == 'en-US':
                print("🔄 Retrying with 'en' language code...")
                transcript = recognizer.recognize_google(audio, language='en')
            elif language.startswith('en'):
                print("🔄 Retrying with 'en' language code...")
                transcript = recognizer.recognize_google(audio, language='en')
            else:
                base_lang = language.split('-')[0]
                print(f"🔄 Retrying with '{base_lang}' language code...")
                transcript = recognizer.recognize_google(audio, language=base_lang)
            
            if transcript:
                print("✅ Speech recognition successful with simplified language code")
                return transcript
                
        except sr.RequestError as e2:
            print(f"⚠️ Second attempt failed: {e2}")
        
        # Strategy 3: Try without specifying language (auto-detect)
        try:
            print("🔄 Retrying with auto-language detection...")
            transcript = recognizer.recognize_google(audio)
            if transcript:
                print("✅ Speech recognition successful with auto-detection")
                return transcript
        except sr.RequestError as e3:
            print(f"⚠️ Third attempt failed: {e3}")
        
        # Strategy 4: Try with different audio parameters
        try:
            print("🔄 Retrying with adjusted audio parameters...")
            # Adjust recognition parameters
            recognizer.energy_threshold = 300
            recognizer.dynamic_energy_threshold = True
            recognizer.pause_threshold = 0.8
            
            transcript = recognizer.recognize_google(audio, language='en')
            if transcript:
                print("✅ Speech recognition successful with adjusted parameters")
                return transcript
        except sr.RequestError as e4:
            print(f"⚠️ Fourth attempt failed: {e4}")
        
        # Strategy 5: Try chunking the audio for better recognition
        try:
            print("🔄 Retrying with audio chunking...")
            transcript = _recognize_chunked_audio(audio_path, language, recognizer)
            if transcript:
                print("✅ Speech recognition successful with audio chunking")
                return transcript
        except Exception as e5:
            print(f"⚠️ Fifth attempt (chunking) failed: {e5}")
        
        print("❌ All recognition strategies failed")
        return None
        
    except sr.UnknownValueError:
        print("❌ Speech recognition could not understand the audio")
        return None
    except Exception as e:
        print(f"❌ Error during speech recognition: {str(e)}")
        return None


def _recognize_chunked_audio(audio_path, language, recognizer):
    """
    Attempt recognition by splitting audio into smaller chunks.
    
    Args:
        audio_path (str): Path to audio file
        language (str): Language code
        recognizer: Speech recognition recognizer instance
    
    Returns:
        str: Recognized text or None if failed
    """
    
    try:
        # Create a new temporary file for chunked audio
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as chunked_audio:
            chunked_audio_path = chunked_audio.name
        
        try:
            # Extract audio in smaller chunks (30 seconds each)
            (
                ffmpeg.input(audio_path)
                .output(chunked_audio_path, 
                       acodec='pcm_s16le',
                       ar=16000,
                       ac=1,
                       f='wav',
                       segment_time=30,
                       segment_format='wav',
                       reset_timestamps=1)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True, quiet=True)
            )
            
            # Try to recognize the chunked audio
            with sr.AudioFile(chunked_audio_path) as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.record(source)
            
            transcript = recognizer.recognize_google(audio, language='en')
            return transcript
            
        finally:
            # Clean up chunked audio file
            if os.path.exists(chunked_audio_path):
                os.unlink(chunked_audio_path)
                
    except Exception as e:
        print(f"❌ Audio chunking failed: {e}")
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


def main():
    """Main function to handle command line arguments and run compression."""
    
    # Check if FFmpeg is available
    if not check_ffmpeg():
        print("❌ FFmpeg not found! Please install FFmpeg and add it to your system PATH.")
        print("Download from: https://ffmpeg.org/download.html")
        sys.exit(1)
    
    parser = argparse.ArgumentParser(
        description="Video Compressor Tool - Compress videos using FFmpeg with optional transcript generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic compression with default settings
  python video_compressor.py input.mp4 output.mp4
  
  # High compression (larger file size reduction)
  python video_compressor.py input.mp4 output.mp4 --crf 30 --preset ultrafast
  
  # Compress and resize to 720p
  python video_compressor.py input.mp4 output.mp4 --resolution 1280 720
  
  # High quality compression
  python video_compressor.py input.mp4 output.mp4 --crf 20 --preset slow
  
  # Compress video and generate transcript
  python video_compressor.py input.mp4 output.mp4 --transcript transcript.txt
  
  # Compress video and generate transcript in Spanish
  python video_compressor.py input.mp4 output.mp4 --transcript transcript.txt --language es-ES
        """
    )
    
    parser.add_argument('input', help='Input video file path')
    parser.add_argument('output', help='Output compressed video file path')
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
    
    print("🎬 Video Compressor Tool")
    print("=" * 50)
    
    # Run compression with optional transcript generation
    success = compress_video_with_transcript(
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
        if args.transcript:
            print("\n🎉 Video compression and transcript generation completed successfully!")
        else:
            print("\n🎉 Video compression completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Video compression failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
