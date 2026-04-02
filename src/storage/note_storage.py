import os
from pathlib import Path
from datetime import datetime
from src.config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class NoteStorage:
    def __init__(self):
        self.config = get_config()
        self.notes_dir = self.config.notes_path
        self._ensure_notes_dir()

    def _ensure_notes_dir(self):
        if not self.notes_dir.exists():
            self.notes_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created notes directory: {self.notes_dir}")

    def _get_daily_filename(self, timestamp: datetime = None) -> Path:
        if timestamp is None:
            timestamp = datetime.now()
        filename = f"{timestamp.strftime('%Y-%m-%d')}.md"
        return self.notes_dir / filename

    def _read_existing_notes(self, filepath: Path) -> str:
        if filepath.exists():
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to read existing notes: {e}")
                raise IOError(f"Cannot read notes file: {filepath}")
        return ""

    def _write_notes(self, filepath: Path, content: str):
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Notes saved to: {filepath}")
        except PermissionError:
            logger.error(f"Permission denied writing to: {filepath}")
            raise IOError(f"Permission denied: {filepath}")
        except Exception as e:
            logger.error(f"Failed to write notes: {e}")
            raise IOError(f"Failed to write notes: {e}")

    def save_note(self, note_content: str, timestamp: datetime = None) -> str:
        if timestamp is None:
            timestamp = datetime.now()

        filepath = self._get_daily_filename(timestamp)

        if filepath.exists():
            existing_content = self._read_existing_notes(filepath)
            full_content = existing_content.rstrip() + "\n\n" + note_content
        else:
            full_content = self._create_new_daily_file(timestamp, note_content)

        self._write_notes(filepath, full_content)
        return str(filepath)

    def _create_new_daily_file(self, timestamp: datetime, note_content: str) -> str:
        header = f"# Daily Notes - {timestamp.strftime('%Y-%m-%d')}\n\n---\n\n"
        return header + note_content

    def note_exists(self, timestamp: datetime = None) -> bool:
        filepath = self._get_daily_filename(timestamp)
        return filepath.exists()
