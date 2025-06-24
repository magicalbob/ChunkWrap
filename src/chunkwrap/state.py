"""State persistence management for chunkwrap."""

import os

STATE_FILE = '.chunkwrap_state'


def read_state():
    """Read the current chunk index from the state file."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return int(f.read().strip())
        except (ValueError, IOError):
            return 0
    return 0


def write_state(idx):
    """Write the current chunk index to the state file."""
    try:
        with open(STATE_FILE, 'w') as f:
            f.write(str(idx))
    except IOError as e:
        print(f"Warning: Failed to write state file: {e}")


def reset_state():
    """Remove the state file, resetting to the beginning."""
    if os.path.exists(STATE_FILE):
        try:
            os.remove(STATE_FILE)
        except OSError as e:
            print(f"Warning: Failed to remove state file: {e}")


def validate_state(idx, total_chunks):
    """Validate that the state index is within valid bounds."""
    return 0 <= idx < total_chunks
