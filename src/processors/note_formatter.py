import re
from datetime import datetime


class NoteFormatter:
    @staticmethod
    def format_notes(ai_response: str, timestamp: datetime = None, prefix: str = "") -> str:
        if timestamp is None:
            timestamp = datetime.now()

        ts = timestamp

        time_str = ts.strftime("%I:%M %p")
        date_str = ts.strftime("%Y-%m-%d")

        formatted = f"---\n\n## {prefix}AI Notes ({time_str})\n\n"
        formatted += ai_response.strip()
        formatted += f"\n\n*Processed: {date_str} {time_str}*"

        return formatted

    @staticmethod
    def extract_topic(ai_response: str) -> str:
        match = re.search(r"##\s+(.+)", ai_response)
        if match:
            topic = match.group(1).strip()
            topic = re.sub(r"\s*\([^)]*\)", "", topic)
            topic = re.sub(r"[^a-zA-Z0-9\s]", "", topic)
            return topic.strip()[:50]
        return "notes"

    @staticmethod
    def format_as_daily_entry(note_content: str, timestamp: datetime = None) -> str:
        if timestamp is None:
            timestamp = datetime.now()

        header = f"# Daily Notes - {timestamp.strftime('%Y-%m-%d')}\n\n---\n\n"
        return header + note_content

    @staticmethod
    def is_valid_note(content: str) -> bool:
        if not content or not content.strip():
            return False
        if len(content.strip()) < 5:
            return False
        return True
