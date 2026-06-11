"""
File attachment management.

Handles file validation, preview, and management for attachments.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Attachment:
    """Represents a file attachment."""

    file_path: str
    name: str = ""
    size: int = 0
    file_type: str = ""
    preview: Optional[str] = None

    def __post_init__(self) -> None:
        """Initialize attachment properties."""
        path = Path(self.file_path)
        
        if not self.name:
            self.name = path.name
        
        if not self.size and path.exists():
            self.size = path.stat().st_size
        
        if not self.file_type:
            self.file_type = path.suffix.lower()

    @property
    def size_formatted(self) -> str:
        """Get formatted file size.
        
        Returns:
            Human-readable file size.
        """
        size = self.size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    @property
    def is_code_file(self) -> bool:
        """Check if file is a code file.
        
        Returns:
            True if code file.
        """
        code_extensions = {
            ".py", ".js", ".ts", ".tsx", ".jsx",
            ".java", ".go", ".rs", ".cpp", ".c", ".h", ".hpp",
            ".cs", ".php", ".rb", ".swift", ".kt", ".scala",
        }
        return self.file_type in code_extensions

    @property
    def is_image(self) -> bool:
        """Check if file is an image.
        
        Returns:
            True if image.
        """
        image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
        return self.file_type in image_extensions

    @property
    def is_config_file(self) -> bool:
        """Check if file is a config file.
        
        Returns:
            True if config file.
        """
        config_extensions = {".json", ".yaml", ".yml", ".toml", ".ini", ".xml"}
        return self.file_type in config_extensions


class FileManager:
    """Manages file operations for attachments."""

    def __init__(
        self,
        max_file_size_mb: int = 10,
        max_attachments: int = 10,
        allowed_extensions: Optional[set[str]] = None,
    ) -> None:
        """Initialize file manager.
        
        Args:
            max_file_size_mb: Maximum file size in MB.
            max_attachments: Maximum number of attachments.
            allowed_extensions: Set of allowed file extensions.
        """
        self.max_file_size_mb = max_file_size_mb
        self.max_attachments = max_attachments
        self.allowed_extensions = allowed_extensions or set()

    def validate_file(self, file_path: str) -> tuple[bool, str]:
        """Validate a file for attachment.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            Tuple of (is_valid, error_message).
        """
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            return False, "File does not exist"
        
        # Check if it's a file
        if not path.is_file():
            return False, "Not a file"
        
        # Check extension
        ext = path.suffix.lower()
        if self.allowed_extensions and ext not in self.allowed_extensions:
            return False, f"File type '{ext}' is not allowed"
        
        # Check file size
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > self.max_file_size_mb:
            return False, f"File size ({size_mb:.1f}MB) exceeds limit ({self.max_file_size_mb}MB)"
        
        return True, ""

    def read_file_content(self, file_path: str) -> str:
        """Read file content.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            File content as string.
        """
        path = Path(file_path)
        
        # Try UTF-8 first
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Try latin-1 as fallback
            return path.read_text(encoding="latin-1")

    def get_preview(self, attachment: Attachment) -> Optional[str]:
        """Get preview content for an attachment.
        
        Args:
            attachment: The attachment.
            
        Returns:
            Preview content or None.
        """
        if attachment.is_code_file or attachment.is_config_file:
            try:
                content = self.read_file_content(attachment.file_path)
                # Return first 500 chars as preview
                return content[:500] + "..." if len(content) > 500 else content
            except Exception:
                return None
        
        return None
