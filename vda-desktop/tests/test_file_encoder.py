"""Tests for file encoder utility."""

import tempfile
from pathlib import Path

from vda.utils.file_encoder import (
    encode_file,
    get_file_category,
    is_image_file,
)


class TestEncodeFile:
    """Test file encoding functionality."""

    def test_encode_text_file(self):
        """Test encoding a text file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            f.write("Hello, World!")
            temp_path = f.name

        try:
            result = encode_file(temp_path)

            assert result is not None
            assert result["name"].endswith(".txt")
            assert result["size"] == 13
            assert "content" in result
            assert result["mime_type"] == "text/plain"
        finally:
            Path(temp_path).unlink()

    def test_encode_python_file(self):
        """Test encoding a Python file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("print('hello')")
            temp_path = f.name

        try:
            result = encode_file(temp_path)

            assert result is not None
            assert result["name"].endswith(".py")
            assert result["mime_type"] == "text/x-python"
        finally:
            Path(temp_path).unlink()

    def test_encode_nonexistent_file(self):
        """Test encoding non-existent file."""
        result = encode_file("/nonexistent/file.txt")
        assert result is None

    def test_encode_directory(self):
        """Test encoding a directory (should fail)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = encode_file(temp_dir)
            assert result is None

    def test_encode_binary_file(self):
        """Test encoding a binary file."""
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".bin", delete=False
        ) as f:
            f.write(b"\x00\x01\x02\x03")
            temp_path = f.name

        try:
            result = encode_file(temp_path)

            assert result is not None
            assert "content" in result
            # Verify base64 encoding
            import base64
            decoded = base64.b64decode(result["content"])
            assert decoded == b"\x00\x01\x02\x03"
        finally:
            Path(temp_path).unlink()


class TestIsImageFile:
    """Test image file detection."""

    def test_png_is_image(self):
        """Test PNG file detected as image."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = f.name

        try:
            assert is_image_file(temp_path) is True
        finally:
            Path(temp_path).unlink()

    def test_jpg_is_image(self):
        """Test JPG file detected as image."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            temp_path = f.name

        try:
            assert is_image_file(temp_path) is True
        finally:
            Path(temp_path).unlink()

    def test_txt_not_image(self):
        """Test text file not detected as image."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            temp_path = f.name

        try:
            assert is_image_file(temp_path) is False
        finally:
            Path(temp_path).unlink()

    def test_py_not_image(self):
        """Test Python file not detected as image."""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            temp_path = f.name

        try:
            assert is_image_file(temp_path) is False
        finally:
            Path(temp_path).unlink()


class TestGetFileCategory:
    """Test file category detection."""

    def test_code_file_category(self):
        """Test code file category."""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            temp_path = f.name

        try:
            category = get_file_category(temp_path)
            assert category == "code"
        finally:
            Path(temp_path).unlink()

    def test_config_file_category(self):
        """Test config file category."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            category = get_file_category(temp_path)
            assert category == "config"
        finally:
            Path(temp_path).unlink()

    def test_document_file_category(self):
        """Test document file category."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            temp_path = f.name

        try:
            category = get_file_category(temp_path)
            assert category == "document"
        finally:
            Path(temp_path).unlink()

    def test_image_file_category(self):
        """Test image file category."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = f.name

        try:
            category = get_file_category(temp_path)
            assert category == "image"
        finally:
            Path(temp_path).unlink()
