#!/usr/bin/env python3
"""
Test script for transcription functionality
"""

from video_compressor import generate_transcript

def main():
    """Test transcription functionality."""
    
    print("🎙️ Testing Transcription Functionality")
    print("=" * 50)
    
    # Test with the available video file
    input_video = "ai-agent.mp4"
    transcript_file = "test_transcript.txt"
    
    print(f"Input video: {input_video}")
    print(f"Output transcript: {transcript_file}")
    print()
    
    # Test transcription
    transcript = generate_transcript(input_video, transcript_file, 'en-US')
    
    if transcript:
        print("\n✅ Transcription successful!")
        print(f"Transcript preview: {transcript[:200]}...")
        print(f"Full transcript saved to: {transcript_file}")
    else:
        print("\n❌ Transcription failed!")
        print("This could be due to:")
        print("- No speech in the video")
        print("- Poor audio quality")
        print("- Network connectivity issues")
        print("- Google Speech API rate limits")

if __name__ == "__main__":
    main()
