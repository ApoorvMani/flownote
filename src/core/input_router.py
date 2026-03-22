"""
FlowNote - Input router that coordinates capture flow
"""

import threading
from typing import Optional, Callable
from enum import Enum

from src.config import get_config
from src.utils.logger import get_logger
from src.input_handlers.clipboard import ClipboardHandler
from src.input_handlers.screenshot import ScreenshotHandler
from src.input_handlers.link_fetcher import LinkFetcher
from src.processors.ai_processor import AIProcessor
from src.processors.note_formatter import NoteFormatter
from src.storage.note_storage import NoteStorage
from src.core.memory import get_memory

logger = get_logger(__name__)


class InputMode(Enum):
    CLIPBOARD = "clipboard"
    SCREENSHOT = "screenshot"
    LINK = "link"
    AUTO = "auto"


class InputRouter:
    def __init__(self, mode: InputMode = InputMode.AUTO, note_style: str = None):
        self.config = get_config()
        self.mode = mode
        self.memory = get_memory()
        self._note_style = note_style or self.memory.get_note_style()
        self.ai_processor = AIProcessor(note_style=self._note_style)
        self.note_formatter = NoteFormatter()
        self.note_storage = NoteStorage()
        self._current_model: Optional[str] = None
        self._last_successful_note: Optional[str] = None

    def set_model(self, model: str):
        self._current_model = model
        self.ai_processor = AIProcessor(model=model, note_style=self._note_style)

    def set_note_style(self, style: str):
        self._note_style = style
        self.ai_processor = AIProcessor(model=self._current_model, note_style=style)

    def capture_and_process(self, mode: Optional[InputMode] = None) -> tuple[bool, str]:
        capture_mode = mode or self.mode
        logger.info(f"Starting capture in {capture_mode.value} mode")

        content = self._get_content(capture_mode)
        if not content:
            return False, ""

        ai_response = self._process_with_ai(content)
        if not ai_response:
            return False, ""

        formatted_note = self._format_and_save(ai_response)
        if formatted_note:
            self._last_successful_note = formatted_note
            topic = self.memory.detect_topic(content)
            self.memory.add_note_to_history(ai_response, source=capture_mode.value, topic=topic)

        return True, formatted_note

    def capture_async(self, mode: InputMode, callback: Callable[[bool, str], None]):
        thread = threading.Thread(target=self._capture_worker, args=(mode, callback), daemon=True)
        thread.start()

    def _capture_worker(self, mode: InputMode, callback: Callable[[bool, str], None]):
        success, note = self.capture_and_process(mode)
        if callback:
            callback(success, note)

    def get_last_note(self) -> Optional[str]:
        return self._last_successful_note or self.memory.get_last_note()

    def revert_last_note(self) -> bool:
        last = self._last_successful_note or self.memory.get_last_note()
        if last:
            logger.info("Reverting last note...")
            from datetime import datetime
            timestamp = datetime.now()
            try:
                self.note_storage.save_note(last, timestamp)
                return True
            except Exception as e:
                logger.error(f"Revert failed: {e}")
                return False
        return False

    def _get_content(self, mode: InputMode) -> str:
        if mode == InputMode.SCREENSHOT:
            return self._get_screenshot_content()
        elif mode == InputMode.LINK:
            return self._get_link_content()
        elif mode == InputMode.CLIPBOARD:
            return self._get_clipboard_content()
        else:
            return self._get_auto_content()

    def _get_auto_content(self) -> str:
        clipboard_text = ClipboardHandler.get_text()

        if not clipboard_text:
            logger.info("Clipboard empty")
            return ""

        if LinkFetcher.is_valid_url(clipboard_text):
            logger.info("Detected URL in clipboard")
            return self._fetch_url(clipboard_text)

        logger.info(f"Clipboard text: {len(clipboard_text)} chars")
        return clipboard_text

    def _get_clipboard_content(self) -> str:
        content = ClipboardHandler.get_text()
        if not content:
            return ""

        if LinkFetcher.is_valid_url(content):
            return self._fetch_url(content)

        return content

    def _get_screenshot_content(self) -> str:
        if not ScreenshotHandler.is_available():
            logger.error("Tesseract not available")
            return ""

        try:
            return ScreenshotHandler.capture_and_extract()
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return ""

    def _get_link_content(self) -> str:
        url = ClipboardHandler.get_text()
        if not url or not LinkFetcher.is_valid_url(url):
            logger.warning("No valid URL in clipboard")
            return ""
        return self._fetch_url(url)

    def _fetch_url(self, url: str) -> str:
        try:
            title, content = LinkFetcher.fetch_and_clean(url)
            logger.info(f"Fetched {len(content)} chars from {title}")
            return content
        except Exception as e:
            logger.error(f"URL fetch failed: {e}")
            return ""

    def _process_with_ai(self, content: str) -> str:
        if not content:
            return ""

        try:
            context = self.memory.build_context_prompt(content)
            topic = self.memory.detect_topic(content)
            if topic:
                topic_style = self.memory.get_topic_style(topic)
                if topic_style:
                    effective_style = topic_style
                else:
                    effective_style = self._note_style
            else:
                effective_style = self._note_style

            response = self.ai_processor.generate_notes(content, style=effective_style, context=context)
            if self.ai_processor.validate_response(response):
                return response
            logger.warning("AI response validation failed")
            return ""
        except Exception as e:
            logger.error(f"AI processing failed: {e}")
            return ""

    def _format_and_save(self, ai_response: str) -> str:
        if not ai_response:
            return ""

        from datetime import datetime
        timestamp = datetime.now()
        formatted = self.note_formatter.format_notes(ai_response, timestamp)

        try:
            self.note_storage.save_note(formatted, timestamp)
            return formatted
        except Exception as e:
            logger.error(f"Save failed: {e}")
            return ""
