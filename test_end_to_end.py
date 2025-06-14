#!/usr/bin/env python3

import json
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from claude_history import get_claude_project_path, extract_prompts, format_output, main


class TestEndToEnd(unittest.TestCase):
    """End-to-end tests for the claude-history tool."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

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

    @patch('claude_history.get_claude_project_path')
    @patch('sys.argv', ['claude_history.py'])
    def test_main_function_with_dates(self, mock_get_path):
        """Test main function with date formatting."""
        self.create_test_session_file()
        mock_get_path.return_value = self.temp_path
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            main()
            output = mock_stdout.getvalue()
            
            self.assertIn("Claude Code Session History", output)
            self.assertIn("Hello, how are you?", output)
            self.assertIn("Can you help me with Python?", output)
            self.assertIn("2024-01-01", output)
            # Should not include assistant messages
            self.assertNotIn("I'm doing well, thank you!", output)

    @patch('claude_history.get_claude_project_path')
    @patch('sys.argv', ['claude_history.py', '--nodate'])
    def test_main_function_without_dates(self, mock_get_path):
        """Test main function without date formatting."""
        self.create_test_session_file()
        mock_get_path.return_value = self.temp_path
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            main()
            output = mock_stdout.getvalue()
            
            self.assertIn("Hello, how are you?", output)
            self.assertIn("Can you help me with Python?", output)
            # Should not contain timestamp formatting
            self.assertNotIn("2024-01-01", output)
            self.assertNotIn("**", output)  # No bold timestamp markers

    @patch('claude_history.get_claude_project_path')
    @patch('sys.argv', ['claude_history.py', '-N'])
    def test_main_function_short_nodate_flag(self, mock_get_path):
        """Test main function with -N flag."""
        self.create_test_session_file()
        mock_get_path.return_value = self.temp_path
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            main()
            output = mock_stdout.getvalue()
            
            self.assertIn("Hello, how are you?", output)
            self.assertNotIn("2024-01-01", output)

    def test_full_workflow_with_multiple_files(self):
        """Test the complete workflow with multiple session files."""
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
        
        # Test extract_prompts function
        messages = extract_prompts(self.temp_path)
        
        # Should be in chronological order
        expected = [
            ("2024-01-01T09:00:00Z", "Earlier message", "user"),
            ("2024-01-01T10:00:00Z", "Hello, how are you?", "user"),
            ("2024-01-01T10:02:00Z", "Can you help me with Python?", "user")
        ]
        
        self.assertEqual(messages, expected)
        
        # Test format_output with dates
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            format_output(messages, show_dates=True)
            output = mock_stdout.getvalue()
            
            lines = output.split('\n')
            # Find the lines with prompts
            prompt_lines = [line for line in lines if 'message' in line.lower() or 'earlier' in line.lower() or 'hello' in line.lower() or 'python' in line.lower()]
            
            # Check chronological order in output
            self.assertTrue(any("Earlier message" in line for line in lines))
            self.assertTrue(any("Hello, how are you?" in line for line in lines))
            self.assertTrue(any("Can you help me with Python?" in line for line in lines))

    def test_edge_cases(self):
        """Test edge cases like malformed JSON."""
        # Create session file with mixed valid/invalid content
        session_file = self.temp_path / 'mixed.jsonl'
        with open(session_file, 'w') as f:
            # Valid line
            f.write(json.dumps({
                "type": "user",
                "timestamp": "2024-01-01T10:00:00Z",
                "message": {"content": "Valid message"}
            }) + '\n')
            
            # Invalid JSON line
            f.write('invalid json line\n')
            
            # Non-user message (should be ignored)
            f.write(json.dumps({
                "type": "assistant",
                "timestamp": "2024-01-01T10:01:00Z",
                "message": {"content": "Assistant message"}
            }) + '\n')
            
            # Another valid user message
            f.write(json.dumps({
                "type": "user",
                "timestamp": "2024-01-01T10:02:00Z",
                "message": {"content": "Another valid message"}
            }) + '\n')
        
        prompts = extract_prompts(self.temp_path)
        
        expected = [
            ("2024-01-01T10:00:00Z", "Valid message", "user"),
            ("2024-01-01T10:02:00Z", "Another valid message", "user")
        ]
        
        self.assertEqual(prompts, expected)

    @patch('claude_history.get_claude_project_path')
    @patch('sys.argv', ['claude_history.py', '--agent'])
    def test_main_function_with_agent_responses(self, mock_get_path):
        """Test main function with agent responses."""
        # Create session file with user and assistant messages
        session_file = self.temp_path / 'session1.jsonl'
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
            }
        ]
        
        with open(session_file, 'w') as f:
            for item in test_data:
                f.write(json.dumps(item) + '\n')
        
        mock_get_path.return_value = self.temp_path
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            main()
            output = mock_stdout.getvalue()
            
            self.assertIn("Claude Code Session History", output)
            self.assertIn("**Prompt:** Hello, how are you?", output)
            self.assertIn("**Response:** I'm doing well, thank you!", output)
            self.assertIn("## 1.", output)  # Section header


if __name__ == '__main__':
    unittest.main()