import time
import requests
from src.config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class NoteStyles:
    PROMPTS = {
        "concise": """Convert to brief bullet notes (3-5 bullets max).

Content:
{content}

Output format:
## Title
• Point 1
• Point 2
• Point 3""",

        "elaborate": """Convert to detailed notes with explanations.

Content:
{content}

Output format:
## Title

**Overview:**
[2-3 sentence summary]

**Key Points:**
• Point 1: [brief explanation]
• Point 2: [brief explanation]
• Point 3: [brief explanation]

**Takeaway:**
[1 sentence conclusion]""",

        "bullets": """Extract all key information as bullet points.

Content:
{content}

Output format:
## Title

• [Bullet 1]
• [Bullet 2]
• [Bullet 3]
• [Bullet 4]
• [Bullet 5]
• [Bullet 6 if relevant]""",

        "summary": """Create a concise summary.

Content:
{content}

Output format:
## Title

[2-3 sentence summary]""",

        "technical": """Convert to technical documentation format.

Content:
{content}

Output format:
## Title

**Definition:**
[What this is]

**Key Components:**
• Component 1
• Component 2
• Component 3

**Usage:**
[How to use/apply]

**Notes:**
[Any important details]""",
    }

    DEFAULT_STYLE = "concise"

    @classmethod
    def get_prompt(cls, style: str = None, content: str = "", context: str = "") -> str:
        if not style:
            style = cls.DEFAULT_STYLE
        prompt_template = cls.PROMPTS.get(style, cls.PROMPTS[cls.DEFAULT_STYLE])
        full_content = content
        if context:
            full_content = f"{context}\n\n--- CONTENT ---\n\n{content}"
        return prompt_template.format(content=full_content)

    @classmethod
    def get_available_styles(cls) -> list:
        return list(cls.PROMPTS.keys())


class AIProcessor:
    def __init__(self, model: str = None, max_retries: int = 2, note_style: str = None):
        self.config = get_config()
        self.base_url = self.config.ollama_base_url
        self.model = model or self.config.ollama_model
        self.timeout = self.config.ollama_timeout
        self.max_retries = max_retries
        self.note_style = note_style or NoteStyles.DEFAULT_STYLE

    def generate_notes(self, content: str, style: str = None, context: str = "") -> str:
        if not content or not content.strip():
            raise ValueError("Content cannot be empty")

        note_style = style or self.note_style
        prompt = NoteStyles.get_prompt(note_style, content, context)
        logger.info(f"Sending request to Ollama ({self.model}, style={note_style})...")

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self._make_request(prompt)
                if response:
                    return response
            except (TimeoutError, ConnectionError, RuntimeError) as e:
                last_error = e
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                continue
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise RuntimeError(f"AI processing failed: {e}")

        if last_error:
            raise type(last_error)(str(last_error))
        raise RuntimeError("AI processing failed after retries")

    def _make_request(self, prompt: str) -> str:
        start_time = time.time()

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 256,
                    },
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            result = response.json()
            elapsed = time.time() - start_time
            logger.info(f"Ollama response in {elapsed:.1f}s")
            return result.get("response", "").strip()

        except requests.exceptions.Timeout:
            logger.error(f"Ollama request timed out after {self.timeout}s")
            raise TimeoutError(f"AI request timed out after {self.timeout} seconds")

        except requests.exceptions.ConnectionError:
            logger.error("Failed to connect to Ollama")
            raise ConnectionError("Cannot connect to Ollama. Is it running?")

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error from Ollama: {e}")
            raise RuntimeError(f"Ollama HTTP error: {e}")

    def validate_response(self, response: str) -> bool:
        if not response:
            return False
        if len(response) < 10:
            return False
        return True

    @staticmethod
    def check_ollama_status(base_url: str) -> dict:
        try:
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                return {"status": "running", "models": models}
            return {"status": "error", "models": [], "message": f"HTTP {response.status_code}"}
        except requests.exceptions.Timeout:
            return {"status": "timeout", "models": [], "message": "Connection timed out"}
        except requests.exceptions.ConnectionError:
            return {"status": "offline", "models": [], "message": "Cannot connect to Ollama"}
        except Exception as e:
            return {"status": "error", "models": [], "message": str(e)}

    @staticmethod
    def get_default_model(base_url: str):
        models = AIProcessor.check_ollama_status(base_url).get("models", [])
        if models:
            return models[0]
        return None
