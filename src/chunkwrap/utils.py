"""Utility functions and helpers for chunkwrap."""

from importlib.metadata import version, PackageNotFoundError


def get_version():
    """Get the version of the chunkwrap package."""
    try:
        return version("chunkwrap")
    except PackageNotFoundError:
        return "unknown"


def validate_encoding(file_path):
    """
    Validate that a file can be read with UTF-8 encoding.
    
    This is a future enhancement for better file handling.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1)  # Just read one character to test
        return True
    except UnicodeDecodeError:
        return False
    except Exception:
        return False


# Constants
DEFAULT_ENCODING = 'utf-8'
MAX_CHUNK_SIZE = 1000000  # 1MB
MIN_CHUNK_SIZE = 1
