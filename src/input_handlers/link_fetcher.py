import re
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from src.utils.logger import get_logger

logger = get_logger(__name__)


class LinkFetcher:
    REMOVE_TAGS = ["script", "style", "nav", "header", "footer", "aside", "form", "iframe", "noscript"]
    MIN_TEXT_LENGTH = 100

    @staticmethod
    def is_valid_url(text: str) -> bool:
        text = text.strip()
        url_pattern = re.compile(
            r"^(?:http|https)://"
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
            r"localhost|"
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
            r"(?::\d+)?"
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )
        return bool(url_pattern.match(text))

    @staticmethod
    def extract_url(text: str) -> str | None:
        text = text.strip()
        if LinkFetcher.is_valid_url(text):
            return text

        url_match = re.search(r"https?://[^\s<>\"\)]+", text)
        if url_match:
            return url_match.group(0).rstrip(".,;:")

        return None

    @staticmethod
    def fetch_content(url: str, timeout: int = 15) -> str:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-US,en;q=0.9",
            }

            response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or "utf-8"

            return response.text

        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching URL: {url}")
            raise TimeoutError(f"Request timed out after {timeout}s")

        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error for URL: {url}")
            raise ConnectionError("Cannot connect. Check your network.")

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error {e.response.status_code} for URL: {url}")
            raise RuntimeError(f"HTTP error {e.response.status_code}")

        except requests.exceptions.InvalidURL:
            logger.error(f"Invalid URL: {url}")
            raise ValueError(f"Invalid URL format: {url}")

        except Exception as e:
            logger.error(f"Unexpected error fetching URL: {e}")
            raise RuntimeError(f"Failed to fetch URL: {e}")

    @staticmethod
    def clean_html(html_content: str) -> str:
        soup = BeautifulSoup(html_content, "html.parser")

        for tag in soup(LinkFetcher.REMOVE_TAGS):
            tag.decompose()

        for tag in soup.find_all(["script", "style", "nav", "header", "footer"]):
            tag.decompose()

        main_content = None
        content_containers = [
            soup.find("article"),
            soup.find("main"),
            soup.find("div", {"class": re.compile(r"content|article|post|entry", re.I)}),
            soup.find("div", {"id": re.compile(r"content|article|post|entry", re.I)}),
        ]

        for container in content_containers:
            if container and len(container.get_text(strip=True)) > LinkFetcher.MIN_TEXT_LENGTH:
                main_content = container
                break

        if not main_content:
            main_content = soup.body if soup.body else soup

        text = main_content.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        text = "\n".join(lines)

        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)

        return text.strip()

    @staticmethod
    def extract_title(soup: BeautifulSoup, base_url: str) -> str:
        title_tag = soup.find("title")
        if title_tag and title_tag.get_text(strip=True):
            return title_tag.get_text(strip=True)

        h1_tag = soup.find("h1")
        if h1_tag and h1_tag.get_text(strip=True):
            return h1_tag.get_text(strip=True)

        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"]

        return urlparse(base_url).netloc

    @staticmethod
    def fetch_and_clean(url: str, timeout: int = 15) -> tuple[str, str]:
        logger.info(f"Fetching URL: {url}")

        raw_html = LinkFetcher.fetch_content(url, timeout)
        soup = BeautifulSoup(raw_html, "html.parser")
        title = LinkFetcher.extract_title(soup, url)
        cleaned_text = LinkFetcher.clean_html(raw_html)

        if len(cleaned_text) < LinkFetcher.MIN_TEXT_LENGTH:
            logger.warning(f"Extracted text too short ({len(cleaned_text)} chars)")

        logger.info(f"Extracted {len(cleaned_text)} characters from {title}")

        return title, cleaned_text

    @staticmethod
    def is_fetchable(url: str) -> bool:
        try:
            parsed = urlparse(url)
            return all([parsed.scheme in ("http", "https"), parsed.netloc])
        except Exception:
            return False
