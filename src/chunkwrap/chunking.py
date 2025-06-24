
"""Text chunking logic for chunkwrap."""


def validate_chunk_size(chunk_size):
    """Validate that chunk size is reasonable."""
    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive")
    if chunk_size > 1000000:  # 1MB character limit
        raise ValueError("Chunk size too large (max 1,000,000 characters)")
    return True


def chunk_file(text, chunk_size):
    """Split text into chunks of specified size."""
    validate_chunk_size(chunk_size)

    if not text:
        return []

    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]


def chunk_at_boundaries(text, chunk_size, boundary_chars=None):
    """
    Split text at natural boundaries when possible.

    This is a future enhancement for smarter chunking.
    Currently just falls back to simple chunking.
    """
    if boundary_chars is None:
        boundary_chars = ['\n\n', '\n', '. ', ' ']

    # For now, just use simple chunking
    # TODO: Implement smart boundary detection
    return chunk_file(text, chunk_size)


def get_chunk_info(chunks, current_idx):
    """Get information about the current chunk."""
    if not chunks or current_idx < 0 or current_idx >= len(chunks):
        return None

    return {
        'chunk': chunks[current_idx],
        'index': current_idx,
        'total': len(chunks),
        'is_last': current_idx == len(chunks) - 1,
        'is_first': current_idx == 0
    }
