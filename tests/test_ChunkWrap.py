import os
import sys
import pytest
import pyperclip
from unittest.mock import mock_open, patch
from io import StringIO

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ChunkWrap.ChunkWrap import read_state, write_state, reset_state, chunk_file, main

STATE_FILE = '.chunkwrap_state'


@pytest.fixture
def setup_state_file():
    """Fixture for setting up and tearing down the state file."""
    # Ensure the state file does not exist before the test
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)

    yield

    # Teardown: remove state file after tests
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)


@pytest.fixture
def sample_file_content():
    """Sample file content for testing."""
    return "This is line 1.\nThis is line 2.\nThis is line 3.\nThis is a longer line for testing purposes."


def test_read_state_initial(setup_state_file):
    """Test reading the initial state."""
    assert read_state() == 0


def test_read_state_with_existing_file(setup_state_file):
    """Test reading state from an existing state file."""
    # Create a state file with content
    with open(STATE_FILE, 'w') as f:
        f.write('5')
    
    assert read_state() == 5


def test_write_state(setup_state_file):
    """Test writing to the state file."""
    write_state(3)
    assert read_state() == 3


def test_reset_state(setup_state_file):
    """Test resetting the state."""
    write_state(5)
    reset_state()
    assert read_state() == 0  # Should reset to 0


def test_reset_state_no_file(setup_state_file):
    """Test resetting state when no state file exists."""
    # Should not raise an error
    reset_state()
    assert read_state() == 0


def test_chunk_file():
    """Test the chunking functionality."""
    text = "This is a test string that will be split into chunks."
    chunks = chunk_file(text, 10)
    assert chunks == ["This is a ", "test strin", "g that wil", "l be split", " into chun", "ks."]
    
    # Test with a larger chunk size (text is 55 chars, so with size 50 it creates 2 chunks)
    chunks = chunk_file(text, 50)
    assert chunks == ["This is a test string that will be split into chun", "ks."]
    
    # Test with chunk size larger than text
    chunks = chunk_file(text, 100)
    assert chunks == ["This is a test string that will be split into chunks."]


def test_chunk_file_empty_string():
    """Test chunking an empty string."""
    chunks = chunk_file("", 10)
    assert chunks == [""]


def test_chunk_file_empty_string():
    """Test chunking an empty string."""
    chunks = chunk_file("", 10)
    assert chunks == []


def test_chunk_file_single_character():
    """Test chunking a single character."""
    chunks = chunk_file("A", 1)
    assert chunks == ["A"]
    
    chunks = chunk_file("A", 5)
    assert chunks == ["A"]


def test_clipboard_copy(mocker):
    """Test copying to clipboard."""
    mocker.patch('pyperclip.copy')  # Mock the copy method

    # Perform a copy operation
    pyperclip.copy("Test copy")
    
    pyperclip.copy.assert_called_with("Test copy")


@patch('sys.argv', ['ChunkWrap.py', '--prompt', 'Test prompt', '--file', 'test.txt'])
@patch('builtins.open', mock_open(read_data='A' * 100))  # 100 character file
@patch('pyperclip.copy')
@patch('builtins.print')
def test_main_multiple_chunks(mock_print, mock_copy, setup_state_file):
    """Test main function with multiple chunks."""
    # Mock a large file that will be split into multiple chunks
    with patch('sys.argv', ['ChunkWrap.py', '--prompt', 'Test prompt', '--file', 'test.txt', '--size', '50']):
        main()
    
    # Should process first chunk
    expected_wrapper = 'Test prompt (chunk 1 of 2)\n"""\n' + 'A' * 50 + '\n"""'
    mock_copy.assert_called_with(expected_wrapper)
    
    mock_print.assert_any_call("Chunk 1 of 2 is now in the paste buffer.")
    mock_print.assert_any_call("Run this script again for the next chunk.")


@patch('sys.argv', ['ChunkWrap.py', '--prompt', 'Test prompt', '--file', 'test.txt', '--size', '10'])
@patch('builtins.open', mock_open(read_data='Short'))
@patch('pyperclip.copy')
@patch('builtins.print')
def test_main_single_chunk_no_counter(mock_print, mock_copy, setup_state_file):
    """Test main function with single chunk (no chunk counter in prompt)."""
    main()
    
    # For single chunk, should not include chunk counter and use regular prompt
    expected_wrapper = 'Test prompt\n"""\nShort\n"""'
    mock_copy.assert_called_with(expected_wrapper)


def test_state_file_persistence(setup_state_file):
    """Test that state persists across function calls."""
    # Write state
    write_state(7)
    
    # Read it back
    assert read_state() == 7
    
    # Write different state
    write_state(10)
    assert read_state() == 10


@patch('sys.argv', ['ChunkWrap.py', '--prompt', 'Test prompt', '--file', 'nonexistent.txt'])
def test_main_file_not_found():
    """Test main function with non-existent file."""
    with pytest.raises(FileNotFoundError):
        main()


def test_chunk_file_various_sizes():
    """Test chunk_file with various chunk sizes."""
    text = "Hello World"
    
    # Chunk size 1
    chunks = chunk_file(text, 1)
    assert len(chunks) == 11  # Each character is a chunk
    assert chunks[0] == "H"
    assert chunks[-1] == "d"
    
    # Chunk size equal to text length
    chunks = chunk_file(text, len(text))
    assert chunks == ["Hello World"]
    
    # Very large chunk size
    chunks = chunk_file(text, 1000)
    assert chunks == ["Hello World"]
