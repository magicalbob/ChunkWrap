import os
import io
import json
import builtins
import pyperclip
import pytest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

# chunkwrap imports
from chunkwrap import output as cw_output
from chunkwrap import cli as cw_cli
from chunkwrap import config as cw_config
from chunkwrap import file_handler as cw_fh
from chunkwrap import security as cw_sec
from chunkwrap import state as cw_state
from chunkwrap import chunking as cw_chunk
from chunkwrap import utils as cw_utils
from chunkwrap.core import ChunkProcessor


# -----------------------
# chunking.py
# -----------------------

def test_validate_chunk_size_bounds():
    with pytest.raises(ValueError):
        cw_chunk.validate_chunk_size(0)
    with pytest.raises(ValueError):
        cw_chunk.validate_chunk_size(-1)
    with pytest.raises(ValueError):
        cw_chunk.validate_chunk_size(1_000_001)
    assert cw_chunk.validate_chunk_size(1) is True

def test_chunk_at_boundaries_delegates_and_custom_boundaries():
    txt = "abcdef"
    # default path
    assert cw_chunk.chunk_at_boundaries(txt, 2) == ["ab","cd","ef"]
    # explicit boundary chars (exercise the branch that sets boundary_chars != None)
    assert cw_chunk.chunk_at_boundaries(txt, 3, boundary_chars=["."]) == ["abc","def"]

def test_get_chunk_info_edges():
    chunks = ["a","b","c"]
    assert cw_chunk.get_chunk_info([], 0) is None
    assert cw_chunk.get_chunk_info(chunks, -1) is None
    assert cw_chunk.get_chunk_info(chunks, 3) is None
    info = cw_chunk.get_chunk_info(chunks, 1)
    assert info["index"] == 1 and info["total"] == 3 and not info["is_first"] and not info["is_last"]


# -----------------------
# utils.py
# -----------------------

def test_validate_encoding_true_and_errors(tmp_path, monkeypatch):
    p = tmp_path / "ok.txt"
    p.write_text("hi", encoding="utf-8")
    assert cw_utils.validate_encoding(str(p)) is True

    # UnicodeDecodeError path
    m = mock_open()
    m.return_value.read.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "boom")
    with patch("builtins.open", m):
        assert cw_utils.validate_encoding("x") is False

    # generic Exception path
    m2 = mock_open()
    m2.return_value.read.side_effect = Exception("nope")
    with patch("builtins.open", m2):
        assert cw_utils.validate_encoding("y") is False


# -----------------------
# file_handler.py
# -----------------------

def test_validate_file_paths_not_a_file_prints_warning():
    with patch("os.path.exists", return_value=True), \
         patch("os.path.isfile", return_value=False), \
         patch("builtins.print") as mp:
        paths = cw_fh.validate_file_paths(["/tmp/dir"])
        assert paths == []
        mp.assert_any_call("Warning: '/tmp/dir' is not a file, skipping...")

def test_read_files_handles_read_exception():
    with patch("os.path.exists", return_value=True), \
         patch("os.path.isfile", return_value=True), \
         patch("builtins.open", side_effect=IOError("denied")), \
         patch("builtins.print") as mp:
        out = cw_fh.read_files(["bad.txt"])
        assert out == "" or "FILE:" not in out
        mp.assert_any_call("Error reading file 'bad.txt': denied")


# -----------------------
# config.py
# -----------------------

#def test_get_config_dir_windows_branch(monkeypatch):
#    # Patch module-level os.name in config namespace
#    monkeypatch.setattr(cw_config.os, "name", "nt")
#    monkeypatch.setenv("APPDATA", "C:\\Users\\Test\\AppData\\Roaming")
#    d = cw_config.get_config_dir()
#    assert str(d).endswith("chunkwrap")

