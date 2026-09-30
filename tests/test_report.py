"""Tests for the Mirage report renderers."""
import json

from mirage.detector import analyze
from mirage.report import render_json, render_markdown

POSTING = """
Bluefin Analytics is hiring a Data Analyst in Dubai.

Responsibilities
- Build dashboards and weekly reports
- Clean and validate incoming data feeds

Requirements
- Two plus years with SQL and Python
- Strong communication skills
- Comfortable presenting findings to non technical stakeholders

About Bluefin Analytics
We are a forty person analytics consultancy in Dubai, founded in 2019.
We help logistics and retail clients turn operational data into decisions.

Compensation
AED 14,000 per month.

Apply at careers@bluefin-analytics.example.com.
"""


def test_markdown_report_has_verdict_and_score():
    a = analyze(POSTING)
    md = render_markdown(a, source="example")
    assert "Verdict: Legitimate" in md
    assert f"Score: {a.score}/100" in md
    assert "No red flags found" in md


def test_json_report_parses():
    a = analyze(POSTING)
    data = json.loads(render_json(a))
    assert data["verdict"] == "Legitimate"
    assert data["score"] == a.score
    assert data["signals"] == []
