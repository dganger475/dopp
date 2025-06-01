import logging
import os
import shutil
from functools import lru_cache
from pathlib import Path

from PIL import Image


class ImageHandler:
    def __init__(self, static_dir="static/extracted_faces/", min_match_threshold=30.0):
        self.static_dir = Path(static_dir)
        self.min_match_threshold = min_match_threshold
        self.logger = self._setup_logger()
        self._verify_directory()

    def _setup_logger(self):
        logger = logging.getLogger("ImageHandler")
        logger.setLevel(logging.INFO)
        os.makedirs("logs", exist_ok=True)  # Create logs directory if it doesn't exist
        handler = logging.FileHandler("logs/image_errors.log")
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)
        return logger

    def _verify_directory(self):
        if not self.static_dir.exists():
            self.static_dir.mkdir(parents=True)
            self.logger.info(f"Created directory: {self.static_dir}")

    @lru_cache(maxsize=1000)
    def get_image_path(self, image_name):
        """Cache and verify image paths"""
        full_path = self.static_dir / image_name
        if not full_path.exists():
            self.logger.error(f"Missing image: {image_name}")
            return None
        return str(full_path)

    def filter_matches(self, matches):
        """Filter and validate matches"""
        valid_matches = []
        for match in matches:
            if isinstance(match, str):  # Handle string filenames
                filename = match
                confidence = 0
            else:  # Handle dict with filename and confidence
                filename = match.get("filename", "")
                confidence = match.get("confidence", 0)

            image_path = self.get_image_path(filename)
            if image_path and confidence >= self.min_match_threshold:
                if self.verify_image_quality(image_path):
                    valid_matches.append(
                        {
                            "filename": filename,
                            "confidence": round(float(confidence), 1),
                            "path": image_path,
                        }
                    )

        # Sort by confidence in descending order
        return sorted(valid_matches, key=lambda x: x["confidence"], reverse=True)

    def verify_image_quality(self, image_path, min_size=(50, 50)):
        """Check if image meets quality standards"""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                if width < min_size[0] or height < min_size[1]:
                    self.logger.warning(
                        f"Low quality image: {image_path} - Size: {width}x{height}"
                    )
                    return False
                return True
        except Exception as e:
            self.logger.error(f"Error checking image {image_path}: {str(e)}")
            return False
