"""
Convert video to Windows-compatible format
Fixes playback issues on Windows Media Player, VLC, etc.
"""
import os
import subprocess
from pathlib import Path


def convert_to_windows_compatible(input_video: str, output_video: str = None) -> str:
    """
    Convert video to Windows-compatible format with proper codecs
    
    Args:
        input_video: Path to input video file
        output_video: Path to output video file (optional)
    
    Returns:
        Path to converted video file
    """
    
    if not os.path.exists(input_video):
        print(f"Error: Input video not found: {input_video}")
        return None
    
    # Generate output filename if not provided
    if output_video is None:
        input_path = Path(input_video)
        output_video = str(input_path.parent / f'{input_path.stem}_WINDOWS_COMPATIBLE.mp4')
    
    print("=" * 60)
    print("Converting to Windows-Compatible Format")
    print("=" * 60)
    print(f"Input:  {input_video}")
    print(f"Output: {output_video}")
    print()
    
    # FFmpeg command with Windows-compatible settings
    cmd = [
        'ffmpeg', '-y',
        '-i', input_video,
        
        # Video codec settings - H.264 baseline profile (most compatible)
        '-c:v', 'libx264',
        '-profile:v', 'baseline',  # Baseline profile for maximum compatibility
        '-level', '3.0',            # Level 3.0 for older devices
        '-pix_fmt', 'yuv420p',      # Standard pixel format
        '-crf', '23',               # Quality (lower = better, 23 is good balance)
        '-preset', 'medium',        # Encoding speed
        
        # Audio codec settings - AAC (Windows compatible)
        '-c:a', 'aac',
        '-b:a', '192k',             # Audio bitrate
        '-ar', '48000',             # Sample rate (48kHz standard)
        '-ac', '2',                 # Stereo audio
        
        # Additional compatibility settings
        '-movflags', '+faststart',  # Enable streaming/quick start
        '-max_muxing_queue_size', '1024',
        
        output_video
    ]
    
    print("Converting video...")
    print("This may take a few minutes depending on video length...")
    print()
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            shell=False,
            text=True
        )
        
        if result.returncode == 0:
            if os.path.exists(output_video):
                file_size = os.path.getsize(output_video) / (1024 * 1024)
                
                print("=" * 60)
                print("✓ CONVERSION SUCCESSFUL!")
                print("=" * 60)
                print(f"Output file: {output_video}")
                print(f"File size: {file_size:.2f} MB")
                print()
                print("This video should now play in:")
                print("  ✓ Windows Media Player")
                print("  ✓ VLC Media Player")
                print("  ✓ Movies & TV app")
                print("  ✓ Any web browser")
                print("  ✓ Mobile devices")
                print()
                
                return output_video
            else:
                print("Error: Output file was not created")
                return None
        else:
            print("=" * 60)
            print("✗ CONVERSION FAILED")
            print("=" * 60)
            error_msg = result.stderr
            print(f"Error: {error_msg[:500]}")
            return None
            
    except Exception as e:
        print(f"Exception occurred: {e}")
        return None


def convert_all_finals():
    """Find and convert all final videos in the project"""
    print("=" * 60)
    print("Searching for Final Videos to Convert")
    print("=" * 60)
    print()
    
    project_dir = Path('.')
    final_dir = project_dir / 'output' / '04_final'
    
    if not final_dir.exists():
        print(f"Error: Final output directory not found: {final_dir}")
        return
    
    # Look for final videos
    video_files = [
        final_dir / 'final_with_text.mp4',
        final_dir / 'video_with_audio.mp4',
        final_dir / 'merged_video_silent.mp4'
    ]
    
    converted_files = []
    
    for video_file in video_files:
        if video_file.exists():
            print(f"Found: {video_file.name}")
            output_file = str(video_file.parent / f'{video_file.stem}_WINDOWS.mp4')
            
            result = convert_to_windows_compatible(str(video_file), output_file)
            if result:
                converted_files.append(result)
            print()
    
    if converted_files:
        print("=" * 60)
        print(f"✓ Converted {len(converted_files)} video(s)")
        print("=" * 60)
        print("\nConverted files:")
        for f in converted_files:
            print(f"  • {f}")
        print("\nYou can now play these files on Windows!")
    else:
        print("No videos were converted. Make sure videos exist in output/04_final/")


def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1:
        # Convert specific file provided as argument
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        convert_to_windows_compatible(input_file, output_file)
    else:
        # Convert all final videos in project
        convert_all_finals()


if __name__ == "__main__":
    main()