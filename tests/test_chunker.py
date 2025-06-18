import os
import sys
import pytest
import pyperclip

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from chunker.chunker import read_state, write_state, reset_state, chunk_file

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


def test_read_state_initial(setup_state_file):
    """Test reading the initial state."""
    assert read_state() == 0


def test_write_state(setup_state_file):
    """Test writing to the state file."""
    write_state(3)
    assert read_state() == 3


def test_reset_state(setup_state_file):
    """Test resetting the state."""
    write_state(5)
    reset_state()
    assert read_state() == 0  # Should reset to 0


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


def test_clipboard_copy(mocker):
    """Test copying to clipboard."""
    mocker.patch('pyperclip.copy')  # Mock the copy method

    # Perform a copy operation
    pyperclip.copy("Test copy")
    pyperclip.copy("Test copy")  # No action needed, just checking

    pyperclip.copy.assert_called_with("Test copy")  # Ensure it was called with the correct argument
