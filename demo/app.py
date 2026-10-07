"""Mirage live demo: ghost check plus plain English translator."""
import os
from datetime import date

import gradio as gr

from mirage.detector import analyze
from mirage.report import render_markdown
from mirage.translator import render_translation_markdown, translate

MIN_TEXT = 50

THEME = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="slate",
    neutral_hue="slate",
    font=["Inter", "system-ui", "sans-serif"],
)

CSS = """
.gradio-container { max-width: 880px !important; }
.mirage-hero {
    background: linear-gradient(135deg, #1a1b4b 0%, #4c1d95 55%, #0e7490 100%);
    border-radius: 16px;
    padding: 28px 32px;
    color: #fff;
    margin-bottom: 20px;
}
.mirage-hero h1 { color: #fff !important; margin: 0 0 6px 0; font-size: 30px; }
.mirage-hero p { color: rgba(255,255,255,.82) !important; margin: 0; font-size: 15px; }
.mirage-card {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 20px 22px;
    margin: 14px 0;
    box-shadow: 0 1px 3px rgba(16,24,40,.06);
}
.mirage-score { font-size: 44px; font-weight: 800; line-height: 1; }
.mirage-verdict {
    display: inline-block;
    font-size: 13px;
    font-weight: 700;
    padding: 4px 12px;
    border-radius: 999px;
    margin-top: 8px;
}
.mirage-pair { border-left: 3px solid #6366f1; padding: 2px 0 2px 14px; margin: 12px 0; }
.mirage-pair .says { color: #6b7280; font-size: 14px; }
.mirage-pair .means { color: #111827; font-size: 15px; font-weight: 600; }
"""


def _parse_posted(posted: str):
    if posted and posted.strip():
        try:
            return date.fromisoformat(posted.strip())
        except ValueError:
            return "error"
    return None


def check_text(text: str, posted: str) -> str:
    text = (text or "").strip()
    if len(text) < MIN_TEXT:
        return "Paste the full job posting text first (at least a few sentences)."
    posted_date = _parse_posted(posted)
    if posted_date == "error":
        return "Posted date must look like YYYY-MM-DD, for example 2026-09-20."
    result = analyze(text, posted=posted_date)
    return render_markdown(result, source="pasted text")


def _verdict_badge(verdict: str) -> str:
    colors = {
        "Legitimate": ("#ecfdf5", "#047857"),
        "Caution": ("#fffbeb", "#b45309"),
        "Suspicious": ("#fff7ed", "#c2410c"),
        "Likely ghost": ("#fef2f2", "#b91c1c"),
    }
    bg, fg = colors.get(verdict, ("#f3f4f6", "#374151"))
    return (
        f'<span class="mirage-verdict" style="background:{bg};color:{fg}">'
        f"{verdict}</span>"
    )


def translate_page(text: str) -> str:
    text = (text or "").strip()
    if len(text) < MIN_TEXT:
        return "Paste the full job posting text first (at least a few sentences)."
    result = analyze(text)
    translation = translate(text)

    parts = [
        '<div class="mirage-card">',
        f'<div class="mirage-score">{result.score}<span style="font-size:20px;color:#6b7280">/100</span></div>',
        _verdict_badge(result.verdict),
        "</div>",
    ]
    if translation is None:
        parts.append(
            '<div class="mirage-card">'
            "The translator needs a Gemini API key on the server. "
            "The ghost score above still stands on its own."
            "</div>"
        )
    else:
        parts.append('<div class="mirage-card">')
        parts.append(f"<p><strong>Straight summary.</strong> {translation.summary}</p>")
        for pair in translation.lines:
            parts.append(
                '<div class="mirage-pair">'
                f'<div class="says">They say: &ldquo;{pair.says}&rdquo;</div>'
                f'<div class="means">They mean: {pair.means}</div>'
                "</div>"
            )
        parts.append("</div>")
    if result.signals:
        parts.append('<div class="mirage-card"><strong>Red flags found.</strong><ul>')
        for s in result.signals:
            parts.append(f"<li><strong>{s.title}.</strong> {s.detail}</li>")
        parts.append("</ul></div>")
    parts.append(
        "<p style='color:#6b7280;font-size:13px'>"
        "Mirage is a screening aid, not a ruling on any employer.</p>"
    )
    return "\n".join(parts)


with gr.Blocks(title="Mirage, the ghost job detector") as demo:
    gr.HTML(
        '<div class="mirage-hero">'
        "<h1>Mirage</h1>"
        "<p>See through ghost jobs before you apply. "
        "Paste a posting, get a score out of 100, every red flag, "
        "and what it really says in plain English.</p>"
        "</div>"
    )
    with gr.Tabs():
        with gr.Tab("Ghost check"):
            ghost_input = gr.Textbox(
                lines=12,
                label="Job posting",
                placeholder="Paste the full posting text here...",
            )
            ghost_date = gr.Textbox(
                label="Posted date, optional (YYYY-MM-DD)",
                placeholder="2026-09-20",
            )
            ghost_btn = gr.Button("Check this posting", variant="primary")
            ghost_out = gr.Markdown(label="Mirage report")
            ghost_btn.click(check_text, [ghost_input, ghost_date], ghost_out)
        with gr.Tab("What it really says"):
            trans_input = gr.Textbox(
                lines=12,
                label="Job posting",
                placeholder="Paste the full posting text here...",
            )
            trans_btn = gr.Button("Translate to plain English", variant="primary")
            trans_out = gr.HTML(label="Translation")
            trans_btn.click(translate_page, trans_input, trans_out)
    gr.Markdown(
        "This demo reads pasted text on purpose. Job boards block automated "
        "readers, so pasting the text is the reliable way to check any posting."
    )

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860)),
        theme=THEME,
        css=CSS,
    )
