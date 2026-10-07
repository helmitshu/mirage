"""Render a Mirage analysis as Markdown or JSON."""
from __future__ import annotations

import json

from .detector import Analysis
from .translator import Translation, render_translation_markdown


def render_markdown(
    a: Analysis, source: str = "", translation: "Translation | None" = None
) -> str:
    lines = ["# Mirage report"]
    if source:
        lines.append(f"Source: {source}")
    lines += ["", f"Verdict: {a.verdict}", f"Score: {a.score}/100", ""]
    if a.signals:
        lines.append("## Signals found")
        lines.append("")
        for s in a.signals:
            lines.append(f"- **{s.title}** ({s.severity}, minus {s.penalty}). {s.detail}")
    else:
        lines.append("No red flags found. The posting reads clean.")
    if a.llm_note:
        lines += ["", "## Second opinion", "", a.llm_note]
    if translation is not None:
        lines += ["", render_translation_markdown(translation).rstrip()]
    lines += ["", "_Mirage is a screening aid, not a ruling on any employer._"]
    return "\n".join(lines) + "\n"


def render_json(
    a: Analysis, source: str = "", translation: "Translation | None" = None
) -> str:
    payload: dict = {
        "source": source,
        "verdict": a.verdict,
        "score": a.score,
        "signals": [
            {
                "id": s.id,
                "title": s.title,
                "severity": s.severity,
                "penalty": s.penalty,
                "detail": s.detail,
            }
            for s in a.signals
        ],
        "llm_note": a.llm_note,
    }
    if translation is not None:
        payload["translation"] = {
            "summary": translation.summary,
            "lines": [
                {"says": p.says, "means": p.means} for p in translation.lines
            ],
        }
    return json.dumps(payload, indent=2) + "\n"
