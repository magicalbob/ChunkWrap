#!/usr/bin/env python3
import argparse
import os
import math
import pyperclip
import re
import json
import tomllib
from importlib.metadata import version, PackageNotFoundError

STATE_FILE = '.chunkwrap_state'
TRUFFLEHOG_REGEX_FILE = 'truffleHogRegexes.json'  # Make sure you have this file with regex patterns

def read_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return int(f.read())
    return 0

def write_state(idx):
    with open(STATE_FILE, 'w') as f:
        f.write(str(idx))

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
    parser = argparse.ArgumentParser(description="Split file(s) into chunks and wrap each chunk for LLM processing.")
    parser.add_argument('--prompt', type=str, required=True, help='Prompt text for regular chunks')
    parser.add_argument('--file', type=str, nargs='+', required=True, help='File(s) to process')
    parser.add_argument('--lastprompt', type=str, help='Prompt for the last chunk (if different)')
    parser.add_argument('--reset', action='store_true', help='Reset chunk index and start over')
    parser.add_argument('--size', type=int, default=10000, help='Chunk size (default 10,000)')
    parser.add_argument('--version', action='version', version=f'%(prog)s {get_version()}')
    args = parser.parse_args()

    if args.reset:
        reset_state()
        print("State reset. Start from first chunk next run.")
        return

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

    # Choose wrapping for this chunk
    if idx < total_chunks - 1:
        wrapper = f"{args.prompt} (chunk {idx+1} of {total_chunks})\n\"\"\"\n{masked_chunk}\n\"\"\""
    else:
        lastprompt = args.lastprompt if args.lastprompt else args.prompt
        wrapper = f"{lastprompt}\n\"\"\"\n{masked_chunk}\n\"\"\""

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
