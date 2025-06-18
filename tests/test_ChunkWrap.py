import os
import sys
import pytest
import pyperclip
from unittest.mock import mock_open, patch, MagicMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from chunkwrap.chunkwrap import read_state, write_state, reset_state, chunk_file, main

STATE_FILE = '.chunkwrap_state'

@pytest.fixture
def setup_state_file():
    """Fixture for setting up and tearing down the state file."""
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
    yield
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)

@pytest.fixture
def sample_file_content():
    return "This is line 1.\nThis is line 2.\nThis is line 3.\nThis is a longer line for testing purposes."

def test_read_state_initial(setup_state_file):
    assert read_state() == 0

def test_read_state_with_existing_file(setup_state_file):
    with open(STATE_FILE, 'w') as f:
        f.write('5')
    assert read_state() == 5

def test_write_state(setup_state_file):
    write_state(3)
    assert read_state() == 3

def test_reset_state(setup_state_file):
    write_state(5)
    reset_state()
    assert read_state() == 0

def test_reset_state_no_file(setup_state_file):
    reset_state()
    assert read_state() == 0

def test_chunk_file():
    text = "This is a test string that will be split into chunks."
    chunks = chunk_file(text, 10)
    assert chunks == ["This is a ", "test strin", "g that wil", "l be split", " into chun", "ks."]

    chunks = chunk_file(text, 50)
    assert chunks == ["This is a test string that will be split into chun", "ks."]

    chunks = chunk_file(text, 100)
    assert chunks == ["This is a test string that will be split into chunks."]

def test_chunk_file_empty_string():
    chunks = chunk_file("", 10)
    assert chunks == []

def test_chunk_file_single_character():
    chunks = chunk_file("A", 1)
    assert chunks == ["A"]

    chunks = chunk_file("A", 5)
    assert chunks == ["A"]

def test_clipboard_copy(mocker):
    mocker.patch('pyperclip.copy')
    pyperclip.copy("Test copy")
    pyperclip.copy.assert_called_with("Test copy")

# Patch get_version so tomllib.load isn't called (fixes binary open bug)
@patch('chunkwrap.chunkwrap.get_version', return_value="test")
@patch('pyperclip.copy')
@patch('builtins.open', new_callable=mock_open, read_data='A' * 100)
@patch('builtins.print')
def test_main_multiple_chunks(mock_print, mock_file, mock_copy, mock_version, setup_state_file):
    # Will use the mocked open for 'test.txt'
    with patch('sys.argv', ['chunkwrap.py', '--prompt', 'Test prompt', '--file', 'test.txt', '--size', '50']):
        main()
    expected_wrapper = 'Test prompt (chunk 1 of 2)\n"""\n' + 'A' * 50 + '\n"""'
    mock_copy.assert_called_with(expected_wrapper)
    mock_print.assert_any_call("Chunk 1 of 2 is now in the paste buffer.")
    mock_print.assert_any_call("Run this script again for the next chunk.")

@patch('chunkwrap.chunkwrap.get_version', return_value="test")
@patch('pyperclip.copy')
@patch('builtins.open', new_callable=mock_open, read_data='Short')
@patch('builtins.print')
def test_main_single_chunk_no_counter(mock_print, mock_file, mock_copy, mock_version, setup_state_file):
    with patch('sys.argv', ['chunkwrap.py', '--prompt', 'Test prompt', '--file', 'test.txt', '--size', '10']):
        main()
    expected_wrapper = 'Test prompt\n"""\nShort\n"""'
    mock_copy.assert_called_with(expected_wrapper)

def test_state_file_persistence(setup_state_file):
    write_state(7)
    assert read_state() == 7
    write_state(10)
    assert read_state() == 10

@patch('sys.argv', ['chunkwrap.py', '--prompt', 'Test prompt', '--file', 'nonexistent.txt'])
def test_main_file_not_found():
    with pytest.raises(FileNotFoundError):
        main()

def test_chunk_file_various_sizes():
    text = "Hello World"
    chunks = chunk_file(text, 1)
    assert len(chunks) == 11
    assert chunks[0] == "H"
    assert chunks[-1] == "d"

    chunks = chunk_file(text, len(text))
    assert chunks == ["Hello World"]

    chunks = chunk_file(text, 1000)
    assert chunks == ["Hello World"]
