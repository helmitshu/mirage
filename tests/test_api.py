"""Tests for the Mirage scoring API."""
import pytest
from fastapi.testclient import TestClient

from api.server import app, _hits

client = TestClient(app)

SCAM = (
    "Work from home opportunity, no experience needed, earn $9000 per week. "
    "Just pay a small $50 registration fee to get started. Contact us only "
    "on Telegram at @fastcash. Our client is hiring now, limited spots, "
    "apply today before it is gone."
)

LEGIT = (
    "We are hiring a Senior Account Manager in Dubai, UAE. You will manage "
    "a portfolio of enterprise clients, run quarterly business reviews, and "
    "partner with our solutions team on renewals. Requirements: 5+ years in "
    "B2B account management, strong Salesforce CRM skills, excellent "
    "communication. We offer a competitive base salary plus commission, "
    "annual bonus, and health insurance. Apply with your resume through our "
    "careers page. Acme Industries LLC, licensed in Dubai since 2011."
)


@pytest.fixture(autouse=True)
def clear_rate_limits():
    _hits.clear()
    yield
    _hits.clear()


def test_health():
    assert client.get("/health").json() == {"ok": True}


def test_score_scam():
    r = client.post("/score", json={"text": SCAM})
    assert r.status_code == 200
    data = r.json()
    assert data["verdict"] == "Likely ghost"
    assert data["score"] < 30
    assert len(data["signals"]) > 0
    assert data["signals"][0]["title"]


def test_score_legit():
    r = client.post("/score", json={"text": LEGIT})
    assert r.status_code == 200
    data = r.json()
    assert data["verdict"] in ("Legitimate", "Caution")
    assert data["score"] >= 55


def test_short_text_rejected():
    r = client.post("/score", json={"text": "too short"})
    assert r.status_code == 422


def test_rate_limit():
    for _ in range(30):
        r = client.post("/score", json={"text": LEGIT})
        assert r.status_code == 200
    r = client.post("/score", json={"text": LEGIT})
    assert r.status_code == 429
