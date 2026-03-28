# Phase 3 Plan: Wave 1 - Send Files with Qwen API (OAuth)

**Wave:** 1  
**Priority:** High  
**Estimated Time:** 3 hours

---

## 🎯 Objective

Enable sending file attachments with Qwen API requests using **OAuth authentication** (no API keys). Files will be encoded as base64 and sent through the authenticated Qwen API.

---

## 🔐 Authentication Note

**Important:** This application uses **OAuth authentication only** (like qwen-code CLI).

- ✅ **OAuth tokens** from Qwen/Google login
- ✅ **1,000 free requests/day** with OAuth
- ❌ **No API keys** required
- ❌ **No OPENAI_API_KEY** needed

The `api_client.py` already uses OAuth tokens from `oauth_handler`. This wave extends it to send files.

---

## 📋 Tasks

### Task 3.1: Base64 File Encoding

**File:** `qwen_desktop/utils/file_encoder.py` (new)

**Implementation:**
```python
import base64
import mimetypes
from pathlib import Path
from typing import Optional

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
```

**Verification:**
- [ ] Function returns dict with content, name, size, mime_type
- [ ] Returns None for non-existent files
- [ ] Handles binary and text files

---

### Task 3.2: Add Attachments to API Request

**File:** `qwen_desktop/core/api_client.py`

**Changes:**
```python
# In send_message() method
async def send_message(
    self,
    message: str,
    conversation_history: list[dict],
    attachments: Optional[list[Attachment]] = None,
) -> AsyncGenerator[str, None]:
    messages = conversation_history.copy()
    
    # Build user message with attachments
    user_message = {"role": "user", "content": message}
    
    if attachments:
        content_parts = [{"type": "text", "text": message}]
        
        for attachment in attachments:
            from qwen_desktop.utils.file_encoder import encode_file
            encoded = encode_file(attachment.file_path)
            
            if encoded:
                if attachment.is_image:
                    # Image format for multimodal models
                    content_parts.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{encoded['mime_type']};base64,{encoded['content']}"
                        }
                    })
                else:
                    # File as text context
                    content_parts.append({
                        "type": "text",
                        "text": f"\n\n--- File: {encoded['name']} ---\n[File content encoded, {encoded['size']} bytes]"
                    })
        
        user_message["content"] = content_parts
    
    messages.append(user_message)
    
    # Stream response
    async for chunk in self.chat(messages):
        yield chunk
```

**Verification:**
- [ ] Attachments included in API request
- [ ] Images sent as image_url format
- [ ] Other files sent as text context
- [ ] API response streams correctly

---

### Task 3.3: Handle API Response with File Context

**File:** `qwen_desktop/core/api_client.py`

**Changes:**
```python
# Add file context to system prompt
async def chat(
    self,
    messages: list[dict],
    model: Optional[str] = None,
    stream: bool = True,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    has_attachments: bool = False,
) -> AsyncGenerator[str, None]:
    model = model or self.settings.get("api_model", "qwen-coder")
    
    # Add system message if attachments present
    if has_attachments:
        system_message = {
            "role": "system",
            "content": "The user has attached files to this message. Analyze the file content carefully when responding."
        }
        messages = [system_message] + messages
    
    # ... rest of existing chat method
```

**Verification:**
- [ ] System message added when attachments present
- [ ] API processes request correctly
- [ ] Response references attached files

---

## 🧪 Tests to Create

**File:** `tests/test_file_encoder.py`

```python
import pytest
from qwen_desktop.utils.file_encoder import encode_file

def test_encode_text_file(tmp_path):
    """Test encoding a text file."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("Hello, World!")
    
    result = encode_file(str(file_path))
    
    assert result is not None
    assert result["name"] == "test.txt"
    assert result["size"] == 13
    assert "content" in result

def test_encode_nonexistent_file():
    """Test encoding non-existent file."""
    result = encode_file("/nonexistent/file.txt")
    assert result is None
```

---

## ✅ Verification Checklist

- [ ] encode_file() function works for text files
- [ ] encode_file() function works for binary files
- [ ] encode_file() returns None for invalid files
- [ ] Attachments sent in API request
- [ ] Images use image_url format
- [ ] Files use text context format
- [ ] API response handles file context
- [ ] Tests pass (new + existing)

---

## 📦 Output

**Files Created:**
- `qwen_desktop/utils/file_encoder.py`
- `tests/test_file_encoder.py`

**Files Modified:**
- `qwen_desktop/core/api_client.py`

---

**Ready to Execute:** Run `/gsd:execute-phase 3` to implement Wave 1.
