"""Session compactor — automatic conversation compaction to prevent context overflow.

Monitors token usage against a configurable threshold (default 80%) and
triggers structured LLM-based summarization when needed. One-time per session
guard prevents re-compaction loops. Structured summarization preserves critical
details (file paths, errors, decisions, pending items) per research Pitfall 4.
"""

import logging
from typing import Any

from vda.core.api_client import APIClient

logger = logging.getLogger(__name__)

COMPACTION_PROMPT = """Summarize the conversation so far for continuation. Preserve all critical details:

CRITICAL — must preserve exactly:
- File paths and file contents modified
- Exact error messages and error codes
- Decisions made and the reasoning
- Commands executed and their output
- Current task state and what remains incomplete

Format:
## COMPACTED CONTEXT
**Task:** {original_task}
**Files modified:** [paths]
**Errors:** [exact messages]
**Decisions:** [key decisions with rationale]
**Pending:** [what remains to be done]
**Summary:** {conversation_summary}"""


class SessionCompactor:
    """Monitors token count and triggers compaction at configurable threshold.

    Uses a rough token estimation (char_count // 4) to determine when the
    conversation approaches the token limit. When the threshold is exceeded,
    compact() sends the conversation to the LLM for structured summarization
    and returns a shortened message list.

    Attributes:
        threshold: Fraction of max_tokens that triggers compaction (0.0-1.0).
        max_tokens: Maximum tokens allowed before compaction is needed.
    """

    def __init__(
        self,
        api_client: APIClient,
        threshold: float = 0.8,
        max_tokens: int = 128000,
    ) -> None:
        """Initialize the session compactor.

        Args:
            api_client: APIClient instance for LLM-based summarization.
            threshold: Fraction of max_tokens that triggers compaction
                (default 0.8 = 80%).
            max_tokens: Maximum token capacity (default 128000).
        """
        self.api_client = api_client
        self.threshold = threshold
        self.max_tokens = max_tokens
        self._compacted = False

    @staticmethod
    def estimate_tokens(messages: list[dict[str, Any]]) -> int:
        """Rough token estimation: ~4 characters per token.

        Per research assumption A5, this is accurate enough for compaction
        threshold triggering. Uses the total character count of all message
        content fields divided by 4.

        Args:
            messages: List of conversation message dicts with 'content' keys.

        Returns:
            Estimated token count.
        """
        total_chars = sum(
            len(str(m.get("content", ""))) for m in messages
        )
        return total_chars // 4

    async def needs_compaction(
        self, messages: list[dict[str, Any]]
    ) -> bool:
        """Check if compaction is needed based on token threshold.

        Returns False if compaction has already occurred in this session
        (one-time guard prevents re-compaction loops).

        Args:
            messages: Current conversation message list.

        Returns:
            True if token ratio exceeds threshold and not yet compacted.
        """
        if self._compacted:
            logger.debug("[Compact] Already compacted this session — skipping")
            return False

        tokens = self.estimate_tokens(messages)
        ratio = tokens / self.max_tokens if self.max_tokens > 0 else 0.0
        logger.info(
            "[Compact] Token ratio: %.1f%% (%d/%d)",
            ratio * 100,
            tokens,
            self.max_tokens,
        )
        return ratio >= self.threshold

    async def compact(
        self,
        messages: list[dict[str, Any]],
        original_task: str,
    ) -> list[dict[str, Any]]:
        """Compress conversation history via LLM summarization.

        Finds the oldest user message, builds the portion to compact from
        that message to the second-to-last, sends it to the LLM for
        structured summarization, and returns a shortened message list
        with the summary prepended as a system message.

        The caller (AgentWorker in Plan 04) is responsible for writing the
        compacted context back to SessionService. SessionCompactor only
        handles the summarization and message list transformation.

        Args:
            messages: Full conversation message list to compact.
            original_task: The original task description for context.

        Returns:
            Compacted message list ([system summary, last_user_message]).
        """
        # Find the oldest user message to summarize from
        oldest_user_idx = 0
        for i, msg in enumerate(messages):
            if msg.get("role") == "user":
                oldest_user_idx = i
                break

        # Build the portion to compact (from oldest user to second-to-last)
        to_compact = messages[oldest_user_idx:-1] if len(messages) > 1 else messages
        conversation_text = "\n".join(
            f"{m.get('role', 'unknown')}: {str(m.get('content', ''))[:500]}"
            for m in to_compact
        )

        # Call LLM for structured summary
        prompt = COMPACTION_PROMPT.format(
            original_task=original_task,
            conversation_summary=conversation_text,
        )
        full_response = ""
        async for chunk in self.api_client.send_message(prompt, []):
            full_response += chunk

        # Build compacted message list
        compacted: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": f"[Previous context compacted: {full_response[:2000]}]",
            }
        ]

        # Keep the last user message if it exists
        if messages and messages[-1].get("role") == "user":
            compacted.append(messages[-1])

        self._compacted = True
        logger.info(
            "[Compact] Done: %d -> %d messages",
            len(messages),
            len(compacted),
        )
        return compacted

    def reset(self) -> None:
        """Reset the compaction flag for a new session.

        Allows needs_compaction() and compact() to be called again
        in subsequent sessions.
        """
        self._compacted = False
        logger.debug("[Compact] Reset compaction flag")
