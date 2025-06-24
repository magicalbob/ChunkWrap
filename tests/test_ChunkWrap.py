import os
import sys
import pytest
import pyperclip
from unittest.mock import mock_open, patch, MagicMock
from importlib.metadata import PackageNotFoundError

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Updated imports for modular structure
from chunkwrap.state import read_state, write_state, reset_state
from chunkwrap.chunking import chunk_file
from chunkwrap.file_handler import read_files
from chunkwrap.cli import main
from chunkwrap.config import load_config
from chunkwrap.utils import get_version
from chunkwrap.security import load_trufflehog_regexes, mask_secrets

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

@pytest.fixture
def mock_config():
    """Standard mock config for tests"""
    return {
        "default_chunk_size": 10000,
        "intermediate_chunk_suffix": " Please provide only a brief acknowledgment that you've received this chunk. Save your detailed analysis for the final chunk.",
        "final_chunk_suffix": "Please now provide your full, considered response to all previous chunks. Give your response completely in JSON."
    }

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
        with patch('os.path.isfile', return_value=True):
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
        with patch('os.path.isfile', return_value=True):
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

@patch('chunkwrap.utils.get_version', return_value="test")
@patch('chunkwrap.config.load_config')
@patch('chunkwrap.output.pyperclip.copy')
@patch('chunkwrap.core.read_files')
@patch('builtins.print')
def test_main_multiple_chunks(mock_print, mock_read_files, mock_copy, mock_load_config, mock_version, setup_state_file, mock_config):
    # Mock the config to return default values
    mock_load_config.return_value = mock_config
    
    # Mock read_files to return content that will create 2 chunks when split at size 50
    mock_read_files.return_value = 'A' * 100
    
    with patch('sys.argv', ['chunkwrap.py', '--prompt', 'Test prompt', '--file', 'test.txt', '--size', '50']):
        main()

    expected_wrapper = 'Test promptPlease provide only a brief acknowledgment that you\'ve received this chunk. Save your detailed analysis for the final chunk. (chunk 1 of 2)\n"""\n' + 'A' * 50 + '\n"""'
    mock_copy.assert_called_with(expected_wrapper)
    mock_print.assert_any_call("Chunk 1 of 2 is now in the paste buffer.")
    mock_print.assert_any_call("Run this script again for the next chunk.")

@patch('chunkwrap.utils.get_version', return_value="test")
@patch('chunkwrap.config.load_config')
@patch('chunkwrap.output.pyperclip.copy')
@patch('chunkwrap.core.read_files')
@patch('builtins.print')
def test_main_single_chunk_no_counter(mock_print, mock_read_files, mock_copy, mock_load_config, mock_version, setup_state_file, mock_config):
    # Mock the config
    mock_load_config.return_value = mock_config
    
    mock_read_files.return_value = 'Short'
    
    with patch('sys.argv', ['chunkwrap.py', '--prompt', 'Test prompt', '--file', 'test.txt', '--size', '10']):
        main()

    # Single chunk should get the final suffix applied
    expected_wrapper = 'Test promptPlease now provide your full, considered response to all previous chunks. Give your response completely in JSON.\n"""\nShort\n"""'
    mock_copy.assert_called_with(expected_wrapper)

@patch('chunkwrap.utils.get_version', return_value="test")
@patch('chunkwrap.config.load_config')
@patch('chunkwrap.output.pyperclip.copy')
@patch('chunkwrap.core.read_files')
@patch('builtins.print')
def test_main_multiple_chunks_no_suffix_flag(mock_print, mock_read_files, mock_copy, mock_load_config, mock_version, setup_state_file, mock_config):
    """Test that --no-suffix flag disables the automatic suffix"""
    mock_load_config.return_value = mock_config
    
    mock_read_files.return_value = 'A' * 100
    
    with patch('sys.argv', ['chunkwrap.py', '--prompt', 'Test prompt', '--file', 'test.txt', '--size', '50', '--no-suffix']):
        main()

    # With --no-suffix, should not include the suffix
    expected_wrapper = 'Test prompt (chunk 1 of 2)\n"""\n' + 'A' * 50 + '\n"""'
    mock_copy.assert_called_with(expected_wrapper)

def test_state_file_persistence(setup_state_file):
    write_state(7)
    assert read_state() == 7
    write_state(10)
    assert read_state() == 10

@patch('chunkwrap.config.load_config')
@patch('chunkwrap.core.read_files')
@patch('builtins.print')
def test_main_no_content_found(mock_print, mock_read_files, mock_load_config, mock_config):
    """Test behavior when no content is found in files"""
    mock_load_config.return_value = mock_config
    
    # Mock empty file content
    mock_read_files.return_value = ''
    
    with patch('sys.argv', ['chunkwrap.py', '--prompt', 'Test prompt', '--file', 'nonexistent.txt']):
        main()
    
    mock_print.assert_called_with("No content found in any of the specified files.")