def test_get_config_dir_unix_branch(monkeypatch):
    monkeypatch.setattr(cw_config.os, "name", "posix")
    monkeypatch.setenv("XDG_CONFIG_HOME", "/home/test/.config")
    d = cw_config.get_config_dir()
    assert str(d).endswith("chunkwrap")

def test_load_config_creates_default_when_missing(tmp_path, monkeypatch):
    cfg_dir = tmp_path / "cfg"
    monkeypatch.setattr(cw_config, "get_config_dir", lambda: cfg_dir)
    # No file exists
    with patch("builtins.print") as mp:
        cfg = cw_config.load_config()
    assert cfg["default_chunk_size"] == 10000
    mp.assert_any_call(f"Created default configuration file at: {cfg_dir / 'config.json'}")

def test_load_config_updates_with_new_defaults(tmp_path, monkeypatch):
    cfg_dir = tmp_path / "cfg2"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cfg_file = cfg_dir / "config.json"
    cfg_file.write_text(json.dumps({"output": "stdout"}), encoding="utf-8")
    monkeypatch.setattr(cw_config, "get_config_dir", lambda: cfg_dir)
    with patch("builtins.print") as mp:
        cfg = cw_config.load_config()
    # Should merge in missing keys and rewrite file
    assert "intermediate_chunk_suffix" in cfg
    mp.assert_any_call("Configuration updated for JSON protocol v1.0")


# -----------------------
# security.py
# -----------------------

def test_validate_regex_patterns_drops_invalid():
    patterns = {"GOOD": r"abc+", "BAD": "("}
    valid = cw_sec.validate_regex_patterns(patterns)
    assert "GOOD" in valid and "BAD" not in valid

def test_mask_secrets_ignores_invalid_and_empty():
    text = "token: abc"
    # invalid pattern is dropped
    result = cw_sec.mask_secrets(text, {"BAD": "("})
    assert "MASKED" not in result
    # empty inputs
    assert cw_sec.mask_secrets("", {"A": "x"}) == ""
    assert cw_sec.mask_secrets("abc", {}) == "abc"
    assert cw_sec.mask_secrets("abc", None) == "abc"

def test_get_default_patterns_has_expected_keys():
    pats = cw_sec.get_default_patterns()
    for key in ["AWS_ACCESS_KEY", "SLACK_TOKEN", "GITHUB_TOKEN", "PRIVATE_KEY"]:
        assert key in pats


# -----------------------
# state.py
# -----------------------

def test_read_state_corrupt_file(tmp_path, monkeypatch):
    sf = tmp_path / ".chunkwrap_state"
    sf.write_text("not-an-int", encoding="utf-8")
    monkeypatch.setattr(cw_state, "STATE_FILE", str(sf))
    assert cw_state.read_state() == 0  # corrupt -> 0

def test_validate_state_bounds():
    assert cw_state.validate_state(0, 3) is True
    assert cw_state.validate_state(2, 3) is True
    assert cw_state.validate_state(-1, 3) is False
    assert cw_state.validate_state(3, 3) is False


# -----------------------
# output.py
# -----------------------

def _mk_args(files, last=False, no_suffix=False, output="stdout"):
    class A: pass
    a = A()
    a.file = files
    a.lastprompt = None
    a.no_suffix = no_suffix
    a.output = output
    a.output_file = None
    a.llm_mode = False
    return a

def test_format_chunk_wrapper_fallback_paths():
    info_mid = {"index": 0, "total": 2, "is_first": True, "is_last": False, "chunk": "X"}
    txt = cw_output.format_chunk_wrapper("P", "BODY", info_mid, args=None, config=None)
    assert "chunk 1 of 2" in txt and "BODY" in txt

    info_last = {"index": 1, "total": 2, "is_first": False, "is_last": True, "chunk": "Y"}
    txt2 = cw_output.format_chunk_wrapper("P", "BODY", info_last, args=None, config=None)
    assert '"""' in txt2 and "BODY" in txt2

