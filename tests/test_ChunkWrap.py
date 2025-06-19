import os
import sys
import pytest
import pyperclip
from unittest.mock import mock_open, patch, MagicMock
from importlib.metadata import PackageNotFoundError

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from chunkwrap.chunkwrap import read_state, write_state, reset_state, chunk_file, read_files, main

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

def test_read_files():
    """Test the new read_files function with mocked file operations"""
    mock_content = "Test file content"
    
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data=mock_content)):
            result = read_files(['test.txt'])
            expected = f"\n{'='*50}\nFILE: test.txt\n{'='*50}\n{mock_content}"
            assert result == expected

def test_read_files_multiple():
    """Test read_files with multiple files"""
    def mock_open_multiple(filename, *args, **kwargs):
        content_map = {
            'file1.txt': 'Content 1',
            'file2.txt': 'Content 2'
        }
        return mock_open(read_data=content_map.get(filename, ''))()
    
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', side_effect=mock_open_multiple):
            result = read_files(['file1.txt', 'file2.txt'])
            assert 'FILE: file1.txt' in result
            assert 'FILE: file2.txt' in result
            assert 'Content 1' in result
            assert 'Content 2' in result

def test_read_files_nonexistent():
    """Test read_files behavior with nonexistent files"""
    with patch('os.path.exists', return_value=False):
        with patch('builtins.print') as mock_print:
            result = read_files(['nonexistent.txt'])
            assert result == ''
            mock_print.assert_called_with("Warning: File 'nonexistent.txt' not found, skipping...")

# Patch get_version so tomllib.load isn't called (fixes binary open bug)
@patch('chunkwrap.chunkwrap.get_version', return_value="test")
@patch('pyperclip.copy')
@patch('chunkwrap.chunkwrap.read_files')
@patch('builtins.print')
def test_main_multiple_chunks(mock_print, mock_read_files, mock_copy, mock_version, setup_state_file):
    # Mock read_files to return content that will create 2 chunks when split at size 50
    mock_read_files.return_value = 'A' * 100
    
    with patch('sys.argv', ['chunkwrap.py', '--prompt', 'Test prompt', '--file', 'test.txt', '--size', '50']):
        main()
    
    expected_wrapper = 'Test prompt (chunk 1 of 2)\n"""\n' + 'A' * 50 + '\n"""'
    mock_copy.assert_called_with(expected_wrapper)
    mock_print.assert_any_call("Chunk 1 of 2 is now in the paste buffer.")
    mock_print.assert_any_call("Run this script again for the next chunk.")

@patch('chunkwrap.chunkwrap.get_version', return_value="test")
@patch('pyperclip.copy')
@patch('chunkwrap.chunkwrap.read_files')
@patch('builtins.print')
def test_main_single_chunk_no_counter(mock_print, mock_read_files, mock_copy, mock_version, setup_state_file):
    mock_read_files.return_value = 'Short'
    
    with patch('sys.argv', ['chunkwrap.py', '--prompt', 'Test prompt', '--file', 'test.txt', '--size', '10']):
        main()
    
    expected_wrapper = 'Test prompt\n"""\nShort\n"""'
    mock_copy.assert_called_with(expected_wrapper)

def test_state_file_persistence(setup_state_file):
    write_state(7)
    assert read_state() == 7
    write_state(10)
    assert read_state() == 10

@patch('chunkwrap.chunkwrap.read_files')
@patch('builtins.print')
def test_main_no_content_found(mock_print, mock_read_files):
    """Test behavior when no content is found in files"""
    mock_read_files.return_value = ''
    
    with patch('sys.argv', ['chunkwrap.py', '--prompt', 'Test prompt', '--file', 'nonexistent.txt']):
        main()
    
    mock_print.assert_called_with("No content found in any of the specified files.")

@patch('chunkwrap.chunkwrap.get_version', return_value="test")
@patch('pyperclip.copy')
@patch('chunkwrap.chunkwrap.read_files')
@patch('builtins.print')
def test_main_multiple_files_info(mock_print, mock_read_files, mock_copy, mock_version, setup_state_file):
    """Test that multiple file processing shows file info"""
    mock_read_files.return_value = 'Short content'
    
    with patch('sys.argv', ['chunkwrap.py', '--prompt', 'Test prompt', '--file', 'file1.txt', 'file2.txt']):
        main()
    
    mock_print.assert_any_call("Processing 2 files: file1.txt, file2.txt")

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

@patch('os.path.exists', return_value=True)
@patch('builtins.open', new_callable=mock_open, read_data='{"API":"API_KEY_[0-9]+"}')
def test_load_trufflehog_regexes_exists(mock_file, mock_exists):
    from chunkwrap.chunkwrap import load_trufflehog_regexes
    result = load_trufflehog_regexes()
    assert "API" in result
    assert result["API"] == "API_KEY_[0-9]+"

@patch('os.path.exists', return_value=False)
def test_load_trufflehog_regexes_missing(mock_exists):
    from chunkwrap.chunkwrap import load_trufflehog_regexes
    assert load_trufflehog_regexes() == {}

def test_mask_secrets_basic():
    from chunkwrap.chunkwrap import mask_secrets
    text = "API key: API_KEY_12345"
    regexes = {"API": "API_KEY_\\d+"}
    result = mask_secrets(text, regexes)
    assert "***MASKED-API***" in result

@patch('chunkwrap.chunkwrap.version', side_effect=PackageNotFoundError)
def test_get_version_fallback(mock_version):  # Make sure this line is indented properly
    from chunkwrap.chunkwrap import get_version
    assert get_version() == "unknown"

@patch('chunkwrap.chunkwrap.read_state', return_value=5)
@patch('chunkwrap.chunkwrap.chunk_file', return_value=['chunk1', 'chunk2', 'chunk3', 'chunk4', 'chunk5'])
@patch('chunkwrap.chunkwrap.read_files', return_value="some data")
@patch('chunkwrap.chunkwrap.load_trufflehog_regexes', return_value={})
@patch('builtins.print')
def test_main_all_chunks_processed(mock_print, mock_regexes, mock_read_files, mock_chunks, mock_state):
    with patch('sys.argv', ['chunkwrap.py', '--prompt', 'Prompt', '--file', 'file.txt']):
        from chunkwrap.chunkwrap import main
        main()
    mock_print.assert_any_call("All chunks processed! Use --reset to start over.")
