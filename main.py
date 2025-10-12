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


class HeadphoneAdVideoGenerator:
    
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
        
        self.audio_generator = AudioGenerator(self.project_dir / 'output')
        self.text_overlay = TextOverlay(self.dirs['final'])
    
    def _create_directories(self):
        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        print("Directory structure created\n")
    
    def load_story(self, story_path: str) -> str:
        with open(story_path, 'r', encoding='utf-8') as f:
            story = f.read()
        print(f"Story loaded: {len(story)} characters\n")
        return story
    
    def generate_storyboard_text(self, story: str) -> List[Dict]:
        prompt = f"""Based on the following wireless headphone advertisement story, create a detailed storyboard for a 60-second video.

Requirements:
1. Break the story into 6-8 scenes, each 8-10 seconds
2. Each scene must include:
   - scene_number: Scene number
   - duration: Duration in seconds
   - visual_description: Detailed visual description with character appearance, environment, lighting, product display angle, color tone
   - action: Specific action description for video animation
   - dialogue: Dialogue or voiceover text if any
   - camera_angle: Camera angle
   - audio_type: Type of audio for this scene, must be one of: "cafe", "calm", "product"
     * "cafe": Use for scenes before wearing headphones (noisy cafe ambience)
     * "calm": Use for scenes with headphones on (calm music)
     * "product": Use for final product showcase scenes (upbeat music)

3. Special attention:
   - First scene: Establish character and product style with detailed description, audio_type should be "cafe"
   - Middle scenes with headphones: audio_type should be "calm"
   - Last scene: Product close-up highlighting brand logo, audio_type should be "product"
   - Keep character appearance and clothing consistent across all scenes
   - Ensure logical continuity between scenes

4. Output format: Pure JSON array only

Original story:
{story}

Output JSON storyboard.
"""
        
        print("Step 1/5: Generating storyboard...")
        print("-" * 60)
        
        message = self.claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text
        
        try:
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
            
            print(f"\nStoryboard generated successfully")
            print(f"  Scenes: {len(storyboard)}")
            print(f"  Total duration: {sum(s.get('duration', 8) for s in storyboard)}s")
            print(f"  Saved to: {output_path}")
            print(f"  Readable version: {readable_path}\n")
            
            return storyboard
            
        except json.JSONDecodeError as e:
            print(f"\nJSON parsing error: {e}")
            print(f"Response:\n{response_text[:1000]}\n")
            raise
    
    def generate_images(self, storyboard: List[Dict]) -> List[str]:
        image_paths = []
        reference_image_path = None
        
        print("\nStep 2/5: Generating keyframe images...")
        print("-" * 60)
        
        for i, scene in enumerate(storyboard):
            scene_num = scene.get('scene_number', i + 1)
            visual_desc = scene.get('visual_description', '')
            
            if i == 0:
                enhanced_prompt = f"High quality commercial photography, cinematic lighting, 4K resolution. {visual_desc}"
                print(f"Scene {scene_num}: First frame - establishing style")
            elif i == len(storyboard) - 1:
                enhanced_prompt = f"Professional product photography, studio lighting, clean background, 4K. {visual_desc}"
                print(f"Scene {scene_num}: Last frame - product closeup")
            else:
                enhanced_prompt = f"High quality commercial photography, consistent style, cinematic lighting. Same person as reference image. {visual_desc}"
                print(f"Scene {scene_num}: Middle scene (using reference)")
            
            print(f"  Prompt: {enhanced_prompt[:80]}...")
            
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
                        print(f"  Using as reference for consistency")
            
            print(f"  Image saved: {os.path.basename(image_path)}\n")
            time.sleep(3)
            
        print(f"All keyframe images generated: {len(image_paths)} images\n")
        return image_paths
    
    def _call_seedream_api(self, prompt: str, scene_num: int, reference_image: str = None) -> str:
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
                print(f"  Using reference image for consistency")
            except Exception as e:
                print(f"  Warning: Could not load reference image: {e}")
        
        try:
            print(f"  Calling Seedream API...")
            response = requests.post(self.images_api, headers=headers, json=payload, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                
                if 'data' in result and len(result['data']) > 0:
                    image_url = result['data'][0].get('url')
                    
                    if image_url:
                        print(f"  Downloading image...")
                        image_data = requests.get(image_url, timeout=60).content
                        image_path = self.dirs['images'] / f'scene_{scene_num:02d}.png'
                        
                        with open(image_path, 'wb') as f:
                            f.write(image_data)
                        
                        print(f"  Image downloaded successfully")
                        return str(image_path)
            
            raise Exception(f"API returned {response.status_code}: {response.text[:200]}")
            
        except Exception as e:
            print(f"  Image generation failed: {e}")
            
            image_path = self.dirs['images'] / f'scene_{scene_num:02d}.png'
            prompt_path = self.dirs['images'] / f'scene_{scene_num:02d}_prompt.txt'
            
            with open(prompt_path, 'w', encoding='utf-8') as f:
                f.write(f"Scene {scene_num} prompt:\n\n{prompt}\n\n")
                f.write(f"Model: Seedream 4.0\n")
                f.write(f"Size: 1920x1080\n")
                f.write(f"\nError: {str(e)}\n")
            
            with open(image_path, 'w') as f:
                f.write(f"Placeholder for scene {scene_num}")
            
            return str(image_path)
    
    def generate_video_clips(self, image_paths: List[str], storyboard: List[Dict]) -> List[str]:
        video_paths = []
        
        print("\nStep 3/5: Generating video clips...")
        print("-" * 60)
        
        for i, (image_path, scene) in enumerate(zip(image_paths, storyboard)):
            scene_num = scene.get('scene_number', i + 1)
            duration = scene.get('duration', 8)
            action = scene.get('action', '')
            
            print(f"Scene {scene_num}: Generating {duration}s video")
            print(f"  Input image: {os.path.basename(image_path)}")
            print(f"  Motion prompt: {action[:60]}...")
            
            video_path = self._call_seedance_api(
                image_path=image_path,
                motion_prompt=action,
                duration=duration,
                scene_num=scene_num
            )
            
            video_paths.append(video_path)
            print(f"  Video saved: {os.path.basename(video_path)}\n")
            time.sleep(2)
        
        print(f"All video clips generated: {len(video_paths)} clips\n")
        return video_paths
    
    def _call_seedance_api(self, image_path: str, motion_prompt: str, duration: int, scene_num: int) -> str:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        if len(image_data) < 1000:
            print(f"  Skipping placeholder image")
            video_path = self.dirs['videos'] / f'clip_{scene_num:02d}.mp4'
            with open(video_path, 'w') as f:
                f.write(f"Placeholder for video clip {scene_num}")
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
                {
                    "type": "image_url",
                    "image_url": {"url": image_data_url},
                    "role": "first_frame"
                },
                {
                    "type": "text",
                    "text": f"{motion_prompt} --duration {min(duration, 10)} --ratio 16:9 --resolution 720p --fps 24 --watermark false"
                }
            ]
        }
        
        try:
            print(f"  Creating video task...")
            response = requests.post(create_url, headers=headers, json=payload, timeout=60)
            
            if response.status_code != 200:
                raise Exception(f"Create task failed: {response.status_code} - {response.text[:200]}")
            
            result = response.json()
            task_id = result.get('id')
            
            if not task_id:
                raise Exception("No task ID returned")
            
            print(f"  Task created: {task_id}")
            print(f"  Waiting for video generation...")
            
            query_url = f"https://ark.ap-southeast.bytepluses.com/api/v3/contents/generations/tasks/{task_id}"
            
            max_attempts = 60
            for attempt in range(max_attempts):
                time.sleep(10)
                
                status_response = requests.get(query_url, headers=headers, timeout=30)
                
                if status_response.status_code != 200:
                    print(f"  Status query failed: {status_response.status_code}")
                    continue
                
                status_result = status_response.json()
                task_status = status_result.get('status')
                
                print(f"  Status: {task_status} (attempt {attempt + 1}/{max_attempts})")
                
                if task_status == 'succeeded':
                    video_url = status_result.get('content', {}).get('video_url')
                    
                    if video_url:
                        print(f"  Downloading video...")
                        video_data = requests.get(video_url, timeout=120).content
                        video_path = self.dirs['videos'] / f'clip_{scene_num:02d}.mp4'
                        
                        with open(video_path, 'wb') as f:
                            f.write(video_data)
                        
                        print(f"  Video downloaded successfully")
                        return str(video_path)
                    else:
                        raise Exception("No video URL in successful response")
                
                elif task_status == 'failed':
                    error_msg = status_result.get('error', {}).get('message', 'Unknown error')
                    raise Exception(f"Task failed: {error_msg}")
                
                elif task_status in ['queued', 'running']:
                    continue
                
                else:
                    print(f"  Unknown status: {task_status}")
            
            raise Exception("Task timeout after 10 minutes")
            
        except Exception as e:
            print(f"  Video generation failed: {e}")
            
            video_path = self.dirs['videos'] / f'clip_{scene_num:02d}.mp4'
            motion_path = self.dirs['videos'] / f'clip_{scene_num:02d}_motion.txt'
            
            with open(motion_path, 'w', encoding='utf-8') as f:
                f.write(f"Scene {scene_num} video parameters:\n\n")
                f.write(f"Input image: {image_path}\n")
                f.write(f"Duration: {duration}s\n")
                f.write(f"Motion prompt: {motion_prompt}\n\n")
                f.write(f"Model: Seedance Lite I2V\n")
                f.write(f"\nError: {str(e)}\n")
            
            with open(video_path, 'w') as f:
                f.write(f"Placeholder for video clip {scene_num}")
            
            return str(video_path)
    
    def merge_videos(self, video_paths: List[str]) -> str:
        print("\nStep 4/5: Merging video clips...")
        print("-" * 60)
        
        list_file = self.dirs['videos'] / 'concat_list.txt'
        with open(list_file, 'w', encoding='utf-8') as f:
            for video_path in video_paths:
                abs_path = os.path.abspath(video_path).replace('\\', '/')
                f.write(f"file '{abs_path}'\n")
        
        output_path = self.dirs['final'] / 'merged_video.mp4'
        
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(list_file),
            '-c', 'copy',
            str(output_path)
        ]
        
        print(f"Executing FFmpeg...")
        try:
            result = subprocess.run(cmd, capture_output=True, shell=True, check=False)
            
            if result.returncode == 0:
                print(f"Videos merged successfully")
            else:
                try:
                    error_msg = result.stderr.decode('gbk')
                except:
                    error_msg = result.stderr.decode('utf-8', errors='ignore')
                print(f"FFmpeg error: {error_msg[:500]}")
        except FileNotFoundError:
            print("FFmpeg not found")
            raise
        
        return str(output_path)
    
    def add_audio_to_video(self, video_path: str, audio_path: str) -> str:
        print("\nStep 5/5: Adding audio and text...")
        print("-" * 60)
        
        output_path = str(Path(video_path).parent / 'video_with_audio.mp4')
        
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-shortest',
            output_path
        ]
        
        print(f"Merging video with audio...")
        try:
            result = subprocess.run(cmd, capture_output=True, shell=True, check=False)
            
            if result.returncode == 0:
                print(f"Audio added successfully")
            else:
                try:
                    error_msg = result.stderr.decode('gbk')
                except:
                    error_msg = result.stderr.decode('utf-8', errors='ignore')
                print(f"Audio addition warning: {error_msg[:200]}")
        except FileNotFoundError:
            print("FFmpeg not found")
            raise
        
        return output_path
    
    def generate_complete_ad(self, story_path: str, brand_name: str = "HAHA HEADPHONE"):
        print("\n" + "=" * 60)
        print("Wireless Headphone Ad Video Generation System")
        print("=" * 60 + "\n")
        
        try:
            story = self.load_story(story_path)
            storyboard = self.generate_storyboard_text(story)
            
            image_paths = self.generate_images(storyboard)
            
            video_paths = self.generate_video_clips(image_paths, storyboard)
            
            merged_video = self.merge_videos(video_paths)
            
            print("\nGenerating audio timeline...")
            print("-" * 60)
            audio_scenes = []
            for scene in storyboard:
                audio_scenes.append({
                    'type': scene.get('audio_type', 'calm'),
                    'duration': scene.get('duration', 8)
                })
            
            audio_path = self.audio_generator.create_audio_timeline(audio_scenes)
            audio_path = self.audio_generator.add_fade_effects(audio_path)
            
            video_with_audio = self.add_audio_to_video(merged_video, audio_path)
            
            print("\nAdding brand text overlay...")
            print("-" * 60)
            final_video = self.text_overlay.add_stylized_text(
                video_with_audio,
                brand_name=brand_name
            )
            
            print("\n" + "=" * 60)
            print("Process completed successfully")
            print("=" * 60)
            print(f"\nOutput locations:")
            print(f"  Storyboard: {self.dirs['storyboard']}")
            print(f"  Images: {self.dirs['images']}")
            print(f"  Video clips: {self.dirs['videos']}")
            print(f"  Audio: {self.audio_generator.output_dir}")
            print(f"  Final video: {final_video}\n")
            
            return final_video
            
        except Exception as e:
            print(f"\nError occurred: {e}")
            import traceback
            traceback.print_exc()
            raise


def main():
    config_path = 'config.json'
    
    if os.path.exists(config_path):
        print(f"Config file found: {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        api_keys = config.get('api_keys', {})
    else:
        print(f"Config file not found: {config_path}")
        return
    
    story_path = 'story.txt'
    if not os.path.exists(story_path):
        print(f"\nStory file not found: {story_path}")
        return
    
    print(f"Story file found: {story_path}")
    
    brand_name = config.get('brand_name', 'HAHA HEADPHONE')
    
    print("\n" + "=" * 60)
    print("Starting video generation process...")
    print(f"Brand: {brand_name}")
    print("=" * 60)
    
    generator = HeadphoneAdVideoGenerator(api_keys)
    
    try:
        final_video = generator.generate_complete_ad(
            story_path=story_path,
            brand_name=brand_name
        )
        print(f"\nSuccess! Final video: {final_video}")
    except Exception as e:
        print(f"\nGeneration failed: {e}")


if __name__ == "__main__":
    main()