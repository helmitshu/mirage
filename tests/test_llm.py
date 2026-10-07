"""Tests for the Mirage LLM second opinion providers."""
import json

import pytest

from mirage.detector import analyze
from mirage.llm import second_opinion


@pytest.fixture()
def analysis():
    return analyze("We are hiring a senior engineer. Apply on our careers page.")


def _clear_env(monkeypatch):
    for var in (
        "MIRAGE_LLM_PROVIDER",
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
        "ANTHROPIC_API_KEY",
        "MIRAGE_GEMINI_MODEL",
    ):
        monkeypatch.delenv(var, raising=False)


def test_no_keys_returns_none(monkeypatch, analysis):
    _clear_env(monkeypatch)
    assert second_opinion("text", analysis) is None


def test_provider_none_returns_none(monkeypatch, analysis):
    _clear_env(monkeypatch)
    monkeypatch.setenv("MIRAGE_LLM_PROVIDER", "none")
    monkeypatch.setenv("GOOGLE_API_KEY", "fake")
    assert second_opinion("text", analysis) is None


def test_gemini_parses_response(monkeypatch, analysis):
    _clear_env(monkeypatch)
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")

    captured = {}

    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "candidates": [
                    {"content": {"parts": [{"text": "I agree. Thin description."}]}}
                ]
            }

    def fake_post(url, headers, json, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        assert headers["x-goog-api-key"] == "fake-key"
        assert "fake-key" not in url
        return FakeResp()

    import requests

    monkeypatch.setattr(requests, "post", fake_post)
    note = second_opinion("some posting", analysis)
    assert note == "I agree. Thin description."
    assert "gemini-2.5-flash:generateContent" in captured["url"]
    assert captured["json"]["contents"][0]["parts"][0]["text"].startswith(
        "Heuristic verdict:"
    )


def test_gemini_failure_returns_none(monkeypatch, analysis):
    _clear_env(monkeypatch)
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    import requests

    def boom(*a, **k):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(requests, "post", boom)
    assert second_opinion("text", analysis) is None


def test_gemini_model_override(monkeypatch, analysis):
    _clear_env(monkeypatch)
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
    monkeypatch.setenv("MIRAGE_GEMINI_MODEL", "gemini-2.5-flash-lite")

    captured = {}

    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}

    import requests

    def fake_post(url, headers, json, timeout):
        captured["url"] = url
        return FakeResp()

    monkeypatch.setattr(requests, "post", fake_post)
    assert second_opinion("text", analysis) == "ok"
    assert "gemini-2.5-flash-lite:generateContent" in captured["url"]
