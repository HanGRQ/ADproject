import subprocess
from pathlib import Path


class TextOverlay:
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
    
    def add_stylized_text(self, video_path: str, brand_name: str = "HAHA HEADPHONE", 
                         start_time: float = None, duration: float = 5) -> str:
        output_path = str(Path(video_path).parent / 'final_with_text.mp4')
        
        if start_time is None:
            duration_cmd = [
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ]
            result = subprocess.run(duration_cmd, capture_output=True, text=True)
            try:
                total_duration = float(result.stdout.strip())
                start_time = max(0, total_duration - duration)
            except:
                start_time = 50
        
        text_filter = (
            f"drawtext="
            f"text='{brand_name}':"
            f"fontsize=90:"
            f"fontcolor=white:"
            f"x=(w-text_w)/2:"
            f"y=(h-text_h)/2:"
            f"alpha='if(lt(t,{start_time}),0,if(lt(t,{start_time+1}),(t-{start_time})/1,if(lt(t,{start_time+duration-1}),1,({start_time+duration}-t)/1)))':"
            f"shadowcolor=black@0.8:"
            f"shadowx=4:"
            f"shadowy=4"
        )
        
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-vf', text_filter,
            '-codec:a', 'copy',
            output_path
        ]
        
        print(f"Adding brand text: {brand_name}")
        print(f"Display time: {start_time:.1f}s - {start_time+duration:.1f}s")
        
        result = subprocess.run(cmd, capture_output=True, shell=True)
        
        if result.returncode == 0:
            print(f"Text overlay added successfully")
        else:
            print(f"Text overlay warning: {result.stderr.decode()[:200]}")
        
        return output_path