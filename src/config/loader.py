import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


class ConfigurationError(Exception):
    pass


class Config:
    _instance = None

    DEFAULTS = {
        "ollama": {
            "base_url": "http://localhost:11434",
            "model": "llama3",
            "timeout": 30,
        },
        "notes": {
            "path": "./notes",
        },
        "app": {
            "log_level": "INFO",
        },
        "hotkeys": {
            "capture": "ctrl+shift+s",
        },
    }

    _required_top_level_keys = {"ollama", "notes", "app"}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._config = self._load()

    def _load(self) -> dict[str, Any]:
        base_dir = self._find_base_dir()
        config_path = base_dir / "config" / "settings.yaml"
        env_path = base_dir / "config" / ".env"

        if env_path.exists():
            load_dotenv(env_path)

        config = self._load_yaml_config(config_path)
        config = self._apply_defaults(config)
        self._apply_env_overrides(config)
        self._validate(config)

        return config

    def _find_base_dir(self) -> Path:
        current = Path(__file__).resolve()
        for parent in [current] + list(current.parents):
            if (parent / "config" / "settings.yaml").exists():
                return parent
        return Path.cwd()

    def _load_yaml_config(self, path: Path) -> dict:
        try:
            with open(path, "r") as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            raise ConfigurationError(f"Config file not found: {path}")
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in {path}: {e}")

    def _apply_defaults(self, config: dict) -> dict:
        result = self.DEFAULTS.copy()
        for key, value in config.items():
            if isinstance(value, dict) and key in result:
                result[key] = {**result[key], **value}
            else:
                result[key] = value
        return result

    def _apply_env_overrides(self, config: dict):
        overrides = {
            "OLLAMA_BASE_URL": ("ollama", "base_url"),
            "OLLAMA_MODEL": ("ollama", "model"),
            "OLLAMA_TIMEOUT": ("ollama", "timeout"),
            "NOTES_PATH": ("notes", "path"),
            "LOG_LEVEL": ("app", "log_level"),
            "HOTKEY_CAPTURE": ("hotkeys", "capture"),
        }

        for env_var, (section, key) in overrides.items():
            value = os.getenv(env_var)
            if value is not None:
                if key == "timeout":
                    try:
                        value = int(value)
                    except ValueError:
                        raise ConfigurationError(f"{env_var} must be an integer, got: {value}")
                config[section][key] = value

    def _validate(self, config: dict):
        for key in self._required_top_level_keys:
            if key not in config:
                raise ConfigurationError(f"Missing required config section: {key}")

        if not config["ollama"]["base_url"]:
            raise ConfigurationError("ollama.base_url cannot be empty")
        if not config["ollama"]["model"]:
            raise ConfigurationError("ollama.model cannot be empty")
        if config["ollama"]["timeout"] <= 0:
            raise ConfigurationError("ollama.timeout must be positive")

    @property
    def ollama_base_url(self) -> str:
        return self._config["ollama"]["base_url"]

    @property
    def ollama_model(self) -> str:
        return self._config["ollama"]["model"]

    @property
    def ollama_timeout(self) -> int:
        return self._config["ollama"]["timeout"]

    @property
    def notes_path(self) -> Path:
        return Path(self._config["notes"]["path"]).expanduser().resolve()

    @property
    def log_level(self) -> str:
        return self._config["app"]["log_level"]

    @property
    def hotkey_capture(self) -> str:
        return self._config["hotkeys"]["capture"]

    def get_model(self) -> str:
        return self._config["ollama"]["model"]

    def set_model(self, model: str):
        self._config["ollama"]["model"] = model


def get_config() -> Config:
    return Config()
