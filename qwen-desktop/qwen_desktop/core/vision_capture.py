"""
Vision Capture Service.

Listens for global mouse clicks and keyboard presses via pynput.
On each interaction, takes a screenshot and emits it as a PyQt signal
with full metadata (screen resolution, cursor position, timestamp).

Screenshots are only taken when vision_mode is active.
Debounce of 400ms prevents burst captures on rapid events.
"""

import base64
import io
import logging
import threading
from datetime import datetime
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

# ── safe imports ────────────────────────────────────────────────────────────
try:
    import pyautogui
    PYAUTOGUI_OK = True
except ImportError:
    PYAUTOGUI_OK = False
    logger.warning("pyautogui not installed — vision capture disabled")

try:
    from pynput import mouse as pynput_mouse, keyboard as pynput_keyboard
    PYNPUT_OK = True
except ImportError:
    PYNPUT_OK = False
    logger.warning("pynput not installed — interaction detection disabled")

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False
    logger.warning("Pillow not installed — screenshot quality may be lower")


class VisionCaptureService(QObject):
    """
    Fires screenshot_ready(base64_str, metadata) whenever the user
    interacts with the desktop while vision mode is active.

    metadata dict keys:
        screen_width   int
        screen_height  int
        mouse_x        int   (absolute pixels)
        mouse_y        int
        mouse_x_pct    float (0.0–1.0, resolution-independent)
        mouse_y_pct    float
        timestamp      str   (ISO 8601)
    """

    screenshot_ready = pyqtSignal(str, dict)  # base64_png, metadata

    # Debounce: ignore events within this many seconds of the last capture
    DEBOUNCE_SECS: float = 0.4

    def __init__(self, parent=None):
        super().__init__(parent)
        self._active = False
        self._mouse_listener: Optional[object] = None
        self._keyboard_listener: Optional[object] = None
        self._debounce_timer: Optional[threading.Timer] = None
        self._debounce_lock = threading.Lock()
        self._last_capture_time = 0.0

    # ── public API ──────────────────────────────────────────────────────────

    def start(self) -> bool:
        """Start listening for user interactions. Returns True on success."""
        if not PYAUTOGUI_OK or not PYNPUT_OK:
            logger.error("Cannot start vision capture — missing dependencies")
            return False

        if self._active:
            return True

        self._active = True
        self._start_mouse_listener()
        self._start_keyboard_listener()
        logger.info("VisionCaptureService started")
        return True

    def stop(self):
        """Stop all listeners and cancel pending captures."""
        self._active = False

        if self._debounce_timer:
            self._debounce_timer.cancel()
            self._debounce_timer = None

        if self._mouse_listener:
            try:
                self._mouse_listener.stop()
            except Exception:
                pass
            self._mouse_listener = None

        if self._keyboard_listener:
            try:
                self._keyboard_listener.stop()
            except Exception:
                pass
            self._keyboard_listener = None

        logger.info("VisionCaptureService stopped")

    @property
    def is_active(self) -> bool:
        return self._active

    # ── listeners ───────────────────────────────────────────────────────────

    def _start_mouse_listener(self):
        if not PYNPUT_OK:
            return

        def on_click(x, y, button, pressed):
            if pressed and self._active:
                self._schedule_capture()

        try:
            self._mouse_listener = pynput_mouse.Listener(on_click=on_click)
            self._mouse_listener.daemon = True
            self._mouse_listener.start()
        except Exception as e:
            logger.error(f"Mouse listener start failed: {e}")

    def _start_keyboard_listener(self):
        if not PYNPUT_OK:
            return

        def on_press(key):
            if self._active:
                self._schedule_capture()

        try:
            self._keyboard_listener = pynput_keyboard.Listener(on_press=on_press)
            self._keyboard_listener.daemon = True
            self._keyboard_listener.start()
        except Exception as e:
            logger.error(f"Keyboard listener start failed: {e}")

    # ── capture pipeline ────────────────────────────────────────────────────

    def _schedule_capture(self):
        """Debounce: reset timer on each event, capture after silence."""
        with self._debounce_lock:
            if self._debounce_timer:
                self._debounce_timer.cancel()
            self._debounce_timer = threading.Timer(
                self.DEBOUNCE_SECS, self._do_capture
            )
            self._debounce_timer.daemon = True
            self._debounce_timer.start()

    def _do_capture(self):
        """Take screenshot + gather metadata, then emit signal."""
        if not self._active or not PYAUTOGUI_OK:
            return
        try:
            # Screen info
            screen_w, screen_h = pyautogui.size()
            mouse_x, mouse_y = pyautogui.position()

            # Clamp mouse to screen bounds
            mouse_x = max(0, min(mouse_x, screen_w - 1))
            mouse_y = max(0, min(mouse_y, screen_h - 1))

            # Screenshot → base64 PNG
            screenshot = pyautogui.screenshot()

            # Optionally resize for API efficiency (max 1280px wide)
            if PIL_OK and screen_w > 1280:
                ratio = 1280 / screen_w
                new_w = 1280
                new_h = int(screen_h * ratio)
                screenshot = screenshot.resize(
                    (new_w, new_h), Image.LANCZOS
                )

            if PIL_OK:
                screenshot = screenshot.convert("RGB")

            buf = io.BytesIO()
            screenshot.save(buf, format="JPEG", quality=80, optimize=True)
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

            metadata = {
                "screen_width": screen_w,
                "screen_height": screen_h,
                "mouse_x": mouse_x,
                "mouse_y": mouse_y,
                "mouse_x_pct": round(mouse_x / screen_w, 4),
                "mouse_y_pct": round(mouse_y / screen_h, 4),
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(
                f"Vision capture: {screen_w}x{screen_h} | "
                f"mouse=({mouse_x},{mouse_y}) | "
                f"png={len(b64)//1024}KB"
            )

            # Emit on PyQt thread via signal (thread-safe)
            self.screenshot_ready.emit(b64, metadata)

        except Exception as e:
            logger.error(f"Vision capture failed: {e}", exc_info=True)
