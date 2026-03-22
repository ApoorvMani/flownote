"""
FlowNote - Persistent memory for user preferences and history
"""

import json
import os
import shutil
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Any


class Memory:
    _instance = None
    _lock = threading.Lock()

    DEFAULT_MEMORY = {
        "preferences": {
            "note_style": "concise",
            "model": "llama3.2:latest",
            "hotkey": "ctrl+shift+s",
            "auto_expand": True,
            "bubble_position": "bottom_right",
            "user_name": "",
            "user_context": "",
        },
        "history": [],
        "last_notes": [],
        "topic_styles": {},
        "stats": {
            "total_notes": 0,
            "total_captures": 0,
            "last_capture": None,
        }
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._memory_path = self._get_memory_path()
        self._load()

    def _get_memory_path(self) -> Path:
        base = Path.home() / ".flownote"
        base.mkdir(exist_ok=True)
        return base / "memory.json"

    def _load(self):
        if self._memory_path.exists():
            try:
                with open(self._memory_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self._data = self._merge_defaults(loaded)
            except Exception:
                self._data = self.DEFAULT_MEMORY.copy()
        else:
            self._data = self.DEFAULT_MEMORY.copy()

    def _merge_defaults(self, loaded: dict) -> dict:
        result = self.DEFAULT_MEMORY.copy()
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = {**result[key], **value}
            else:
                result[key] = value
        return result

    def _save(self):
        with self._lock:
            temp_path = self._memory_path.with_suffix(".tmp")
            try:
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(self._data, f, indent=2, ensure_ascii=False)
                shutil.move(temp_path, self._memory_path)
            except Exception as e:
                print(f"Warning: Could not save memory: {e}")
                if temp_path.exists():
                    try:
                        temp_path.unlink()
                    except Exception:
                        pass

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        value = self._data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def set(self, key: str, value: Any):
        keys = key.split(".")
        data = self._data
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]
        data[keys[-1]] = value
        self._save()

    def get_preference(self, key: str, default: Any = None) -> Any:
        return self.get(f"preferences.{key}", default)

    def set_preference(self, key: str, value: Any):
        self.set(f"preferences.{key}", value)

    def get_note_style(self) -> str:
        return self.get_preference("note_style", "concise")

    def set_note_style(self, style: str):
        valid_styles = ["concise", "elaborate", "bullets", "summary", "technical"]
        if style not in valid_styles:
            style = "concise"
        self.set_preference("note_style", style)

    def get_topic_style(self, topic: str) -> Optional[str]:
        styles = self.get("topic_styles", {})
        topic_data = styles.get(topic.lower())
        if topic_data:
            return topic_data.get("note_style")
        return None

    def set_topic_style(self, topic: str, note_style: str):
        self.set(f"topic_styles.{topic.lower()}.note_style", note_style)
        self.set(f"topic_styles.{topic.lower()}.last_used", datetime.now().isoformat())

    def detect_topic(self, content: str) -> Optional[str]:
        content_lower = content.lower()
        topics = {
            "machine learning": ["machine learning", "ml", "neural network", "deep learning", "ai model"],
            "python": ["python", "pip", "numpy", "pandas"],
            "linux": ["linux", "ubuntu", "bash", "shell", "terminal"],
            "coding": ["code", "programming", "function", "api", "debug"],
            "security": ["security", "cybersecurity", "encryption", "auth", "vulnerability"],
            "devops": ["docker", "kubernetes", "ci/cd", "deployment", "cloud"],
        }
        for topic, keywords in topics.items():
            if any(kw in content_lower for kw in keywords):
                return topic
        return None

    def add_note_to_history(self, note: str, source: str = "clipboard", topic: str = None):
        history = self.get("history", [])
        entry = {
            "note": note[:500],
            "source": source,
            "topic": topic,
            "timestamp": datetime.now().isoformat(),
        }
        history.insert(0, entry)
        history = history[:50]
        self.set("history", history)

        last_notes = self.get("last_notes", [])
        last_notes.insert(0, note[:300])
        last_notes = last_notes[:10]
        self.set("last_notes", last_notes)

        stats = self.get("stats", {})
        stats["total_notes"] = stats.get("total_notes", 0) + 1
        stats["total_captures"] = stats.get("total_captures", 0) + 1
        stats["last_capture"] = datetime.now().isoformat()
        self.set("stats", stats)

        if topic:
            self.set_topic_style(topic, self.get_note_style())

    def get_last_note(self) -> Optional[str]:
        notes = self.get("last_notes", [])
        return notes[0] if notes else None

    def get_last_notes(self, count: int = 5) -> list:
        return self.get("last_notes", [])[:count]

    def get_history(self, count: int = 10) -> list:
        return self.get("history", [])[:count]

    def get_stats(self) -> dict:
        return self.get("stats", {})

    def clear_history(self):
        self.set("history", [])
        self.set("last_notes", [])
        self._save()

    def set_user_context(self, context: str):
        self.set_preference("user_context", context)

    def get_user_context(self) -> str:
        return self.get_preference("user_context", "")

    def set_user_name(self, name: str):
        self.set_preference("user_name", name)

    def get_user_name(self) -> str:
        return self.get_preference("user_name", "")

    def build_context_prompt(self, content: str) -> str:
        parts = []
        user_name = self.get_user_name()
        if user_name:
            parts.append(f"User: {user_name}")

        user_context = self.get_user_context()
        if user_context:
            parts.append(f"Context: {user_context}")

        topic = self.detect_topic(content)
        if topic:
            topic_style = self.get_topic_style(topic)
            if topic_style and topic_style != self.get_note_style():
                parts.append(f"Topic detected: {topic} (preferred style: {topic_style})")

        last_note = self.get_last_note()
        if last_note:
            parts.append(f"Previous note: {last_note[:100]}...")

        return "\n".join(parts) if parts else ""


def get_memory() -> Memory:
    return Memory()
