"""Tests for the Mirage rules engine, using fictional postings."""
from datetime import date, timedelta

from mirage.detector import analyze

LEGIT = """
Harborline Logistics is hiring an Operations Manager for our Dubai office.

About Harborline Logistics
We run cold chain logistics across the UAE. Forty people, founded 2018,
based in Jebel Ali. Learn more at https://harborline-logistics.example.com.

Responsibilities
- Run daily warehouse operations and lead a team of twelve
- Own inventory accuracy and monthly cycle counts
- Coordinate inbound and outbound freight schedules

Requirements
- Five plus years in warehouse or logistics operations
- Experience with a WMS, we use NetSuite
- Based in the UAE or willing to relocate

Compensation
AED 18,000 per month plus annual bonus and health insurance.

Apply
Send your CV to careers@harborline-logistics.example.com with the subject
Operations Manager Dubai.
"""

GHOST = """
A leading company is urgently hiring!!! Immediate joiners needed, limited
slots available so apply immediately!!!

We offer a competitive salary and an attractive package for the right
candidate. Great growth opportunity with our client.

Requirements: must be hardworking. Send CV to quickhire2026@gmail.com.
"""

SCAM = """
NO EXPERIENCE NEEDED! Earn $12,000 per month working from home as a
shipping assistant!

Simple tasks, just receive packages and forward them. Contact us ONLY on
Telegram @fastcashjobs. A $50 refundable training deposit is required
before you start, fully returned with your first paycheck!
"""


def test_legit_posting_scores_high():
    a = analyze(LEGIT)
    assert a.verdict == "Legitimate"
    assert a.score >= 80
    assert a.signals == []


def test_ghost_posting_is_suspicious():
    a = analyze(GHOST)
    ids = {s.id for s in a.signals}
    assert "anonymous_employer" in ids
    assert "vague_pay" in ids
    assert "pressure_language" in ids
    assert a.verdict in ("Caution", "Suspicious")


def test_scam_posting_is_likely_ghost():
    a = analyze(SCAM)
    ids = {s.id for s in a.signals}
    assert "money_request" in ids
    assert "too_good_combo" in ids
    assert "off_platform_contact" in ids
    assert a.verdict == "Likely ghost"
    assert a.score < 30


def test_stale_posting_flag():
    old = date.today() - timedelta(days=90)
    a = analyze(LEGIT, posted=old)
    ids = {s.id for s in a.signals}
    assert "stale_posting" in ids


def test_recent_posting_not_stale():
    recent = date.today() - timedelta(days=10)
    a = analyze(LEGIT, posted=recent)
    ids = {s.id for s in a.signals}
    assert "stale_posting" not in ids
