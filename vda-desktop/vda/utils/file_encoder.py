"""
File encoding utility for VDA API.

Encodes files to base64 for sending with OAuth-authenticated API requests.
"""

import base64
import mimetypes
from pathlib import Path
from typing import Optional

# Maximum file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024


def encode_file(file_path: str) -> Optional[dict]:
    """Encode file to base64 with metadata.
    
    Args:
        file_path: Path to file.
        
    Returns:
        Dictionary with encoded content and metadata, or None on error.
    """
    path = Path(file_path)
    
    if not path.exists() or not path.is_file():
        return None
    
    # Check file size before loading into memory
    if path.stat().st_size > MAX_FILE_SIZE:
        return None
    
    try:
        # Read and encode file
        with open(path, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf-8")
        
        # Detect MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        
        return {
            "content": content,
            "name": path.name,
            "size": path.stat().st_size,
            "mime_type": mime_type or "application/octet-stream",
        }
    except Exception as e:
        print(f"Error encoding file: {e}")
        return None


def is_image_file(file_path: str) -> bool:
    """Check if file is an image.
    
    Args:
        file_path: Path to file.
        
    Returns:
        True if image file.
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        return mime_type.startswith("image/")
    return False


def get_file_category(file_path: str) -> str:
    """Get file category for API handling.
    
    Args:
        file_path: Path to file.
        
    Returns:
        Category string: 'image', 'code', 'config', 'document', or 'other'.
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    path = Path(file_path)
    ext = path.suffix.lower()
    
    if mime_type and mime_type.startswith("image/"):
        return "image"
    elif ext in {".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c", ".h"}:
        return "code"
    elif ext in {".json", ".yaml", ".yml", ".toml", ".ini", ".xml"}:
        return "config"
    elif mime_type and mime_type.startswith("text/"):
        return "document"
    else:
        return "other"
