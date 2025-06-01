"""
Storage abstraction for file uploads.
This module provides a unified interface for storing files locally or in cloud storage.
"""

"""
Storage Utilities
=================

Provides utilities for managing storage, file uploads, and retrieval.
"""
import logging
import os
import shutil
from abc import ABC, abstractmethod

from flask import current_app, url_for
from werkzeug.utils import secure_filename

# Configure logging
logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def save(self, file_obj, filename, folder=None):
        """
        Save a file to storage.

        Args:
            file_obj: The file object to save
            filename: The filename to use
            folder: The folder to save to (optional)

        Returns:
            tuple: (success, filepath or error_message)
        """
        pass

    @abstractmethod
    def get_url(self, filename, folder=None):
        """
        Get the URL for a file.

        Args:
            filename: The filename to get the URL for
            folder: The folder the file is in (optional)

        Returns:
            str: The URL for the file
        """
        pass

    @abstractmethod
    def delete(self, filename, folder=None):
        """
        Delete a file from storage.

        Args:
            filename: The filename to delete
            folder: The folder the file is in (optional)

        Returns:
            bool: True if the file was deleted, False otherwise
        """
        pass


class LocalStorage(StorageBackend):
    """Local filesystem storage backend."""

    def __init__(self, base_path=None, base_url=None):
        """
        Initialize local storage.

        Args:
            base_path: The base directory for file storage
            base_url: The base URL for file access
        """
        self.base_path = base_path
        self.base_url = base_url

    def _get_path(self, filename, folder=None):
        """
        Get the full path for a file.

        Args:
            filename: The filename
            folder: The folder (optional)

        Returns:
            str: The full path
        """
        if self.base_path is None:
            self.base_path = current_app.config["UPLOAD_FOLDER"]

        if folder:
            return os.path.join(self.base_path, folder, filename)
        else:
            return os.path.join(self.base_path, filename)

    def save(self, file_obj, filename, folder=None):
        """
        Save a file to local storage.

        Args:
            file_obj: The file object to save
            filename: The filename to use
            folder: The folder to save to (optional)

        Returns:
            tuple: (success, filepath or error_message)
        """
        try:
            # Ensure filename is secure
            filename = secure_filename(filename)

            # Get the full path
            filepath = self._get_path(filename, folder)

            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Save the file
            file_obj.save(filepath)

            return True, filepath
        except Exception as e:
            logger.error(f"Error saving file to local storage: {e}")
            return False, str(e)

    def get_url(self, filename, folder=None):
        """
        Get the URL for a file in local storage.

        Args:
            filename: The filename to get the URL for
            folder: The folder the file is in (optional)

        Returns:
            str: The URL for the file
        """
        try:
            if self.base_url is None:
                # Use Flask's url_for to generate the URL
                if folder:
                    return url_for("static", filename=f"{folder}/{filename}")
                else:
                    return url_for("static", filename=filename)
            else:
                # Use the base URL
                if folder:
                    return f"{self.base_url}/{folder}/{filename}"
                else:
                    return f"{self.base_url}/{filename}"
        except Exception as e:
            logger.error(f"Error getting URL for file: {e}")
            return ""

    def delete(self, filename, folder=None):
        """
        Delete a file from local storage.

        Args:
            filename: The filename to delete
            folder: The folder the file is in (optional)

        Returns:
            bool: True if the file was deleted, False otherwise
        """
        try:
            filepath = self._get_path(filename, folder)
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file from local storage: {e}")
            return False


class S3Storage(StorageBackend):
    """Amazon S3 storage backend."""

    def __init__(
        self, bucket_name=None, aws_access_key=None, aws_secret_key=None, region=None
    ):
        """
        Initialize S3 storage.

        Args:
            bucket_name: The S3 bucket name
            aws_access_key: The AWS access key
            aws_secret_key: The AWS secret key
            region: The AWS region
        """
        self.bucket_name = bucket_name or os.environ.get("S3_BUCKET")
        self.aws_access_key = aws_access_key or os.environ.get("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = aws_secret_key or os.environ.get("AWS_SECRET_ACCESS_KEY")
        self.region = region or os.environ.get("AWS_REGION", "us-east-1")

        # Import boto3 only if S3 storage is used
        try:
            import boto3

            self.s3 = boto3.client(
                "s3",
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.region,
            )
        except ImportError:
            logger.warning("boto3 not installed. S3 storage will not work.")
            self.s3 = None
        except Exception as e:
            logger.error(f"Error initializing S3 client: {e}")
            self.s3 = None

    def _get_key(self, filename, folder=None):
        """
        Get the S3 key for a file.

        Args:
            filename: The filename
            folder: The folder (optional)

        Returns:
            str: The S3 key
        """
        if folder:
            return f"{folder}/{filename}"
        else:
            return filename

    def save(self, file_obj, filename, folder=None):
        """
        Save a file to S3 storage.

        Args:
            file_obj: The file object to save
            filename: The filename to use
            folder: The folder to save to (optional)

        Returns:
            tuple: (success, filepath or error_message)
        """
        if self.s3 is None:
            return False, "S3 client not initialized"

        try:
            # Ensure filename is secure
            filename = secure_filename(filename)

            # Get the S3 key
            key = self._get_key(filename, folder)

            # Upload the file
            self.s3.upload_fileobj(file_obj, self.bucket_name, key)

            return True, key
        except Exception as e:
            logger.error(f"Error saving file to S3: {e}")
            return False, str(e)

    def get_url(self, filename, folder=None):
        """
        Get the URL for a file in S3 storage.

        Args:
            filename: The filename to get the URL for
            folder: The folder the file is in (optional)

        Returns:
            str: The URL for the file
        """
        if self.s3 is None:
            return ""

        try:
            key = self._get_key(filename, folder)
            return f"https://{self.bucket_name}.s3.amazonaws.com/{key}"
        except Exception as e:
            logger.error(f"Error getting URL for file: {e}")
            return ""

    def delete(self, filename, folder=None):
        """
        Delete a file from S3 storage.

        Args:
            filename: The filename to delete
            folder: The folder the file is in (optional)

        Returns:
            bool: True if the file was deleted, False otherwise
        """
        if self.s3 is None:
            return False

        try:
            key = self._get_key(filename, folder)
            self.s3.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except Exception as e:
            logger.error(f"Error deleting file from S3: {e}")
            return False


# Factory function to get the appropriate storage backend
def get_storage(storage_type=None):
    """
    Get a storage backend.

    Args:
        storage_type: The type of storage to use ('local' or 's3')

    Returns:
        StorageBackend: A storage backend instance
    """
    if storage_type is None:
        storage_type = os.environ.get("STORAGE_TYPE", "local")

    if storage_type.lower() == "s3":
        return S3Storage()
    else:
        return LocalStorage()


# Default storage instance
storage = get_storage()