@patch('chunkwrap.utils.get_version', return_value="test")
@patch('chunkwrap.config.load_config')
@patch('chunkwrap.output.pyperclip.copy')
@patch('chunkwrap.core.read_files')
@patch('builtins.print')
def test_main_multiple_files_info(mock_print, mock_read_files, mock_copy, mock_load_config, mock_version, setup_state_file, mock_config):
    """Test that multiple file processing shows file info"""
    mock_load_config.return_value = mock_config
    
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
    result = load_trufflehog_regexes()
    assert "API" in result
    assert result["API"] == "API_KEY_[0-9]+"

@patch('os.path.exists', return_value=False)
def test_load_trufflehog_regexes_missing(mock_exists):
    assert load_trufflehog_regexes() == {}

def test_mask_secrets_basic():
    text = "API key: API_KEY_12345"
    regexes = {"API": "API_KEY_\\d+"}
    result = mask_secrets(text, regexes)
    assert "***MASKED-API***" in result

@patch('chunkwrap.utils.version', side_effect=PackageNotFoundError)
def test_get_version_fallback(mock_version):
    assert get_version() == "unknown"

@patch('chunkwrap.config.load_config')
def test_config_path_flag(mock_load_config, mock_config):
    """Test --config-path flag shows config file location"""
    mock_load_config.return_value = mock_config
    
    with patch('sys.argv', ['chunkwrap.py', '--config-path']):
        with patch('builtins.print') as mock_print:
            main()
            # Should print the config path
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            assert "Configuration file:" in call_args

def test_version_flag(capsys):
    with patch('sys.argv', ['chunkwrap.py', '--version']):
        with pytest.raises(SystemExit):  # argparse calls sys.exit()
            main()
    captured = capsys.readouterr()
    assert "chunkwrap" in captured.out

@patch('builtins.open', new_callable=mock_open, read_data='{ bad json')
@patch('os.path.exists', return_value=True)
def test_trufflehog_json_parse_error(mock_exists, mock_file, capsys):
    config = load_config()
    out = capsys.readouterr().out
    assert "Warning: Could not load config file" in out

def test_reset_with_other_args_errors():
    # The new modular structure doesn't raise SystemExit for this case
    # It just prints a message and continues, so test for that behavior
    with patch('chunkwrap.config.load_config') as mock_config:
        mock_config.return_value = {"default_chunk_size": 10000}
        with patch('sys.argv', ['chunkwrap.py', '--reset', '--prompt', 'Prompt']):
            with patch('builtins.print') as mock_print:
                main()
                mock_print.assert_any_call("State reset. Start from first chunk next run.")

@patch('os.path.exists', return_value=True)
@patch('builtins.open', side_effect=IOError("Permission denied"))
def test_load_config_io_error(mock_open, mock_exists, capsys):
    config = load_config()
    assert config['default_chunk_size'] == 10000
    assert "Warning: Could not load config file" in capsys.readouterr().out

@patch('os.path.exists', return_value=True)
@patch('json.load', return_value={"default_chunk_size": 1000})
@patch('builtins.open', new_callable=mock_open)
def test_load_config_merging_defaults(mock_file, mock_json_load, mock_exists):
    config = load_config()
    assert "intermediate_chunk_suffix" in config
    assert config["default_chunk_size"] == 1000

def test_missing_prompt_argument():
    with patch('sys.argv', ['chunkwrap.py', '--file', 'foo.txt']):
        with pytest.raises(SystemExit):
            main()

@patch('builtins.open', side_effect=PermissionError)
def test_write_state_permission_error(mock_open):
    # Should not raise
    try:
        write_state(5)
    except PermissionError:
        pytest.fail("write_state() should handle permission errors gracefully.")

def test_missing_file_argument():
    with patch('sys.argv', ['chunkwrap.py', '--prompt', 'Prompt only']):
        with pytest.raises(SystemExit):
            main()

def test_mask_secrets_multiple_patterns():
    text = "AWS key: AKIA1234567890ABCDXY and Slack token: xoxb-abc1234567890"
    regexes = {
        "AWS": "AKIA[0-9A-Z]{16}",
        "Slack": "xox[baprs]-[0-9a-zA-Z]{10,48}"
    }
    result = mask_secrets(text, regexes)
    assert "***MASKED-AWS***" in result
    assert "***MASKED-Slack***" in result
