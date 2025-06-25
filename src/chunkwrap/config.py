"""Configuration management for chunkwrap."""

import os
import json
from pathlib import Path


def get_config_dir():
    """Get the configuration directory following XDG Base Directory specification."""
    if os.name == 'nt':  # Windows
        config_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
        return Path(config_dir) / 'chunkwrap'
    else:  # Unix-like (Linux, macOS, etc.)
        config_dir = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
        return Path(config_dir) / 'chunkwrap'


def get_config_file_path():
    """Get the full path to the configuration file."""
    return get_config_dir() / 'config.json'


def create_default_config():
    """Create the default configuration dictionary."""
    return {
        "default_chunk_size": 10000,
        "intermediate_chunk_suffix": " Please provide only a brief acknowledgment that you've received this chunk. Save your detailed analysis for the final chunk.",
        "final_chunk_suffix": "Please now provide your full, considered response to all previous chunks.",
        "output": "clipboard",
        "output_file": None
    }


def merge_configs(default_config, user_config):
    """Merge user configuration with defaults, returning merged config."""
    return {**default_config, **user_config}


def load_config():
    """Load configuration from file, creating default if it doesn't exist."""
    config_file = get_config_file_path()
    default_config = create_default_config()

    if not config_file.exists():
        # Create config directory if it doesn't exist
        config_file.parent.mkdir(parents=True, exist_ok=True)

        # Create default config file
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)

        print(f"Created default configuration file at: {config_file}")
        return default_config

    try:
        with open(config_file, 'r') as f:
            user_config = json.load(f)

        # Merge with defaults in case new options were added
        merged_config = merge_configs(default_config, user_config)

        # Update config file if new defaults were added
        if merged_config != user_config:
            with open(config_file, 'w') as f:
                json.dump(merged_config, f, indent=2)

        return merged_config

    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load config file {config_file}: {e}")
        print("Using default configuration.")
        return default_config
