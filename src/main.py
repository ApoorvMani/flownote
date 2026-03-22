import sys
import argparse
import threading
import time
from datetime import datetime

from src.config import get_config
from src.utils.logger import get_logger
from src.utils.ollama_checker import OllamaChecker
from src.input_handlers.clipboard import ClipboardHandler
from src.input_handlers.screenshot import ScreenshotHandler
from src.input_handlers.link_fetcher import LinkFetcher
from src.processors.ai_processor import AIProcessor
from src.processors.note_formatter import NoteFormatter
from src.storage.note_storage import NoteStorage


class NotesTool:
    def __init__(self, mode: str = "clipboard"):
        self.config = get_config()
        self.logger = get_logger("notes_tool")
        self.mode = mode
        self._selected_model = None
        self.logger.info(f"Notes Tool initialized (mode: {mode})")

    def run(self):
        self.logger.info("Starting notes capture process...")

        if not self._check_ollama():
            return False

        content = self._get_content()
        if not content:
            self.logger.error("No content provided")
            return False

        ai_response = self._process_with_ai(content)
        if not ai_response:
            return False

        note = self._format_and_save(ai_response)
        if note:
            self.logger.info("Notes saved successfully!")
            print("\n" + "=" * 50)
            print("SUCCESS: Notes saved to file")
            print("=" * 50)
            return True

        return False

    def run_capture(self):
        try:
            self.run()
        except Exception as e:
            self.logger.error(f"Capture failed: {e}")

    def _check_ollama(self) -> bool:
        self.logger.info("Checking Ollama status...")
        base_url = self.config.ollama_base_url

        if not OllamaChecker.ensure_ollama_running(base_url):
            return False

        self._selected_model = OllamaChecker.auto_select_model(base_url, self.config.ollama_model)
        if self._selected_model:
            self.logger.info(f"Selected model: {self._selected_model}")

        return True

    def _get_content(self) -> str:
        if self.mode == "screenshot":
            return self._get_screenshot_content()
        elif self.mode == "link":
            return self._get_link_content()
        return self._get_clipboard_content()

    def _get_clipboard_content(self) -> str:
        self.logger.info("Getting content from clipboard...")
        content = ClipboardHandler.get_content_or_prompt()

        if not content:
            self.logger.warning("No content available")
            print("\nERROR: No content to process")
            return ""

        if LinkFetcher.is_valid_url(content):
            return self._get_link_content_from_url(content)

        self.logger.info(f"Content retrieved ({len(content)} characters)")
        return content

    def _get_link_content(self) -> str:
        print("\nEnter URL to fetch: ", end="")
        url = input().strip()

        if not url:
            print("ERROR: No URL provided")
            return ""

        return self._get_link_content_from_url(url)

    def _get_link_content_from_url(self, url: str) -> str:
        self.logger.info(f"Fetching URL: {url}")

        try:
            title, content = LinkFetcher.fetch_and_clean(url)

            if len(content) < 100:
                self.logger.warning(f"Extracted content very short ({len(content)} chars)")
                print(f"\nWARNING: Page may not have meaningful content")

            self.logger.info(f"Extracted {len(content)} characters from {title}")
            return content

        except TimeoutError as e:
            self.logger.error(f"Timeout fetching URL: {e}")
            print(f"\nERROR: {e}")
            return ""
        except ConnectionError as e:
            self.logger.error(f"Network error: {e}")
            print(f"\nERROR: {e}")
            return ""
        except ValueError as e:
            self.logger.error(f"Invalid URL: {e}")
            print(f"\nERROR: {e}")
            return ""
        except RuntimeError as e:
            self.logger.error(f"Fetch failed: {e}")
            print(f"\nERROR: {e}")
            return ""
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            print(f"\nERROR: {e}")
            return ""

    def _get_screenshot_content(self) -> str:
        self.logger.info("Capturing screenshot...")

        if not ScreenshotHandler.is_available():
            self.logger.error("OCR not available. Install tesseract-ocr.")
            print("\nERROR: Tesseract OCR not installed")
            print("\nInstall instructions:")
            print("  Ubuntu/Debian: sudo apt install tesseract-ocr")
            print("  macOS: brew install tesseract")
            print("  Windows: https://github.com/UB-Mannheim/tesseract/wiki")
            return ""

        try:
            content = ScreenshotHandler.capture_and_extract()
            if not content:
                self.logger.warning("No text found in screenshot")
                print("\nWARNING: No text detected in screenshot")
                return ""

            self.logger.info(f"Screenshot OCR extracted {len(content)} characters")
            return content

        except RuntimeError as e:
            if "Tesseract" in str(e):
                print(f"\nERROR: {e}")
            else:
                print(f"\nERROR: {e}")
            return ""
        except Exception as e:
            self.logger.error(f"Screenshot capture failed: {e}")
            print(f"\nERROR: {e}")
            return ""

    def _process_with_ai(self, content: str) -> str:
        self.logger.info("Processing content with AI...")
        model = self._selected_model or self.config.ollama_model
        processor = AIProcessor(model=model)

        try:
            response = processor.generate_notes(content)
            if not processor.validate_response(response):
                self.logger.error("AI response validation failed")
                print("\nERROR: Invalid response from AI")
                return ""

            self.logger.info(f"AI processing complete ({len(response)} chars)")
            return response

        except TimeoutError as e:
            self.logger.error(f"AI timeout: {e}")
            print(f"\nERROR: {e}")
            print("Suggestion: Try again or use smaller text")
            return ""
        except ConnectionError as e:
            self.logger.error(f"Connection error: {e}")
            print(f"\nERROR: {e}")
            return ""
        except Exception as e:
            self.logger.error(f"AI processing failed: {e}")
            print(f"\nERROR: {e}")
            return ""

    def _format_and_save(self, ai_response: str) -> bool:
        timestamp = datetime.now()
        formatter = NoteFormatter()
        storage = NoteStorage()

        prefix_map = {"screenshot": "[SCREENSHOT] ", "link": "[LINK] "}
        prefix = prefix_map.get(self.mode, "")

        formatted_note = formatter.format_notes(ai_response, timestamp, prefix)

        try:
            filepath = storage.save_note(formatted_note, timestamp)
            print(f"File: {filepath}")
            return True
        except IOError as e:
            self.logger.error(f"Failed to save notes: {e}")
            print(f"\nERROR: Failed to save notes - {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error saving notes: {e}")
            print(f"\nERROR: {e}")
            return False


