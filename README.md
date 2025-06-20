chunkwrap
=========

A Python utility for splitting large files into manageable chunks, masking secrets, and wrapping each chunk with custom prompts for Large Language Model (LLM) processing.

Overview
--------

chunkwrap helps you prepare large files for LLM workflows by:

-   Splitting them into smaller, prompt-ready chunks

-   Redacting secrets via TruffleHog-style regexes

-   Tracking progress across invocations

-   Supporting clipboard-based interaction or (soon) alternate output modes

Features
--------

-   **Configurable chunking**: Choose chunk size (default: 10,000 characters)

-   **Multi-file support**: Concatenate multiple inputs into a single stream

-   **Secret masking**: Redact sensitive patterns using configurable regexes

-   **Prompt wrapping**: Use distinct prompts for intermediate and final chunks

-   **Clipboard integration**: Copy output chunk directly to your paste buffer

-   **State tracking**: Progress is remembered across runs using a local `.chunkwrap_state` file

-   **Optional prompt suffix**: Append boilerplate only to intermediate chunks

Installation
------------

1.  Clone the repository:

    ```bash
    git clone https://github.com/your/repo.git
    cd chunkwrap
    ```

2.  Install dependencies:

    ```bash
    pip install pyperclip
    ```

3.  On first run, a default config file will be created at:

    -   Linux/macOS: `~/.config/chunkwrap/config.json`

    -   Windows: `%APPDATA%\chunkwrap\config.json`

Usage
-----

### Minimal example

```bash
python chunkwrap.py --prompt "Analyze this:" --file myscript.py
```

### Multiple files

```bash
python chunkwrap.py --prompt "Review each file:" --file a.py b.md
```

### Secret masking

Place a `truffleHogRegexes.json` file in the same directory:

json

```
{
  "AWS": "AKIA[0-9A-Z]{16}",
  "Slack": "xox[baprs]-[0-9a-zA-Z]{10,48}"
}

```

Each match will be replaced with `***MASKED-<KEY>***`.

### Custom chunk size

```bash
python chunkwrap.py --prompt "Summarize section:" --file notes.txt --size 5000
```

### Final chunk prompt

```bash
python chunkwrap.py --prompt "Analyze chunk:" --lastprompt "Now summarize everything:" --file long.txt
```

### Disable prompt suffix

```bash
python chunkwrap.py --prompt "Chunk:" --file script.py --no-suffix
```

### Show config path

```bash
python chunkwrap.py --config-path
```

### Reset state

```bash
python chunkwrap.py --reset
```

Output Format
-------------

Each chunk is wrapped like:

```
Your prompt (chunk 2 of 4)
"""
[redacted content]
"""
```

Final chunk omits the index and uses `--lastprompt` if provided.

Configuration File
------------------

On first run, `chunkwrap` creates a configuration file at the following path:

-   **Linux/macOS**: `~/.config/chunkwrap/config.json`

-   **Windows**: `%APPDATA%\chunkwrap\config.json`

This file allows you to customize the default behavior of the tool. You can edit it manually to override any of the options below.

### Available Options

```json
{
  "default_chunk_size": 10000,
  "intermediate_chunk_suffix": " Please provide only a brief acknowledgment that you've received this chunk. Save your detailed analysis for the final chunk.",
  "final_chunk_suffix": "Please now provide your full, considered response to all previous chunks."
}
```

-   **`default_chunk_size`**: *(integer)*\
    Sets the default number of characters per chunk when `--size` is not specified on the command line.

-   **`intermediate_chunk_suffix`**: *(string)*\
    This text is appended to the `--prompt` on all intermediate (non-final) chunks unless the `--no-suffix` flag is used.

-   **`final_chunk_suffix`**: *(string)*\
    This text is appended to the `--lastprompt` (or `--prompt`, if `--lastprompt` is not used) for the final chunk. It's intended to signal to the LLM that a full, detailed response is now appropriate.

### Example

You might modify your config to create tighter chunking and less verbose suffixes:

```json
{
  "default_chunk_size": 5000,
  "intermediate_chunk_suffix": " Brief reply only, please.",
  "final_chunk_suffix": " Full summary now."
}
```

These values will be automatically merged with any defaults added in future releases, so missing keys will not cause errors.

Roadmap
-------

### Near-term improvements

~~1.  **Auto-prompt modification for non-final chunks**: Automatically append instructions to non-final chunks asking the LLM to reserve comprehensive responses for the final chunk. This prevents information loss when users only review the last response in a sequence.~~

~~2.  **Reset investigation**: The `reset` command does not work as expected, and needs some love & attention.~~

1.  **Configurable prompt suffixes**: Add support for automatically appending standard instructions to all prompts (e.g., "Use concise responses for intermediate chunks").

~~3.  **External configuration management**: Move configuration options to `~/.config/chunkwrap.json` with CLI commands for managing settings.~~

2.  **Make cross platform**: local usage on Mac is good. My test machine is via ssh to a linux machine. The current code does not support this. Consider adding optional argument `chunkwrap [--output {clipboard|stdout|file}]` to handle this situation.

### Future considerations

-   **Chunk overlap**: Add optional overlap between chunks to preserve context across boundaries
-   **Smart chunking**: Break at natural boundaries (sentences, paragraphs) rather than arbitrary character counts
-   **Output formats**: Support for different wrapper formats (XML tags, markdown blocks, etc.)
-   **Parallel processing**: For very large file sets, allow processing multiple chunks simultaneously
-   **Integration modes**: Direct API integration with popular LLM services

Requirements
------------

-   Python 3.11+

-   `pyperclip`

License
-------

GNU General Public License v3.0 --- see LICENSE for details.
