"""Output handling and formatting for chunkwrap."""

import pyperclip


def create_prompt_text(base_prompt, config, chunk_info, args):
    """Create the appropriate prompt text based on chunk position."""
    if chunk_info['is_last']:
        # Last chunk
        lastprompt = args.lastprompt if args.lastprompt else base_prompt
        return lastprompt + config.get("final_chunk_suffix", "")
    else:
        # Intermediate chunk
        if chunk_info['total'] > 1 and not args.no_suffix:
            return base_prompt + config['intermediate_chunk_suffix']
        else:
            return base_prompt


def format_chunk_wrapper(prompt_text, masked_chunk, chunk_info):
    """Format the chunk with prompt and wrapper."""
    if chunk_info['is_last']:
        # Final chunk doesn't show index
        return f'{prompt_text}\n"""\n{masked_chunk}\n"""'
    else:
        # Intermediate chunk shows index
        return f'{prompt_text} (chunk {chunk_info["index"]+1} of {chunk_info["total"]})\n"""\n{masked_chunk}\n"""'


def handle_clipboard_output(content, chunk_info):
    """Copy content to clipboard and show confirmation."""
    try:
        pyperclip.copy(content)
        print(f"Chunk {chunk_info['index']+1} of {chunk_info['total']} is now in the paste buffer.")
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
        print(f"Chunk {chunk_info['index']+1} of {chunk_info['total']} written to {output_file}.")
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
    
    if chunk_info['is_last']:
        print("That was the last chunk! Use --reset for new file or prompt.")
    else:
        print("Run this script again for the next chunk.")
