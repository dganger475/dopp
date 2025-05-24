import os
from datetime import datetime

import cv2
import face_recognition
import fitz
import torch
from basicsr.archs.rrdbnet_arch import RRDBNet
from basicsr.utils import imwrite
from basicsr.utils.download_util import load_file_from_url
from basicsr.utils.registry import ARCH_REGISTRY
from PIL import Image
from torch.hub import download_url_to_file, get_dir

import numpy as np
from gfpgan import GFPGANer


def load_models():
    """Load all enhancement models."""
    models = {}
    
    # Load GFPGAN
    print("Loading GFPGAN model...")
    gfpgan_path = 'GFPGANv1.4.pth'
    if not os.path.exists(gfpgan_path):
        print("Downloading GFPGAN model...")
        import wget
        wget.download('https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth')
    
    models['gfpgan'] = GFPGANer(
        model_path=gfpgan_path,
        upscale=1,
        arch='clean',
        channel_multiplier=2,
        bg_upsampler=None
    )

    # Load Real-ESRGAN
    print("Loading Real-ESRGAN model...")
    esrgan_path = 'RealESRGAN_x4plus_anime_6B.pth'
    if not os.path.exists(esrgan_path):
        print("Downloading Real-ESRGAN model...")
        url = 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth'
        download_url_to_file(url, esrgan_path, progress=True)
    
    models['esrgan'] = RRDBNet(
        num_in_ch=3,
        num_out_ch=3,
        num_feat=64,
        num_block=6,
        num_grow_ch=32,
        scale=4
    )
    models['esrgan'].load_state_dict(torch.load(esrgan_path)['params_ema'])
    models['esrgan'].eval()

    return models

def enhance_face_variant(image, settings, models):
    """Apply different enhancement settings to face images."""
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Standard 300x300 resize
    aspect = image.width / image.height
    if aspect > 1:
        new_width = 300
        new_height = int(300 / aspect)
    else:
        new_height = 300
        new_width = int(300 * aspect)
    image = image.resize((new_width, new_height), Image.LANCZOS)
    
    # Create centered image
    background = Image.new('RGB', (300, 300), (0, 0, 0))
    offset_x = (300 - new_width) // 2
    offset_y = (300 - new_height) // 2
    background.paste(image, (offset_x, offset_y))
    image = background
    
    try:
        if settings['name'] == 'original':
            return image
            
        elif settings['name'] == 'gfpgan':
            cv2_img = np.array(image)
            cv2_img = cv2_img[:, :, ::-1].copy()
            _, _, output = models['gfpgan'].enhance(
                cv2_img,
                has_aligned=False,
                only_center_face=True,
                paste_back=True
            )
            return Image.fromarray(cv2.cvtColor(output, cv2.COLOR_BGR2RGB))
            
        elif settings['name'] == 'esrgan':
            # Prepare input for Real-ESRGAN
            input_tensor = torch.from_numpy(np.array(image)).float().permute(2, 0, 1).unsqueeze(0) / 255.0
            with torch.no_grad():
                output = models['esrgan'](input_tensor)
            output = output.squeeze(0).permute(1, 2, 0).clamp(0, 1).numpy()
            return Image.fromarray((output * 255).astype(np.uint8))
            
    except Exception as e:
        print(f"Error during {settings['name']} enhancement: {e}")
        return image
    
    return image

def extract_test_faces(pdf_path, page_range=(0,5)):
    """Extract faces with different enhancement settings."""
    # Load all models
    models = load_models()
    
    settings_list = [
        {'name': 'original'},
        {'name': 'gfpgan'},
        {'name': 'esrgan'}
    ]

    # Create timestamped output directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = f"enhancement_tests_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    print(f"Saving results to: {output_dir}")
    
    try:
        doc = fitz.open(pdf_path)
        start_page, end_page = page_range
        end_page = min(end_page, len(doc))
        
        for page_num in range(start_page, end_page):
            print(f"Processing page {page_num + 1}")
            page = doc[page_num]
            
            # Get high-resolution pixmap
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Convert to numpy array for face detection
            np_img = np.array(img)
            face_locations = face_recognition.face_locations(np_img)
            
            print(f"Found {len(face_locations)} faces on page {page_num + 1}")
            
            for face_idx, (top, right, bottom, left) in enumerate(face_locations):
                # Extract face with padding
                height = bottom - top
                width = right - left
                padding = int(max(height, width) * 0.4)
                
                top = max(0, top - padding)
                bottom = min(img.height, bottom + padding)
                left = max(0, left - padding)
                right = min(img.width, right + padding)
                
                face_img = img.crop((left, top, right, bottom))
                
                # Apply different enhancement settings
                for settings in settings_list:
                    enhanced_face = enhance_face_variant(face_img, settings, models)
                    
                    # Save with settings name in filename
                    output_filename = f"page_{page_num+1}_face_{face_idx+1}_{settings['name']}.jpg"
                    output_path = os.path.join(output_dir, output_filename)
                    enhanced_face.save(output_path, 'JPEG', quality=100)
                    
                print(f"Processed face {face_idx + 1} with all enhancement settings")
                
    except Exception as e:
        print(f"Error processing PDF: {e}")
    finally:
        if 'doc' in locals():
            doc.close()

if __name__ == "__main__":
    pdf_path = input("Enter the path to your yearbook PDF: ")
    start_page = int(input("Enter starting page number (0-based): "))
    end_page = int(input("Enter ending page number: "))
    
    extract_test_faces(pdf_path, (start_page, end_page)) 