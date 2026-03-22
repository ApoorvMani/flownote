import pyperclip
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ClipboardHandler:
    @staticmethod
    def get_text() -> str:
        try:
            text = pyperclip.paste()
            return text.strip() if text else ""
        except Exception as e:
            logger.error(f"Failed to read clipboard: {e}")
            return ""

    @staticmethod
    def is_empty() -> bool:
        text = ClipboardHandler.get_text()
        return not text or not text.strip()

    @staticmethod
    def has_content() -> bool:
        return not ClipboardHandler.is_empty()

    @staticmethod
    def get_content_or_prompt() -> str:
        content = ClipboardHandler.get_text()
        if content and content.strip():
            logger.info("Content retrieved from clipboard")
            return content.strip()

        logger.info("Clipboard is empty, prompting user for input...")
        print("\n" + "=" * 50)
        print("CLIPBOARD EMPTY - Manual Input Required")
        print("=" * 50)
        print("Paste or type your content below.")
        print("Press Enter twice (empty line) to finish.")
        print("-" * 50)

        lines = []
        while True:
            try:
                line = input()
                if line == "":
                    break
                lines.append(line)
            except EOFError:
                break

        content = "\n".join(lines).strip()
        if content:
            logger.info(f"Manual input received ({len(content)} chars)")
        return content
