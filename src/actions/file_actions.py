"""
File-related action handlers
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import expand_path


class FileActions:
    """Handles file and folder operations"""

    def open_folder(self, path: str) -> str:
        """
        Open a folder in Windows Explorer

        Args:
            path: Full path to folder

        Returns:
            Success message
        """
        path = expand_path(path)

        if not os.path.exists(path):
            raise FileNotFoundError(f"Folder does not exist: {path}")

        if not os.path.isdir(path):
            raise NotADirectoryError(f"Path is not a directory: {path}")

        # Open folder in Windows Explorer
        subprocess.run(['explorer', path], check=True)

        return f"Opened folder: {path}"

    def find_file(
        self,
        path: str,
        pattern: str,
        latest: bool = False,
        recursive: bool = False,
        show_in_explorer: bool = True
    ) -> Dict:
        """
        Search for files matching a pattern

        Args:
            path: Directory to search in
            pattern: File pattern (e.g., '*.pdf', 'report*.docx')
            latest: If True, return only the most recent file
            recursive: Search in subdirectories
            show_in_explorer: If True, open Explorer and highlight the found file(s)

        Returns:
            Dict with found files information
        """
        path = Path(expand_path(path))

        if not path.exists():
            raise FileNotFoundError(f"Directory does not exist: {path}")

        if not path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {path}")

        # Search for files
        if recursive:
            files = list(path.rglob(pattern))
        else:
            files = list(path.glob(pattern))

        if not files:
            return {
                'found': False,
                'count': 0,
                'files': [],
                'message': f'No files matching "{pattern}" found in {path}'
            }

        # Sort by modification time (newest first)
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        # Prepare file info
        file_info = []
        for f in files:
            stat = f.stat()
            file_info.append({
                'path': str(f),
                'name': f.name,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })

        if latest:
            result = {
                'found': True,
                'count': 1,
                'files': [file_info[0]],
                'message': f'Found latest file: {file_info[0]["name"]}'
            }
            # Show the file in Explorer if requested
            if show_in_explorer and file_info:
                file_path = file_info[0]['path']
                # Use explorer /select to open and highlight the file
                # Don't check return code as it may return 1 even on success in some environments
                subprocess.run(f'explorer /select,"{file_path}"', shell=True)
                result['message'] += ' (Opened in Explorer)'
        else:
            result = {
                'found': True,
                'count': len(file_info),
                'files': file_info,
                'message': f'Found {len(file_info)} file(s) matching "{pattern}"'
            }
            # Show the first file in Explorer if requested
            if show_in_explorer and file_info:
                file_path = file_info[0]['path']
                # Use explorer /select to open and highlight the file
                # Don't check return code as it may return 1 even on success in some environments
                subprocess.run(f'explorer /select,"{file_path}"', shell=True)
                result['message'] += ' (Opened first file in Explorer)'

        return result

    def create_file(self, path: str, content: str, overwrite: bool = False) -> str:
        """
        Create a new text file

        Args:
            path: Full path for new file
            content: Text content to write
            overwrite: Overwrite if exists

        Returns:
            Success message
        """
        path = Path(expand_path(path))

        # Check if file exists
        if path.exists() and not overwrite:
            raise FileExistsError(f"File already exists: {path}. Use overwrite=True to replace.")

        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

        return f"Created file: {path} ({len(content)} characters)"

    def open_file(self, path: str) -> str:
        """
        Open a file with its default application

        Args:
            path: Full path to file

        Returns:
            Success message
        """
        path = Path(expand_path(path))

        if not path.exists():
            raise FileNotFoundError(f"File does not exist: {path}")

        if not path.is_file():
            raise IsADirectoryError(f"Path is a directory, not a file: {path}")

        # Open file with default application
        os.startfile(str(path))

        return f"Opened file: {path}"

    def show_file_in_explorer(self, path: str) -> str:
        """
        Open Windows Explorer and highlight/select a specific file

        Args:
            path: Full path to file

        Returns:
            Success message
        """
        path = Path(expand_path(path))

        if not path.exists():
            raise FileNotFoundError(f"File does not exist: {path}")

        # Use explorer /select to open Explorer and highlight the file
        # Don't check return code as it may return 1 even on success in some environments
        subprocess.run(f'explorer /select,"{str(path)}"', shell=True)

        return f"Opened Explorer and highlighted: {path.name}"

    def list_files(self, path: str, details: bool = False) -> Dict:
        """
        List all files in a directory

        Args:
            path: Directory path
            details: Include file size and modified date

        Returns:
            Dict with file listing
        """
        path = Path(expand_path(path))

        if not path.exists():
            raise FileNotFoundError(f"Directory does not exist: {path}")

        if not path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {path}")

        files = []
        for item in path.iterdir():
            if item.is_file():
                if details:
                    stat = item.stat()
                    files.append({
                        'name': item.name,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                else:
                    files.append(item.name)

        return {
            'path': str(path),
            'count': len(files),
            'files': files
        }

    def copy_file(self, source: str, destination: str, overwrite: bool = False) -> str:
        """
        Copy a file from source to destination

        Args:
            source: Source file path
            destination: Destination path (can be file or directory)
            overwrite: Overwrite if exists

        Returns:
            Success message
        """
        import shutil

        source = Path(expand_path(source))
        destination = Path(expand_path(destination))

        if not source.exists():
            raise FileNotFoundError(f"Source file does not exist: {source}")

        if not source.is_file():
            raise IsADirectoryError(f"Source is not a file: {source}")

        # If destination is a directory, use the source filename
        if destination.is_dir():
            destination = destination / source.name

        # Check if destination exists
        if destination.exists() and not overwrite:
            raise FileExistsError(f"Destination already exists: {destination}. Use overwrite=True to replace.")

        # Create parent directories if needed
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Copy the file
        shutil.copy2(source, destination)

        return f"Copied '{source.name}' to '{destination}'"

    def move_file(self, source: str, destination: str, overwrite: bool = False) -> str:
        """
        Move a file from source to destination

        Args:
            source: Source file path
            destination: Destination path (can be file or directory)
            overwrite: Overwrite if exists

        Returns:
            Success message
        """
        import shutil

        source = Path(expand_path(source))
        destination = Path(expand_path(destination))

        if not source.exists():
            raise FileNotFoundError(f"Source file does not exist: {source}")

        if not source.is_file():
            raise IsADirectoryError(f"Source is not a file: {source}")

        # If destination is a directory, use the source filename
        if destination.is_dir():
            destination = destination / source.name

        # Check if destination exists
        if destination.exists() and not overwrite:
            raise FileExistsError(f"Destination already exists: {destination}. Use overwrite=True to replace.")

        # Create parent directories if needed
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Move the file
        shutil.move(str(source), str(destination))

        return f"Moved '{source.name}' to '{destination}'"

    def delete_file(self, path: str) -> str:
        """
        Delete a file

        Args:
            path: File path to delete

        Returns:
            Success message
        """
        path = Path(expand_path(path))

        if not path.exists():
            raise FileNotFoundError(f"File does not exist: {path}")

        if not path.is_file():
            raise IsADirectoryError(f"Path is a directory, not a file: {path}")

        # Delete the file
        path.unlink()

        return f"Deleted file: {path.name}"
