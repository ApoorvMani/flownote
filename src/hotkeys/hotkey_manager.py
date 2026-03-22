import threading
import time
import sys
import signal
from src.utils.logger import get_logger

logger = get_logger(__name__)


class HotkeyManager:
    def __init__(self, shortcut: str = "ctrl+shift+s"):
        self.shortcut = shortcut.lower()
        self.running = False
        self.listener_thread = None
        self._callback = None
        self._shutdown_event = threading.Event()

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        logger.info("Shutdown signal received")
        self.stop()
        sys.exit(0)

    def register(self, callback):
        self._callback = callback
        logger.info(f"Hotkey callback registered: {self.shortcut}")

    def _hotkey_loop(self):
        try:
            import keyboard
            logger.info(f"Listening for hotkey: {self.shortcut}")

            while self.running and not self._shutdown_event.is_set():
                try:
                    event = keyboard.read_event(suppress=True)
                    if event.event_type == keyboard.KEY_DOWN:
                        if keyboard.is_pressed(self.shortcut):
                            logger.info("Hotkey triggered!")
                            if self._callback:
                                try:
                                    self._callback()
                                except Exception as e:
                                    logger.error(f"Hotkey callback error: {e}")
                            time.sleep(0.5)
                except Exception as e:
                    logger.error(f"Hotkey read error: {e}")
                    time.sleep(1)

        except ImportError:
            logger.error("keyboard library not installed. Run: pip install keyboard")
            self.running = False

    def start(self):
        if self.running:
            logger.warning("Hotkey manager already running")
            return

        self.running = True
        self._shutdown_event.clear()
        self.listener_thread = threading.Thread(target=self._hotkey_loop, daemon=True)
        self.listener_thread.start()
        logger.info("Hotkey manager started")

    def stop(self):
        if not self.running:
            return

        logger.info("Stopping hotkey manager...")
        self.running = False
        self._shutdown_event.set()

        if self.listener_thread and self.listener_thread.is_alive():
            self.listener_thread.join(timeout=2)

        logger.info("Hotkey manager stopped")

    def is_running(self) -> bool:
        return self.running
