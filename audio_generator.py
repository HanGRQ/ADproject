import os
import random
from pathlib import Path
from typing import Dict, List
import subprocess


class AudioGenerator:
    """Generate and manage audio for video scenes"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir / 'audio'
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_cafe_noise(self, duration: float) -> str:
        """Generate cafe ambient noise"""
        output_path = self.output_dir / 'cafe_noise.mp3'
        
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', f'anoisesrc=d={duration}:c=brown:r=44100:a=0.3',
            '-af', 'highpass=f=200,lowpass=f=3000,volume=0.4',
            str(output_path)
        ]
        
        print(f"Generating cafe noise: {duration}s")
        subprocess.run(cmd, capture_output=True, shell=False)
        
        return str(output_path)
    
    def generate_calm_music(self, duration: float) -> str:
        """Generate calm background music"""
        output_path = self.output_dir / 'calm_music.mp3'
        
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', f'sine=frequency=440:duration={duration}',
            '-f', 'lavfi',
            '-i', f'sine=frequency=523:duration={duration}',
            '-f', 'lavfi',
            '-i', f'sine=frequency=659:duration={duration}',
            '-filter_complex',
            '[0:a][1:a][2:a]amix=inputs=3:duration=longest:dropout_transition=2,volume=0.2,lowpass=f=2000',
            str(output_path)
        ]
        
        print(f"Generating calm music: {duration}s")
        subprocess.run(cmd, capture_output=True, shell=False)
        
        return str(output_path)
    
    def generate_product_music(self, duration: float) -> str:
        """Generate upbeat product music"""
        output_path = self.output_dir / 'product_music.mp3'
        
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', f'sine=frequency=880:duration={duration}',
            '-f', 'lavfi',
            '-i', f'sine=frequency=1046:duration={duration}',
            '-filter_complex',
            '[0:a][1:a]amix=inputs=2:duration=longest,volume=0.3,highpass=f=500',
            str(output_path)
        ]
        
        print(f"Generating product music: {duration}s")
        subprocess.run(cmd, capture_output=True, shell=False)
        
        return str(output_path)
    
    def create_audio_timeline(self, scene_durations: List[Dict]) -> str:
        """Create complete audio timeline for all scenes"""
        print("\nCreating audio timeline...")
        print("-" * 60)
        
        audio_segments = []
        current_time = 0
        
        for i, scene in enumerate(scene_durations):
            scene_type = scene['type']
            duration = scene['duration']
            
            if scene_type == 'cafe':
                audio_path = self.generate_cafe_noise(duration)
                print(f"Scene {i+1}: Cafe noise ({duration}s)")
            elif scene_type == 'calm':
                audio_path = self.generate_calm_music(duration)
                print(f"Scene {i+1}: Calm music ({duration}s)")
            elif scene_type == 'product':
                audio_path = self.generate_product_music(duration)
                print(f"Scene {i+1}: Product music ({duration}s)")
            else:
                audio_path = self.generate_calm_music(duration)
                print(f"Scene {i+1}: Default music ({duration}s)")
            
            audio_segments.append({
                'path': audio_path,
                'start': current_time,
                'duration': duration
            })
            current_time += duration
        
        final_audio = self._merge_audio_segments(audio_segments)
        
        print(f"\nAudio timeline created: {final_audio}")
        return final_audio
    
    def _merge_audio_segments(self, segments: List[Dict]) -> str:
        """Merge multiple audio segments into one file"""
        output_path = self.output_dir / 'final_audio.mp3'
        
        if len(segments) == 1:
            return segments[0]['path']
        
        # Build input list
        inputs = []
        for seg in segments:
            inputs.extend(['-i', seg['path']])
        
        # Build filter complex for concatenation
        filter_complex = f"concat=n={len(segments)}:v=0:a=1[out]"
        
        cmd = ['ffmpeg', '-y'] + inputs + [
            '-filter_complex', filter_complex,
            '-map', '[out]',
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, shell=False)
        
        if result.returncode == 0:
            print(f"Audio segments merged successfully")
        else:
            print(f"Warning: Audio merge may have issues")
        
        return str(output_path)
    
    def add_fade_effects(self, audio_path: str) -> str:
        """Add fade in/out effects to audio"""
        
        # Check if input audio exists
        if not os.path.exists(audio_path):
            print(f"Warning: Audio file not found: {audio_path}")
            return audio_path
        
        output_path = self.output_dir / 'final_audio_faded.mp3'
        
        # Get audio duration first
        duration_cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            audio_path
        ]
        
        try:
            result = subprocess.run(duration_cmd, capture_output=True, text=True, timeout=10)
            duration = float(result.stdout.strip())
            fade_out_start = max(0, duration - 2)
        except:
            fade_out_start = 58  # Default fallback
        
        cmd = [
            'ffmpeg', '-y',
            '-i', audio_path,
            '-af', f'afade=t=in:st=0:d=1,afade=t=out:st={fade_out_start}:d=2',
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, shell=False)
        
        if result.returncode == 0 and os.path.exists(output_path):
            print(f"Fade effects added successfully")
            return str(output_path)
        else:
            print(f"Warning: Could not add fade effects, using original audio")
            return audio_path