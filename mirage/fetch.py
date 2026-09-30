"""Fetch a job posting URL and extract readable text."""
from __future__ import annotations

import re
import urllib.parse
from html.parser import HTMLParser

import requests

_SKIP_TAGS = {"script", "style", "nav", "header", "footer", "aside"}

_BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)


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


def _extract_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    return parser.text()


def fetch_url(url: str, timeout: int = 15) -> str:
    """Download the URL and return its visible text."""
    try:
        resp = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": _BROWSER_UA},
        )
        resp.raise_for_status()
        text = _extract_text(resp.text)
        if len(text) >= 200:
            return text
    except requests.RequestException:
        pass
    try:
        reader_url = "https://r.jina.ai/" + urllib.parse.quote(url, safe="")
        resp = requests.get(
            reader_url,
            timeout=timeout + 10,
            headers={"User-Agent": _BROWSER_UA},
        )
        resp.raise_for_status()
        text = resp.text.strip()
        if len(text) >= 200:
            return text
    except requests.RequestException:
        pass
    raise RuntimeError(
        "Could not read the page. The site blocks automated reading. "
        "Paste the posting text instead."
    )
