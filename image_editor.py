import os
import json
import time
import requests
import base64
from pathlib import Path
from typing import List, Dict, Optional


class ImageEditor:
    """Use Seededit model to edit images for consistency"""
    
    def __init__(self, api_key: str, project_dir: Path):
        self.api_key = api_key
        self.project_dir = project_dir
        self.edit_api = "https://ark.ap-southeast.bytepluses.com/api/v3/images/generations"
        
    def analyze_image_consistency(self, image_paths: List[str], storyboard: List[Dict]) -> List[Dict]:
        """Analyze image consistency issues and generate edit instructions"""
        print("\nAnalyzing image consistency...")
        print("-" * 60)
        
        consistency_issues = []
        
        for i, (image_path, scene) in enumerate(zip(image_paths, storyboard)):
            scene_num = scene.get('scene_number', i + 1)
            
            issues = {
                'scene_num': scene_num,
                'image_path': image_path,
                'edits_needed': []
            }
            
            # Check first scene (establish baseline)
            if i == 0:
                issues['is_reference'] = True
                issues['edits_needed'].append({
                    'type': 'enhance',
                    'description': 'Ensure clear character appearance, clothing, and environment details as reference'
                })
            else:
                issues['is_reference'] = False
                
                # Check middle scenes for consistency
                visual_desc = scene.get('visual_description', '').lower()
                
                # Check headphone usage
                if 'wearing headphones' in visual_desc or 'with headphones' in visual_desc:
                    issues['edits_needed'].append({
                        'type': 'remove_object',
                        'description': 'Remove extra headphones from table or other locations, keep only worn headphones'
                    })
                
                # Check background consistency
                if i > 0:
                    issues['edits_needed'].append({
                        'type': 'match_style',
                        'description': 'Match background style, lighting, and color tone of first frame'
                    })
                
                # Check character consistency
                issues['edits_needed'].append({
                    'type': 'match_character',
                    'description': 'Ensure character appearance and clothing match reference image'
                })
            
            # Last scene (product closeup)
            if i == len(image_paths) - 1:
                issues['edits_needed'].append({
                    'type': 'product_focus',
                    'description': 'Clear product closeup, highlight brand logo, professional lighting'
                })
            
            consistency_issues.append(issues)
            
            print(f"Scene {scene_num}: Found {len(issues['edits_needed'])} items to edit")
        
        return consistency_issues
    
    def edit_image_for_consistency(self, image_path: str, edit_instruction: str, 
                                   reference_image: Optional[str] = None,
                                   scene_num: int = 1) -> str:
        """Use Seededit to edit image for consistency"""
        
        print(f"\nEditing image for scene {scene_num}...")
        print(f"  Edit instruction: {edit_instruction}")
        
        # Read original image
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Check if placeholder
        if len(image_data) < 1000:
            print(f"  Skipping placeholder image")
            return image_path
        
        # Prepare API request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Encode original image
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        image_data_url = f"data:image/png;base64,{image_base64}"
        
        payload = {
            "model": "seededit-1-0-250828",
            "prompt": edit_instruction,
            "image": image_data_url,
            "size": "1920x1080",
            "response_format": "url",
            "watermark": False
        }
        
        # Add reference image if available
        if reference_image and os.path.exists(reference_image):
            try:
                with open(reference_image, 'rb') as f:
                    ref_data = f.read()
                ref_base64 = base64.b64encode(ref_data).decode('utf-8')
                payload["reference_image"] = f"data:image/png;base64,{ref_base64}"
                print(f"  Using reference image for style consistency")
            except Exception as e:
                print(f"  Warning: Could not load reference image: {e}")
        
        try:
            print(f"  Calling Seededit API...")
            response = requests.post(self.edit_api, headers=headers, json=payload, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                
                if 'data' in result and len(result['data']) > 0:
                    edited_image_url = result['data'][0].get('url')
                    
                    if edited_image_url:
                        print(f"  Downloading edited image...")
                        edited_image_data = requests.get(edited_image_url, timeout=60).content
                        
                        # Save edited image (overwrite original)
                        edited_path = image_path.replace('.png', '_edited.png')
                        with open(edited_path, 'wb') as f:
                            f.write(edited_image_data)
                        
                        print(f"  Image editing complete")
                        return edited_path
            
            print(f"  API returned error: {response.status_code}")
            return image_path
            
        except Exception as e:
            print(f"  Image editing failed: {e}")
            return image_path
    
    def process_all_images(self, image_paths: List[str], storyboard: List[Dict]) -> List[str]:
        """Process all images for consistency"""
        print("\n=== Starting Image Consistency Processing ===\n")
        
        # Analyze consistency issues
        consistency_issues = self.analyze_image_consistency(image_paths, storyboard)
        
        # Edit images
        edited_image_paths = []
        reference_image = None
        
        for i, issue in enumerate(consistency_issues):
            image_path = issue['image_path']
            scene_num = issue['scene_num']
            
            # First image as reference
            if issue.get('is_reference', False):
                print(f"\nScene {scene_num}: Set as reference image")
                reference_image = image_path
                edited_image_paths.append(image_path)
                continue
            
            # If edits needed
            if issue['edits_needed']:
                # Combine all edit instructions
                edit_instructions = []
                for edit in issue['edits_needed']:
                    edit_instructions.append(edit['description'])
                
                combined_instruction = (
                    f"Maintain consistent style, lighting, and color tone with reference image. "
                    f"{' '.join(edit_instructions)} "
                    f"Ensure character appearance and clothing exactly match reference image."
                )
                
                # Edit image
                edited_path = self.edit_image_for_consistency(
                    image_path=image_path,
                    edit_instruction=combined_instruction,
                    reference_image=reference_image,
                    scene_num=scene_num
                )
                
                edited_image_paths.append(edited_path)
                time.sleep(3)  # API rate limiting
            else:
                edited_image_paths.append(image_path)
        
        print(f"\nImage consistency processing complete: {len(edited_image_paths)} images")
        return edited_image_paths