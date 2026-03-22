"""
FlowNote - Global hotkey listener daemon
"""

import threading
import time
import signal
import sys
from typing import Callable, Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)


class HotkeyListener:
    def __init__(self, shortcut: str = "ctrl+shift+s"):
        self.shortcut = shortcut.lower()
        self._running = False
        self._listener_thread: Optional[threading.Thread] = None
        self._callback: Optional[Callable] = None
        self._last_trigger = 0.0
        self._debounce_seconds = 1.5
        self._shutdown_event = threading.Event()

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def register_callback(self, callback: Callable):
        self._callback = callback
        logger.info(f"Hotkey callback registered: {self.shortcut}")

    def start(self):
        if self._running:
            logger.warning("Hotkey listener already running")
            return

        logger.info(f"Starting hotkey listener: {self.shortcut}")
        self._running = True
        self._shutdown_event.clear()
        self._listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listener_thread.start()

    def stop(self):
        if not self._running:
            return

        logger.info("Stopping hotkey listener...")
        self._running = False
        self._shutdown_event.set()

        if self._listener_thread and self._listener_thread.is_alive():
            self._listener_thread.join(timeout=2)

        logger.info("Hotkey listener stopped")

    def is_running(self) -> bool:
        return self._running

    def _signal_handler(self, signum, frame):
        logger.info(f"Received signal {signum}")
        self.stop()
        sys.exit(0)

    def _listen_loop(self):
        try:
            import keyboard
            logger.info(f"Listening for hotkey: {self.shortcut}")

            while self._running and not self._shutdown_event.is_set():
                try:
                    if keyboard.is_pressed(self.shortcut):
                        current_time = time.time()
                        if current_time - self._last_trigger > self._debounce_seconds:
                            self._last_trigger = current_time
                            self._trigger_callback()
                    time.sleep(0.05)
                except Exception as e:
                    logger.error(f"Hotkey error: {e}")
                    time.sleep(1)

        except ImportError:
            logger.error("keyboard library not installed. Run: pip install keyboard")
            self._running = False

    def _trigger_callback(self):
        logger.info("Hotkey triggered!")
        if self._callback:
            try:
                self._callback()
            except Exception as e:
                logger.error(f"Hotkey callback error: {e}")
