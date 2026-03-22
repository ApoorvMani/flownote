import re
import pytesseract
from PIL import Image
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ScreenshotHandler:
    @staticmethod
    def capture_region(x: int = 0, y: int = 0, width: int = None, height: int = None) -> Image.Image:
        try:
            import mss
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                if width is None:
                    width = monitor["width"]
                if height is None:
                    height = monitor["height"]

                region = {
                    "left": x,
                    "top": y,
                    "width": width,
                    "height": height,
                }
                screenshot = sct.grab(region)
                return Image.frombytes("RGB", screenshot.size, screenshot.rgb)
        except ImportError:
            logger.warning("mss not available, trying pyautogui")
            import pyautogui
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            return screenshot.convert("RGB")
        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            raise RuntimeError(f"Screenshot capture failed: {e}")

    @staticmethod
    def capture_full_screen() -> Image.Image:
        try:
            import mss
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                return Image.frombytes("RGB", screenshot.size, screenshot.rgb)
        except ImportError:
            logger.warning("mss not available, trying pyautogui")
            import pyautogui
            return pyautogui.screenshot().convert("RGB")
        except Exception as e:
            logger.error(f"Full screen capture failed: {e}")
            raise RuntimeError(f"Full screen capture failed: {e}")

    @staticmethod
    def extract_text(image: Image.Image, lang: str = "eng") -> str:
        try:
            text = pytesseract.image_to_string(image, lang=lang)
            return text.strip()
        except pytesseract.TesseractNotFoundError:
            logger.error("Tesseract not installed. Install with: sudo apt install tesseract-ocr")
            raise RuntimeError("Tesseract OCR not installed. Please install tesseract-ocr")
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            raise RuntimeError(f"OCR extraction failed: {e}")

    @staticmethod
    def clean_ocr_text(text: str) -> str:
        if not text:
            return ""

        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"([a-z])\.([A-Z])", r"\1. \2", text)
        text = re.sub(r"\|", "I", text)
        text = re.sub(r"[âãäå]", "a", text)
        text = re.sub(r"[èéêë]", "e", text)
        text = re.sub(r"[ìíîï]", "i", text)
        text = re.sub(r"[òóôõ]", "o", text)
        text = re.sub(r"[ùúûü]", "u", text)

        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if len(line) > 2:
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()

    @staticmethod
    def capture_and_extract(x: int = 0, y: int = 0, width: int = None, height: int = None) -> str:
        logger.info("Capturing screenshot...")
        image = ScreenshotHandler.capture_region(x, y, width, height)

        logger.info("Extracting text via OCR...")
        raw_text = ScreenshotHandler.extract_text(image)

        if not raw_text:
            logger.warning("No text found in screenshot")
            return ""

        cleaned_text = ScreenshotHandler.clean_ocr_text(raw_text)
        logger.info(f"OCR extracted {len(cleaned_text)} characters")
        return cleaned_text

    @staticmethod
    def is_available() -> bool:
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False
