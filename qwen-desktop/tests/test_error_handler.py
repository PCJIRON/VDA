"""Tests for error handling utilities."""

import pytest
import httpx

from qwen_desktop.utils.error_handler import (
    ErrorType,
    classify_error,
    get_user_message,
    get_suggested_action,
)


class TestClassifyError:
    """Test error classification."""

    def test_auth_error_401(self):
        """Test 401 classified as auth error."""
        error_type = classify_error(status_code=401)
        assert error_type == ErrorType.AUTH_ERROR

    def test_auth_error_403(self):
        """Test 403 classified as auth error."""
        error_type = classify_error(status_code=403)
        assert error_type == ErrorType.AUTH_ERROR

    def test_rate_limit_error_429(self):
        """Test 429 classified as rate limit error."""
        error_type = classify_error(status_code=429)
        assert error_type == ErrorType.RATE_LIMIT

    def test_server_error_500(self):
        """Test 500 classified as server error."""
        error_type = classify_error(status_code=500)
        assert error_type == ErrorType.SERVER_ERROR

    def test_server_error_503(self):
        """Test 503 classified as server error."""
        error_type = classify_error(status_code=503)
        assert error_type == ErrorType.SERVER_ERROR

    def test_network_error(self):
        """Test network error classified correctly."""
        error = httpx.ConnectError("Connection failed")
        error_type = classify_error(error=error)
        assert error_type == ErrorType.NETWORK_ERROR

    def test_timeout_error(self):
        """Test timeout error classified correctly."""
        error = httpx.TimeoutException("Request timed out")
        error_type = classify_error(error=error)
        assert error_type == ErrorType.NETWORK_ERROR

    def test_unknown_error(self):
        """Test unknown error classified correctly."""
        error_type = classify_error(status_code=404)
        assert error_type == ErrorType.UNKNOWN

    def test_no_info_returns_unknown(self):
        """Test no info returns unknown."""
        error_type = classify_error()
        assert error_type == ErrorType.UNKNOWN


class TestGetUserMessage:
    """Test user-friendly error messages."""

    def test_auth_error_message(self):
        """Test auth error message."""
        msg = get_user_message(ErrorType.AUTH_ERROR)
        assert "Authentication failed" in msg
        assert "log in again" in msg

    def test_rate_limit_message(self):
        """Test rate limit message."""
        msg = get_user_message(ErrorType.RATE_LIMIT)
        assert "Rate limit exceeded" in msg
        assert "quota" in msg

    def test_network_error_message(self):
        """Test network error message."""
        msg = get_user_message(ErrorType.NETWORK_ERROR)
        assert "Network error" in msg
        assert "internet connection" in msg

    def test_server_error_message(self):
        """Test server error message."""
        msg = get_user_message(ErrorType.SERVER_ERROR)
        assert "server error" in msg.lower()
        assert "temporary" in msg

    def test_file_error_message_with_details(self):
        """Test file error message with details."""
        msg = get_user_message(ErrorType.FILE_ERROR, "File too large")
        assert "File error" in msg
        assert "File too large" in msg

    def test_unknown_error_message(self):
        """Test unknown error message."""
        msg = get_user_message(ErrorType.UNKNOWN, "Something went wrong")
        assert "error occurred" in msg


class TestGetSuggestedAction:
    """Test suggested actions for errors."""

    def test_auth_action(self):
        """Test auth error action."""
        action = get_suggested_action(ErrorType.AUTH_ERROR)
        assert "Login" in action

    def test_rate_limit_action(self):
        """Test rate limit action."""
        action = get_suggested_action(ErrorType.RATE_LIMIT)
        assert "Wait" in action or "hours" in action

    def test_network_action(self):
        """Test network error action."""
        action = get_suggested_action(ErrorType.NETWORK_ERROR)
        assert "Check" in action and "connection" in action

    def test_server_action(self):
        """Test server error action."""
        action = get_suggested_action(ErrorType.SERVER_ERROR)
        assert "Wait" in action or "retry" in action.lower()
