"""Mirage live demo: paste a job posting, get the ghost score."""
import os
from datetime import date

import gradio as gr

from mirage.detector import analyze
from mirage.report import render_markdown


def check_text(text: str, posted: str) -> str:
    text = (text or "").strip()
    if len(text) < 50:
        return "Paste the full job posting text first (at least a few sentences)."
    posted_date = None
    if posted and posted.strip():
        try:
            posted_date = date.fromisoformat(posted.strip())
        except ValueError:
            return "Posted date must look like YYYY-MM-DD, for example 2026-09-20."
    result = analyze(text, posted=posted_date)
    return render_markdown(result, source="pasted text")


demo = gr.Interface(
    fn=check_text,
    inputs=[
        gr.Textbox(
            lines=12,
            label="Job posting",
            placeholder="Paste the full posting text here...",
        ),
        gr.Textbox(
            label="Posted date, optional (YYYY-MM-DD)",
            placeholder="2026-09-20",
        ),
    ],
    outputs=gr.Markdown(label="Mirage report"),
    title="Mirage, the ghost job detector",
    description=(
        "Paste a job posting. Get a score out of 100 and every red flag "
        "in plain English. "
        "This demo reads pasted text on purpose. Job boards like Indeed and "
        "LinkedIn block automated readers, so pasting the text is the reliable "
        "way to check any posting."
    ),
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))
