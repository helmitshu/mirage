"""Fetch a job posting URL and extract readable text."""
from __future__ import annotations

import re
from html.parser import HTMLParser

import requests

_SKIP_TAGS = {"script", "style", "nav", "header", "footer", "aside"}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip = False

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in _SKIP_TAGS:
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP_TAGS:
            self._skip = False

    def handle_data(self, data: str) -> None:
        if not self._skip:
            text = data.strip()
            if text:
                self.parts.append(text)

    def text(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self.parts)).strip()


def fetch_url(url: str, timeout: int = 15) -> str:
    """Download the URL and return its visible text."""
    try:
        resp = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "Mirage/0.1 job posting analyzer"},
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Could not fetch the URL: {exc}") from exc
    parser = _TextExtractor()
    parser.feed(resp.text)
    text = parser.text()
    if len(text) < 200:
        raise RuntimeError(
            "The page had almost no readable text. It may need JavaScript or a login."
        )
    return text
