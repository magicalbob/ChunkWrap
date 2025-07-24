"""Output handling and formatting for chunkwrap with JSON protocol."""

import json
import pyperclip
from datetime import datetime


def create_json_metadata(chunk_info, args, config):
    """Create metadata object for JSON protocol."""
    return {
        "protocol_version": "1.0",
        "timestamp": datetime.now().isoformat(),
        "chunk_index": chunk_info["index"] + 1,
        "total_chunks": chunk_info["total"],
        "is_first_chunk": chunk_info["is_first"],
        "is_last_chunk": chunk_info["is_last"],
        "chunk_size": len(chunk_info["chunk"]),
        "source_files": args.file,
        "processing_options": {
            "secrets_masked": True,
            "suffix_disabled": getattr(args, 'no_suffix', False),
            "custom_last_prompt": getattr(args, 'lastprompt', None) is not None
        }
    }


def create_prompt_text(base_prompt, config, chunk_info, args):
    """Create the appropriate prompt text based on chunk position."""
    if chunk_info['is_last']:
        # Last chunk
        lastprompt = getattr(args, 'lastprompt', None)
        lastprompt = lastprompt if lastprompt else base_prompt
        return lastprompt + config.get("final_chunk_suffix", "")
    else:
        # Intermediate chunk
        if chunk_info['total'] > 1 and not getattr(args, 'no_suffix', False):
            return base_prompt + config['intermediate_chunk_suffix']
        else:
            return base_prompt


def format_chunk_wrapper(prompt_text, masked_chunk, chunk_info, args=None, config=None):
    """Format the chunk with JSON protocol wrapper."""
    # This function maintains compatibility with existing calls while using JSON
    if args is None or config is None:
        # Fallback to simple format if called without full context
        if chunk_info['is_last']:
            return f'{prompt_text}\n"""\n{masked_chunk}\n"""'
        else:
            return f'{prompt_text} (chunk {chunk_info["index"]+1} of {chunk_info["total"]})\n"""\n{masked_chunk}\n"""'
    
    return format_json_wrapper(prompt_text, masked_chunk, chunk_info, args, config)


def format_json_wrapper(prompt_text, masked_chunk, chunk_info, args, config):
    """Format the chunk with JSON protocol wrapper."""
    metadata = create_json_metadata(chunk_info, args, config)

    # Determine if this is for LLM processing or human consumption
    is_for_llm = getattr(args, 'llm_mode', False)  # Add this flag

    json_payload = {
        "metadata": metadata,
        "prompt": prompt_text,
        "content": masked_chunk,
        "instructions": {
            "response_format": "json" if is_for_llm else "natural",
            "target_audience": "llm" if is_for_llm else "human",
            "required_fields": [...] if is_for_llm else [],
            "processing_notes": []
        }
    }

    return json.dumps(json_payload, indent=2, ensure_ascii=False)


def handle_clipboard_output(content, chunk_info):
    """Copy content to clipboard and show confirmation."""
    try:
        pyperclip.copy(content)
        print(f"JSON-wrapped chunk {chunk_info['index']+1} of {chunk_info['total']} is now in the paste buffer.")
        return True
    except Exception as e:
        print(f"Error copying to clipboard: {e}")
        return False


def handle_stdout_output(content):
    """Print content to stdout."""
    print(content)
    return True


def handle_file_output(content, output_file, chunk_info):
    """Write content to specified file."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"JSON-wrapped chunk {chunk_info['index']+1} of {chunk_info['total']} written to {output_file}.")
        return True
    except Exception as e:
        print(f"Error writing to file: {e}")
        return False


def output_chunk(content, args, chunk_info):
    """Handle output based on the specified output mode."""
    if args.output == 'clipboard':
        return handle_clipboard_output(content, chunk_info)
    elif args.output == 'stdout':
        return handle_stdout_output(content)
    elif args.output == 'file':
        return handle_file_output(content, args.output_file, chunk_info)
    else:
        print(f"Unknown output mode: {args.output}")
        return False


def print_progress_info(args, chunk_info):
    """Print information about processing progress."""
    if len(args.file) > 1:
        print(f"Processing {len(args.file)} files: {', '.join(args.file)}")

    print(f"Using JSON protocol v1.0 for structured LLM communication")
    
    if chunk_info['is_last']:
        print("That was the last chunk! Use --reset for new file or prompt.")
    else:
        print("Run this script again for the next chunk.")
