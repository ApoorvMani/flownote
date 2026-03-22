import requests
from src.utils.logger import get_logger
from src.processors.ai_processor import AIProcessor

logger = get_logger(__name__)


class OllamaChecker:
    @staticmethod
    def is_running(base_url: str) -> bool:
        status = AIProcessor.check_ollama_status(base_url)
        return status.get("status") == "running"

    @staticmethod
    def get_available_models(base_url: str) -> list[str]:
        status = AIProcessor.check_ollama_status(base_url)
        return status.get("models", [])

    @staticmethod
    def ensure_ollama_running(base_url: str) -> bool:
        status = AIProcessor.check_ollama_status(base_url)
        s = status.get("status")

        if s == "running":
            logger.info("Ollama is running")
            models = status.get("models", [])
            if models:
                logger.info(f"Available models: {', '.join(models)}")
            return True

        logger.error("=" * 50)
        logger.error("ERROR: Ollama is not running")
        logger.error("=" * 50)
        logger.error("")
        logger.error("Please start Ollama by running:")
        logger.error("  ollama serve")
        logger.error("")
        logger.error(f"Expected Ollama at: {base_url}")
        if status.get("message"):
            logger.error(f"Issue: {status['message']}")
        logger.error("")
        return False

    @staticmethod
    def auto_select_model(base_url: str, preferred_model: str = None) -> str | None:
        models = OllamaChecker.get_available_models(base_url)
        if not models:
            return preferred_model

        if preferred_model and preferred_model in models:
            logger.info(f"Using configured model: {preferred_model}")
            return preferred_model

        if preferred_model:
            prefix = preferred_model.split(":")[0]
            for model in models:
                if prefix in model:
                    logger.info(f"Using compatible model: {model}")
                    return model

        logger.info(f"Using default model: {models[0]}")
        return models[0]
