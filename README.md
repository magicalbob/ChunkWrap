# ChunkWrap

A Python utility for splitting large files into manageable chunks and wrapping them with custom prompts for Large Language Model (LLM) processing.

## Overview

ChunkWrap helps you process large files with LLMs by automatically splitting them into smaller chunks and wrapping each chunk with your specified prompt. It maintains state between runs, so you can process one chunk at a time without losing track of your progress.

## Features

- **Automatic chunking**: Split files into configurable chunk sizes (default 10,000 characters)
- **State management**: Remembers which chunk you're on between runs
- **Clipboard integration**: Automatically copies wrapped chunks to your clipboard
- **Custom prompts**: Use different prompts for regular chunks vs. the final chunk
- **Progress tracking**: Shows current chunk number and total chunks

## Installation

1. Clone or download the script
2. Install the required dependency:
   ```bash
   pip install pyperclip
   ```

## Usage

### Basic Usage

```bash
python chunkwrap.py --prompt "Analyze this code:" --file myfile.txt
```

### Advanced Usage

```bash
# Custom chunk size
python chunkwrap.py --prompt "Review this code:" --file large_file.py --size 5000

# Different prompt for the last chunk
python chunkwrap.py --prompt "Analyze this code chunk:" --file code.py --lastprompt "Analyze this final code chunk and provide a summary:"

# Reset state to start over
python chunkwrap.py --reset
```

## Command Line Arguments

- `--prompt` (required): The prompt text to wrap around each chunk
- `--file` (required): Path to the file you want to process
- `--lastprompt` (optional): Different prompt for the final chunk
- `--size` (optional): Chunk size in characters (default: 10,000)
- `--reset` (optional): Reset the chunk counter and start from the beginning

## How It Works

1. **First run**: Reads your file, splits it into chunks, wraps the first chunk with your prompt, and copies it to clipboard
2. **Subsequent runs**: Continues from where you left off, processing the next chunk
3. **State tracking**: Uses a `.chunkwrap_state` file to remember your progress
4. **Completion**: Notifies you when all chunks are processed

## Example Workflow

```bash
# Start processing a large Python file
python chunkwrap.py --prompt "Please review this Python code for bugs:" --file large_script.py

# Output: "Chunk 1 of 5 is now in the paste buffer. Run this script again for the next chunk."
# Paste into your LLM, get response, then run again...

python chunkwrap.py --prompt "Please review this Python code for bugs:" --file large_script.py

# Output: "Chunk 2 of 5 is now in the paste buffer. Run this script again for the next chunk."
# Continue until all chunks are processed...

# When done with this file, reset for a new file
python chunkwrap.py --reset
```

## Output Format

Each chunk is wrapped in triple quotes with your prompt:

```
Your prompt here (chunk 1 of 3)
"""
[chunk content here]
"""
```

The final chunk omits the chunk counter and uses `--lastprompt` if provided.

## State File

ChunkWrap creates a `.chunkwrap_state` file in the current directory to track progress. Delete this file or use `--reset` to start over with a new file or prompt.

## Use Cases

- Processing large codebases with LLMs
- Analyzing lengthy documents in sections  
- Breaking down large text files for review
- Sequential processing of any large text content

## Requirements

- Python 3.6+
- pyperclip library

## License
This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for more details.
