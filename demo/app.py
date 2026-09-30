"""Mirage live demo: paste a job posting, get the ghost score."""
import os
from datetime import date

import gradio as gr

from mirage.detector import analyze
from mirage.fetch import fetch_url
from mirage.report import render_markdown


def run_analysis(text: str, posted: str, source: str) -> str:
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
    return render_markdown(result, source=source)


def check_text(text: str, posted: str) -> str:
    return run_analysis(text, posted, "pasted text")


def check_url(url: str, posted: str) -> str:
    url = (url or "").strip()
    if not url:
        return "Paste a link to the job posting first."
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        text = fetch_url(url)
    except RuntimeError as exc:
        return str(exc)
    return run_analysis(text, posted, url)


def make_text_tab() -> gr.Interface:
    return gr.Interface(
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
            "in plain English."
        ),
    )


def make_url_tab() -> gr.Interface:
    return gr.Interface(
        fn=check_url,
        inputs=[
            gr.Textbox(
                label="Posting link",
                placeholder="https://example.com/jobs/123",
            ),
            gr.Textbox(
                label="Posted date, optional (YYYY-MM-DD)",
                placeholder="2026-09-20",
            ),
        ],
        outputs=gr.Markdown(label="Mirage report"),
        title="Mirage, the ghost job detector",
        description=(
            "Drop in a link to the posting. Mirage reads the page and scores it. "
            "Some sites block automated reading or need JavaScript, "
            "if the link fails, paste the text instead."
        ),
    )


demo = gr.TabbedInterface(
    [make_text_tab(), make_url_tab()],
    ["Paste text", "Paste link"],
    title="Mirage, the ghost job detector",
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))