def test_format_json_wrapper_structure(monkeypatch):
    args = _mk_args(["a.txt"])
    info = {"index": 0, "total": 1, "is_first": True, "is_last": True, "chunk": "C"}
    out = cw_output.format_json_wrapper("PROMPT", "BODY", info, args, config={"x":1})
    data = json.loads(out)
    assert data["metadata"]["protocol_version"] == "1.0"
    assert data["prompt"] == "PROMPT"
    assert data["content"] == "BODY"

def test_handle_stdout_output_captures(capsys):
    assert cw_output.handle_stdout_output("X")
    assert "X" in capsys.readouterr().out

def test_handle_file_output_success(tmp_path, capsys):
    p = tmp_path / "out.json"
    info = {"index": 0, "total": 1}
    assert cw_output.handle_file_output("C", str(p), info)
    assert p.read_text(encoding="utf-8") == "C"
    assert "written to" in capsys.readouterr().out

def test_handle_file_output_error(capsys):
    with patch("builtins.open", side_effect=IOError("nope")):
        ok = cw_output.handle_file_output("C", "/root/x", {"index":0,"total":9})
        assert not ok
        assert "Error writing to file" in capsys.readouterr().out


# -----------------------
# cli.py
# -----------------------

def test_cli_output_file_requires_output_file_flag(monkeypatch):
    # Ensure config doesn't predefine output_file
    monkeypatch.setattr(cw_cli, "load_config", lambda: {"default_chunk_size": 10_000, "output": "clipboard", "output_file": None})
    with patch("sys.argv", ["chunkwrap.py", "--prompt", "p", "--file", "foo.txt", "--output", "file"]):
        with pytest.raises(SystemExit):
            cw_cli.main()

def test_validate_args_reset_conflict_branch():
    # Hit the branch directly (main short-circuits with --reset)
    cfg = {"default_chunk_size": 10000}
    parser = cw_cli.create_parser()
    args = parser.parse_args(["--reset", "--prompt", "x"])
    err = cw_cli.validate_args(args, cfg)
    assert err == "--reset cannot be used with other arguments"


# -----------------------
# core.py (budget and end-state branches)
# -----------------------

def test_processor_size_too_small_triggers_error(monkeypatch, capsys):
    cfg = {"default_chunk_size": 10000, "intermediate_chunk_suffix": "", "final_chunk_suffix": "", "output":"stdout", "output_file": None}
    proc = ChunkProcessor(cfg)

    # Make read_files return non-empty; use absurdly tiny size so overhead doesn't fit.
    monkeypatch.setattr("chunkwrap.core.read_files", lambda files: "x")
    class Args:
        file = ["a.txt"]
        prompt = "p"
        lastprompt = None
        size = 1  # smaller than wrapper overhead
        no_suffix = False
        output = "stdout"
        output_file = None
        llm_mode = False
    proc.process_files(Args)
    out = capsys.readouterr().out
    assert "Error: Current wrapper/metadata exceeds --size" in out

def test_processor_all_chunks_processed_message(monkeypatch, capsys, tmp_path):
    cfg = {"default_chunk_size": 10000, "intermediate_chunk_suffix": "", "final_chunk_suffix": "", "output":"stdout", "output_file": None}
    proc = ChunkProcessor(cfg)

    # Make one tiny chunk succeed
    monkeypatch.setattr("chunkwrap.core.read_files", lambda files: "hello")
    # Force state to 1 while total_chunks == 1 -> "All chunks processed!"
    sf = tmp_path / ".chunkwrap_state"
    sf.write_text("1", encoding="utf-8")
    monkeypatch.setattr("chunkwrap.state.STATE_FILE", str(sf))

    class Args:
        file = ["a.txt"]
        prompt = "p"
        lastprompt = None
        size = 10_000
        no_suffix = False
        output = "stdout"
        output_file = None
        llm_mode = False

    proc.process_files(Args)
    assert "All chunks processed!" in capsys.readouterr().out
