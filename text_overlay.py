import subprocess
import os
from pathlib import Path


class TextOverlay:
    """Add text overlay to videos with Windows-compatible output"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
    
    def add_stylized_text(self, video_path: str, brand_name: str = "HAHA HEADPHONE", 
                         start_time: float = None, duration: float = 5) -> str:
        """Add stylized text overlay and ensure Windows compatibility"""
        
        # Check input
        if not os.path.exists(video_path):
            print(f"Error: Input video not found: {video_path}")
            return video_path
        
        file_size = os.path.getsize(video_path)
        if file_size < 1000:
            print(f"Error: Input video too small: {file_size} bytes")
            return video_path
        
        output_path = str(Path(video_path).parent / 'final_with_text.mp4')
        
        # Get video duration
        if start_time is None:
            duration_cmd = [
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ]
            
            try:
                result = subprocess.run(duration_cmd, capture_output=True, text=True, timeout=10)
                total_duration = float(result.stdout.strip())
                start_time = max(0, total_duration - duration)
                print(f"Video duration: {total_duration:.2f}s")
                print(f"Text appears at: {start_time:.2f}s for {duration}s")
            except Exception as e:
                print(f"Could not get duration: {e}")
                start_time = 50
        
        # Escape brand name
        safe_brand_name = brand_name.replace("'", "\\'")
        
        # Text filter
        text_filter = (
            f"drawtext="
            f"text='{safe_brand_name}':"
            f"fontsize=90:"
            f"fontcolor=white:"
            f"x=(w-text_w)/2:"
            f"y=(h-text_h)/2:"
            f"alpha='if(lt(t,{start_time}),0,"
            f"if(lt(t,{start_time+1}),(t-{start_time})/1,"
            f"if(lt(t,{start_time+duration-1}),1,"
            f"({start_time+duration}-t)/1)))':"
            f"shadowcolor=black@0.8:"
            f"shadowx=4:"
            f"shadowy=4"
        )
        
        # IMPORTANT: Use Windows-compatible encoding settings
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-vf', text_filter,
            
            # Windows-compatible video codec
            '-c:v', 'libx264',
            '-profile:v', 'baseline',  # Baseline profile for compatibility
            '-level', '3.0',
            '-pix_fmt', 'yuv420p',
            '-crf', '23',
            '-preset', 'medium',
            
            # Windows-compatible audio codec
            '-c:a', 'aac',
            '-b:a', '192k',
            '-ar', '48000',
            
            # Fast start for streaming
            '-movflags', '+faststart',
            
            output_path
        ]
        
        print(f"Adding text: {brand_name}")
        print("Encoding with Windows-compatible settings...")
        
        result = subprocess.run(cmd, capture_output=True, shell=False)
        
        if result.returncode == 0:
            print(f"✓ Text overlay added successfully")
            print(f"  Output: {output_path}")
            
            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path) / (1024 * 1024)
                print(f"  Size: {output_size:.2f} MB")
                print(f"  Format: Windows-compatible MP4")
                return output_path
            else:
                print(f"Error: Output not created")
                return video_path
        else:
            error_msg = result.stderr.decode('utf-8', errors='ignore')
            print(f"Text overlay failed: {error_msg[:300]}")
            print(f"Returning original video")
            return video_path