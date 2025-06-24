"""Secret masking and security features for chunkwrap."""

import os
import json
import re

TRUFFLEHOG_REGEX_FILE = 'truffleHogRegexes.json'


def load_trufflehog_regexes():
    """Load TruffleHog regex patterns from JSON file."""
    if not os.path.exists(TRUFFLEHOG_REGEX_FILE):
        return {}
    
    try:
        with open(TRUFFLEHOG_REGEX_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load TruffleHog regex file {TRUFFLEHOG_REGEX_FILE}: {e}")
        return {}


def validate_regex_patterns(patterns):
    """Validate that regex patterns are compilable."""
    valid_patterns = {}
    
    for key, pattern in patterns.items():
        try:
            re.compile(pattern)
            valid_patterns[key] = pattern
        except re.error as e:
            print(f"Warning: Invalid regex pattern for '{key}': {e}")
            continue
    
    return valid_patterns


def mask_secrets(text, regex_patterns):
    """Mask sensitive information using TruffleHog regex patterns."""
    if not text or not regex_patterns:
        return text
    
    # Validate patterns before using them
    valid_patterns = validate_regex_patterns(regex_patterns)
    
    masked_text = text
    for key, pattern in valid_patterns.items():
        try:
            masked_text = re.sub(pattern, f'***MASKED-{key}***', masked_text)
        except re.error as e:
            print(f"Warning: Error applying regex pattern '{key}': {e}")
            continue
    
    return masked_text


def get_default_patterns():
    """Get a set of default security patterns."""
    return {
        "AWS_ACCESS_KEY": r"AKIA[0-9A-Z]{16}",
        "SLACK_TOKEN": r"xox[baprs]-[0-9a-zA-Z]{10,48}",
        "GITHUB_TOKEN": r"ghp_[a-zA-Z0-9]{36}",
        "PRIVATE_KEY": r"-----BEGIN (RSA |)PRIVATE KEY-----"
    }
