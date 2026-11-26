# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python command-line utility called `claude-history` that extracts and formats user prompts and optionally assistant responses from Claude Code session files. The tool parses JSONL session files stored in `~/.claude/projects/` and outputs a chronologically ordered markdown report of conversations.

## Commands

### Running the Tool
```bash
python3 claude_history.py                    # Use current directory project
python3 claude_history.py ~/my-project       # Use specific project directory
python3 claude_history.py -N                 # Output without timestamps
python3 claude_history.py --nodate ~/project # Specific project without timestamps
python3 claude_history.py -a                 # Include assistant responses
python3 claude_history.py --agent ~/project  # Include responses for specific project
python3 claude_history.py -a -N ~/project    # Agent responses without timestamps
```

### Making Executable
```bash
chmod +x claude_history.py
./claude_history.py
```

### Running Tests
```bash
python3 test_claude_history.py               # Unit tests
python3 test_end_to_end.py                   # End-to-end tests
python3 run_tests.py                         # All tests
python3 run_tests.py unit                    # Unit tests only
python3 run_tests.py integration             # Integration tests only
```

## Architecture

The application follows a functional design with four main components:

1. **Path Resolution (`get_claude_project_path`)**: Converts project paths to Claude's internal naming convention (replacing every non-alphanumeric character with `-`) and returns the exact session directory in `~/.claude/projects/`, with no similar-name fallback

2. **Data Extraction (`extract_prompts`)**: Parses JSONL files to extract user messages and optionally assistant responses with timestamps, filtering for appropriate message types with string content

3. **Output Formatting (`format_output`)**: Generates markdown output with chronologically sorted messages, supporting both simple list format (user-only) and conversational format (with assistant responses), converting ISO timestamps to readable format

4. **CLI Interface (`main`)**: Handles command-line arguments using argparse with optional project path parameter

The tool expects Claude session files to be stored as JSONL format in the standard Claude projects directory structure.

## Testing

The project includes comprehensive tests:

- **Unit Tests** (`test_claude_history.py`): Test individual functions with mocked dependencies
- **End-to-End Tests** (`test_end_to_end.py`): Test complete workflows with mocked file system
- **Integration Tests** (`test_integration.py`): Test CLI functionality with subprocess calls
- **Test Fixtures** (`tests/fixtures/`): Sample JSONL files for testing various scenarios
- **Test Runner** (`run_tests.py`): Utility to run specific test suites

Key test scenarios covered:
- Path resolution (exact match only)
- JSONL parsing with malformed data handling  
- Chronological sorting across multiple files
- CLI argument parsing including `--nodate/-N` and `--agent/-a` flags
- Output formatting with and without timestamps
- Conversational formatting with prompt/response pairs
- Message type filtering (user vs assistant messages)