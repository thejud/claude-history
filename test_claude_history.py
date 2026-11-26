#!/usr/bin/env python3

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, mock_open

from claude_history import get_claude_project_path, extract_prompts, format_output


class TestGetClaudeProjectPath(unittest.TestCase):
    """Test cases for get_claude_project_path function."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch('claude_history.Path.home')
    def test_exact_match_exists(self, mock_home):
        """Test when exact escaped path exists."""
        mock_home.return_value = self.temp_path
        claude_projects_dir = self.temp_path / '.claude' / 'projects'
        claude_projects_dir.mkdir(parents=True)
        
        # On Windows resolve() adds the drive: C:\test\project -> C--test-project
        drive = Path('/').resolve().drive.replace(':', '-')
        expected_dir = claude_projects_dir / f'{drive}-test-project'
        expected_dir.mkdir()
        
        result = get_claude_project_path('/test/project')
        self.assertEqual(result, expected_dir)

    @patch('claude_history.Path.home')
    def test_similar_name_is_not_matched(self, mock_home):
        """Test that another project with a similar name is never returned."""
        mock_home.return_value = self.temp_path
        claude_projects_dir = self.temp_path / '.claude' / 'projects'
        claude_projects_dir.mkdir(parents=True)
        
        # A look-alike directory that must be ignored
        existing_dir = claude_projects_dir / 'some-prefix-my_project-suffix'
        existing_dir.mkdir()
        
        with patch('claude_history.Path.cwd', return_value=Path('/path/to/my-project')):
            result = get_claude_project_path()
            self.assertNotEqual(result, existing_dir)
            self.assertFalse(result.exists())

    @patch('claude_history.Path.home')
    def test_no_match_returns_expected_path(self, mock_home):
        """Test that non-existent path returns expected directory."""
        mock_home.return_value = self.temp_path
        claude_projects_dir = self.temp_path / '.claude' / 'projects'
        claude_projects_dir.mkdir(parents=True)
        
        project_path = '/nonexistent/project'
        result = get_claude_project_path(project_path)
        drive = Path('/').resolve().drive.replace(':', '-')
        expected = claude_projects_dir / f'{drive}-nonexistent-project'
        self.assertEqual(result, expected)

    @patch('claude_history.Path.cwd')
    def test_uses_current_directory_when_none(self, mock_cwd):
        """Test that current directory is used when project_dir is None."""
        mock_cwd.return_value = Path('/current/dir')
        
        with patch('claude_history.Path.home') as mock_home:
            mock_home.return_value = self.temp_path
            claude_projects_dir = self.temp_path / '.claude' / 'projects'
            claude_projects_dir.mkdir(parents=True)
            
            result = get_claude_project_path(None)
            expected = claude_projects_dir / '-current-dir'
            self.assertEqual(result, expected)


class TestExtractPrompts(unittest.TestCase):
    """Test cases for extract_prompts function."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_extract_prompts_success(self):
        """Test successful extraction of prompts from JSONL files."""
        # Create test JSONL file
        session_file = self.temp_path / 'session1.jsonl'
        test_data = [
            {
                "type": "user",
                "timestamp": "2024-01-01T10:00:00Z",
                "message": {"content": "First prompt"}
            },
            {
                "type": "assistant",
                "timestamp": "2024-01-01T10:01:00Z",
                "message": {"content": "Assistant response"}
            },
            {
                "type": "user",
                "timestamp": "2024-01-01T10:02:00Z",
                "message": {"content": "Second prompt"}
            }
        ]
        
        with open(session_file, 'w') as f:
            for item in test_data:
                f.write(json.dumps(item) + '\n')
        
        result = extract_prompts(self.temp_path)
        
        expected = [
            ("2024-01-01T10:00:00Z", "First prompt", "user"),
            ("2024-01-01T10:02:00Z", "Second prompt", "user")
        ]
        
        self.assertEqual(result, expected)

    def test_extract_prompts_chronological_order(self):
        """Test that prompts are returned in chronological order."""
        # Create test JSONL file with out-of-order timestamps
        session_file = self.temp_path / 'session1.jsonl'
        test_data = [
            {
                "type": "user",
                "timestamp": "2024-01-01T10:02:00Z",
                "message": {"content": "Third prompt"}
            },
            {
                "type": "user",
                "timestamp": "2024-01-01T10:00:00Z",
                "message": {"content": "First prompt"}
            },
            {
                "type": "user",
                "timestamp": "2024-01-01T10:01:00Z",
                "message": {"content": "Second prompt"}
            }
        ]
        
        with open(session_file, 'w') as f:
            for item in test_data:
                f.write(json.dumps(item) + '\n')
        
        result = extract_prompts(self.temp_path)
        
        expected = [
            ("2024-01-01T10:00:00Z", "First prompt", "user"),
            ("2024-01-01T10:01:00Z", "Second prompt", "user"),
            ("2024-01-01T10:02:00Z", "Third prompt", "user")
        ]
        
        self.assertEqual(result, expected)

    def test_extract_prompts_multiple_files(self):
        """Test extraction from multiple JSONL files."""
        # Create first session file
        session_file1 = self.temp_path / 'session1.jsonl'
        with open(session_file1, 'w') as f:
            data = {
                "type": "user",
                "timestamp": "2024-01-01T10:00:00Z",
                "message": {"content": "From file 1"}
            }
            f.write(json.dumps(data) + '\n')
        
        # Create second session file
        session_file2 = self.temp_path / 'session2.jsonl'
        with open(session_file2, 'w') as f:
            data = {
                "type": "user",
                "timestamp": "2024-01-01T09:00:00Z",
                "message": {"content": "From file 2"}
            }
            f.write(json.dumps(data) + '\n')
        
        result = extract_prompts(self.temp_path)
        
        expected = [
            ("2024-01-01T09:00:00Z", "From file 2", "user"),
            ("2024-01-01T10:00:00Z", "From file 1", "user")
        ]
        
        self.assertEqual(result, expected)

    def test_extract_prompts_invalid_json_ignored(self):
        """Test that invalid JSON lines are ignored."""
        session_file = self.temp_path / 'session1.jsonl'
        with open(session_file, 'w') as f:
            # Valid line
            f.write(json.dumps({
                "type": "user",
                "timestamp": "2024-01-01T10:00:00Z",
                "message": {"content": "Valid prompt"}
            }) + '\n')
            
            # Invalid JSON line
            f.write('invalid json line\n')
            
            # Another valid line
            f.write(json.dumps({
                "type": "user",
                "timestamp": "2024-01-01T10:01:00Z",
                "message": {"content": "Another valid prompt"}
            }) + '\n')
        
        result = extract_prompts(self.temp_path)
        
        expected = [
            ("2024-01-01T10:00:00Z", "Valid prompt", "user"),
            ("2024-01-01T10:01:00Z", "Another valid prompt", "user")
        ]
        
        self.assertEqual(result, expected)

    def test_extract_prompts_nonexistent_directory(self):
        """Test that nonexistent directory raises SystemExit."""
        nonexistent_path = self.temp_path / 'nonexistent'
        
        with self.assertRaises(SystemExit):
            extract_prompts(nonexistent_path)

    def test_extract_prompts_no_jsonl_files(self):
        """Test that directory with no JSONL files raises SystemExit."""
        # Create some non-JSONL files
        (self.temp_path / 'readme.txt').touch()
        (self.temp_path / 'config.json').touch()
        
        with self.assertRaises(SystemExit):
            extract_prompts(self.temp_path)

    def test_extract_prompts_with_agent_responses(self):
        """Test extraction including assistant responses."""
        session_file = self.temp_path / 'session1.jsonl'
        test_data = [
            {
                "type": "user",
                "timestamp": "2024-01-01T10:00:00Z",
                "message": {"content": "User prompt"}
            },
            {
                "type": "assistant",
                "timestamp": "2024-01-01T10:01:00Z",
                "message": {"content": [{"type": "text", "text": "Assistant response"}]}
            },
            {
                "type": "user",
                "timestamp": "2024-01-01T10:02:00Z",
                "message": {"content": "Another user prompt"}
            }
        ]
        
        with open(session_file, 'w') as f:
            for item in test_data:
                f.write(json.dumps(item) + '\n')
        
        # Test without agent responses
        result_no_agent = extract_prompts(self.temp_path, include_agent=False)
        expected_no_agent = [
            ("2024-01-01T10:00:00Z", "User prompt", "user"),
            ("2024-01-01T10:02:00Z", "Another user prompt", "user")
        ]
        self.assertEqual(result_no_agent, expected_no_agent)
        
        # Test with agent responses
        result_with_agent = extract_prompts(self.temp_path, include_agent=True)
        expected_with_agent = [
            ("2024-01-01T10:00:00Z", "User prompt", "user"),
            ("2024-01-01T10:01:00Z", "Assistant response", "assistant"),
            ("2024-01-01T10:02:00Z", "Another user prompt", "user")
        ]
        self.assertEqual(result_with_agent, expected_with_agent)

    def test_extract_prompts_mixed_content_types(self):
        """Test extraction with mixed content types in assistant messages."""
        session_file = self.temp_path / 'session1.jsonl'
        test_data = [
            {
                "type": "user",
                "timestamp": "2024-01-01T10:00:00Z",
                "message": {"content": "User prompt"}
            },
            {
                "type": "assistant",
                "timestamp": "2024-01-01T10:01:00Z",
                "message": {
                    "content": [
                        {"type": "text", "text": "Here's some text"},
                        {"type": "code", "language": "python", "content": "print('hello')"},
                        {"type": "text", "text": "More text after code"}
                    ]
                }
            }
        ]
        
        with open(session_file, 'w') as f:
            for item in test_data:
                f.write(json.dumps(item) + '\n')
        
        # Test that only text content is extracted
        result_with_agent = extract_prompts(self.temp_path, include_agent=True)
        expected_with_agent = [
            ("2024-01-01T10:00:00Z", "User prompt", "user"),
            ("2024-01-01T10:01:00Z", "Here's some text\nMore text after code", "assistant")
        ]
        self.assertEqual(result_with_agent, expected_with_agent)

    def test_extract_prompts_real_claude_format(self):
        """Test extraction with real Claude Code assistant message format."""
        session_file = self.temp_path / 'session1.jsonl'
        test_data = [
            {
                "type": "user",
                "timestamp": "2024-01-01T10:00:00Z",
                "message": {"content": "User prompt"}
            },
            {
                "type": "assistant",
                "timestamp": "2024-01-01T10:01:00Z",
                "message": {
                    "content": [
                        {"type": "text", "text": "Assistant response part 1"},
                        {"type": "text", "text": "Assistant response part 2"}
                    ]
                }
            }
        ]
        
        with open(session_file, 'w') as f:
            for item in test_data:
                f.write(json.dumps(item) + '\n')
        
        # Test with agent responses using real format
        result_with_agent = extract_prompts(self.temp_path, include_agent=True)
        expected_with_agent = [
            ("2024-01-01T10:00:00Z", "User prompt", "user"),
            ("2024-01-01T10:01:00Z", "Assistant response part 1\nAssistant response part 2", "assistant")
        ]
        self.assertEqual(result_with_agent, expected_with_agent)


