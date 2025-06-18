#!/usr/bin/env python3
import argparse
import os
import math
import pyperclip

STATE_FILE = '.chunkwrap_state'

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

def main():
    parser = argparse.ArgumentParser(description="Split file into chunks and wrap each chunk for LLM processing.")
    parser.add_argument('--prompt', type=str, required=True, help='Prompt text for regular chunks')
    parser.add_argument('--file', type=str, required=True, help='File to process')
    parser.add_argument('--lastprompt', type=str, help='Prompt for the last chunk (if different)')
    parser.add_argument('--reset', action='store_true', help='Reset chunk index and start over')
    parser.add_argument('--size', type=int, default=10000, help='Chunk size (default 10,000)')
    args = parser.parse_args()

    if args.reset:
        reset_state()
        print("State reset. Start from first chunk next run.")
        return

    with open(args.file, 'r', encoding='utf-8') as f:
        content = f.read()

    chunks = chunk_file(content, args.size)
    total_chunks = len(chunks)
    idx = read_state()

    if idx >= total_chunks:
        print("All chunks processed! Use --reset to start over.")
        return

    chunk = chunks[idx]

    # Choose wrapping for this chunk
    if idx < total_chunks - 1:
        # Not last chunk
        wrapper = f"{args.prompt} (chunk {idx+1} of {total_chunks})\n\"\"\"\n{chunk}\n\"\"\""
    else:
        lastprompt = args.lastprompt if args.lastprompt else args.prompt
        wrapper = f"{lastprompt}\n\"\"\"\n{chunk}\n\"\"\""

    pyperclip.copy(wrapper)
    print(f"Chunk {idx+1} of {total_chunks} is now in the paste buffer.")
    if idx < total_chunks - 1:
        print("Run this script again for the next chunk.")
    else:
        print("That was the last chunk! Use --reset for new file or prompt.")

    write_state(idx + 1)

if __name__ == "__main__":
    main()
