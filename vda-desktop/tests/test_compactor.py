"""Tests for the SessionCompactor subsystem.

Covers token estimation, threshold trigger, one-time compaction guard,
compaction output format, last user message preservation, reset behavior,
and prompt format validation.
"""

from unittest.mock import MagicMock

from vda.core.agent_manager import SessionCompactor
from vda.core.agent_manager.session_compactor import (
    COMPACTION_PROMPT,
)


class TestSessionCompactor:
    """Test SessionCompactor token estimation, threshold, and compaction."""

    def setup_method(self):
        """Create a fresh compactor for each test."""
        self.mock_client = MagicMock()
        self.compactor = SessionCompactor(
            self.mock_client, threshold=0.8, max_tokens=128000
        )

    def test_estimate_tokens_empty(self):
        """Empty message list estimates to 0 tokens."""
        tokens = SessionCompactor.estimate_tokens([])
        assert tokens == 0

    def test_estimate_tokens_short_message(self):
        """Short message estimates ~len//4 tokens."""
        messages = [
            {"role": "user", "content": "Hello, world!"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        tokens = SessionCompactor.estimate_tokens(messages)
        expected = (13 + 9) // 4  # 22 // 4 = 5
        assert tokens == expected

    def test_estimate_tokens_ignores_non_content_fields(self):
        """Fields without 'content' key should not add to estimate."""
        messages = [
            {"role": "user", "content": "Test"},
            {"role": "system", "extra": "data"},
        ]
        tokens = SessionCompactor.estimate_tokens(messages)
        # Only the first message has content: "Test" (4 chars / 4 = 1)
        assert tokens == 1

    def test_needs_compaction_below_threshold(self):
        """Messages under 80% threshold should return False."""
        # 1000 chars ~ 250 tokens, out of 128000 max = 0.2%
        messages = [{"role": "user", "content": "x" * 1000}]
        result = self.compactor.needs_compaction(messages)

        import asyncio

        needs = asyncio.run(result)
        assert needs is False

    def test_needs_compaction_at_threshold(self):
        """Messages at exactly 80% threshold should return True."""
        # max_tokens=1000, threshold=0.8 → 800 tokens needed
        # 800 tokens * 4 chars/token = 3200 chars
        compactor = SessionCompactor(
            self.mock_client, threshold=0.8, max_tokens=1000
        )
        messages = [{"role": "user", "content": "x" * 3200}]

        import asyncio

        needs = asyncio.run(compactor.needs_compaction(messages))
        assert needs is True

    def test_needs_compaction_exactly_threshold(self):
        """Messages at exactly threshold boundary return True."""
        compactor = SessionCompactor(
            self.mock_client, threshold=0.5, max_tokens=400
        )
        # 800 chars / 4 = 200 tokens, 200/400 = 50% = exactly threshold
        messages = [{"role": "user", "content": "x" * 800}]

        import asyncio

        needs = asyncio.run(compactor.needs_compaction(messages))
        assert needs is True

    def test_one_time_compaction(self):
        """After first compaction, needs_compaction() returns False."""
        compactor = SessionCompactor(
            self.mock_client, threshold=0.1, max_tokens=100
        )
        messages = [{"role": "user", "content": "x" * 50}]

        import asyncio

        # First check - should need compaction
        assert asyncio.run(compactor.needs_compaction(messages)) is True

        # Simulate compaction
        async def _mock_stream():
            yield "Compacted summary of conversation"

        self.mock_client.send_message.return_value = _mock_stream()
        asyncio.run(compactor.compact(messages, "test task"))

        # After compaction, should not need it
        assert asyncio.run(compactor.needs_compaction(messages)) is False

    def test_compact_reduces_message_count(self):
        """compact() returns shorter list vs input."""
        messages = [
            {"role": "user", "content": "Step 1: Do something"},
            {"role": "assistant", "content": "OK, doing step 1"},
            {"role": "user", "content": "Step 2: Do more"},
            {"role": "assistant", "content": "OK, doing step 2"},
            {"role": "user", "content": "Final step"},
        ]

        async def _mock_stream():
            yield "## COMPACTED CONTEXT\n**Task:** test\n**Summary:** Done work"

        self.mock_client.send_message.return_value = _mock_stream()

        import asyncio

        compacted = asyncio.run(
            self.compactor.compact(messages, "test task")
        )

        # Should have fewer messages than input
        assert len(compacted) < len(messages)
        # Should have at least 1 system message
        assert compacted[0]["role"] == "system"
        assert "COMPACTED CONTEXT" in compacted[0]["content"] or "compacted" in compacted[0]["content"].lower()

    def test_compact_preserves_last_user_message(self):
        """Last user message is preserved when it exists."""
        messages = [
            {"role": "user", "content": "Old message"},
            {"role": "assistant", "content": "Response"},
            {"role": "user", "content": "Final question"},
        ]

        async def _mock_stream():
            yield "Summary of old messages"

        self.mock_client.send_message.return_value = _mock_stream()

        import asyncio

        compacted = asyncio.run(
            self.compactor.compact(messages, "test task")
        )

        # Should have last user message
        last_msg = compacted[-1]
        assert last_msg["role"] == "user"
        assert last_msg["content"] == "Final question"

    def test_compact_no_last_user_message(self):
        """If last message is not user, only system summary is returned."""
        messages = [
            {"role": "user", "content": "Old message"},
            {"role": "assistant", "content": "Final response"},
        ]

        async def _mock_stream():
            yield "Summary"

        self.mock_client.send_message.return_value = _mock_stream()

        import asyncio

        compacted = asyncio.run(
            self.compactor.compact(messages, "test task")
        )

        # Only system message, since last is not user
        assert len(compacted) == 1
        assert compacted[0]["role"] == "system"

    def test_reset_allows_re_compaction(self):
        """After reset, needs_compaction returns to original behavior."""
        compactor = SessionCompactor(
            self.mock_client, threshold=0.1, max_tokens=100
        )
        messages = [{"role": "user", "content": "x" * 50}]

        import asyncio

        # Compact once
        async def _mock_stream():
            yield "Summary"

        self.mock_client.send_message.return_value = _mock_stream()
        asyncio.run(compactor.compact(messages, "test"))

        # After compaction, blocking
        assert asyncio.run(compactor.needs_compaction(messages)) is False

        # Reset
        compactor.reset()
        assert compactor._compacted is False

        # After reset, should need compaction again
        assert asyncio.run(compactor.needs_compaction(messages)) is True

    def test_compaction_prompt_format(self):
        """COMPACTION_PROMPT contains all required fields."""
        required_fields = [
            "**Task:**",
            "**Files modified:**",
            "**Errors:**",
            "**Decisions:**",
            "**Pending:**",
            "**Summary:**",
        ]
        for field in required_fields:
            assert field in COMPACTION_PROMPT, (
                f"Missing required field in COMPACTION_PROMPT: {field}"
            )

        # Verify the prompt has the structured format header
        assert "## COMPACTED CONTEXT" in COMPACTION_PROMPT

    def test_compact_calls_api_with_structured_prompt(self):
        """compact() sends a properly formatted prompt to the API."""
        messages = [
            {"role": "user", "content": "Help me refactor the file"},
            {"role": "assistant", "content": "I'll help refactor"},
            {"role": "user", "content": "Here's the code"},
        ]

        async def _mock_stream():
            yield "Structured summary"

        self.mock_client.send_message.return_value = _mock_stream()

        import asyncio

        asyncio.run(self.compactor.compact(messages, "Refactor task"))

        # Verify API was called with COMPACTION_PROMPT
        self.mock_client.send_message.assert_called_once()
        args, _ = self.mock_client.send_message.call_args
        prompt_arg = args[0]
        assert "Refactor task" in prompt_arg

    def test_default_threshold_and_max_tokens(self):
        """Default constructor values match research recommendations."""
        compactor = SessionCompactor(self.mock_client)
        assert compactor.threshold == 0.8
        assert compactor.max_tokens == 128000
        assert compactor._compacted is False
