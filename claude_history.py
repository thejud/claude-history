#!/usr/bin/env python3

"""
Claude History - Extract and format prompts from Claude Code session files

Usage:
    claude-history [options] [project-path]
    claude-history                    # Use current directory project
    claude-history ~/my-project       # Use specific project directory
    claude-history -N                 # Output without timestamps
    claude-history --nodate ~/project # Specific project without timestamps
    claude-history -a                 # Include assistant responses
    claude-history --agent ~/project  # Include responses for specific project

Examples:
    claude-history
    claude-history ~/s/my-app
    claude-history -N ~/s/my-app
    claude-history -a ~/s/my-app
    claude-history -a -N ~/s/my-app   # Agent responses without timestamps
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional


def get_claude_project_path(project_dir: Optional[str] = None) -> Path:
    """
    Get the Claude session files directory for a project.
    
    Args:
        project_dir: Project directory path, uses current directory if None
        
    Returns:
        Path to Claude session files directory
    """
    if project_dir is None:
        project_path = Path.cwd()
    else:
        project_path = Path(project_dir).resolve()
    
    # Convert path to Claude's naming convention (replace / with -)
    escaped_path = str(project_path).replace('/', '-')
    claude_projects_dir = Path.home() / '.claude' / 'projects'
    
    # Look for exact match first
    claude_dir = claude_projects_dir / escaped_path
    if claude_dir.exists():
        return claude_dir
    
    # If not found, search for matching directories
    if claude_projects_dir.exists():
        project_name = project_path.name
        # Try with both underscores and dashes
        search_names = [project_name, project_name.replace('_', '-'), project_name.replace('-', '_')]
        
        for dir_path in claude_projects_dir.iterdir():
            if dir_path.is_dir():
                for search_name in search_names:
                    if search_name in dir_path.name:
                        return dir_path
    
    # Return the expected path if no match found
    return claude_dir


def extract_prompts(claude_dir: Path, include_agent: bool = False) -> List[tuple]:
    """
    Extract user prompts and optionally assistant responses from Claude session files with timestamps.
    
    Args:
        claude_dir: Directory containing Claude session files
        include_agent: Whether to include assistant responses
        
    Returns:
        List of tuples (timestamp, content, message_type) sorted chronologically
    """
    if not claude_dir.exists():
        print(f"Error: No Claude session files found for this project", file=sys.stderr)
        print(f"Expected directory: {claude_dir}", file=sys.stderr)
        sys.exit(1)
    
    session_files = list(claude_dir.glob('*.jsonl'))
    if not session_files:
        print(f"Error: No session files found in {claude_dir}", file=sys.stderr)
        sys.exit(1)
    
    messages_with_timestamps = []
    
    for session_file in session_files:
        with open(session_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    message_type = data.get('type')
                    
                    if message_type == 'user' and isinstance(data.get('message', {}).get('content'), str):
                        timestamp = data.get('timestamp', '')
                        content = data['message']['content']
                        messages_with_timestamps.append((timestamp, content, 'user'))
                    elif include_agent and message_type == 'assistant':
                        # Handle assistant messages with nested content structure
                        message_content = data.get('message', {}).get('content')
                        if isinstance(message_content, list) and len(message_content) > 0:
                            # Extract text from content array
                            text_parts = []
                            for content_item in message_content:
                                if (isinstance(content_item, dict) and 
                                    content_item.get('type') == 'text' and 
                                    'text' in content_item):
                                    text_parts.append(content_item['text'])
                            
                            if text_parts:
                                timestamp = data.get('timestamp', '')
                                content = '\n'.join(text_parts)
                                messages_with_timestamps.append((timestamp, content, 'assistant'))
                except json.JSONDecodeError:
                    continue
    
    # Sort by timestamp
    messages_with_timestamps.sort(key=lambda x: x[0])
    
    return messages_with_timestamps


def format_output(messages_with_timestamps: List[tuple], show_dates: bool = True, include_agent: bool = False) -> None:
    """
    Format and print messages as markdown in chronological order.
    
    Args:
        messages_with_timestamps: List of tuples (timestamp, content, message_type)
        show_dates: Whether to include timestamps in output
        include_agent: Whether assistant responses are included
    """
    print("# Claude Code Session History")
    print()
    print(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if include_agent:
        # Group messages into conversation pairs
        i = 1
        for idx, (timestamp, content, message_type) in enumerate(messages_with_timestamps):
            if message_type == 'user':
                # Format timestamp for display
                if show_dates:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except (ValueError, AttributeError):
                        formatted_time = timestamp
                    
                    print(f"## {i}. **{formatted_time}**")
                else:
                    print(f"## {i}.")
                
                print(f"**Prompt:** {content}")
                print()
                
                # Look for the next assistant response
                if idx + 1 < len(messages_with_timestamps):
                    next_timestamp, next_content, next_type = messages_with_timestamps[idx + 1]
                    if next_type == 'assistant':
                        print(f"**Response:** {next_content}")
                        print()
                
                i += 1
    else:
        # Original format for user messages only
        user_count = 1
        for timestamp, content, message_type in messages_with_timestamps:
            if message_type == 'user':
                if show_dates:
                    # Format timestamp for display (convert from ISO format)
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except (ValueError, AttributeError):
                        formatted_time = timestamp
                    
                    print(f"- {user_count}. **{formatted_time}** - {content}")
                else:
                    print(f"- {user_count}. {content}")
                
                user_count += 1


def main() -> None:
    """Main function to handle command line arguments and process prompts."""
    parser = argparse.ArgumentParser(
        description="Extract and format prompts from Claude Code session files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Use current directory project
  %(prog)s ~/my-project       # Use specific project directory
  %(prog)s -N                 # Output without timestamps
  %(prog)s --nodate ~/project # Specific project without timestamps
  %(prog)s -a                 # Include assistant responses
  %(prog)s --agent ~/project  # Include responses for specific project
        """
    )
    
    parser.add_argument(
        "project_path",
        nargs="?",
        help="Project directory path (defaults to current directory)"
    )
    
    parser.add_argument(
        "-N", "--nodate",
        action="store_true",
        help="Print messages without timestamps (still sorted chronologically)"
    )
    
    parser.add_argument(
        "-a", "--agent",
        action="store_true",
        help="Include assistant responses in output with prompt/response format"
    )
    
    args = parser.parse_args()
    
    claude_project_path = get_claude_project_path(args.project_path)
    messages_with_timestamps = extract_prompts(claude_project_path, include_agent=args.agent)
    format_output(messages_with_timestamps, show_dates=not args.nodate, include_agent=args.agent)


if __name__ == "__main__":
    main()