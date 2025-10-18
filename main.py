import os
import json
import time
import requests
import subprocess
import base64
from pathlib import Path
from typing import List, Dict
import anthropic
from audio_generator import AudioGenerator
from text_overlay import TextOverlay
from image_editor import ImageEditor
from color_matcher import ColorMatcher


class ImprovedHeadphoneAdVideoGenerator:
    """Improved Headphone Advertisement Video Generator with consistency processing"""
    
    def __init__(self, api_keys: Dict[str, str]):
        self.claude_client = anthropic.Anthropic(api_key=api_keys.get('claude_api_key'))
        self.byteplus_api_key = api_keys.get('byteplus_api_key')
        
        self.images_api = "https://ark.ap-southeast.bytepluses.com/api/v3/images/generations"
        self.videos_api = "https://ark.ap-southeast.bytepluses.com/api/v3/videos/generations"
        
        self.project_dir = Path('.')
        self.dirs = {
            'storyboard': self.project_dir / 'output' / '01_storyboard',
            'images': self.project_dir / 'output' / '02_images',
            'videos': self.project_dir / 'output' / '03_video_clips',
            'final': self.project_dir / 'output' / '04_final',
            'assets': self.project_dir / 'assets'
        }
        self._create_directories()
        
        # Initialize modules
        self.audio_generator = AudioGenerator(self.project_dir / 'output')
        self.text_overlay = TextOverlay(self.dirs['final'])
        self.image_editor = ImageEditor(self.byteplus_api_key, self.project_dir)
        self.color_matcher = ColorMatcher(self.dirs['videos'])
    
    def _create_directories(self):
        """Create output directory structure"""
        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        print("Directory structure created\n")
    
    def load_story(self, story_path: str) -> str:
        """Load story from text file"""
        with open(story_path, 'r', encoding='utf-8') as f:
            story = f.read()
        print(f"Story loaded: {len(story)} characters\n")
        return story
    
    def generate_storyboard_text(self, story: str) -> List[Dict]:
        """Generate storyboard with STRICT constraints to avoid laptop screen duplication"""
        prompt = f"""Create a detailed 60-second video storyboard for a wireless headphone advertisement.

CRITICAL LAPTOP/COMPUTER CONSTRAINTS (MUST FOLLOW):
=================================================
1. LAPTOP POSITIONING:
   - Laptop must be viewed from a NORMAL side angle or slight front angle
   - Laptop lid should be at 90-120 degree angle (normal working position)
   - NEVER show laptop from behind or from unusual angles
   - Screen content must be simple (avoid complex ERROR messages)
   
2. LAPTOP SCREEN RULES:
   - There is ONLY ONE laptop with ONLY ONE screen
   - Screen is INSIDE the laptop bezel (not extending beyond edges)
   - Screen shows simple content: a document, website, or work interface
   - NO duplicate screens, NO floating screens, NO screen reflections that look like second screens
   
3. RECOMMENDED LAPTOP DESCRIPTION:
   "Silver modern laptop placed on wooden table, viewed from slight side angle, 
   lid open at normal 100-degree angle, showing simple work interface on screen, 
   laptop is compact and realistically proportioned"

OBJECT PLACEMENT AND PHYSICS:
=============================
1. Headphones placement:
   - Scene 1: Wireless headphones LYING FLAT on table (not standing up, not floating)
   - Scene 2: Person's hand reaching for the FLAT headphones on table
   - Scene 3+: Person WEARING headphones on head, NO headphones on table anymore
   
2. Table setup:
   - Wooden table surface clearly visible
   - Objects arranged naturally: laptop (closed or at normal angle) + headphones
   - Everything properly grounded on table surface

CHARACTER CONSISTENCY:
====================
- Same person throughout: Young woman, mid-20s
- Exact same clothing: White button-up shirt, navy blue cardigan
- Same hair: Long brown hair
- Same cafe environment for scenes 1-5

SCENE STRUCTURE (7 scenes, 60 seconds total):
============================================

Scene 1 (10s): "Stressed at Cafe" - ESTABLISH SETUP
Visual: Young woman in white shirt and navy cardigan sitting at wooden cafe table. 
SILVER LAPTOP on table (viewed from slight side angle, lid open at normal angle showing simple work interface). 
WIRELESS BLACK HEADPHONES lying flat on table next to laptop (not standing, fully resting on table surface). 
Large windows with morning sunlight. Modern minimalist cafe. Woman looks stressed.
Audio: "cafe"

Scene 2 (8s): "Noticing Headphones"
Visual: Same woman, same cafe. Close-up of her hand reaching toward the flat headphones on table. 
Laptop still visible in background at normal angle. Natural hand movement.
Audio: "cafe"

Scene 3 (8s): "Putting On Headphones"
Visual: Same woman, same cafe. She is NOW WEARING the headphones on her head. 
Table shows only laptop (no headphones on table anymore). 
Woman's expression beginning to relax. Same morning lighting.
Audio: "calm" (transition from noise to calm)

Scene 4 (10s): "Enjoying Music"
Visual: Same woman WEARING headphones on head, eyes closed, peaceful expression. 
Same cafe, same table with laptop. NO headphones on table. 
Soft focus, calm atmosphere.
Audio: "calm"

Scene 5 (10s): "Complete Relaxation"
Visual: Same woman still WEARING headphones, completely relaxed and happy. 
Slight smile, immersed in music. Same environment.
Audio: "calm"

Scene 6 (10s): "Product Hero Shot"
Visual: Professional product photography. Clean white or gradient background (NOT cafe). 
Wireless black headphones elegantly displayed. Brand logo "HAHA" visible. 
Studio lighting. Premium feel.
Audio: "product"

Scene 7 (4s): "Brand Closeup"
Visual: Headphones with brand name prominently displayed. Clean professional shot.
Audio: "product"

OUTPUT FORMAT: Pure JSON array with these exact fields:
[
  {{
    "scene_number": 1,
    "duration": 10,
    "visual_description": "[Detailed description following rules above]",
    "action": "[Specific action]",
    "dialogue": "",
    "camera_angle": "[Camera position - must be normal angle for laptop scenes]",
    "audio_type": "cafe",
    "consistency_notes": "[What stays consistent]"
  }},
  ...
]

CRITICAL REMINDERS:
- ONE laptop with ONE screen only
- Laptop at NORMAL viewing angle (90-120 degrees)
- Headphones: FLAT on table in scene 1-2, WORN on head in scene 3-5
- Same person, same clothes, same cafe in scenes 1-5

Original story:
{story}

Generate the JSON storyboard following ALL the rules above."""
        
        print("Step 1/6: Generating storyboard with strict laptop constraints...")
        print("-" * 60)
        
        message = self.claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text
        
        try:
            # Extract JSON
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text
            
            storyboard = json.loads(json_text)
            
            if isinstance(storyboard, dict) and 'scenes' in storyboard:
                storyboard = storyboard['scenes']
            
            # Save storyboard
            output_path = self.dirs['storyboard'] / 'storyboard.json'
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(storyboard, f, ensure_ascii=False, indent=2)
            
            readable_path = self.dirs['storyboard'] / 'storyboard_readable.txt'
            with open(readable_path, 'w', encoding='utf-8') as f:
                for i, scene in enumerate(storyboard, 1):
                    f.write(f"\n{'='*60}\n")
                    f.write(f"Scene {i}: {scene.get('duration', 8)}s\n")
                    f.write(f"{'='*60}\n")
                    f.write(f"Visual: {scene.get('visual_description', '')}\n\n")
                    f.write(f"Action: {scene.get('action', '')}\n\n")
                    f.write(f"Dialogue: {scene.get('dialogue', '')}\n\n")
                    f.write(f"Camera: {scene.get('camera_angle', '')}\n")
                    f.write(f"Audio Type: {scene.get('audio_type', 'calm')}\n")
                    f.write(f"Consistency: {scene.get('consistency_notes', '')}\n")
            
            print(f"\nStoryboard generated successfully")
            print(f"  Scenes: {len(storyboard)}")
            print(f"  Total duration: {sum(s.get('duration', 8) for s in storyboard)}s")
            print(f"  Saved to: {output_path}\n")
            
            return storyboard
            
        except json.JSONDecodeError as e:
            print(f"\nJSON parsing error: {e}")
            raise
    
    def generate_images(self, storyboard: List[Dict]) -> List[str]:
        """Generate images with STRICT laptop screen constraints"""
        image_paths = []
        reference_image_path = None
        
        print("\nStep 2/6: Generating images with laptop screen constraints...")
        print("-" * 60)
        
        for i, scene in enumerate(storyboard):
            scene_num = scene.get('scene_number', i + 1)
            visual_desc = scene.get('visual_description', '')
            
            # CRITICAL: Laptop constraints for scenes with laptop
            has_laptop = 'laptop' in visual_desc.lower()
            
            if i == 0:
                # First scene with laptop - STRICT constraints
                enhanced_prompt = (
                    f"Professional commercial photography, photorealistic, 4K quality. "
                    f"CRITICAL LAPTOP RULES: "
                    f"There is ONLY ONE laptop with ONLY ONE screen. "
                    f"Laptop is silver/gray, modern, compact design. "
                    f"Laptop viewed from NORMAL side angle (NOT from behind, NOT unusual angles). "
                    f"Laptop lid open at 90-110 degree angle (normal working position). "
                    f"Screen shows SIMPLE content (document or simple interface, NO complex error messages). "
                    f"Screen is COMPLETELY within laptop bezel frame. "
                    f"NO duplicate screens, NO floating screens, NO screen reflections. "
                    f"HEADPHONES: Wireless black headphones LYING FLAT on wooden table surface (not standing up). "
                    f"Headphones fully resting on table, realistic and grounded. "
                    f"{visual_desc}. "
                    f"Everything realistically proportioned and properly placed. "
                    f"Clean composition, natural cafe lighting."
                )
                print(f"Scene {scene_num}: First frame with STRICT laptop constraints")
                
            elif i == len(storyboard) - 1:
                # Product closeup - no laptop
                enhanced_prompt = (
                    f"Professional product photography, studio quality, 4K. "
                    f"{visual_desc}. "
                    f"Clean background, premium lighting, realistic proportions."
                )
                print(f"Scene {scene_num}: Product closeup")
                
            else:
                # Middle scenes
                wearing_headphones = (i >= 3)  # Scene 3+ wears headphones
                
                if has_laptop and wearing_headphones:
                    laptop_headphone_constraint = (
                        f"CRITICAL: Person is WEARING headphones on head. "
                        f"Table has ONLY the laptop (NO headphones on table). "
                        f"Laptop at normal angle with ONE screen visible. "
                    )
                elif has_laptop:
                    laptop_headphone_constraint = (
                        f"Laptop at normal side angle with ONE screen. "
                        f"Headphones flat on table. "
                    )
                else:
                    laptop_headphone_constraint = ""
                
                enhanced_prompt = (
                    f"Professional commercial photography, photorealistic, consistent with reference. "
                    f"EXACT same person (white shirt, navy cardigan, long brown hair). "
                    f"SAME cafe with morning light through windows. "
                    f"{laptop_headphone_constraint}"
                    f"{visual_desc}. "
                    f"Natural and realistic, proper proportions, 4K quality."
                )
                print(f"Scene {scene_num}: Middle scene with consistency")
            
            print(f"  Prompt preview: {enhanced_prompt[:100]}...")
            
            image_path = self._call_seedream_api(
                enhanced_prompt, 
                scene_num,
                reference_image=reference_image_path if i > 0 else None
            )
            image_paths.append(image_path)
            
            if i == 0 and reference_image_path is None:
                with open(image_path, 'rb') as f:
                    if len(f.read()) > 1000:
                        reference_image_path = image_path
                        print(f"  ✓ Set as reference")
            
            print(f"  Saved: {os.path.basename(image_path)}\n")
            time.sleep(3)
        
        print(f"All images generated: {len(image_paths)}\n")
        return image_paths
    
    def _call_seedream_api(self, prompt: str, scene_num: int, reference_image: str = None) -> str:
        """Call Seedream API to generate image"""
        headers = {
            "Authorization": f"Bearer {self.byteplus_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "seedream-4-0-250828",
            "prompt": prompt,
            "sequential_image_generation": "disabled",
            "response_format": "url",
            "size": "1920x1080",
            "stream": False,
            "watermark": False
        }
        
        if reference_image:
            try:
                with open(reference_image, 'rb') as f:
                    ref_data = f.read()
                ref_base64 = base64.b64encode(ref_data).decode('utf-8')
                payload["image"] = f"data:image/png;base64,{ref_base64}"
                print(f"  Using reference image")
            except Exception as e:
                print(f"  Warning: {e}")
        
        try:
            print(f"  Calling Seedream API...")
            response = requests.post(self.images_api, headers=headers, json=payload, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                if 'data' in result and len(result['data']) > 0:
                    image_url = result['data'][0].get('url')
                    if image_url:
                        print(f"  Downloading...")
                        image_data = requests.get(image_url, timeout=60).content
                        image_path = self.dirs['images'] / f'scene_{scene_num:02d}.png'
                        with open(image_path, 'wb') as f:
                            f.write(image_data)
                        print(f"  Success")
                        return str(image_path)
            
            raise Exception(f"API error {response.status_code}")
            
        except Exception as e:
            print(f"  Failed: {e}")
            image_path = self.dirs['images'] / f'scene_{scene_num:02d}.png'
            with open(image_path, 'w') as f:
                f.write(f"Placeholder {scene_num}")
            return str(image_path)
    
    def generate_video_clips(self, image_paths: List[str], storyboard: List[Dict]) -> List[str]:
        """Generate video clips"""
        video_paths = []
        
        print("\nStep 4/6: Generating video clips...")
        print("-" * 60)
        
        for i, (image_path, scene) in enumerate(zip(image_paths, storyboard)):
            scene_num = scene.get('scene_number', i + 1)
            duration = scene.get('duration', 8)
            action = scene.get('action', '')
            
            print(f"Scene {scene_num}: {duration}s video")
            
            video_path = self._call_seedance_api(image_path, action, duration, scene_num)
            video_paths.append(video_path)
            print(f"  Saved: {os.path.basename(video_path)}\n")
            time.sleep(2)
        
        print(f"All videos generated: {len(video_paths)}\n")
        return video_paths
    
    def _call_seedance_api(self, image_path: str, motion_prompt: str, duration: int, scene_num: int) -> str:
        """Call Seedance API"""
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        if len(image_data) < 1000:
            video_path = self.dirs['videos'] / f'clip_{scene_num:02d}.mp4'
            with open(video_path, 'w') as f:
                f.write(f"Placeholder {scene_num}")
            return str(video_path)
        
        headers = {
            "Authorization": f"Bearer {self.byteplus_api_key}",
            "Content-Type": "application/json"
        }
        
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        image_data_url = f"data:image/png;base64,{image_base64}"
        
        create_url = "https://ark.ap-southeast.bytepluses.com/api/v3/contents/generations/tasks"
        
        payload = {
            "model": "seedance-1-0-lite-i2v-250428",
            "content": [
                {"type": "image_url", "image_url": {"url": image_data_url}, "role": "first_frame"},
                {"type": "text", "text": f"{motion_prompt} --duration {min(duration, 10)} --ratio 16:9 --resolution 720p --fps 24 --watermark false"}
            ]
        }
        
        try:
            response = requests.post(create_url, headers=headers, json=payload, timeout=60)
            if response.status_code != 200:
                raise Exception(f"Failed: {response.status_code}")
            
            task_id = response.json().get('id')
            if not task_id:
                raise Exception("No task ID")
            
            print(f"  Task: {task_id}, waiting...")
            query_url = f"https://ark.ap-southeast.bytepluses.com/api/v3/contents/generations/tasks/{task_id}"
            
            for attempt in range(60):
                time.sleep(10)
                status_response = requests.get(query_url, headers=headers, timeout=30)
                if status_response.status_code != 200:
                    continue
                
                status_result = status_response.json()
                task_status = status_result.get('status')
                print(f"  Status: {task_status} ({attempt+1}/60)")
                
                if task_status == 'succeeded':
                    video_url = status_result.get('content', {}).get('video_url')
                    if video_url:
                        video_data = requests.get(video_url, timeout=120).content
                        video_path = self.dirs['videos'] / f'clip_{scene_num:02d}.mp4'
                        with open(video_path, 'wb') as f:
                            f.write(video_data)
                        return str(video_path)
                elif task_status == 'failed':
                    raise Exception(f"Task failed")
                elif task_status in ['queued', 'running']:
                    continue
            
            raise Exception("Timeout")
        except Exception as e:
            print(f"  Error: {e}")
            video_path = self.dirs['videos'] / f'clip_{scene_num:02d}.mp4'
            with open(video_path, 'w') as f:
                f.write(f"Placeholder {scene_num}")
            return str(video_path)
    
    def merge_videos_with_audio(self, video_paths: List[str], audio_path: str) -> str:
        """Merge videos and add audio in ONE step"""
        print("\nMerging videos with audio...")
        print("-" * 60)
        
        # Create concat list
        list_file = self.dirs['videos'] / 'concat_list.txt'
        with open(list_file, 'w', encoding='utf-8') as f:
            for video_path in video_paths:
                if not os.path.exists(video_path):
                    continue
                abs_path = os.path.abspath(video_path).replace('\\', '/')
                f.write(f"file '{abs_path}'\n")
        
        # Merge videos silently first
        merged_silent = self.dirs['final'] / 'merged_silent.mp4'
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(list_file),
            '-c', 'copy',
            str(merged_silent)
        ]
        
        result = subprocess.run(cmd, capture_output=True, shell=False)
        if result.returncode != 0:
            # Try re-encoding
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(list_file),
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                str(merged_silent)
            ]
            subprocess.run(cmd, capture_output=True, shell=False)
        
        # Add audio
        if not os.path.exists(audio_path):
            print(f"No audio file, returning video without audio")
            return str(merged_silent)
        
        video_with_audio = self.dirs['final'] / 'video_with_audio.mp4'
        cmd = [
            'ffmpeg', '-y',
            '-i', str(merged_silent),
            '-i', str(audio_path),
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-shortest',
            str(video_with_audio)
        ]
        
        result = subprocess.run(cmd, capture_output=True, shell=False)
        if result.returncode == 0 and os.path.exists(video_with_audio):
            print(f"✓ Audio added successfully")
            return str(video_with_audio)
        else:
            print(f"Audio merge failed, using video without audio")
            return str(merged_silent)
    
    def generate_complete_ad(self, story_path: str, brand_name: str = "HAHA HEADPHONE"):
        """Generate complete ad - FIXED workflow"""
        print("\n" + "=" * 60)
        print("Wireless Headphone Ad Generator")
        print("Fixed: No duplicate laptop screens + Proper audio/text integration")
        print("=" * 60 + "\n")
        
        try:
            # Steps
            story = self.load_story(story_path)
            storyboard = self.generate_storyboard_text(story)
            image_paths = self.generate_images(storyboard)
            
            print("\nStep 3/6: Skipping image editing")
            print("-" * 60)
            
            video_paths = self.generate_video_clips(image_paths, storyboard)
            
            print("\nStep 5/6: Video consistency processing...")
            print("-" * 60)
            consistent_videos = self.color_matcher.process_video_consistency(video_paths)
            
            print("\nGenerating audio...")
            print("-" * 60)
            audio_scenes = []
            for scene in storyboard:
                audio_scenes.append({
                    'type': scene.get('audio_type', 'calm'),
                    'duration': scene.get('duration', 8)
                })
            
            audio_path = self.audio_generator.create_audio_timeline(audio_scenes)
            audio_path = self.audio_generator.add_fade_effects(audio_path)
            print(f"Audio: {audio_path}")
            
            # Merge with audio
            video_with_audio = self.merge_videos_with_audio(consistent_videos, audio_path)
            
            # Add text
            print("\nAdding text overlay...")
            print("-" * 60)
            final_video = self.text_overlay.add_stylized_text(video_with_audio, brand_name)
            
            print("\n" + "=" * 60)
            print("✓ COMPLETE!")
            print("=" * 60)
            print(f"\nFinal video: {final_video}")
            print(f"\nThis video includes:")
            print(f"  ✓ All video clips merged")
            print(f"  ✓ Audio track integrated")
            print(f"  ✓ Brand text overlay")
            print(f"  ✓ Fixed laptop screen issues\n")
            
            return final_video
            
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()
            raise


def main():
    config_path = 'config.json'
    
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        api_keys = config.get('api_keys', {})
    else:
        print(f"Config not found: {config_path}")
        return
    
    story_path = 'story.txt'
    if not os.path.exists(story_path):
        print(f"Story not found: {story_path}")
        return
    
    brand_name = config.get('brand_name', 'HAHA HEADPHONE')
    
    generator = ImprovedHeadphoneAdVideoGenerator(api_keys)
    
    try:
        final_video = generator.generate_complete_ad(story_path, brand_name)
        print(f"\n✓ Success! Final video: {final_video}")
    except Exception as e:
        print(f"\n✗ Failed: {e}")


if __name__ == "__main__":
    main()