import logging
import sys
from pathlib import Path


class Logger:
    _instance = None
    _logger = None

    def __new__(cls, name: str = "notes_tool"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._setup_logger(name)
        return cls._instance

    def _setup_logger(self, name: str):
        self._logger = logging.getLogger(name)
        self._logger.setLevel(logging.INFO)

        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%H:%M:%S",
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

    def set_level(self, level: str):
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        self._logger.setLevel(numeric_level)
        for handler in self._logger.handlers:
            handler.setLevel(numeric_level)

    def info(self, msg: str):
        self._logger.info(msg)

    def warning(self, msg: str):
        self._logger.warning(msg)

    def error(self, msg: str):
        self._logger.error(msg)

    def debug(self, msg: str):
        self._logger.debug(msg)


def get_logger(name: str = "notes_tool") -> Logger:
    return Logger(name)
