"""Tests for the shared base API client."""

from unittest.mock import MagicMock, patch

import pytest

from vda.core._base_client import BaseClient


class ConcreteClient(BaseClient):
    def _get_headers(self) -> dict:
        return {"Authorization": "Bearer test-key"}


@pytest.fixture
def client():
    settings = MagicMock()
    settings.get.return_value = "test-value"
    with patch("vda.core._base_client.ProviderConfig") as MockConfig:
        MockConfig.return_value.get_base_url.return_value = "https://api.test.com"
        MockConfig.return_value.get_provider_id.return_value = "test"
        client = ConcreteClient(settings)
        yield client


class TestBaseClient:
    def test_init(self, client):
        assert client._get_base_url() == "https://api.test.com"

    def test_get_headers(self, client):
        headers = client._get_headers()
        assert headers["Authorization"] == "Bearer test-key"

    def test_create_client(self, client):
        with patch("vda.core._base_client.httpx.AsyncClient") as MockClient:
            c = client._create_client()
            MockClient.assert_called_once()

    def test_ensure_system_prompt_adds_when_missing(self, client):
        messages = [{"role": "user", "content": "hi"}]
        client._ensure_system_prompt(messages, vision_mode=True)
        assert any(m.get("role") == "system" for m in messages)

    def test_ensure_system_prompt_skips_when_present(self, client):
        messages = [{"role": "system", "content": "existing"}, {"role": "user", "content": "hi"}]
        client._ensure_system_prompt(messages, vision_mode=True)
        system_count = sum(1 for m in messages if m["role"] == "system")
        assert system_count == 1

    def test_build_user_content_text_only(self):
        content, text = BaseClient._build_user_content("hello world", None)
        assert content[0]["type"] == "text"
        assert content[0]["text"] == "hello world"
        assert text == "hello world"

    def test_build_user_content_with_image_attachment(self):
        attachments = [{"type": "image", "base64": "AAAA", "mime": "image/png"}]
        content, text = BaseClient._build_user_content("describe", attachments)
        assert any(c["type"] == "image_url" for c in content)

    def test_build_user_content_with_file_attachment(self):
        attachments = [{"type": "file", "content": "file content", "name": "test.py"}]
        content, text = BaseClient._build_user_content("read this", attachments)
        assert text and "test.py" in text

    def test_build_user_content_list_message(self):
        msg = [{"type": "text", "text": "hello"}]
        content, text = BaseClient._build_user_content(msg, None)
        assert content == msg

    def test_build_payload(self, client):
        messages = [{"role": "user", "content": "hi"}]
        payload = client._build_payload("test-model", messages)
        assert payload["model"] == "test-model"
        assert payload["messages"] == messages
        assert payload["stream"] is True

    def test_handle_stream_error(self, client):
        mock_response = MagicMock()
        mock_response.status_code = 401
        error = client._handle_stream_error(mock_response, "test")
        assert "401" in error
