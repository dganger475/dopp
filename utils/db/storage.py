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
import b2sdk.v2 as b2
from rate_limit import rate_limit

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


class B2Storage(StorageBackend):
    """Backblaze B2 storage backend."""

    def __init__(self, application_key_id=None, application_key=None, bucket_name=None):
        """
        Initialize B2 storage.

        Args:
            application_key_id: B2 application key ID
            application_key: B2 application key
            bucket_name: B2 bucket name
        """
        self.application_key_id = application_key_id or os.getenv('B2_APPLICATION_KEY_ID')
        self.application_key = application_key or os.getenv('B2_APPLICATION_KEY')
        self.bucket_name = bucket_name or os.getenv('B2_BUCKET_NAME')
        
        if not all([self.application_key_id, self.application_key, self.bucket_name]):
            raise ValueError("B2 credentials not properly configured")
        
        # Initialize B2 client
        self.info = b2.InMemoryAccountInfo()
        self.b2_api = b2.B2Api(self.info)
        self.b2_api.authorize_account("production", self.application_key_id, self.application_key)
        self.bucket = self.b2_api.get_bucket_by_name(self.bucket_name)

    def _get_key(self, filename, folder=None):
        """Get the B2 key for a file."""
        if folder:
            return f"{folder}/{filename}"
        return filename

    @rate_limit(max_retries=3, delay=2)
    def save(self, file_obj, filename, folder=None):
        """
        Save a file to B2 storage with rate limiting.

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

            # Get the B2 key
            key = self._get_key(filename, folder)

            # Upload the file with retry logic
            self.bucket.upload_bytes(
                file_obj.read(),
                key,
                content_type=file_obj.content_type
            )

            return True, key
        except b2.exception.DownloadCapExceeded as e:
            logger.error(f"B2 download cap exceeded: {e}")
            raise  # Let the decorator handle the retry
        except Exception as e:
            logger.error(f"Error saving file to B2: {e}")
            return False, str(e)

    @rate_limit(max_retries=3, delay=2)
    def get_url(self, filename, folder=None):
        """
        Get the URL for a file in B2 storage with rate limiting.

        Args:
            filename: The filename to get the URL for
            folder: The folder the file is in (optional)

        Returns:
            str: The URL for the file
        """
        try:
            key = self._get_key(filename, folder)
            # Get a download URL that's valid for 1 hour
            download_url = self.bucket.get_download_url(key)
            return download_url
        except b2.exception.DownloadCapExceeded as e:
            logger.error(f"B2 download cap exceeded: {e}")
            raise  # Let the decorator handle the retry
        except Exception as e:
            logger.error(f"Error getting URL for file: {e}")
            return ""

    @rate_limit(max_retries=3, delay=2)
    def delete(self, filename, folder=None):
        """
        Delete a file from B2 storage with rate limiting.

        Args:
            filename: The filename to delete
            folder: The folder the file is in (optional)

        Returns:
            bool: True if the file was deleted, False otherwise
        """
        try:
            key = self._get_key(filename, folder)
            file_version = self.bucket.get_file_info_by_name(key)
            if file_version:
                self.bucket.delete_file_version(file_version.id_, file_version.file_name)
                return True
            return False
        except b2.exception.DownloadCapExceeded as e:
            logger.error(f"B2 download cap exceeded: {e}")
            raise  # Let the decorator handle the retry
        except Exception as e:
            logger.error(f"Error deleting file from B2: {e}")
            return False


# Factory function to get the appropriate storage backend
def get_storage(storage_type=None):
    """
    Get a storage backend.

    Args:
        storage_type: The type of storage to use ('local' or 's3' or 'b2')

    Returns:
        StorageBackend: A storage backend instance
    """
    if storage_type is None:
        storage_type = os.environ.get("STORAGE_TYPE", "local")

    if storage_type.lower() == "s3":
        return S3Storage()
    elif storage_type.lower() == "b2":
        return B2Storage()
    else:
        return LocalStorage()


# Default storage instance
storage = get_storage()
