"""
Utility functions for Desktop Automation Agent
"""

import os
from pathlib import Path
from typing import Optional


def expand_path(path: str) -> str:
    """
    Expand environment variables and user home directory in paths

    Args:
        path: Path string potentially containing variables

    Returns:
        Expanded path string
    """
    # Expand ~ to home directory
    path = os.path.expanduser(path)

    # Expand environment variables like %USERPROFILE%, $HOME, etc.
    path = os.path.expandvars(path)

    # Normalize path separators
    path = os.path.normpath(path)

    return path


def get_file_size_human(size_bytes: int) -> str:
    """
    Convert file size in bytes to human-readable format

    Args:
        size_bytes: Size in bytes

    Returns:
        Human-readable size string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0

    return f"{size_bytes:.1f} PB"


def is_safe_path(path: str, allowed_dirs: list) -> bool:
    """
    Check if a path is within allowed directories

    Args:
        path: Path to check
        allowed_dirs: List of allowed directory paths

    Returns:
        True if path is safe, False otherwise
    """
    path = Path(expand_path(path)).resolve()

    for allowed_dir in allowed_dirs:
        allowed_path = Path(expand_path(allowed_dir)).resolve()
        try:
            # Check if path is relative to allowed directory
            path.relative_to(allowed_path)
            return True
        except ValueError:
            continue

    return False


def sanitize_filename(filename: str) -> str:
    """
    Remove or replace invalid characters from filename

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Windows invalid characters
    invalid_chars = '<>:"/\\|?*'

    for char in invalid_chars:
        filename = filename.replace(char, '_')

    return filename


def confirm_action(prompt: str, default: bool = False) -> bool:
    """
    Ask user for confirmation

    Args:
        prompt: Prompt message
        default: Default answer if user presses Enter

    Returns:
        True if confirmed, False otherwise
    """
    default_str = "Y/n" if default else "y/N"
    response = input(f"{prompt} [{default_str}]: ").strip().lower()

    if not response:
        return default

    return response in ['y', 'yes']
