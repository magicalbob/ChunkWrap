"""
chunkwrap - A utility for splitting large files into manageable chunks for LLM processing.
"""

from .core import ChunkProcessor
from .cli import main

__version__ = "2.4.1"
__all__ = ["ChunkProcessor", "main"]
