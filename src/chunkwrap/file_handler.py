"""File operations and content processing for chunkwrap."""

import os
from pathlib import Path


def validate_file_paths(file_paths):
    """Validate that file paths exist and are readable."""
    valid_paths = []
    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"Warning: File '{file_path}' not found, skipping...")
            continue
        if not os.path.isfile(file_path):
            print(f"Warning: '{file_path}' is not a file, skipping...")
            continue
        valid_paths.append(file_path)
    return valid_paths


def create_file_header(file_path):
    """Create a header to identify file content in the combined output."""
    return f"\n{'='*50}\nFILE: {file_path}\n{'='*50}\n"


def read_files(file_paths):
    """Read multiple files and concatenate their content with file separators."""
    valid_paths = validate_file_paths(file_paths)
    
    if not valid_paths:
        return ""
    
    combined_content = []
    
    for file_path in valid_paths:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Add file header to identify content source
                file_header = create_file_header(file_path)
                combined_content.append(file_header + content)
        except Exception as e:
            print(f"Error reading file '{file_path}': {e}")
            continue
    
    return '\n'.join(combined_content)
