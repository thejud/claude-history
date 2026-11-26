#!/usr/bin/env python3

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class TestCLIIntegration(unittest.TestCase):
    """Integration tests for the command-line interface."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.script_path = Path(__file__).parent / 'claude_history.py'

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_test_session_file(self, filename='session1.jsonl'):
        """Create a test session file with sample data."""
        session_file = self.temp_path / filename
        test_data = [
            {
                "type": "user",
                "timestamp": "2024-01-01T10:00:00Z",
                "message": {"content": "Hello, how are you?"}
            },
            {
                "type": "assistant",
                "timestamp": "2024-01-01T10:01:00Z",
                "message": {"content": [{"type": "text", "text": "I'm doing well, thank you!"}]}
            },
            {
                "type": "user",
                "timestamp": "2024-01-01T10:02:00Z",
                "message": {"content": "Can you help me with Python?"}
            }
        ]
        
        with open(session_file, 'w') as f:
            for item in test_data:
                f.write(json.dumps(item) + '\n')
        
        return session_file

    def test_cli_basic_functionality(self):
        """Test basic CLI functionality with a project directory."""
        self.create_test_session_file()
        
        # Create a wrapper script that directly calls extract_prompts with temp path
        wrapper_script = f"""
import sys
sys.path.insert(0, {str(self.script_path.parent)!r})
from claude_history import extract_prompts, format_output
from pathlib import Path

messages = extract_prompts(Path({str(self.temp_path)!r}))
format_output(messages, show_dates=True, include_agent=False)
"""
        
        result = subprocess.run(
            [sys.executable, '-c', wrapper_script],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("Claude Code Session History", result.stdout)
        self.assertIn("Hello, how are you?", result.stdout)
        self.assertIn("Can you help me with Python?", result.stdout)
        # Should not include assistant messages
        self.assertNotIn("I'm doing well, thank you!", result.stdout)

    def test_cli_with_nodate_flag(self):
        """Test CLI with --nodate flag."""
        self.create_test_session_file()
        
        wrapper_script = f"""
import sys
sys.path.insert(0, {str(self.script_path.parent)!r})
from claude_history import extract_prompts, format_output
from pathlib import Path

messages = extract_prompts(Path({str(self.temp_path)!r}))
format_output(messages, show_dates=False, include_agent=False)
"""
        
        result = subprocess.run(
            [sys.executable, '-c', wrapper_script],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("Hello, how are you?", result.stdout)
        # Should not contain timestamp formatting
        self.assertNotIn("2024-01-01", result.stdout)
        self.assertNotIn("**", result.stdout)  # No bold timestamp markers

    def test_cli_with_short_nodate_flag(self):
        """Test CLI with -N flag."""
        self.create_test_session_file()
        
        wrapper_script = f"""
import sys
sys.path.insert(0, {str(self.script_path.parent)!r})
from claude_history import extract_prompts, format_output
from pathlib import Path

messages = extract_prompts(Path({str(self.temp_path)!r}))
format_output(messages, show_dates=False, include_agent=False)
"""
        
        result = subprocess.run(
            [sys.executable, '-c', wrapper_script],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("Hello, how are you?", result.stdout)
        self.assertNotIn("2024-01-01", result.stdout)

    def test_cli_nonexistent_directory(self):
        """Test CLI with nonexistent directory."""
        nonexistent_path = self.temp_path / 'nonexistent'
        
        result = subprocess.run(
            [sys.executable, str(self.script_path), str(nonexistent_path)],
            capture_output=True,
            text=True
        )
        
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("No Claude session files found", result.stderr)

    def test_cli_help_flag(self):
        """Test CLI help flag."""
        result = subprocess.run(
            [sys.executable, str(self.script_path), '--help'],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("Extract and format prompts", result.stdout)
        self.assertIn("--nodate", result.stdout)
        self.assertIn("-N", result.stdout)

    def test_cli_multiple_session_files(self):
        """Test CLI with multiple session files."""
        # Create first session file
        self.create_test_session_file('session1.jsonl')
        
        # Create second session file with different timestamp
        session_file2 = self.temp_path / 'session2.jsonl'
        test_data2 = [
            {
                "type": "user",
                "timestamp": "2024-01-01T09:00:00Z",
                "message": {"content": "Earlier message"}
            }
        ]
        
        with open(session_file2, 'w') as f:
            for item in test_data2:
                f.write(json.dumps(item) + '\n')
        
        wrapper_script = f"""
import sys
sys.path.insert(0, {str(self.script_path.parent)!r})
from claude_history import extract_prompts, format_output
from pathlib import Path

messages = extract_prompts(Path({str(self.temp_path)!r}))
format_output(messages, show_dates=True, include_agent=False)
"""
        
        result = subprocess.run(
            [sys.executable, '-c', wrapper_script],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        # Check chronological order
        output_lines = result.stdout.split('\n')
        earlier_line = next((line for line in output_lines if "Earlier message" in line), None)
        hello_line = next((line for line in output_lines if "Hello, how are you?" in line), None)
        
        self.assertIsNotNone(earlier_line)
        self.assertIsNotNone(hello_line)
        
        # Earlier message should appear first in output
        earlier_index = output_lines.index(earlier_line)
        hello_index = output_lines.index(hello_line)
        self.assertLess(earlier_index, hello_index)


if __name__ == '__main__':
    unittest.main()