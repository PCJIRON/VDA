"""Tests for clicker engine and strategies."""

from unittest.mock import MagicMock, patch

import pytest

from vda.core.clickers.engine import ClickerEngine, ClickResult, ClickStrategy


class PassThroughStrategy(ClickStrategy):
    @property
    def name(self) -> str:
        return "passthrough"

    def click(self, x: int, y: int, **kwargs) -> ClickResult:
        return ClickResult(True, x, y, self.name, 1.0)


class FailingStrategy(ClickStrategy):
    @property
    def name(self) -> str:
        return "failing"

    def click(self, x: int, y: int, **kwargs) -> ClickResult:
        return ClickResult(False, x, y, self.name, 0.0)


class CrashingStrategy(ClickStrategy):
    @property
    def name(self) -> str:
        return "crashing"

    def click(self, x: int, y: int, **kwargs) -> ClickResult:
        raise RuntimeError("strategy crash")


@pytest.fixture
def engine():
    strategies = [PassThroughStrategy()]
    return ClickerEngine(strategies)


class TestClickResult:
    def test_dataclass_fields(self):
        r = ClickResult(True, 100, 200, "test", 0.95)
        assert r.success is True
        assert r.x == 100
        assert r.y == 200
        assert r.strategy_used == "test"
        assert r.confidence == 0.95


class TestClickerEngine:
    def test_execute_with_first_strategy(self, engine):
        result = engine.execute(100, 200)
        assert result.success is True
        assert result.strategy_used == "passthrough"

    def test_execute_falls_through_to_next(self):
        strategies = [FailingStrategy(), PassThroughStrategy()]
        engine = ClickerEngine(strategies)
        result = engine.execute(100, 200)
        assert result.success is True
        assert result.strategy_used == "passthrough"

    def test_execute_returns_failure_when_all_fail(self):
        strategies = [FailingStrategy(), FailingStrategy()]
        engine = ClickerEngine(strategies)
        result = engine.execute(100, 200)
        assert result.success is False
        assert result.strategy_used == "none"

    def test_execute_handles_crashing_strategy(self):
        strategies = [CrashingStrategy(), PassThroughStrategy()]
        engine = ClickerEngine(strategies)
        result = engine.execute(100, 200)
        assert result.success is True
        assert result.strategy_used == "passthrough"

    @patch("vda.core.clickers.engine.restore_failsafe")
    def test_execute_with_failsafe(self, mock_failsafe, engine):
        mock_failsafe.return_value.__enter__ = MagicMock()
        mock_failsafe.return_value.__exit__ = MagicMock()
        engine.execute_with_failsafe(100, 200)


class TestPassThroughStrategy:
    def test_click_returns_result(self):
        strategy = PassThroughStrategy()
        result = strategy.click(100, 200)
        assert result.success is True
        assert result.x == 100
        assert result.y == 200
        assert result.strategy_used == "passthrough"

    def test_name_property(self):
        strategy = PassThroughStrategy()
        assert strategy.name == "passthrough"
