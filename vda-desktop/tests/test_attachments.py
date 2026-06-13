"""Tests for file attachments."""

import tempfile
from pathlib import Path

from vda.attachments.file_manager import Attachment, FileManager


class TestAttachment:
    """Test Attachment dataclass."""

    def test_create_attachment(self):
        """Test creating an attachment."""
        attachment = Attachment(file_path="/path/to/file.py")

        assert attachment.name == "file.py"
        assert attachment.file_type == ".py"

    def test_attachment_size_formatted(self):
        """Test file size formatting."""
        attachment = Attachment(
            file_path="/path/to/file.py",
            size=1536,
        )

        assert attachment.size_formatted == "1.5 KB"

    def test_is_code_file(self):
        """Test code file detection."""
        py_file = Attachment(file_path="/path/to/file.py")
        txt_file = Attachment(file_path="/path/to/file.txt")

        assert py_file.is_code_file
        assert not txt_file.is_code_file

    def test_is_image(self):
        """Test image detection."""
        img_file = Attachment(file_path="/path/to/image.png")
        txt_file = Attachment(file_path="/path/to/file.txt")

        assert img_file.is_image
        assert not txt_file.is_image


class TestFileManager:
    """Test file manager."""

    def test_validate_file_not_exists(self):
        """Test validation of non-existent file."""
        manager = FileManager()

        is_valid, error = manager.validate_file("/nonexistent/file.py")

        assert not is_valid
        assert "does not exist" in error

    def test_validate_file_with_temp(self):
        """Test validation with temporary file."""
        manager = FileManager()

        # Create a temp file
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(b"print('hello')")
            temp_path = f.name

        try:
            is_valid, error = manager.validate_file(temp_path)
            assert is_valid
            assert error == ""
        finally:
            Path(temp_path).unlink()

    def test_validate_file_size_limit(self):
        """Test file size validation."""
        manager = FileManager(max_file_size_mb=1)

        # Create a temp file larger than 1MB
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(b"x" * (2 * 1024 * 1024))  # 2MB
            temp_path = f.name

        try:
            is_valid, error = manager.validate_file(temp_path)
            assert not is_valid
            assert "exceeds limit" in error
        finally:
            Path(temp_path).unlink()

    def test_read_file_content(self):
        """Test reading file content."""
        manager = FileManager()

        with tempfile.NamedTemporaryFile(
            suffix=".py", delete=False, mode="w", encoding="utf-8"
        ) as f:
            f.write("print('hello')")
            temp_path = f.name

        try:
            content = manager.read_file_content(temp_path)
            assert content == "print('hello')"
        finally:
            Path(temp_path).unlink()

    def test_get_preview_code_file(self):
        """Test getting preview for code file."""
        manager = FileManager()

        with tempfile.NamedTemporaryFile(
            suffix=".py", delete=False, mode="w", encoding="utf-8"
        ) as f:
            content = "print('hello')\nprint('world')"
            f.write(content)
            temp_path = f.name

        try:
            attachment = Attachment(file_path=temp_path)
            preview = manager.get_preview(attachment)
            assert preview == content
        finally:
            Path(temp_path).unlink()
