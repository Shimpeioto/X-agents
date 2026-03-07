"""Fetch a URL and extract readable text content.

Usage:
    python3 scripts/fetch_url.py <url> [--max-chars 5000]

Returns extracted text to stdout. Exits 0 on success, 1 on failure.
Uses requests + stdlib html.parser — no extra dependencies.
"""

import argparse
import re
import sys
from html.parser import HTMLParser

import requests


# Tags whose content we skip entirely
_SKIP_TAGS = {"script", "style", "noscript", "svg", "head", "nav", "footer", "header"}

# Block-level tags that should produce line breaks
_BLOCK_TAGS = {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "br", "tr", "blockquote", "pre", "article", "section"}


class _TextExtractor(HTMLParser):
    """Simple HTML-to-text extractor using stdlib only."""

    def __init__(self):
        super().__init__()
        self._pieces: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
        elif tag in _BLOCK_TAGS and self._skip_depth == 0:
            self._pieces.append("\n")

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
        elif tag in _BLOCK_TAGS and self._skip_depth == 0:
            self._pieces.append("\n")

    def handle_data(self, data):
        if self._skip_depth == 0:
            self._pieces.append(data)

    def get_text(self) -> str:
        raw = "".join(self._pieces)
        # Collapse whitespace within lines, preserve line breaks
        lines = raw.split("\n")
        cleaned = []
        for line in lines:
            stripped = " ".join(line.split())
            if stripped:
                cleaned.append(stripped)
        return "\n".join(cleaned)


def fetch_url(url: str, max_chars: int = 5000, timeout: int = 15) -> str:
    """Fetch URL and return extracted text content.

    Args:
        url: The URL to fetch.
        max_chars: Maximum characters to return (truncates with notice).
        timeout: Request timeout in seconds.

    Returns:
        Extracted text content.

    Raises:
        RuntimeError: On fetch or parse failure.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; MarcBot/1.0)",
        "Accept": "text/html,application/xhtml+xml,text/plain,application/json",
    }

    resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
    resp.raise_for_status()

    content_type = resp.headers.get("content-type", "")

    # Plain text or JSON — return directly
    if "text/plain" in content_type or "application/json" in content_type:
        text = resp.text.strip()
    else:
        # HTML — extract text
        parser = _TextExtractor()
        parser.feed(resp.text)
        text = parser.get_text()

    if not text:
        raise RuntimeError("No readable content extracted from the page.")

    if len(text) > max_chars:
        text = text[:max_chars] + f"\n\n... (truncated at {max_chars} characters)"

    return text


def main():
    parser = argparse.ArgumentParser(description="Fetch URL and extract text content")
    parser.add_argument("url", help="URL to fetch")
    parser.add_argument("--max-chars", type=int, default=5000, help="Max characters to return (default: 5000)")
    args = parser.parse_args()

    try:
        text = fetch_url(args.url, max_chars=args.max_chars)
        print(text)
    except Exception as e:
        print(f"Error fetching URL: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
