"""Optional Claude second opinion pass."""
from __future__ import annotations

import os

from .detector import Analysis

SYSTEM = (
    "You are a skeptical job search advisor. Read the posting and the "
    "heuristic findings. Reply in at most five short sentences of plain "
    "English, using only commas and periods. Say whether you agree with "
    "the verdict and name the strongest reason."
)


def second_opinion(text: str, analysis: Analysis) -> str | None:
    """Ask Claude for a second opinion. Returns None when unavailable."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
    except ImportError:
        return None
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
    findings = (
        "; ".join(f"{s.title}: {s.detail}" for s in analysis.signals)
        or "no red flags found"
    )
    try:
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=model,
            max_tokens=300,
            system=SYSTEM,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Heuristic verdict: {analysis.verdict} "
                        f"({analysis.score}/100). Findings: {findings}. "
                        f"Posting text: {text[:6000]}"
                    ),
                }
            ],
        )
        return msg.content[0].text.strip() or None
    except Exception:
        return None
