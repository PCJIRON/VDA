"""QThread worker for streaming API responses."""

import asyncio
import logging

from PyQt6.QtCore import QThread, pyqtSignal

from qwen_desktop.core.thinking_filter import extract_thinking

logger = logging.getLogger(__name__)


class APIServerWorker(QThread):
    chunk_received = pyqtSignal(str)
    thinking_changed = pyqtSignal(str)
    finished_response = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, api_client, message, history, vision_mode=False):
        super().__init__()
        self.api_client = api_client
        self.message = message
        self.history = list(history)
        self.vision_mode = vision_mode
        self._full_response = ""
        self._thinking = ""
        self._visible = ""

    def run(self):
        try:
            asyncio.run(self._stream())
        except Exception as e:
            self.error_occurred.emit(str(e))

    async def _stream(self):
        try:
            chunk_count = 0
            async for chunk in self.api_client.send_message(
                self.message, self.history, vision_mode=self.vision_mode
            ):
                chunk_count += 1
                if chunk_count == 1:
                    logger.info(f"[Worker] First chunk received ({len(chunk)} chars): {chunk[:80]}")
                self._full_response += chunk
                visible, thinking = extract_thinking(self._full_response)
                if visible != self._visible:
                    self._visible = visible
                    self.chunk_received.emit(visible)
                if thinking != self._thinking:
                    self._thinking = thinking
                    self.thinking_changed.emit(thinking)
            logger.info(f"[Worker] Stream complete: {chunk_count} chunks, {len(self._full_response)} chars total, visible={len(self._visible)}")
            if not self._full_response and chunk_count == 0:
                logger.warning("[Worker] API returned no content")
                self.finished_response.emit("")
                return
            final_visible = self._visible if self._visible else self._full_response
            self.finished_response.emit(final_visible)
        except Exception as e:
            logger.error(f"[Worker] Stream error: {e}", exc_info=True)
            self.error_occurred.emit(str(e))
