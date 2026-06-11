"""
Error handling utilities for Qwen Desktop.

Provides error classification and user-friendly error messages.
"""

from enum import Enum
from typing import Optional
import httpx


class ErrorType(Enum):
    """Types of errors that can occur."""
    AUTH_ERROR = "auth_error"
    RATE_LIMIT = "rate_limit"
    NETWORK_ERROR = "network_error"
    SERVER_ERROR = "server_error"
    FILE_ERROR = "file_error"
    UNKNOWN = "unknown"


def classify_error(
    status_code: Optional[int] = None,
    error: Optional[Exception] = None,
) -> ErrorType:
    """Classify an error based on status code or exception type.
    
    Args:
        status_code: HTTP status code if available.
        error: Exception that was raised.
        
    Returns:
        ErrorType classification.
    """
    if status_code:
        if status_code == 401 or status_code == 403:
            return ErrorType.AUTH_ERROR
        elif status_code == 429:
            return ErrorType.RATE_LIMIT
        elif status_code >= 500:
            return ErrorType.SERVER_ERROR
        elif status_code >= 400:
            return ErrorType.UNKNOWN
    
    if error:
        if isinstance(error, (httpx.ConnectError, httpx.NetworkError)):
            return ErrorType.NETWORK_ERROR
        elif isinstance(error, httpx.TimeoutException):
            return ErrorType.NETWORK_ERROR
        elif isinstance(error, httpx.RequestError):
            return ErrorType.NETWORK_ERROR
    
    return ErrorType.UNKNOWN


def get_user_message(error_type: ErrorType, details: str = "") -> str:
    """Get user-friendly error message.
    
    Args:
        error_type: Type of error.
        details: Additional error details.
        
    Returns:
        User-friendly message string.
    """
    messages = {
        ErrorType.AUTH_ERROR: (
            "Authentication failed. Please log in again to continue."
        ),
        ErrorType.RATE_LIMIT: (
            "Rate limit exceeded. The API provider is throttling requests. "
            "VDA will retry automatically with backoff. If this persists, "
            "wait a minute or switch to a provider with higher rate limits."
        ),
        ErrorType.NETWORK_ERROR: (
            "Network error. Please check your internet connection and try again."
        ),
        ErrorType.SERVER_ERROR: (
            "API server error. This is temporary - please try again in a moment."
        ),
        ErrorType.FILE_ERROR: (
            f"File error: {details}" if details else "Failed to process file."
        ),
        ErrorType.UNKNOWN: (
            f"An error occurred: {details}" if details else "An unexpected error occurred."
        ),
    }
    
    return messages.get(error_type, messages[ErrorType.UNKNOWN])


def get_suggested_action(error_type: ErrorType) -> str:
    """Get suggested action for error type.
    
    Args:
        error_type: Type of error.
        
    Returns:
        Suggested action string.
    """
    actions = {
        ErrorType.AUTH_ERROR: "Click 'Login' to re-authenticate",
        ErrorType.RATE_LIMIT: "Wait ~30s, then retry (VDA auto-retries with backoff)",
        ErrorType.NETWORK_ERROR: "Check connection, then retry",
        ErrorType.SERVER_ERROR: "Wait a moment, then retry",
        ErrorType.FILE_ERROR: "Check file and try again",
        ErrorType.UNKNOWN: "Try again or restart the app",
    }
    
    return actions.get(error_type, actions[ErrorType.UNKNOWN])
