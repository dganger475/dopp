"""
FAISS index manager for efficient similarity search.
This module provides a lazy-loading singleton for the FAISS index.
"""

import logging
import os
import pickle
import threading

import faiss
from flask import current_app

import numpy as np

# Configure logging
logger = logging.getLogger(__name__)


class FaissIndexManager:
    """
    Singleton class for managing the FAISS index.
    Provides lazy loading and thread-safe access to the index.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Ensure singleton instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(FaissIndexManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        """Initialize the FAISS index manager."""
        if not self._initialized:
            self._index = None
            self._filenames = None
            self._initialized = True
            self._loaded = False
            self._loading = False

    def _get_index_path(self):
        """Get the path to the FAISS index file."""
        try:
            return current_app.config["INDEX_PATH"]
        except RuntimeError:
            # Not in Flask context
            return os.environ.get("INDEX_PATH", "faces.index")

    def _get_map_path(self):
        """Get the path to the filenames mapping file."""
        try:
            return current_app.config["MAP_PATH"]
        except RuntimeError:
            # Not in Flask context
            return os.environ.get("MAP_PATH", "faces_filenames.pkl")

    def is_loaded(self):
        """Check if the index is loaded."""
        return self._loaded

    def is_loading(self):
        """Check if the index is currently being loaded."""
        return self._loading

    def load_index(self, force=False):
        """
        Load the FAISS index and filenames mapping.

        Args:
            force: Force reloading even if already loaded

        Returns:
            bool: True if loaded successfully, False otherwise
        """
        if self._loaded and not force:
            return True

        if self._loading:
            logger.info("Index is already being loaded")
            return False

        with self._lock:
            self._loading = True
            try:
                index_path = self._get_index_path()
                map_path = self._get_map_path()

                logger.info(f"Loading FAISS index from {index_path}")
                if not os.path.exists(index_path):
                    logger.error(f"FAISS index file not found: {index_path}")
                    self._loading = False
                    return False

                if not os.path.exists(map_path):
                    logger.error(f"Filenames mapping file not found: {map_path}")
                    self._loading = False
                    return False

                # Load the FAISS index
                self._index = faiss.read_index(index_path)

                # Load the filenames mapping
                with open(map_path, "rb") as f:
                    self._filenames = pickle.load(f)

                logger.info(
                    f"FAISS index loaded successfully with {self._index.ntotal} vectors"
                )
                self._loaded = True
                self._loading = False
                return True
            except Exception as e:
                logger.error(f"Error loading FAISS index: {e}")
                self._loaded = False
                self._loading = False
                return False

    def search(self, query_vector, top_k=20):
        """
        Search the FAISS index for similar vectors.

        Args:
            query_vector: The query vector to search for
            top_k: The number of results to return

        Returns:
            tuple: (distances, indices, filenames)
        """
        if not self._loaded:
            if not self.load_index():
                return [], [], []

        with self._lock:
            try:
                # Ensure query vector is in the right shape
                if isinstance(query_vector, list):
                    query_vector = np.array(query_vector, dtype=np.float32)

                if len(query_vector.shape) == 1:
                    query_vector = query_vector.reshape(1, -1)

                # Ensure the vector is float32
                query_vector = query_vector.astype(np.float32)

                # Search the index
                distances, indices = self._index.search(query_vector, top_k)

                # Get the filenames for the results
                result_filenames = []
                for idx in indices[0]:
                    if idx >= 0 and idx < len(self._filenames):
                        result_filenames.append(self._filenames[idx])
                    else:
                        result_filenames.append(None)

                return distances[0], indices[0], result_filenames
            except Exception as e:
                logger.error(f"Error searching FAISS index: {e}")
                return [], [], []

    def rebuild_index(self, face_encodings=None, filenames=None, dimension=128):
        """
        Rebuild the FAISS index from scratch.

        Args:
            face_encodings: The face encodings to index
            filenames: The filenames corresponding to the encodings
            dimension: The dimension of the face encodings

        Returns:
            bool: True if rebuilt successfully, False otherwise
        """
        import sqlite3

        with self._lock:
            try:
                # If no face encodings provided, load from database
                if face_encodings is None or filenames is None:
                    logger.info("Loading face encodings from database")

                    # Determine database path with proper fallbacks
                    logger.info("Determining database path with proper fallbacks")

                    # First try environment variable (set by app.py)
                    db_path = os.environ.get("DB_PATH")
                    if db_path and os.path.exists(db_path):
                        logger.info(
                            f"Using database path from environment variable: {db_path}"
                        )
                    else:
                        # Try explicit hardcoded path as first fallback
                        explicit_path = (
                            r"C:\Users\1439\Documents\DopplegangerApp\faces.db"
                        )
                        if os.path.exists(explicit_path):
                            logger.info(
                                f"Using explicit hardcoded database path: {explicit_path}"
                            )
                            db_path = explicit_path
                        else:
                            # Try to get from Flask app config as second fallback
                            try:
                                app_config_path = current_app.config.get("DB_PATH")
                                if app_config_path and os.path.exists(app_config_path):
                                    logger.info(
                                        f"Using database path from app config: {app_config_path}"
                                    )
                                    db_path = app_config_path
                                else:
                                    # Last resort: use default path
                                    default_path = "faces.db"
                                    if os.path.exists(default_path):
                                        logger.warning(
                                            f"Using default database path: {default_path}"
                                        )
                                        db_path = default_path
                                    else:
                                        logger.error(
                                            "Could not find a valid database file"
                                        )
                                        return False
                            except RuntimeError:
                                # Not in Flask context - try with a relative path
                                relative_path = "faces.db"
                                if os.path.exists(relative_path):
                                    logger.warning(
                                        f"Using relative database path: {relative_path}"
                                    )
                                    db_path = relative_path
                                else:
                                    logger.error("Could not find a valid database file")
                                    return False

                    # Ensure we have an absolute path
                    if not db_path:
                        logger.error("No valid database path could be determined")
                        return False

                    if not os.path.isabs(db_path):
                        db_path = os.path.abspath(db_path)

                    logger.info(f"Final absolute database path: {db_path}")

                    # Double-check that the file exists and is accessible
                    if not os.path.exists(db_path):
                        logger.error(f"Final database path does not exist: {db_path}")
                        return False

                    if not os.access(db_path, os.R_OK):
                        logger.error(f"Database file is not readable: {db_path}")
                        return False

                    # Verify file size is reasonable
                    try:
                        file_size = os.path.getsize(db_path)
                        if file_size < 1000:  # Less than 1KB
                            logger.warning(
                                f"Database file is suspiciously small: {file_size} bytes"
                            )
                        logger.info(f"Database file size: {file_size} bytes")
                    except Exception as e:
                        logger.error(f"Error checking database file size: {e}")

                    # Ensure the database file exists
                    if not os.path.exists(db_path):
                        logger.error(f"Database file not found: {db_path}")
                        # Print working directory for debugging
                        logger.error(f"Current working directory: {os.getcwd()}")
                        # List directories in parent folder
                        try:
                            parent_dir = os.path.dirname(db_path)
                            if os.path.exists(parent_dir):
                                dir_contents = os.listdir(parent_dir)
                                logger.error(
                                    f"Contents of {parent_dir}: {dir_contents}"
                                )
                        except Exception as e:
                            logger.error(f"Error listing parent directory: {e}")
                        return False

                    # Log file size and permissions for debugging
                    try:
                        file_size = os.path.getsize(db_path)
                        logger.info(f"Database file size: {file_size} bytes")

                        # Check file permissions
                        if os.access(db_path, os.R_OK):
                            logger.info(f"Database file is readable")
                        else:
                            logger.error(f"Database file is not readable")
                            return False
                    except Exception as e:
                        logger.error(f"Error checking file details: {e}")

                    # Connect directly to the database to avoid any configuration issues
                    conn = None
                    try:
                        # Additional file access verification
                        logger.info(
                            f"Verifying database file before connection: {db_path}"
                        )

                        # Test opening the file directly first to verify access
                        try:
                            with open(db_path, "rb") as test_file:
                                # Read first 100 bytes to verify it's a valid file
                                header = test_file.read(100)
                                logger.info(
                                    f"Successfully opened database file, header length: {len(header)}"
                                )

                                # Check if it looks like a SQLite file (should start with "SQLite format")
                                if not header.startswith(b"SQLite format"):
                                    logger.warning(
                                        f"File does not appear to be a valid SQLite database (header doesn't start with 'SQLite format')"
                                    )
                        except IOError as io_error:
                            logger.error(
                                f"Failed to open database file directly: {io_error}"
                            )
                            return False

                        # First, try direct connection regardless of platform
                        logger.info(
                            f"Attempting direct connection to database at: {db_path}"
                        )
                        try:
                            # Try direct connection first (this often works better on Windows)
                            conn = sqlite3.connect(
                                db_path, timeout=30, check_same_thread=False
                            )
                            logger.info("Direct database connection successful")
                        except sqlite3.OperationalError as oe:
                            logger.warning(f"Direct connection failed: {oe}")

                            # Fall back to URI connection for Windows paths with special characters
                            if os.name == "nt":  # Windows
                                try:
                                    # Import urllib for proper URL encoding
                                    import urllib.parse

                                    # Replace backslashes with forward slashes
                                    uri_path = db_path.replace("\\", "/")

                                    # Properly encode the path for URI
                                    # Don't encode the drive letter colon
                                    if ":" in uri_path:
                                        drive, rest = uri_path.split(":", 1)
                                        encoded_path = (
                                            f"{drive}:{urllib.parse.quote(rest)}"
                                        )
                                    else:
                                        encoded_path = urllib.parse.quote(uri_path)

                                    # Add URI prefix with proper encoding
                                    uri = f"file:{encoded_path}?mode=ro"
                                    logger.info(
                                        f"Using properly encoded URI format for Windows: {uri}"
                                    )

                                    # Connect with URI format
                                    conn = sqlite3.connect(
                                        uri,
                                        uri=True,
                                        timeout=30,
                                        check_same_thread=False,
                                    )
                                    logger.info("URI connection successful")
                                except Exception as uri_error:
                                    logger.error(
                                        f"URI connection also failed: {uri_error}"
                                    )

                                    # Last resort: try with normalized path
                                    try:
                                        import pathlib

                                        norm_path = str(pathlib.Path(db_path).resolve())
                                        logger.info(
                                            f"Trying with normalized path: {norm_path}"
                                        )
                                        conn = sqlite3.connect(
                                            norm_path,
                                            timeout=30,
                                            check_same_thread=False,
                                        )
                                        logger.info(
                                            "Normalized path connection successful"
                                        )
                                    except Exception as norm_error:
                                        logger.error(
                                            f"All connection attempts failed: {norm_error}"
                                        )
                                        return False
                            else:
                                # For non-Windows platforms, rethrow the original error
                                logger.error(
                                    f"Database connection failed on non-Windows platform: {oe}"
                                )
                                return False

                        # Set row factory explicitly
                        logger.info("Setting SQLite row factory")
                        conn.row_factory = sqlite3.Row

                        # Test the connection with a simple query
                        cursor = conn.cursor()
                        cursor.execute("SELECT sqlite_version()")
                        version = cursor.fetchone()[0]
                        logger.info(
                            f"Database connection established successfully. SQLite version: {version}"
                        )

                        # List all tables for debugging
                        cursor.execute(
                            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                        )
                        all_tables = [row[0] for row in cursor.fetchall()]
                        logger.info(f"All tables in database: {all_tables}")

                        # Check database file status again after connection
                        if os.path.exists(db_path):
                            stat_info = os.stat(db_path)
                            logger.info(
                                f"Database file size after connection: {stat_info.st_size} bytes"
                            )
                            logger.info(f"File permission mode: {stat_info.st_mode}")
                            logger.info(f"Last modified: {stat_info.st_mtime}")
                        else:
                            logger.warning(
                                "Database file path no longer exists after connection!"
                            )
                    except sqlite3.Error as sql_e:
                        logger.error(f"SQLite error connecting to database: {sql_e}")
                        return False
                    except Exception as e:
                        logger.error(f"Failed to connect to database: {e}")
                        return False

                    try:
                        # Verify database integrity
                        logger.info("Verifying database integrity")
                        try:
                            # Use pragma integrity_check
                            cursor = conn.cursor()
                            cursor.execute("PRAGMA integrity_check")
                            integrity_result = cursor.fetchone()[0]
                            if integrity_result == "ok":
                                logger.info("Database integrity check passed")
                            else:
                                logger.warning(
                                    f"Database integrity check failed: {integrity_result}"
                                )
                        except Exception as integrity_error:
                            logger.warning(
                                f"Failed to check database integrity: {integrity_error}"
                            )

                        # Verify the faces table exists and has the right schema
                        cursor = conn.cursor()
                        logger.info("Verifying 'faces' table existence")
                        cursor.execute(
                            "SELECT name FROM sqlite_master WHERE type='table' AND name='faces'"
                        )
                        table_check = cursor.fetchone()
                        if not table_check:
                            logger.error("Table 'faces' does not exist in the database")

                            # Try querying 'faces_v2' as an alternative
                            logger.info("Checking for alternative table 'faces_v2'")
                            cursor.execute(
                                "SELECT name FROM sqlite_master WHERE type='table' AND name='faces_v2'"
                            )
                            if cursor.fetchone():
                                logger.info(
                                    "Found alternative table 'faces_v2', trying to use it"
                                )
                                # Create a view temporarily to map faces_v2 to faces
                                try:
                                    cursor.execute(
                                        "CREATE TEMP VIEW faces AS SELECT * FROM faces_v2"
                                    )
                                    logger.info(
                                        "Created temporary view 'faces' from 'faces_v2' table"
                                    )
                                    # Verify it worked
                                    cursor.execute("SELECT COUNT(*) FROM faces LIMIT 1")
                                    logger.info(
                                        "Successfully queried temporary view 'faces'"
                                    )
                                    # Continue processing with the new view
                                    return self.rebuild_index(
                                        face_encodings, filenames, dimension
                                    )
                                except Exception as view_error:
                                    logger.error(
                                        f"Failed to create temporary view from faces_v2: {view_error}"
                                    )

                            # Log all tables that do exist to help with debugging
                            cursor.execute(
                                "SELECT name FROM sqlite_master WHERE type='table'"
                            )
                            tables = [row[0] for row in cursor.fetchall()]
                            logger.error(f"Existing tables in database: {tables}")

                            # If there are tables, check their schemas
                            if tables:
                                for table in tables:
                                    try:
                                        cursor.execute(f"PRAGMA table_info({table})")
                                        columns = [
                                            f"{row[1]} ({row[2]})"
                                            for row in cursor.fetchall()
                                        ]
                                        logger.info(
                                            f"Table '{table}' columns: {columns}"
                                        )
                                    except Exception as schema_error:
                                        logger.error(
                                            f"Error checking schema for table '{table}': {schema_error}"
                                        )

                            conn.close()
                            return False

                        # Verify the table has the required columns
                        logger.info("Verifying 'faces' table schema")
                        cursor.execute("PRAGMA table_info(faces)")
                        columns_info = cursor.fetchall()
                        columns = {row[1]: row[2] for row in columns_info}

                        # Log the full column info for debugging
                        logger.info(f"Full column info: {columns_info}")

                        if "filename" not in columns or "encoding" not in columns:
                            logger.error(
                                f"Table 'faces' is missing required columns. Available columns: {list(columns.keys())}"
                            )
                            conn.close()
                            return False

                        logger.info(f"Table schema verified successfully: {columns}")

                        # Check if there are any rows with encodings
                        try:
                            cursor.execute(
                                "SELECT COUNT(*) FROM faces WHERE encoding IS NOT NULL"
                            )
                            count = cursor.fetchone()[0]
                            logger.info(
                                f"Found {count} rows with encodings in the faces table"
                            )

                            # If we have encodings, check the first one to verify format
                            if count > 0:
                                cursor.execute(
                                    "SELECT filename, encoding FROM faces WHERE encoding IS NOT NULL LIMIT 1"
                                )
                                sample_row = cursor.fetchone()
                                if sample_row and sample_row["encoding"]:
                                    encoding_size = len(sample_row["encoding"])
                                    logger.info(
                                        f"Sample encoding size: {encoding_size} bytes for file {sample_row['filename']}"
                                    )

                                    # Try to unpickle the first encoding to verify format
                                    try:
                                        sample_encoding = pickle.loads(
                                            sample_row["encoding"]
                                        )
                                        if sample_encoding is not None:
                                            if hasattr(sample_encoding, "shape"):
                                                logger.info(
                                                    f"Sample encoding shape: {sample_encoding.shape}, dtype: {sample_encoding.dtype}"
                                                )
                                            else:
                                                logger.info(
                                                    f"Sample encoding type: {type(sample_encoding)}, length: {len(sample_encoding)}"
                                                )
                                    except Exception as e:
                                        logger.error(
                                            f"Error unpickling sample encoding: {e}"
                                        )
                        except sqlite3.Error as sql_e:
                            logger.error(f"SQL error counting encodings: {sql_e}")
                            conn.close()
                            return False

                        if count == 0:
                            logger.error(
                                "No face encodings found in database (encoding column is NULL for all rows)"
                            )
                            conn.close()
                            return False

                        # Get encoding data with more detailed logging
                        logger.info("Executing query to get face encodings")
                        # Get encodings in smaller batches to prevent memory issues
                        batch_size = 5000
                        offset = 0
                        total_processed = 0
                        max_encodings = min(
                            count, 50000
                        )  # Limit to 50,000 encodings for memory safety

                        logger.info(
                            f"Fetching up to {max_encodings} encodings in batches of {batch_size}"
                        )

                        # Use a single query with LIMIT and OFFSET for batching
                        cursor.execute(
                            "SELECT filename, encoding FROM faces WHERE encoding IS NOT NULL ORDER BY RANDOM() LIMIT ?",
                            (max_encodings,),
                        )
                        rows = cursor.fetchall()

                        logger.info(f"Fetched {len(rows)} rows for processing")

                        logger.info(f"Query returned {len(rows)} rows with encodings")

                        if not rows:
                            logger.error("No face encodings found in database")
                            conn.close()
                            return False

                        filenames = []
                        face_encodings = []

                        success_count = 0
                        error_count = 0

                        for row in rows:
                            try:
                                filename = row["filename"]
                                # Handle potential None or empty BLOB
                                if row["encoding"] is None:
                                    logger.warning(
                                        f"Skipping row with NULL encoding: {filename}"
                                    )
                                    error_count += 1
                                    continue

                                # Check if the encoding is an empty blob
                                if (
                                    isinstance(row["encoding"], bytes)
                                    and len(row["encoding"]) == 0
                                ):
                                    logger.warning(
                                        f"Skipping row with empty BLOB encoding: {filename}"
                                    )
                                    error_count += 1
                                    continue

                                try:
                                    encoding = pickle.loads(row["encoding"])
                                except pickle.UnpicklingError as unpickle_error:
                                    logger.error(
                                        f"Failed to unpickle encoding for {filename}: {unpickle_error}"
                                    )
                                    error_count += 1
                                    continue
                                except Exception as pickle_error:
                                    logger.error(
                                        f"Unknown error unpickling encoding for {filename}: {pickle_error}"
                                    )
                                    error_count += 1
                                    continue

                                # Verify encoding dimensions and data type
                                if encoding is None:
                                    logger.warning(
                                        f"Unpickled encoding is None for {filename}"
                                    )
                                    error_count += 1
                                    continue

                                try:
                                    # Check if encoding has the expected size and type
                                    encoding_array = np.array(encoding)
                                    if encoding_array.size == 0:
                                        logger.warning(
                                            f"Encoding for {filename} is empty array"
                                        )
                                        error_count += 1
                                        continue

                                    # Log the first successful encoding shape to help with debugging
                                    if success_count == 0:
                                        logger.info(
                                            f"First valid encoding shape: {encoding_array.shape}, dtype: {encoding_array.dtype}"
                                        )

                                    filenames.append(filename)
                                    face_encodings.append(encoding)
                                    success_count += 1

                                    # Log progress for large databases
                                    if success_count % 1000 == 0:
                                        logger.info(
                                            f"Processed {success_count} encodings so far..."
                                        )

                                except Exception as array_error:
                                    logger.error(
                                        f"Error converting encoding to array for {filename}: {array_error}"
                                    )
                                    error_count += 1
                            except Exception as e:
                                logger.error(
                                    f"Error processing row for {row['filename'] if 'filename' in row else 'unknown'}: {e}"
                                )
                                error_count += 1

                        logger.info(
                            f"Successfully processed {success_count} encodings, {error_count} errors"
                        )
                    except Exception as e:
                        logger.error(f"Error querying database: {e}")
                        conn.close()
                        return False
                    finally:
                        conn.close()

                # Verify we have enough vectors to create a meaningful index
                if len(face_encodings) == 0:
                    logger.error("No valid face encodings found to build index")
                    return False

                logger.info(
                    f"Creating new FAISS index with {len(face_encodings)} vectors"
                )

                try:
                    # Create a new FAISS index
                    self._index = faiss.IndexFlatL2(dimension)

                    # Convert to numpy array with appropriate type
                    logger.info("Converting encodings to numpy array")
                    face_encodings_array = np.array(face_encodings, dtype=np.float32)

                    # Log array details for debugging
                    logger.info(
                        f"Face encodings array shape: {face_encodings_array.shape}, dtype: {face_encodings_array.dtype}"
                    )

                    # Add the face encodings to the index
                    logger.info("Adding vectors to FAISS index")
                    self._index.add(face_encodings_array)

                    logger.info(
                        f"Successfully added {self._index.ntotal} vectors to the index"
                    )
                except Exception as e:
                    logger.error(f"Error creating FAISS index: {e}")
                    return False

                # Save the filenames mapping
                self._filenames = filenames

                # Save the index and mapping to disk
                index_path = self._get_index_path()
                map_path = self._get_map_path()

                faiss.write_index(self._index, index_path)
                with open(map_path, "wb") as f:
                    pickle.dump(filenames, f)

                logger.info(
                    f"FAISS index rebuilt and saved successfully with {self._index.ntotal} vectors"
                )
                self._loaded = True
                return True
            except Exception as e:
                logger.error(f"Error rebuilding FAISS index: {e}")
                self._loaded = False
                return False


# Create a global instance of the FAISS index manager
faiss_index_manager = FaissIndexManager()
