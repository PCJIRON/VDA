"""Screen environment detection — DPI, monitor layout, OS platform."""

import ctypes
import logging
import platform
import subprocess
from dataclasses import dataclass
from typing import Dict, List

import pyautogui

logger = logging.getLogger(__name__)


@dataclass
class ScreenEnv:
    """Screen environment detected at runtime"""
    os: str
    logical_w: int
    logical_h: int
    physical_w: int
    physical_h: int
    scale_x: float
    scale_y: float
    dpi: float
    is_hidpi: bool
    monitors: list
    wayland: bool


class ScreenDetector:
    """Runtime screen environment detection."""

    @staticmethod
    def detect() -> ScreenEnv:
        os_name = platform.system().lower()

        if "windows" in os_name:
            return ScreenDetector._detect_windows()
        elif "darwin" in os_name:
            return ScreenDetector._detect_mac()
        else:
            return ScreenDetector._detect_linux()

    @staticmethod
    def _detect_windows() -> ScreenEnv:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32

        phys_w = user32.GetSystemMetrics(0)
        phys_h = user32.GetSystemMetrics(1)

        hdc = user32.GetDC(0)
        dpi_x = gdi32.GetDeviceCaps(hdc, 88)
        dpi_y = gdi32.GetDeviceCaps(hdc, 90)
        user32.ReleaseDC(0, hdc)

        scale_x = dpi_x / 96.0
        scale_y = dpi_y / 96.0

        log_w, log_h = pyautogui.size()

        monitors = ScreenDetector._get_windows_monitors()

        logger.info(f"[ENV] Windows: {log_w}x{log_h} @ {dpi_x} DPI (scale {scale_x:.2f}x)")

        return ScreenEnv(
            os="windows",
            logical_w=log_w, logical_h=log_h,
            physical_w=phys_w, physical_h=phys_h,
            scale_x=scale_x, scale_y=scale_y,
            dpi=float(dpi_x),
            is_hidpi=(scale_x > 1.0),
            monitors=monitors,
            wayland=False
        )

    @staticmethod
    def _get_windows_monitors() -> List[Dict]:  # noqa: N802
        monitors = []
        try:
            EnumDisplayMonitors = ctypes.windll.user32.EnumDisplayMonitors
            GetMonitorInfoW = ctypes.windll.user32.GetMonitorInfoW

            class RECT(ctypes.Structure):
                _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                            ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

            class MONITORINFO(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_ulong), ("rcMonitor", RECT),
                            ("rcWork", RECT), ("dwFlags", ctypes.c_ulong)]

            def callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
                info = MONITORINFO()
                info.cbSize = ctypes.sizeof(MONITORINFO)
                GetMonitorInfoW(hMonitor, ctypes.byref(info))
                r = info.rcMonitor
                monitors.append({
                    "x": r.left, "y": r.top,
                    "w": r.right - r.left,
                    "h": r.bottom - r.top,
                    "primary": bool(info.dwFlags & 1)
                })
                return True

            MONITORENUMPROC = ctypes.WINFUNCTYPE(
                ctypes.c_bool, ctypes.c_ulong, ctypes.c_ulong,
                ctypes.POINTER(RECT), ctypes.c_double)
            EnumDisplayMonitors(0, None, MONITORENUMPROC(callback), 0)
        except Exception as e:
            logger.warning(f"Monitor detection failed: {e}")
            monitors = [{"x": 0, "y": 0, "w": 1920, "h": 1080, "primary": True}]
        return monitors

    @staticmethod
    def _detect_mac() -> ScreenEnv:
        try:
            from AppKit import NSScreen
            screen = NSScreen.mainScreen()
            frame = screen.frame()
            backing = screen.backingScaleFactor()

            log_w = int(frame.size.width)
            log_h = int(frame.size.height)
            phys_w = int(log_w * backing)
            phys_h = int(log_h * backing)

            monitors = []
            for s in NSScreen.screens():
                f = s.frame()
                monitors.append({
                    "x": int(f.origin.x), "y": int(f.origin.y),
                    "w": int(f.size.width), "h": int(f.size.height),
                    "scale": s.backingScaleFactor()
                })

            logger.info(f"[ENV] macOS: {log_w}x{log_h} @ {backing:.1f}x (Retina)")

        except ImportError:
            log_w, log_h = pyautogui.size()
            ss = pyautogui.screenshot()
            phys_w, phys_h = ss.size
            backing = phys_w / log_w if log_w > 0 else 1.0
            monitors = [{"x": 0, "y": 0, "w": log_w, "h": log_h, "scale": backing}]
            logger.warning(f"[ENV] macOS fallback: {log_w}x{log_h} @ {backing:.1f}x")

        return ScreenEnv(
            os="mac",
            logical_w=log_w, logical_h=log_h,
            physical_w=phys_w, physical_h=phys_h,
            scale_x=backing, scale_y=backing,
            dpi=96.0 * backing,
            is_hidpi=(backing > 1.0),
            monitors=monitors,
            wayland=False
        )

    @staticmethod
    def _detect_linux() -> ScreenEnv:
        wayland = bool(
            subprocess.run(["sh", "-c", "echo $WAYLAND_DISPLAY"],
                           capture_output=True).stdout.strip()
        )

        log_w, log_h = pyautogui.size()

        scale = 1.0
        try:
            result = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "scaling-factor"],
                capture_output=True, text=True)
            scale = float(result.stdout.strip().strip("'")) or 1.0
        except Exception as e:
            logger.debug(f"Scaling detection failed: {e}")

        phys_w, phys_h = log_w, log_h
        try:
            out = subprocess.run(["xrandr", "--current"],
                                  capture_output=True, text=True).stdout
            for line in out.splitlines():
                if " connected " in line and "*" in line:
                    import re
                    m = re.search(r"(\d+)x(\d+)\+0\+0", line)
                    if m:
                        phys_w, phys_h = int(m[1]), int(m[2])
                        break
        except Exception as e:
            logger.debug(f"xrandr failed: {e}")

        logger.info(f"[ENV] Linux: {log_w}x{log_h} (scale {scale:.1f}x, Wayland={wayland})")

        return ScreenEnv(
            os="linux",
            logical_w=log_w, logical_h=log_h,
            physical_w=phys_w, physical_h=phys_h,
            scale_x=phys_w / log_w if log_w else 1.0,
            scale_y=phys_h / log_h if log_h else 1.0,
            dpi=96.0 * scale,
            is_hidpi=(scale > 1.0),
            monitors=[{"x": 0, "y": 0, "w": log_w, "h": log_h}],
            wayland=wayland
        )


__all__ = ["ScreenEnv", "ScreenDetector"]
