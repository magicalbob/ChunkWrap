chunkwrap
=========

A Python utility for splitting large files into manageable chunks, masking secrets, and wrapping each chunk with custom prompts for Large Language Model (LLM) processing.

Overview
--------

chunkwrap helps you prepare large files for LLM workflows by:

-   Splitting them into smaller, prompt-ready chunks
-   Redacting secrets via TruffleHog-style regexes
-   Tracking progress across invocations
-   Supporting multiple output modes: clipboard, stdout, or file

Features
--------

-   **Configurable chunking**: Choose chunk size (default: 10,000 characters)
-   **Multi-file support**: Concatenate multiple inputs into a single stream
-   **Secret masking**: Redact sensitive patterns using configurable regexes
-   **Prompt wrapping**: Use distinct prompts for intermediate and final chunks
-   **Clipboard integration**: Copy output chunk directly to your paste buffer
-   **Output flexibility**: Send wrapped output to stdout or a file
-   **State tracking**: Progress is remembered across runs using a local `.chunkwrap_state` file
-   **Optional prompt suffix**: Append boilerplate only to intermediate chunks

Installation
------------

1.  To install from source, clone the repository:

    ```bash
    git clone https://github.com/magicalbob/chunkwrap.git
    cd chunkwrap
    ```

    Or just install from PyPI:

    ```bash
    pip install chunkwrap
    ```

2.  Install dependencies (if installed from source):

    ```bash
    pip install -e .
    ```

    Or for developer tools:

    ```bash
    pip install -e ".[dev]"
    ```

3.  On first run, a default config file will be created at:

    -   Linux/macOS: `~/.config/chunkwrap/config.json`
    -   Windows: `%APPDATA%\chunkwrap\config.json`

Usage
-----

### Minimal example

```bash
chunkwrap --prompt "Analyze this:" --file myscript.py
```

### Multiple files

```bash
chunkwrap --prompt "Review each file:" --file a.py b.md
```

### Secret masking

Place a `truffleHogRegexes.json` file in the same directory:

```json
{
  "AWS": "AKIA[0-9A-Z]{16}",
  "Slack": "xox[baprs]-[0-9a-zA-Z]{10,48}"
}
```

Each match will be replaced with `***MASKED-<KEY>***`.

### Custom chunk size

```bash
chunkwrap --prompt "Summarize section:" --file notes.txt --size 5000
```

### Final chunk prompt

```bash
chunkwrap --prompt "Analyze chunk:" --lastprompt "Now summarize everything:" --file long.txt
```

### Disable prompt suffix

```bash
chunkwrap --prompt "Chunk:" --file script.py --no-suffix
```

### Show config path

```bash
chunkwrap --config-path
```

### Reset state

```bash
chunkwrap --reset
```

### Output options

```bash
chunkwrap --prompt "Analyze:" --file myfile.txt --output stdout
chunkwrap --prompt "Analyze:" --file myfile.txt --output file --output-file output.txt
```

- `--output clipboard` (default): copy the output chunk to the clipboard
- `--output stdout`: print the output chunk to standard output
- `--output file`: write the output chunk to the file specified by `--output-file`

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
  "final_chunk_suffix": "Please now provide your full, considered response to all previous chunks.",
  "output": "clipboard",
  "output_file": null
}
```

-   **`default_chunk_size`**: *(integer)*\
    Sets the default number of characters per chunk when `--size` is not specified on the command line.

-   **`intermediate_chunk_suffix`**: *(string)*\
    This text is appended to the `--prompt` on all intermediate (non-final) chunks unless the `--no-suffix` flag is used.

-   **`final_chunk_suffix`**: *(string)*\
    This text is appended to the `--lastprompt` (or `--prompt`, if `--lastprompt` is not used) for the final chunk. It's intended to signal to the LLM that a full, detailed response is now appropriate.

-   **`output`**: *(string: clipboard, stdout, file)*\
    Default output destination for processed chunks. Can be overridden via --output.

-   **`output_file`**: *(string or null)*\
    File path used when output is set to "file". Can be overridden via --output-file.

### Example

You might modify your config to create tighter chunking and less verbose suffixes:

```json
{
  "default_chunk_size": 5000,
  "intermediate_chunk_suffix": "Brief reply only, please.",
  "final_chunk_suffix": "Full summary now."
}
```

These values will be automatically merged with any defaults added in future releases, so missing keys will not cause errors.

Roadmap
-------

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
