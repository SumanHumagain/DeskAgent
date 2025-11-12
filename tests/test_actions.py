"""
Basic tests for action handlers
"""

import pytest
import os
import tempfile
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from actions.file_actions import FileActions


class TestFileActions:
    """Test file action handlers"""

    def setup_method(self):
        """Setup test fixtures"""
        self.file_actions = FileActions()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup after tests"""
        # Clean up temp directory
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_create_file(self):
        """Test file creation"""
        file_path = os.path.join(self.temp_dir, 'test.txt')
        content = 'Hello, World!'

        result = self.file_actions.create_file(file_path, content)

        assert os.path.exists(file_path)
        assert 'Created file' in result

        with open(file_path, 'r') as f:
            assert f.read() == content

    def test_create_file_overwrite(self):
        """Test file overwrite"""
        file_path = os.path.join(self.temp_dir, 'test.txt')

        # Create initial file
        self.file_actions.create_file(file_path, 'Initial content')

        # Try to create again without overwrite - should raise error
        with pytest.raises(FileExistsError):
            self.file_actions.create_file(file_path, 'New content')

        # Create with overwrite - should succeed
        result = self.file_actions.create_file(file_path, 'New content', overwrite=True)
        assert 'Created file' in result

        with open(file_path, 'r') as f:
            assert f.read() == 'New content'

    def test_find_file(self):
        """Test file searching"""
        # Create test files
        Path(self.temp_dir, 'test1.txt').write_text('Test 1')
        Path(self.temp_dir, 'test2.txt').write_text('Test 2')
        Path(self.temp_dir, 'other.pdf').write_text('PDF content')

        # Search for .txt files
        result = self.file_actions.find_file(self.temp_dir, '*.txt')

        assert result['found'] is True
        assert result['count'] == 2

    def test_find_file_latest(self):
        """Test finding latest file"""
        import time

        # Create files with delays to ensure different timestamps
        Path(self.temp_dir, 'old.txt').write_text('Old')
        time.sleep(0.1)
        Path(self.temp_dir, 'new.txt').write_text('New')

        # Find latest
        result = self.file_actions.find_file(self.temp_dir, '*.txt', latest=True)

        assert result['found'] is True
        assert result['count'] == 1
        assert 'new.txt' in result['files'][0]['name']

    def test_list_files(self):
        """Test listing files in directory"""
        # Create test files
        Path(self.temp_dir, 'file1.txt').write_text('Content 1')
        Path(self.temp_dir, 'file2.txt').write_text('Content 2')

        result = self.file_actions.list_files(self.temp_dir)

        assert result['count'] == 2
        assert 'file1.txt' in result['files']
        assert 'file2.txt' in result['files']

    def test_list_files_with_details(self):
        """Test listing files with details"""
        # Create test file
        Path(self.temp_dir, 'test.txt').write_text('Test content')

        result = self.file_actions.list_files(self.temp_dir, details=True)

        assert result['count'] == 1
        file_info = result['files'][0]
        assert 'name' in file_info
        assert 'size' in file_info
        assert 'modified' in file_info


# Add more test classes for other action types
# class TestAppActions:
#     pass

# class TestEmailActions:
#     pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
