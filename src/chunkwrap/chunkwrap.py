#!/usr/bin/env python3
import argparse
import os
import math
import pyperclip
import re
import json
import tomllib
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path

STATE_FILE = '.chunkwrap_state'
TRUFFLEHOG_REGEX_FILE = 'truffleHogRegexes.json'  # Make sure you have this file with regex patterns

def get_config_dir():
    """Get the configuration directory following XDG Base Directory specification"""
    if os.name == 'nt':  # Windows
        config_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
        return Path(config_dir) / 'chunkwrap'
    else:  # Unix-like (Linux, macOS, etc.)
        config_dir = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
        return Path(config_dir) / 'chunkwrap'

def get_config_file_path():
    """Get the full path to the configuration file"""
    return get_config_dir() / 'config.json'

def load_config():
    """Load configuration from file, creating default if it doesn't exist"""
    config_file = get_config_file_path()
    
    # Default configuration
    default_config = {
        "default_chunk_size": 10000,
        "intermediate_chunk_suffix": " Please provide only a brief acknowledgment that you've received this chunk. Save your detailed analysis for the final chunk.",
        "final_chunk_suffix": "Please now provide your full, considered response to all previous chunks."
    }
    
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
            config = json.load(f)
        
        # Merge with defaults in case new options were added
        merged_config = {**default_config, **config}
        
        # Update config file if new defaults were added
        if merged_config != config:
            with open(config_file, 'w') as f:
                json.dump(merged_config, f, indent=2)
        
        return merged_config
    
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load config file {config_file}: {e}")
        print("Using default configuration.")
        return default_config

def read_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return int(f.read())
    return 0

def write_state(idx):
    try:
        with open(STATE_FILE, 'w') as f:
            f.write(str(idx))
    except IOError as e:
        print(f"Warning: Failed to write state file: {e}")

def reset_state():
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)

def chunk_file(text, chunk_size):
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

def load_trufflehog_regexes():
    if os.path.exists(TRUFFLEHOG_REGEX_FILE):
        with open(TRUFFLEHOG_REGEX_FILE, 'r') as f:
            return json.load(f)
    return {}

def mask_secrets(text, regex_patterns):
    """Mask sensitive information using TruffleHog regex patterns"""
    for key, pattern in regex_patterns.items():
        text = re.sub(pattern, f'***MASKED-{key}***', text)
    return text

def read_files(file_paths):
    """Read multiple files and concatenate their content with file separators"""
    combined_content = []
    
    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"Warning: File '{file_path}' not found, skipping...")
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Add file header to identify content source
                file_header = f"\n{'='*50}\n" + f"FILE: {file_path}\n" + f"{'='*50}\n"
                combined_content.append(file_header + content)
        except Exception as e:
            print(f"Error reading file '{file_path}': {e}")
            continue
    
    return '\n'.join(combined_content)

def get_version():
    try:
        return version("chunkwrap")
    except PackageNotFoundError:
        return "unknown"

def main():
    # Load configuration
    config = load_config()
    
    parser = argparse.ArgumentParser(description="Split file(s) into chunks and wrap each chunk for LLM processing.")
    
    parser.add_argument('--prompt', type=str, help='Prompt text for regular chunks')
    parser.add_argument('--file', type=str, nargs='+', help='File(s) to process')
    parser.add_argument('--lastprompt', type=str, help='Prompt for the last chunk (if different)')
    parser.add_argument('--reset', action='store_true', help='Reset chunk index and start over')
    parser.add_argument('--size', type=int, default=config['default_chunk_size'], help=f'Chunk size (default: {config["default_chunk_size"]})')
    parser.add_argument('--no-suffix', action='store_true', help='Disable automatic suffix for intermediate chunks')
    parser.add_argument('--config-path', action='store_true', help='Show configuration file path and exit')
    parser.add_argument('--version', action='version', version=f'%(prog)s {get_version()}')
    
    args = parser.parse_args()

    if args.config_path:
        print(f"Configuration file: {get_config_file_path()}")
        return

    if args.reset:
        # Ensure reset is used alone
        if args.prompt or args.file or args.lastprompt or args.size != config['default_chunk_size']:
            parser.error("--reset cannot be used with other arguments")
        reset_state()
        print("State reset. Start from first chunk next run.")
        return

    # Validate required arguments for normal operation
    if not args.prompt:
        parser.error("--prompt is required when not using --reset")
    if not args.file:
        parser.error("--file is required when not using --reset")

    # Load TruffleHog regex patterns
    regex_patterns = load_trufflehog_regexes()

    # Read all files and combine content
    content = read_files(args.file)
    
    if not content.strip():
        print("No content found in any of the specified files.")
        return

    chunks = chunk_file(content, args.size)
    total_chunks = len(chunks)
    idx = read_state()

    if idx >= total_chunks:
        print("All chunks processed! Use --reset to start over.")
        return

    chunk = chunks[idx]

    # Mask secrets
    masked_chunk = mask_secrets(chunk, regex_patterns)

    # Build the prompt with appropriate suffix
    base_prompt = args.prompt
    
    # Choose wrapping for this chunk
    if idx < total_chunks - 1:
        # This is an intermediate chunk (not the final one)
        if total_chunks > 1 and not args.no_suffix:
            # Add suffix only if there are multiple chunks and suffix is enabled
            prompt_with_suffix = base_prompt + config['intermediate_chunk_suffix']
        else:
            prompt_with_suffix = base_prompt
        
        wrapper = f"{prompt_with_suffix} (chunk {idx+1} of {total_chunks})\n\"\"\"\n{masked_chunk}\n\"\"\""
    else:
        # This is the final chunk
        lastprompt = args.lastprompt if args.lastprompt else args.prompt
        final_prompt = lastprompt + config.get("final_chunk_suffix", "")
        wrapper = f"{final_prompt}\n\"\"\"\n{masked_chunk}\n\"\"\""

    pyperclip.copy(wrapper)
    print(f"Chunk {idx+1} of {total_chunks} is now in the paste buffer.")
    if len(args.file) > 1:
        print(f"Processing {len(args.file)} files: {', '.join(args.file)}")
    if idx < total_chunks - 1:
        print("Run this script again for the next chunk.")
    else:
        print("That was the last chunk! Use --reset for new file or prompt.")

    write_state(idx + 1)

if __name__ == "__main__":
    main()
