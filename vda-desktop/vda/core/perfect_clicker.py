"""Shim for backward compatibility.

The original ``perfect_clicker.py`` has been split into a package under
``vda.core.perfect_clicker``.  This file re-exports the public APIs so
existing imports continue to work.
"""

from vda.core.perfect_clicker import SelfCalibrator, PerfectClicker
