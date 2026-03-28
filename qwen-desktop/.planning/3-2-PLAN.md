# Phase 3 Plan: Wave 2 - Rate Limiting (OAuth Free Tier)

**Wave:** 2  
**Priority:** High  
**Estimated Time:** 2 hours

---

## 🎯 Objective

Implement rate limiting for OAuth free tier (1,000 requests/day per user) to prevent quota exhaustion and provide clear usage feedback.

---

## 🔐 OAuth Rate Limits

**Qwen OAuth Free Tier:**
- **1,000 requests per day** per authenticated user
- **Resets at midnight UTC**
- **Shared across all devices** for same account

**Why Rate Limit:**
- Prevent accidental quota exhaustion
- Show users their remaining quota
- Provide warnings before limit reached
- Auto-pause when limit exceeded

---

## 📋 Tasks

### Task 3.4: Implement Token Bucket Rate Limiter

**File:** `qwen_desktop/utils/rate_limiter.py` (new)

**Implementation:**
```python
from datetime import datetime, timedelta
from typing import Optional

class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, max_requests: int = 1000, period_seconds: int = 86400) -> None:
        """Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests per period.
            period_seconds: Period in seconds (default: 24 hours).
        """
        self.max_requests = max_requests
        self.period = timedelta(seconds=period_seconds)
        self.tokens = float(max_requests)
        self.last_refill = datetime.now()
        self.last_request: Optional[datetime] = None

    def acquire(self) -> bool:
        """Try to acquire a token.
        
        Returns:
            True if token acquired, False if rate limited.
        """
        self._refill()
        
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            self.last_request = datetime.now()
            return True
        
        return False

    def wait_time(self) -> timedelta:
        """Get time to wait until next token available.
        
        Returns:
            Time delta to wait.
        """
        self._refill()
        
        if self.tokens >= 1.0:
            return timedelta(0)
        
        tokens_needed = 1.0 - self.tokens
        refill_rate = self.max_requests / self.period.total_seconds()
        seconds_to_wait = tokens_needed / refill_rate
        
        return timedelta(seconds=seconds_to_wait)

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = datetime.now()
        elapsed = now - self.last_refill
        
        # Calculate tokens to add
        refill_rate = self.max_requests / self.period.total_seconds()
        tokens_to_add = elapsed.total_seconds() * refill_rate
        
        self.tokens = min(self.max_requests, self.tokens + tokens_to_add)
        self.last_refill = now

    def get_usage(self) -> dict:
        """Get current usage statistics.
        
        Returns:
            Dictionary with tokens_remaining, requests_made, reset_time.
        """
        self._refill()
        
        reset_time = self.last_refill + self.period
        
        return {
            "tokens_remaining": int(self.tokens),
            "requests_made": self.max_requests - int(self.tokens),
            "max_requests": self.max_requests,
            "reset_time": reset_time,
        }
```

**Verification:**
- [ ] acquire() returns True when tokens available
- [ ] acquire() returns False when rate limited
- [ ] wait_time() returns correct wait duration
- [ ] Tokens refill over time
- [ ] get_usage() returns accurate stats

---

### Task 3.5: Integrate Rate Limiter with API Client

**File:** `qwen_desktop/core/api_client.py`

**Changes:**
```python
from qwen_desktop.utils.rate_limiter import RateLimiter

class APIClient:
    def __init__(
        self,
        settings: Settings,
        oauth_handler: Optional[OAuthHandler] = None,
    ) -> None:
        self.settings = settings
        self.oauth_handler = oauth_handler
        
        # Rate limiter (1000 requests per day for free tier)
        self.rate_limiter = RateLimiter(max_requests=1000, period_seconds=86400)
        
        # ... rest of __init__

class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""
    def __init__(self, message: str, wait_time: timedelta):
        super().__init__(message)
        self.wait_time = wait_time

    async def chat(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        stream: bool = True,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        # Check rate limit before making request
        if not self.rate_limiter.acquire():
            wait_time = self.rate_limiter.wait_time()
            raise RateLimitError(
                f"Rate limit exceeded. Please wait {wait_time}",
                wait_time
            )
        
        # ... rest of existing chat method
```

**Verification:**
- [ ] Rate limiter initialized in API client
- [ ] acquire() called before each API request
- [ ] RateLimitError raised when limit exceeded
- [ ] Error includes wait time

---

### Task 3.6: Show Rate Limit Status in UI

**File:** `qwen_desktop/ui/main_window.py`

