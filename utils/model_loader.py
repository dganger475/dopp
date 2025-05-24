"""
Model loader utility for downloading and managing large model files.

This module handles downloading large model files from external storage
when they're not available locally. It's designed to work with Docker volumes
to keep the container image size small.
"""

import hashlib
import logging
import os
from pathlib import Path

import requests
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Model definitions with download URLs and checksums
MODEL_DEFINITIONS = {
    "face_quality_classifier.h5": {
        "url": os.environ.get("FACE_QUALITY_MODEL_URL", ""),
        "md5": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",  # Replace with actual MD5
        "required": False,
    },
    "GFPGANv1.4.pth": {
        "url": os.environ.get("GFPGAN_MODEL_URL", ""),
        "md5": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",  # Replace with actual MD5
        "required": False,
    },
    "RealESRGAN_x4plus_anime_6B.pth": {
        "url": os.environ.get("ESRGAN_MODEL_URL", ""),
        "md5": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",  # Replace with actual MD5
        "required": False,
    },
    "ESPCN_x4.pb": {
        "url": os.environ.get("ESPCN_MODEL_URL", ""),
        "md5": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",  # Replace with actual MD5
        "required": False,
    },
}


def get_file_md5(file_path):
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def download_file(url, destination):
    """Download a file with progress bar."""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get("content-length", 0))

    # Ensure directory exists
    os.makedirs(os.path.dirname(destination), exist_ok=True)

    with open(destination, "wb") as f:
        with tqdm(
            total=total_size,
            unit="B",
            unit_scale=True,
            desc=os.path.basename(destination),
        ) as pbar:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))

    return destination


def ensure_model_files():
    """Ensure all required model files are available."""
    app_root = Path(os.environ.get("APP_ROOT", os.getcwd()))
    models_dir = os.environ.get("MODELS_DIR", app_root)

    missing_required = []

    for model_name, model_info in MODEL_DEFINITIONS.items():
        model_path = os.path.join(models_dir, model_name)

        # Check if model exists and has correct MD5
        if not os.path.exists(model_path):
            logger.info(f"Model file {model_name} not found locally.")

            # If URL is provided, try to download
            if model_info["url"]:
                try:
                    logger.info(f"Downloading {model_name} from {model_info['url']}...")
                    download_file(model_info["url"], model_path)

                    # Verify MD5 if provided
                    if model_info["md5"]:
                        file_md5 = get_file_md5(model_path)
                        if file_md5 != model_info["md5"]:
                            logger.warning(
                                f"MD5 mismatch for {model_name}. Expected: {model_info['md5']}, Got: {file_md5}"
                            )

                    logger.info(f"Successfully downloaded {model_name}")
                except Exception as e:
                    logger.error(f"Failed to download {model_name}: {e}")
                    if model_info["required"]:
                        missing_required.append(model_name)
            elif model_info["required"]:
                missing_required.append(model_name)

    if missing_required:
        logger.error(f"Missing required model files: {', '.join(missing_required)}")
        return False

    return True


if __name__ == "__main__":
    # When run directly, attempt to download all models
    ensure_model_files()
