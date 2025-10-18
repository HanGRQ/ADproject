import subprocess
import os
from pathlib import Path
from typing import List


class ColorMatcher:
    """Video color matching and lighting consistency processing"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.temp_dir = output_dir / 'temp_color_match'
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze_video_colors(self, video_path: str) -> dict:
        """Analyze video color information"""
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=avg_frame_rate,r_frame_rate',
            '-of', 'json',
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        try:
            import json
            data = json.loads(result.stdout)
            return data
        except:
            return {}
    
    def normalize_video_brightness(self, video_path: str, scene_num: int) -> str:
        """Normalize video brightness"""
        output_path = self.temp_dir / f'normalized_{scene_num:02d}.mp4'
        
        # Use FFmpeg eq filter to normalize brightness and contrast
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-vf', 'eq=brightness=0:contrast=1.1:saturation=1.0,curves=preset=lighter',
            '-c:a', 'copy',
            str(output_path)
        ]
        
        print(f"  Normalizing brightness for scene {scene_num}...")
        result = subprocess.run(cmd, capture_output=True, shell=True)
        
        if result.returncode == 0:
            return str(output_path)
        return video_path
    
    def match_color_to_reference(self, video_path: str, reference_video: str, 
                                scene_num: int) -> str:
        """Match video colors to reference video"""
        output_path = self.temp_dir / f'matched_{scene_num:02d}.mp4'
        
        # Use colorlevels and curves filters for color matching
        # This is a basic implementation, adjust as needed
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-vf', (
                'colorlevels=rimax=0.902:gimax=0.902:bimax=0.902,'
                'colorbalance=rs=0.1:gs=0:bs=-0.1:rm=0:gm=0:bm=0:rh=0:gh=0:bh=0,'
                'eq=contrast=1.05:brightness=0:saturation=1.0'
            ),
            '-c:a', 'copy',
            str(output_path)
        ]
        
        print(f"  Matching colors of scene {scene_num} to reference video...")
        result = subprocess.run(cmd, capture_output=True, shell=True)
        
        if result.returncode == 0:
            return str(output_path)
        return video_path
    
    def smooth_transitions(self, video_paths: List[str]) -> List[str]:
        """Add smooth transitions between video clips"""
        print("\nAdding smooth transitions between scenes...")
        print("-" * 60)
        
        smoothed_paths = []
        
        for i, video_path in enumerate(video_paths):
            scene_num = i + 1
            output_path = self.temp_dir / f'smoothed_{scene_num:02d}.mp4'
            
            # Add fade out effect at end (0.5 seconds)
            # Next video starts with fade in effect (0.5 seconds)
            if i < len(video_paths) - 1:
                fade_duration = 0.5
                
                cmd = [
                    'ffmpeg', '-y',
                    '-i', video_path,
                    '-vf', f'fade=t=out:st=7.5:d={fade_duration}',
                    '-c:a', 'copy',
                    str(output_path)
                ]
            else:
                # Last video doesn't need fade out
                cmd = [
                    'ffmpeg', '-y',
                    '-i', video_path,
                    '-c', 'copy',
                    str(output_path)
                ]
            
            result = subprocess.run(cmd, capture_output=True, shell=True)
            
            if result.returncode == 0:
                smoothed_paths.append(str(output_path))
                print(f"  Scene {scene_num}: Transition effect added")
            else:
                smoothed_paths.append(video_path)
                print(f"  Scene {scene_num}: Using original video")
        
        return smoothed_paths
    
    def apply_uniform_color_grading(self, video_paths: List[str]) -> List[str]:
        """Apply uniform color grading to all videos"""
        print("\nApplying uniform color grading...")
        print("-" * 60)
        
        graded_paths = []
        reference_video = video_paths[0] if video_paths else None
        
        for i, video_path in enumerate(video_paths):
            scene_num = i + 1
            
            # Check if placeholder
            if not os.path.exists(video_path) or os.path.getsize(video_path) < 1000:
                print(f"  Scene {scene_num}: Skipping placeholder")
                graded_paths.append(video_path)
                continue
            
            # First video as reference
            if i == 0:
                print(f"  Scene {scene_num}: Set as reference video")
                # Only normalize brightness
                graded_path = self.normalize_video_brightness(video_path, scene_num)
                graded_paths.append(graded_path)
            else:
                # Other videos match to reference
                print(f"  Scene {scene_num}: Matching colors and lighting")
                # First normalize
                normalized = self.normalize_video_brightness(video_path, scene_num)
                # Then match colors
                graded_path = self.match_color_to_reference(
                    normalized, 
                    reference_video, 
                    scene_num
                )
                graded_paths.append(graded_path)
        
        print(f"\nColor grading complete: {len(graded_paths)} video clips")
        return graded_paths
    
    def process_video_consistency(self, video_paths: List[str]) -> List[str]:
        """Process video consistency (color, lighting, transitions)"""
        print("\n=== Starting Video Consistency Processing ===\n")
        
        # Step 1: Uniform color grading
        graded_videos = self.apply_uniform_color_grading(video_paths)
        
        # Step 2: Add smooth transitions
        final_videos = self.smooth_transitions(graded_videos)
        
        return final_videos