class TestFormatOutput(unittest.TestCase):
    """Test cases for format_output function."""

    def test_format_output_with_dates(self):
        """Test output formatting with dates."""
        messages = [
            ("2024-01-01T10:00:00Z", "First prompt", "user"),
            ("2024-01-01T10:01:00Z", "Second prompt", "user")
        ]
        
        with patch('builtins.print') as mock_print:
            format_output(messages, show_dates=True)
            
            # Check that print was called with expected format
            calls = mock_print.call_args_list
            self.assertTrue(any("**2024-01-01 10:00:00**" in str(call) for call in calls))
            self.assertTrue(any("First prompt" in str(call) for call in calls))

    def test_format_output_without_dates(self):
        """Test output formatting without dates."""
        messages = [
            ("2024-01-01T10:00:00Z", "First prompt", "user"),
            ("2024-01-01T10:01:00Z", "Second prompt", "user")
        ]
        
        with patch('builtins.print') as mock_print:
            format_output(messages, show_dates=False)
            
            # Check that timestamps are not in output
            calls = mock_print.call_args_list
            output_text = ''.join(str(call) for call in calls)
            self.assertNotIn("2024-01-01", output_text)
            self.assertIn("1. First prompt", output_text)
            self.assertIn("2. Second prompt", output_text)

    def test_format_output_invalid_timestamp(self):
        """Test handling of invalid timestamps."""
        messages = [
            ("invalid-timestamp", "Prompt with bad timestamp", "user"),
            ("2024-01-01T10:00:00Z", "Prompt with good timestamp", "user")
        ]
        
        with patch('builtins.print') as mock_print:
            format_output(messages, show_dates=True)
            
            # Should not raise exception and should use raw timestamp
            calls = mock_print.call_args_list
            output_text = ''.join(str(call) for call in calls)
            self.assertIn("invalid-timestamp", output_text)

    def test_format_output_with_agent_responses(self):
        """Test output formatting with agent responses."""
        messages = [
            ("2024-01-01T10:00:00Z", "User prompt", "user"),
            ("2024-01-01T10:01:00Z", "Assistant response", "assistant"),
            ("2024-01-01T10:02:00Z", "Another prompt", "user")
        ]
        
        with patch('builtins.print') as mock_print:
            format_output(messages, show_dates=True, include_agent=True)
            
            # Check that both prompts and responses are included
            calls = mock_print.call_args_list
            output_text = ''.join(str(call) for call in calls)
            self.assertIn("**Prompt:** User prompt", output_text)
            self.assertIn("**Response:** Assistant response", output_text)
            self.assertIn("**Prompt:** Another prompt", output_text)

    def test_format_output_agent_without_dates(self):
        """Test agent output formatting without dates."""
        messages = [
            ("2024-01-01T10:00:00Z", "User prompt", "user"),
            ("2024-01-01T10:01:00Z", "Assistant response", "assistant")
        ]
        
        with patch('builtins.print') as mock_print:
            format_output(messages, show_dates=False, include_agent=True)
            
            # Check format without timestamps
            calls = mock_print.call_args_list
            output_text = ''.join(str(call) for call in calls)
            self.assertNotIn("2024-01-01", output_text)
            self.assertIn("## 1.", output_text)  # Section header without timestamp
            self.assertIn("**Prompt:** User prompt", output_text)
            self.assertIn("**Response:** Assistant response", output_text)


if __name__ == '__main__':
    unittest.main()