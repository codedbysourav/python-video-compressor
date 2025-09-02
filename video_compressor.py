#!/usr/bin/env python3
"""
Video Compressor Tool
A Python script to compress video files using FFmpeg with various quality and resolution options.
"""

import os
import sys
import argparse
import ffmpeg
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


def main():
    """Main function to handle command line arguments and run compression."""
    
    # Check if FFmpeg is available
    if not check_ffmpeg():
        print("❌ FFmpeg not found! Please install FFmpeg and add it to your system PATH.")
        print("Download from: https://ffmpeg.org/download.html")
        sys.exit(1)
    
    parser = argparse.ArgumentParser(
        description="Video Compressor Tool - Compress videos using FFmpeg",
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
    
    # Run compression
    success = compress_video(
        input_file=args.input,
        output_file=args.output,
        crf=args.crf,
        preset=args.preset,
        resolution=args.resolution,
        audio_codec=args.audio_codec,
        audio_bitrate=args.audio_bitrate
    )
    
    if success:
        print("\n🎉 Video compression completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Video compression failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
