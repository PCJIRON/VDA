"""Tests for the PermissionSystem.

Covers allow/deny/ask logic for different tool types and agent type
configurations, session caching behavior, and the PermissionDecision enum.
"""

import pytest

from qwen_desktop.core.agent_manager.permission_system import (
    PermissionSystem,
    PermissionDecision,
)


# Test configuration matching defaults.py AGENT_TYPES
TEST_AGENT_TYPES = {
    "main": {
        "tools": [
            "web_search", "web_fetch", "terminal",
            "file_read", "file_write", "file_glob", "file_grep",
            "voice",
        ],
        "permission_defaults": {
            "allow_read": True,
            "ask_mutation": True,
            "deny_destructive": True,
        },
    },
    "web": {
        "tools": ["web_search", "web_fetch"],
        "permission_defaults": {
            "allow_read": True,
            "ask_mutation": False,
            "deny_destructive": True,
        },
    },
    "terminal": {
        "tools": ["terminal"],
        "permission_defaults": {
            "allow_read": False,
            "ask_mutation": True,
            "deny_destructive": True,
        },
    },
    "file": {
        "tools": ["file_read", "file_write", "file_glob", "file_grep"],
        "permission_defaults": {
            "allow_read": True,
            "ask_mutation": True,
            "deny_destructive": True,
        },
    },
    "voice": {
        "tools": ["voice"],
        "permission_defaults": {
            "allow_read": True,
            "ask_mutation": False,
            "deny_destructive": True,
        },
    },
}


@pytest.fixture
def perm_system():
    """Create a PermissionSystem with test agent types."""
    return PermissionSystem(settings={"agent_types": TEST_AGENT_TYPES})


class TestPermissionSystem:
    """Test permission allow/deny/ask logic."""

    def test_allow_read_tool(self, perm_system):
        """Read-only tools for 'main' agent should return ALLOW."""
        result = perm_system.check_permission("file_read", agent_type="main")
        assert result == PermissionDecision.ALLOW

    def test_allow_web_search(self, perm_system):
        """Web search is a read tool, should be ALLOW for main."""
        result = perm_system.check_permission("web_search", agent_type="main")
        assert result == PermissionDecision.ALLOW

    def test_ask_mutation_tool(self, perm_system):
        """Mutation tools for 'main' agent should return ASK."""
        result = perm_system.check_permission("terminal", agent_type="main")
        assert result == PermissionDecision.ASK

    def test_ask_file_write(self, perm_system):
        """file_write is a mutation tool, should return ASK."""
        result = perm_system.check_permission("file_write", agent_type="main")
        assert result == PermissionDecision.ASK

    def test_unknown_tool_asks(self, perm_system):
        """Unknown tools should return ASK."""
        result = perm_system.check_permission("unknown_tool", agent_type="main")
        assert result == PermissionDecision.ASK

    def test_agent_type_scoping_web_allows_search(self, perm_system):
        """'web_search' is in web agent scope → ALLOW."""
        result = perm_system.check_permission("web_search", agent_type="web")
        assert result == PermissionDecision.ALLOW

    def test_agent_type_scoping_web_denies_terminal(self, perm_system):
        """'terminal' is not in web agent scope → ASK (tool not in allowed list)."""
        result = perm_system.check_permission("terminal", agent_type="web")
        assert result == PermissionDecision.ASK

    def test_agent_type_scoping_terminal_asks_mutation(self, perm_system):
        """terminal agent calls terminal tool → ASK (mutation)."""
        result = perm_system.check_permission("terminal", agent_type="terminal")
        assert result == PermissionDecision.ASK

    def test_cache_works(self, perm_system):
        """Cached decisions are returned without re-evaluation."""
        # First call — uncached
        result1 = perm_system.check_permission("file_read", agent_type="main")
        assert result1 == PermissionDecision.ALLOW

        # Cache the decision explicitly (overrides default if needed)
        perm_system.cache_decision(
            "file_read", "main", None, PermissionDecision.ALLOW
        )

        # Second call — should be cached
        result2 = perm_system.check_permission("file_read", agent_type="main")
        assert result2 == PermissionDecision.ALLOW

    def test_cache_deny_works(self, perm_system):
        """Cached DENY decision is returned."""
        perm_system.cache_decision(
            "file_write", "main", {"path": "/test"}, PermissionDecision.DENY
        )
        result = perm_system.check_permission(
            "file_write", "main", {"path": "/test"}
        )
        assert result == PermissionDecision.DENY

    def test_cache_clear(self, perm_system):
        """After clear_cache, previously cached entry is re-evaluated."""
        # Cache a decision
        perm_system.cache_decision(
            "file_read", "main", None, PermissionDecision.ALLOW
        )
        assert len(perm_system._cache) > 0

        # Clear cache
        perm_system.clear_cache()

        # Should be re-evaluated (file_read → read tool → ALLOW)
        result = perm_system.check_permission("file_read", agent_type="main")
        assert result == PermissionDecision.ALLOW

    def test_cache_diff_args_different_entry(self, perm_system):
        """Different args should produce different cache entries."""
        perm_system.cache_decision(
            "file_write", "main", {"path": "/a"}, PermissionDecision.ALLOW
        )
        perm_system.cache_decision(
            "file_write", "main", {"path": "/b"}, PermissionDecision.DENY
        )

        result_a = perm_system.check_permission(
            "file_write", "main", {"path": "/a"}
        )
        result_b = perm_system.check_permission(
            "file_write", "main", {"path": "/b"}
        )

        assert result_a == PermissionDecision.ALLOW
        assert result_b == PermissionDecision.DENY

    def test_permission_decision_enum(self):
        """Verify ALLOW, DENY, ASK all exist with correct values."""
        assert PermissionDecision.ALLOW.value == "allow"
        assert PermissionDecision.DENY.value == "deny"
        assert PermissionDecision.ASK.value == "ask"

    def test_no_settings_fallback(self):
        """PermissionSystem without settings uses module-level AGENT_TYPES."""
        system = PermissionSystem()
        # Should not crash — uses defaults.py AGENT_TYPES constant
        result = system.check_permission("web_search", agent_type="main")
        assert result in (
            PermissionDecision.ALLOW,
            PermissionDecision.ASK,
        )

    def test_agent_type_without_tools_list(self):
        """Agent type without explicit tools list uses default classification."""
        system = PermissionSystem(settings={"agent_types": {"custom": {}}})
        # No tools list means no restriction — web_search classified as read → ALLOW
        result = system.check_permission("web_search", agent_type="custom")
        assert result == PermissionDecision.ALLOW

    def test_empty_agent_type_asks(self):
        """Empty agent type config should return ASK."""
        system = PermissionSystem(settings={"agent_types": {}})
        result = system.check_permission("terminal", agent_type="nonexistent")
        assert result == PermissionDecision.ASK