class HotkeyRunner:
    _thread_lock = threading.Lock()
    _active_threads: int = 0
    _max_threads: int = 5

    def __init__(self, shortcut: str | None = None, mode: str = "clipboard"):
        self.config = get_config()
        self.shortcut = (shortcut or self.config.hotkey_capture).lower()
        self.mode = mode
        self.logger = get_logger("hotkey_runner")
        self._running = False
        self._listener_thread = None

    def _can_spawn_worker(self) -> bool:
        with self._thread_lock:
            if self._active_threads >= self._max_threads:
                return False
            self._active_threads += 1
            return True

    def _release_worker(self):
        with self._thread_lock:
            self._active_threads = max(0, self._active_threads - 1)

    def _capture_worker(self):
        try:
            self.logger.info("Starting capture worker...")
            tool = NotesTool(mode=self.mode)
            tool.run_capture()
        finally:
            self._release_worker()

    def _hotkey_loop(self):
        import keyboard

        self.logger.info(f"Listening for hotkey: {self.shortcut}")
        print(f"\n[{time.strftime('%H:%M:%S')}] Hotkey active: {self.shortcut.upper()}")
        print(f"[{time.strftime('%H:%M:%S')}] Press Ctrl+C to stop\n")

        last_trigger = 0

        while self._running:
            try:
                if keyboard.is_pressed(self.shortcut):
                    now = time.time()
                    if now - last_trigger > 1.5:
                        last_trigger = now
                        print(f"\n[{time.strftime('%H:%M:%S')}] Hotkey triggered!")
                        if self._can_spawn_worker():
                            threading.Thread(target=self._capture_worker, daemon=True).start()
                        else:
                            print(f"[{time.strftime('%H:%M:%S')}] Max threads reached, ignoring")
                time.sleep(0.05)
            except Exception as e:
                self.logger.error(f"Hotkey error: {e}")
                time.sleep(1)

    def start(self):
        if self._running:
            return

        self._running = True
        self._listener_thread = threading.Thread(target=self._hotkey_loop, daemon=True)
        self._listener_thread.start()
        self.logger.info("Hotkey runner started")

    def stop(self):
        self._running = False
        self.logger.info("Hotkey runner stopped")

    def is_running(self) -> bool:
        return self._running


def main():
    parser = argparse.ArgumentParser(
        description="AI-Powered Note Taking Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                     # Clipboard mode (default)
  python run.py --clipboard         # Same as above
  python run.py --screenshot        # Screenshot OCR mode
  python run.py --link              # URL fetching mode
  python run.py --hotkey            # Background hotkey mode
  python run.py --hotkey --screenshot  # Hotkey with screenshot
        """
    )
    parser.add_argument("--clipboard", action="store_true", default=True, help="Capture from clipboard (default)")
    parser.add_argument("--screenshot", action="store_true", help="Capture screen and extract via OCR")
    parser.add_argument("--link", action="store_true", help="Fetch and summarize URL")
    parser.add_argument("--hotkey", action="store_true", help="Run with global hotkey")
    parser.add_argument("--shortcut", default=None, help=f"Custom hotkey (default: ctrl+shift+s)")

    args = parser.parse_args()

    mode = "clipboard"
    if args.screenshot:
        mode = "screenshot"
    elif args.link:
        mode = "link"

    if args.hotkey:
        run_hotkey_mode(args.shortcut, mode)
    else:
        run_one_shot(mode)


def run_one_shot(mode: str):
    print("\n" + "=" * 50)
    print("NOTES TOOL - AI-Powered Note Taking")
    print("=" * 50)
    print(f"Mode: {mode.upper()}")
    print()

    tool = NotesTool(mode=mode)
    success = tool.run()

    if success:
        print("\nDone!")
        sys.exit(0)
    else:
        print("\nFailed. Check logs for details.")
        sys.exit(1)


def run_hotkey_mode(shortcut: str, mode: str):
    print("\n" + "=" * 50)
    print("NOTES TOOL - AI-Powered Note Taking (Hotkey Mode)")
    print("=" * 50)
    print(f"Mode: {mode.upper()}")
    print(f"Shortcut: {(shortcut or 'ctrl+shift+s').upper()}")
    print()

    runner = HotkeyRunner(shortcut=shortcut, mode=mode)

    try:
        runner.start()
        while runner.is_running():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        runner.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()
