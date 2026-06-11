"""Perfect Clicker package.

Re-exports ``SelfCalibrator`` and ``PerfectClicker`` so existing imports keep
working.
"""

from .calibrator import SelfCalibrator
from .clicker import PerfectClicker

__all__ = ["SelfCalibrator", "PerfectClicker"]
