"""
Rate limiter for Qwen OAuth free tier.

Implements fixed window rate limiting to manage API quota (1,000 requests/day).
State persisted to disk to prevent bypass via restart.
"""

from datetime import datetime, timedelta
from typing import Optional
import threading
import json
from pathlib import Path


class RateLimiter:
    """Token bucket rate limiter for OAuth API."""

    def __init__(
        self,
        max_requests: int = 1000,
        period_seconds: int = 86400,
    ) -> None:
        """Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests per period (default: 1000/day).
            period_seconds: Period in seconds (default: 86400 = 24 hours).
        """
        self.max_requests = max_requests
        self.period = timedelta(seconds=period_seconds)
        
        # State persistence to prevent bypass via restart
        self._state_path = Path.home() / ".qwen-desktop" / "rate_limit.json"
        self._load_state()
        
        self._lock = threading.Lock()

    def acquire(self) -> bool:
        """Try to acquire a token.
        
        Returns:
            True if token acquired, False if rate limited.
        """
        with self._lock:
            self._refill()
            
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                self.last_request = datetime.now()
                self._save_state()
                return True
            
            return False
    
    def _load_state(self) -> None:
        """Load state from disk."""
        if self._state_path.exists():
            try:
                with open(self._state_path) as f:
                    state = json.load(f)
                self.tokens = float(state.get("tokens", self.max_requests))
                self.last_refill = datetime.fromisoformat(state["last_refill"])
            except (json.JSONDecodeError, KeyError, ValueError):
                # Corrupted state, reset
                self.tokens = float(self.max_requests)
                self.last_refill = datetime.now()
        else:
            self.tokens = float(self.max_requests)
            self.last_refill = datetime.now()
    
    def _save_state(self) -> None:
        """Save state to disk."""
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._state_path, "w") as f:
            json.dump({
                "tokens": self.tokens,
                "last_refill": self.last_refill.isoformat(),
            }, f)

    def wait_time(self) -> timedelta:
        """Get time to wait until next token available.
        
        Returns:
            Time delta to wait.
        """
        with self._lock:
            self._refill()
            
            if self.tokens >= 1.0:
                return timedelta(0)
            
            tokens_needed = max(0, 1.0 - self.tokens)
            refill_rate = self.max_requests / self.period.total_seconds()
            seconds_to_wait = tokens_needed / refill_rate
            
            return timedelta(seconds=seconds_to_wait)

    def _refill(self) -> None:
        """Refill tokens at start of new day (fixed window)."""
        now = datetime.now()
        # Reset at midnight (fixed window - new day = new quota)
        if now.date() > self.last_refill.date():
            self.tokens = float(self.max_requests)
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
            "period_hours": self.period.total_seconds() / 3600,
        }

    def reset(self) -> None:
        """Reset rate limiter to full capacity."""
        self.tokens = float(self.max_requests)
        self.last_refill = datetime.now()
        self.last_request = None
