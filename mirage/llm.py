"""Optional LLM second opinion pass.

Providers, in order of preference:
  1. Gemini (GOOGLE_API_KEY or GEMINI_API_KEY) - free tier friendly,
     the right default for a free product.
  2. Claude (ANTHROPIC_API_KEY) - kept for backward compatibility.

Set MIRAGE_LLM_PROVIDER to gemini, claude, or none to force a choice.
Set MIRAGE_GEMINI_MODEL to override the default model.

Returns None whenever no key is configured or the call fails, so the
rules engine verdict always stands on its own.
"""
from __future__ import annotations

import os

from .detector import Analysis

SYSTEM = (
    "You are a skeptical job search advisor. Read the posting and the "
    "heuristic findings. Reply in at most five short sentences of plain "
    "English, using only commas and periods. Say whether you agree with "
    "the verdict and name the strongest reason."
)

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models"


def _findings(analysis: Analysis) -> str:
    return (
        "; ".join(f"{s.title}: {s.detail}" for s in analysis.signals)
        or "no red flags found"
    )


def _prompt(text: str, analysis: Analysis) -> str:
    return (
        f"Heuristic verdict: {analysis.verdict} "
        f"({analysis.score}/100). Findings: {_findings(analysis)}. "
        f"Posting text: {text[:6000]}"
    )


def _gemini_opinion(text: str, analysis: Analysis) -> str | None:
    key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not key:
        return None
    try:
        import requests
    except ImportError:
        return None
    model = os.environ.get("MIRAGE_GEMINI_MODEL", "gemini-2.5-flash")
    url = f"{GEMINI_ENDPOINT}/{model}:generateContent"
    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM}]},
        "contents": [{"parts": [{"text": _prompt(text, analysis)}]}],
        "generationConfig": {"maxOutputTokens": 300, "temperature": 0.2},
    }
    try:
        resp = requests.post(
            url,
            headers={"x-goog-api-key": key, "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        parts = data["candidates"][0]["content"]["parts"]
        note = "".join(p.get("text", "") for p in parts).strip()
        return note or None
    except Exception:
        return None


def _claude_opinion(text: str, analysis: Analysis) -> str | None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
    except ImportError:
        return None
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
    try:
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=model,
            max_tokens=300,
            system=SYSTEM,
            messages=[{"role": "user", "content": _prompt(text, analysis)}],
        )
        return msg.content[0].text.strip() or None
    except Exception:
        return None


def second_opinion(text: str, analysis: Analysis) -> str | None:
    """Ask the configured LLM for a second opinion. None when unavailable."""
    provider = os.environ.get("MIRAGE_LLM_PROVIDER", "auto").lower()
    if provider == "none":
        return None
    if provider == "gemini":
        return _gemini_opinion(text, analysis)
    if provider == "claude":
        return _claude_opinion(text, analysis)
    # auto: prefer Gemini (free tier), fall back to Claude
    return _gemini_opinion(text, analysis) or _claude_opinion(text, analysis)
