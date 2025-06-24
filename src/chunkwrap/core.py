"""Main application logic and coordination for chunkwrap."""

from .file_handler import read_files
from .chunking import chunk_file, get_chunk_info
from .security import load_trufflehog_regexes, mask_secrets
from .state import read_state, write_state
from .output import create_prompt_text, format_chunk_wrapper, output_chunk, print_progress_info


class ChunkProcessor:
    """Main processor for handling file chunking and output."""
    
    def __init__(self, config):
        """Initialize the processor with configuration."""
        self.config = config
        self.regex_patterns = load_trufflehog_regexes()
    
    def process_files(self, args):
        """Process files according to the provided arguments."""
        # Read and combine all files
        content = read_files(args.file)
        
        if not content.strip():
            print("No content found in any of the specified files.")
            return
        
        # Create chunks
        chunks = chunk_file(content, args.size)
        total_chunks = len(chunks)
        
        # Get current state
        current_idx = read_state()
        
        if current_idx >= total_chunks:
            print("All chunks processed! Use --reset to start over.")
            return
        
        # Get current chunk info
        chunk_info = get_chunk_info(chunks, current_idx)
        if not chunk_info:
            print("Error: Invalid chunk index")
            return
        
        # Process current chunk
        success = self._process_current_chunk(args, chunk_info)
        
        if success:
            # Update state and show progress
            write_state(current_idx + 1)
            print_progress_info(args, chunk_info)
    
    def _process_current_chunk(self, args, chunk_info):
        """Process the current chunk and handle output."""
        # Mask secrets in the chunk
        masked_chunk = mask_secrets(chunk_info['chunk'], self.regex_patterns)
        
        # Create appropriate prompt text
        prompt_text = create_prompt_text(args.prompt, self.config, chunk_info, args)
        
        # Format the complete wrapper
        wrapper = format_chunk_wrapper(prompt_text, masked_chunk, chunk_info)
        
        # Output the chunk
        return output_chunk(wrapper, args, chunk_info)
    
    def get_current_chunk(self):
        """Get information about the current chunk without processing."""
        current_idx = read_state()
        return current_idx
    
    def should_continue_processing(self, total_chunks):
        """Check if there are more chunks to process."""
        current_idx = read_state()
        return current_idx < total_chunks
