#!/usr/bin/env python3
"""
Example usage of the Video Compressor Tool
This script demonstrates how to use the video compressor programmatically.
"""

import os
import sys
from video_compressor import compress_video, check_ffmpeg


def main():
    """Example usage of the video compressor."""
    
    print("🎬 Video Compressor - Example Usage")
    print("=" * 50)
    
    # Check if FFmpeg is available
    if not check_ffmpeg():
        print("❌ FFmpeg not found! Please install FFmpeg first.")
        return
    
    # Example input file (you can change this)
    input_file = "input.mp4"
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"❌ Input file '{input_file}' not found.")
        print("Please place your video file in the same directory or update the input_file variable.")
        return
    
    print(f"✅ Input file found: {input_file}")
    print()
    
    # Example 1: Basic compression (default settings)
    print("📹 Example 1: Basic compression (CRF=28, preset=fast)")
    print("-" * 50)
    success1 = compress_video(
        input_file=input_file,
        output_file="compressed_basic.mp4"
    )
    print()
    
    # Example 2: High compression for maximum size reduction
    print("📹 Example 2: High compression (CRF=30, preset=ultrafast)")
    print("-" * 50)
    success2 = compress_video(
        input_file=input_file,
        output_file="compressed_high.mp4",
        crf=30,
        preset='ultrafast'
    )
    print()
    
    # Example 3: High quality compression
    print("📹 Example 3: High quality (CRF=20, preset=slow)")
    print("-" * 50)
    success3 = compress_video(
        input_file=input_file,
        output_file="compressed_quality.mp4",
        crf=20,
        preset='slow'
    )
    print()
    
    # Example 4: Compress and resize to 720p
    print("📹 Example 4: Compress and resize to 720p (CRF=28, preset=fast)")
    print("-" * 50)
    success4 = compress_video(
        input_file=input_file,
        output_file="compressed_720p.mp4",
        crf=28,
        preset='fast',
        resolution=(1280, 720)
    )
    print()
    
    # Example 5: Custom audio settings
    print("📹 Example 5: Custom audio settings (MP3, 96k)")
    print("-" * 50)
    success5 = compress_video(
        input_file=input_file,
        output_file="compressed_mp3.mp4",
        crf=28,
        preset='fast',
        audio_codec='mp3',
        audio_bitrate='96k'
    )
    print()
    
    # Summary
    print("📊 Compression Summary")
    print("=" * 50)
    examples = [
        ("Basic", success1, "compressed_basic.mp4"),
        ("High compression", success2, "compressed_high.mp4"),
        ("High quality", success3, "compressed_quality.mp4"),
        ("720p resize", success4, "compressed_720p.mp4"),
        ("MP3 audio", success5, "compressed_mp3.mp4")
    ]
    
    for name, success, output_file in examples:
        status = "✅ Success" if success else "❌ Failed"
        if success and os.path.exists(output_file):
            size = os.path.getsize(output_file) / (1024 * 1024)  # Size in MB
            print(f"{name:15} {status:12} {size:6.1f} MB")
        else:
            print(f"{name:15} {status:12} N/A")
    
    print()
    print("🎉 Examples completed! Check the output files above.")
    print("\n💡 Tips:")
    print("- Use CRF 18-20 for high quality (archiving)")
    print("- Use CRF 21-25 for good quality (general use)")
    print("- Use CRF 26-28 for balanced quality/size (default)")
    print("- Use CRF 29-30 for maximum compression")
    print("- Combine high CRF with resolution downscaling for maximum size reduction")


if __name__ == "__main__":
    main()
