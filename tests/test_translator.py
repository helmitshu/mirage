"""Tests for the Mirage posting translator."""
import json

import pytest

from mirage.translator import (
    Translation,
    _parse,
    render_translation_markdown,
    translate,
)


@pytest.fixture()
def posting():
    return (
        "We are a fast paced startup looking for a rockstar engineer. "
        "You will wear many hats in a dynamic environment. We offer "
        "competitive salary and equity. Apply now, this opportunity will "
        "not last long. Contact us on Telegram for next steps."
    )


def _clear_env(monkeypatch):
    for var in ("GOOGLE_API_KEY", "GEMINI_API_KEY", "MIRAGE_GEMINI_MODEL"):
        monkeypatch.delenv(var, raising=False)


def test_no_key_returns_none(monkeypatch, posting):
    _clear_env(monkeypatch)
    assert translate(posting) is None


def test_short_text_returns_none(monkeypatch):
    _clear_env(monkeypatch)
    import os

    monkeypatch.setenv("GOOGLE_API_KEY", "fake")
    assert translate("too short") is None


def test_parses_translation(monkeypatch, posting):
    _clear_env(monkeypatch)
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")

    body = {
        "summary": "A startup job with vague pay and odd contact.",
        "translations": [
            {"says": "fast paced", "means": "you will work long hours"},
            {"says": "competitive salary", "means": "pay is below market"},
        ],
    }

    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "candidates": [
                    {"content": {"parts": [{"text": json.dumps(body)}]}}
                ]
            }

    import requests

    def fake_post(url, headers, json, timeout):
        assert headers["x-goog-api-key"] == "fake-key"
        assert "fake-key" not in url
        assert json["generationConfig"]["responseMimeType"] == "application/json"
        return FakeResp()

    monkeypatch.setattr(requests, "post", fake_post)
    t = translate(posting)
    assert isinstance(t, Translation)
    assert t.summary.startswith("A startup job")
    assert len(t.lines) == 2
    assert t.lines[0].says == "fast paced"
    assert "long hours" in t.lines[0].means


def test_bad_json_returns_none():
    assert _parse("not json at all {{{") is None
    assert _parse('{"summary": "", "translations": []}') is None


def test_failure_returns_none(monkeypatch, posting):
    _clear_env(monkeypatch)
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    import requests

    def boom(*a, **k):
        raise requests.Timeout("slow")

    monkeypatch.setattr(requests, "post", boom)
    assert translate(posting) is None


def test_render_markdown():
    t = Translation(
        summary="Plain summary.",
        lines=[],
    )
    out = render_translation_markdown(t)
    assert "## What it really says" in out
    assert "Plain summary." in out
    assert "\u2014" not in out