**Changes:**
```python
def _setup_toolbar(self) -> None:
    # ... existing toolbar setup
    
    # Rate limit indicator
    self.rate_limit_label = QLabel("")
    self.rate_limit_label.setStyleSheet("color: #888; padding: 5px;")
    toolbar.addWidget(self.rate_limit_label)
    
    # Update rate limit display periodically
    from PyQt6.QtCore import QTimer
    self.rate_limit_timer = QTimer()
    self.rate_limit_timer.timeout.connect(self._update_rate_limit_display)
    self.rate_limit_timer.start(60000)  # Update every minute

def _update_rate_limit_display(self) -> None:
    """Update rate limit status display."""
    if hasattr(self, 'api_client') and self.api_client:
        usage = self.api_client.rate_limiter.get_usage()
        remaining = usage["tokens_remaining"]
        
        if remaining < 10:
            color = "#ff4444"  # Red for low
        elif remaining < 100:
            color = "#ffaa00"  # Orange for warning
        else:
            color = "#44aa44"  # Green for OK
        
        self.rate_limit_label.setText(f"API: {remaining} left")
        self.rate_limit_label.setStyleSheet(f"color: {color}; padding: 5px;")

def _on_message_sent(self, message: str) -> None:
    """Handle message sent event."""
    try:
        # Add user message to chat
        self.chat_widget.add_message(message, is_user=True)
        self.chat_widget.set_typing_indicator(True)
        
        # Send to API
        # ... existing API call
        
    except RateLimitError as e:
        self.chat_widget.set_typing_indicator(False)
        wait_minutes = int(e.wait_time.total_seconds() / 60)
        self.statusbar.showMessage(
            f"Rate limit exceeded. Please wait {wait_minutes} minutes.",
            10000
        )
        # Show error message in chat
        self.chat_widget.add_message(
            f"⚠️ Rate limit exceeded. Please wait {wait_minutes} minutes before sending more messages.",
            is_system=True
        )
```

**Verification:**
- [ ] Rate limit label shows remaining requests
- [ ] Color changes based on remaining quota
- [ ] Updates every minute
- [ ] Rate limit error shows user-friendly message
- [ ] Wait time displayed correctly

---

## 🧪 Tests to Create

**File:** `tests/test_rate_limiter.py`

```python
import pytest
from datetime import timedelta
from qwen_desktop.utils.rate_limiter import RateLimiter

def test_acquire_success():
    """Test acquiring token when available."""
    limiter = RateLimiter(max_requests=10, period_seconds=60)
    
    # Should succeed for first 10 requests
    for i in range(10):
        assert limiter.acquire() is True

def test_acquire_failure():
    """Test acquiring token when exhausted."""
    limiter = RateLimiter(max_requests=1, period_seconds=60)
    
    # First request succeeds
    assert limiter.acquire() is True
    
    # Second request fails
    assert limiter.acquire() is False

def test_wait_time():
    """Test wait time calculation."""
    limiter = RateLimiter(max_requests=1, period_seconds=60)
    
    # Exhaust tokens
    limiter.acquire()
    
    # Should have to wait
    wait = limiter.wait_time()
    assert wait > timedelta(0)
    assert wait <= timedelta(seconds=60)

def test_get_usage():
    """Test usage statistics."""
    limiter = RateLimiter(max_requests=100, period_seconds=60)
    
    # Make 10 requests
    for _ in range(10):
        limiter.acquire()
    
    usage = limiter.get_usage()
    assert usage["requests_made"] == 10
    assert usage["tokens_remaining"] == 90
    assert usage["max_requests"] == 100
```

---

## ✅ Verification Checklist

- [ ] RateLimiter class implemented
- [ ] Token bucket algorithm works correctly
- [ ] acquire() returns True/False appropriately
- [ ] wait_time() calculates correct duration
- [ ] get_usage() returns accurate stats
- [ ] API client checks rate limit before requests
- [ ] RateLimitError raised when limit exceeded
- [ ] UI shows remaining requests
- [ ] UI color changes based on quota
- [ ] Rate limit error shows user-friendly message
- [ ] Tests pass

---

## 📦 Output

**Files Created:**
- `qwen_desktop/utils/rate_limiter.py`
- `tests/test_rate_limiter.py`

**Files Modified:**
- `qwen_desktop/core/api_client.py`
- `qwen_desktop/ui/main_window.py`

---

**Ready to Execute:** Run `/gsd:execute-phase 3` to implement Wave 2.
