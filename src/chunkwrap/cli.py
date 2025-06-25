#!/usr/bin/env python3
"""Command-line interface for chunkwrap."""

import argparse
from .config import load_config, get_config_file_path
from .state import reset_state
from .core import ChunkProcessor
from .utils import get_version


def create_parser():
    """Create and configure the argument parser."""
    config = load_config()

    parser = argparse.ArgumentParser(
        description="Split file(s) into chunks and wrap each chunk for LLM processing."
    )

    parser.add_argument('--prompt', type=str, help='Prompt text for regular chunks')
    parser.add_argument('--file', type=str, nargs='+', help='File(s) to process')
    parser.add_argument('--lastprompt', type=str, help='Prompt for the last chunk (if different)')
    parser.add_argument('--reset', action='store_true', help='Reset chunk index and start over')
    parser.add_argument('--size', type=int, default=config['default_chunk_size'],
                       help=f'Chunk size (default: {config["default_chunk_size"]})')
    parser.add_argument('--no-suffix', action='store_true',
                       help='Disable automatic suffix for intermediate chunks')
    parser.add_argument('--config-path', action='store_true',
                       help='Show configuration file path and exit')
    parser.add_argument('--version', action='version', version=f'%(prog)s {get_version()}')
    parser.add_argument('--output', choices=['clipboard', 'stdout', 'file'],
                        default=config.get('output', 'clipboard'),
                        help='Where to send the output (default: clipboard or config override)')
    parser.add_argument('--output-file', type=str,
                        default=config.get('output_file'),
                        help='Output file name (used if --output file)')

    return parser


def validate_args(args, config):
    """Validate command line arguments."""
    if args.reset:
        if args.prompt or args.file or args.lastprompt or args.size != config['default_chunk_size']:
            return "--reset cannot be used with other arguments"
        return None

    if not args.prompt:
        return "--prompt is required when not using --reset"

    if not args.file:
        return "--file is required when not using --reset"

    if args.output == 'file' and not args.output_file:
        return "--output-file must be specified when using --output file (or set in config.json)"

    return None


def handle_special_commands(args):
    """Handle special commands that don't require full processing."""
    if args.config_path:
        print(f"Configuration file: {get_config_file_path()}")
        return True

    if args.reset:
        reset_state()
        print("State reset. Start from first chunk next run.")
        return True

    return False


def main():
    """Main entry point for the CLI."""
    config = load_config()
    parser = create_parser()
    args = parser.parse_args()

    # Handle special commands first
    if handle_special_commands(args):
        return

    # Validate arguments
    error = validate_args(args, config)
    if error:
        parser.error(error)

    # Create and run the processor
    processor = ChunkProcessor(config)
    processor.process_files(args)


if __name__ == "__main__":
    main()
