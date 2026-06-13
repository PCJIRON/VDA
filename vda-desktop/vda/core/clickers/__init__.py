"""Clicker engine package — consolidated click execution with pluggable strategies."""

from vda.core.clickers.engine import ClickerEngine, ClickResult, ClickStrategy

__all__ = ["ClickerEngine", "ClickStrategy", "ClickResult"]
