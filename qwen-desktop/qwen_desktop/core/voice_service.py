"""
Voice Service - Speech-to-Text using SpeechRecognition.

Runs in a background thread, continuously listens for speech
until explicitly stopped by the user.
Supports Hindi + English recognition.
"""

import logging
import threading
import time
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    logger.warning("SpeechRecognition not available. Install with: pip install SpeechRecognition")


class VoiceService(QObject):
    """Background voice recognition service.

    Signals:
        text_recognized: Emitted when speech is converted to text.
        error_occurred: Emitted on recognition errors.
        state_changed: Emitted when recording state changes (True/False).
    """

    text_recognized = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    state_changed = pyqtSignal(bool)

    # English first, then Hindi fallback for better English recognition
    LANGUAGES = [
        ("en-US", "English (US)"),
        ("en-IN", "English (India)"),
        ("en-GB", "English (UK)"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._recognizer: Optional[sr.Recognizer] = None
        self._microphone: Optional[sr.Microphone] = None
        self._listening = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_recognized_text = ""
        self._last_recognized_time = 0
        self._debounce_seconds = 2.0  # Prevent duplicate recognition

    def is_available(self) -> bool:
        """Check if speech recognition is available."""
        return SPEECH_RECOGNITION_AVAILABLE

    def start(self):
        """Start continuous voice recognition in background thread."""
        if not self.is_available():
            self.error_occurred.emit("SpeechRecognition not installed. Run: pip install SpeechRecognition PyAudio")
            return

        if self._listening:
            return

        self._stop_event.clear()
        self._listening = True
        self._last_recognized_text = ""
        self._last_recognized_time = 0
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        self.state_changed.emit(True)
        logger.info("Voice service started")

    def stop(self):
        """Stop voice recognition."""
        if not self._listening:
            return

        self._stop_event.set()
        self._listening = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self.state_changed.emit(False)
        logger.info("Voice service stopped")

    def toggle(self) -> bool:
        """Toggle voice recognition on/off. Returns new state."""
        if self._listening:
            self.stop()
            return False
        else:
            self.start()
            return True

    @property
    def is_listening(self) -> bool:
        return self._listening

    def _is_duplicate(self, text: str) -> bool:
        """Check if text is a duplicate recognition within debounce window."""
        now = time.time()
        if text.strip().lower() == self._last_recognized_text.strip().lower():
            if now - self._last_recognized_time < self._debounce_seconds:
                return True
        self._last_recognized_text = text
        self._last_recognized_time = now
        return False

    def _listen_loop(self):
        """Main listening loop - runs in background thread."""
        try:
            self._recognizer = sr.Recognizer()
            self._recognizer.energy_threshold = 300
            self._recognizer.dynamic_energy_threshold = True
            self._recognizer.pause_threshold = 0.8
            self._recognizer.non_speaking_duration = 0.5
            self._recognizer.phrase_threshold = 0.3

            self._microphone = sr.Microphone()

            with self._microphone as source:
                logger.info("Adjusting for ambient noise...")
                self._recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info("Listening for speech...")

                while not self._stop_event.is_set():
                    try:
                        audio = self._recognizer.listen(
                            source,
                            timeout=5,
                            phrase_time_limit=15
                        )

                        if self._stop_event.is_set():
                            break

                        logger.info("Processing speech...")

                        # Try multiple languages, pick best result
                        recognized_text = None
                        for lang_code, lang_name in self.LANGUAGES:
                            try:
                                text = self._recognizer.recognize_google(audio, language=lang_code)
                                if text and text.strip():
                                    recognized_text = text.strip()
                                    logger.info(f"Recognized ({lang_name}): {recognized_text}")
                                    break
                            except sr.UnknownValueError:
                                continue

                        if recognized_text and not self._is_duplicate(recognized_text):
                            self.text_recognized.emit(recognized_text)
                        elif recognized_text:
                            logger.debug(f"Duplicate recognition skipped: {recognized_text}")

                    except sr.WaitTimeoutError:
                        continue
                    except sr.UnknownValueError:
                        continue
                    except sr.RequestError as e:
                        self.error_occurred.emit(f"Speech API error: {e}")
                        break
                    except Exception as e:
                        if self._stop_event.is_set():
                            break
                        logger.error(f"Voice recognition error: {e}")
                        continue

        except Exception as e:
            self.error_occurred.emit(f"Microphone error: {e}")
            logger.error(f"Voice service error: {e}", exc_info=True)
        finally:
            self._listening = False
            self.state_changed.emit(False)
            logger.info("Voice service stopped")
