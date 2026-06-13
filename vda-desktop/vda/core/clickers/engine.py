"""ClickerEngine orchestrator and ClickStrategy abstract base class."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from vda.utils.safety import restore_failsafe
from vda.utils.screen import ScreenDetector, ScreenEnv

logger = logging.getLogger(__name__)


@dataclass
class ClickResult:
    success: bool
    x: int
    y: int
    strategy_used: str
    confidence: float


class ClickStrategy(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def click(self, x: int, y: int, **kwargs) -> ClickResult:
        ...


class ClickerEngine:
    def __init__(self, strategies: list[ClickStrategy]) -> None:
        self.strategies = strategies

    def execute(self, x: int, y: int, target_name: Optional[str] = None) -> ClickResult:
        for strategy in self.strategies:
            try:
                result = strategy.click(x, y, target_name=target_name)
                if result.success:
                    return result
                logger.debug(f"Strategy {strategy.name} failed for ({x}, {y})")
            except Exception as e:
                logger.warning(f"Strategy {strategy.name} raised: {e}")
        return ClickResult(False, x, y, "none", 0.0)

    def execute_with_failsafe(self, x: int, y: int, target_name: Optional[str] = None) -> ClickResult:
        with restore_failsafe():
            return self.execute(x, y, target_name)

    @staticmethod
    def detect_screen() -> ScreenEnv:
        return ScreenDetector.detect()
