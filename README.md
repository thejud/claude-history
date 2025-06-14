# Claude History

A command-line utility to extract and format conversation history from Claude Code session files.

## Overview

Claude History parses JSONL session files stored by Claude Code and outputs a chronologically ordered markdown report of your conversations. You can view just user prompts or include assistant responses in a structured format.

## Installation

1. Clone or download the repository
2. Make the script executable:
   ```bash
   chmod +x claude_history.py
   ```

## Usage

### Basic Commands

```bash
# Extract prompts from current directory project
python3 claude_history.py

# Extract prompts from specific project
python3 claude_history.py ~/my-project

# Include assistant responses
python3 claude_history.py --agent ~/my-project

# Output without timestamps (still chronologically sorted)
python3 claude_history.py --nodate ~/my-project

# Combine flags
python3 claude_history.py -a -N ~/my-project  # Agent responses without timestamps
```

### Command Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--agent` | `-a` | Include assistant responses in output |
| `--nodate` | `-N` | Print messages without timestamps |
| `--help` | `-h` | Show help message |

## Output Formats

### User Prompts Only (Default)
```markdown
# Claude Code Session History

Generated on: 2024-01-01 12:00:00

- 1. **2024-01-01 10:00:00** - Hello, can you help me with Python?
- 2. **2024-01-01 10:02:00** - How do I parse JSON files?
- 3. **2024-01-01 10:04:00** - What about error handling?
```

### With Assistant Responses (`--agent`)
```markdown
# Claude Code Session History

Generated on: 2024-01-01 12:00:00

## 1. **2024-01-01 10:00:00**
**Prompt:** Hello, can you help me with Python?

**Response:** I'd be happy to help you with Python! What specific task are you working on?

## 2. **2024-01-01 10:02:00**
**Prompt:** How do I parse JSON files?

**Response:** You can use Python's built-in json module. Here's how...
```

## How It Works

Claude History works by:

1. **Path Resolution**: Converts your project path to Claude's internal naming convention and locates session files in `~/.claude/projects/`
2. **Data Extraction**: Parses JSONL files to extract user messages and optionally assistant responses
3. **Chronological Sorting**: Orders all messages by timestamp across multiple session files
4. **Formatted Output**: Generates clean markdown output with timestamps and structured conversation format

## Development

### Running Tests

```bash
# Run all tests
python3 run_tests.py

# Run specific test suites
python3 run_tests.py unit           # Unit tests only
python3 run_tests.py integration    # Integration tests only

# Run individual test files
python3 test_claude_history.py      # Core functionality tests
python3 test_end_to_end.py          # End-to-end workflow tests
```

### Project Structure

```
claude_history/
├── claude_history.py           # Main script
├── test_claude_history.py      # Unit tests
├── test_end_to_end.py          # End-to-end tests
├── test_integration.py         # Integration tests
├── run_tests.py                # Test runner utility
├── tests/
│   └── fixtures/               # Sample JSONL test files
├── CLAUDE.md                   # Development guidance
└── README.md                   # This file
```

## Requirements

- Python 3.6+
- No external dependencies (uses only standard library)

## Author

Created by **Jud Dagnall** with **Claude Code**

## License

This project is provided as-is for educational and personal use.

## Contributing

Feel free to submit issues and pull requests to improve the tool!