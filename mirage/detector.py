"""Heuristic rules engine. Turns a job posting into a 0-100 legitimacy score."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from .signals import Signal

FREE_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com",
    "live.com",
    "aol.com",
    "icloud.com",
    "proton.me",
    "protonmail.com",
    "zoho.com",
}

CHAT_APPS = ("telegram", "whatsapp", "signal")


@dataclass
class Analysis:
    score: int
    verdict: str
    signals: list[Signal]
    llm_note: str | None = None
    checked_at: str = field(default_factory=lambda: date.today().isoformat())


def _money_request(text: str, low: str) -> Signal | None:
    patterns = [
        r"pay (?:a|an|any) (?:fee|deposit|payment|charge)",
        r"(?:refundable|security) deposit",
        r"training deposit",
        r"refundable.{0,25}deposit",
        r"(?:training|application|registration|processing|visa) fee",
        r"send (?:us |me )?money",
        r"wire transfer",
        r"gift ?cards?",
        r"cryptocurrency|crypto payment",
        r"western union|moneygram",
    ]
    if any(re.search(p, low) for p in patterns):
        return Signal(
            id="money_request",
            title="Money request",
            severity="critical",
            detail="The posting asks you to pay something. Real employers never charge applicants.",
            penalty=30,
        )
    return None


def _too_good_combo(text: str, low: str) -> Signal | None:
    no_exp = "no experience" in low
    remote = re.search(r"work(?:ing)? from home|\bwfh\b|\bremote\b", low)
    monthlies = list(_monthly_figures(low))
    if no_exp and remote and any(v >= 5000 for v in monthlies):
        return Signal(
            id="too_good_combo",
            title="Too good combo",
            severity="critical",
            detail="No experience plus work from home plus high pay. This is the classic scam shape.",
            penalty=30,
        )
    return None


def _off_platform_contact(text: str, low: str) -> Signal | None:
    apps = [a for a in CHAT_APPS if a in low]
    if not apps:
        return None
    domains = re.findall(r"[\w.+-]+@([\w-]+\.[\w.]+)", text)
    company_mail = any(d.lower() not in FREE_EMAIL_DOMAINS for d in domains)
    if company_mail:
        return None
    return Signal(
        id="off_platform_contact",
        title="Off platform contact",
        severity="high",
        detail=f"Contact runs through {', '.join(apps)} with no company email anywhere. "
        "Legit hiring runs on company domains.",
        penalty=18,
    )


def _free_email_only(text: str, low: str) -> Signal | None:
    domains = re.findall(r"[\w.+-]+@([\w-]+\.[\w.]+)", text)
    if not domains:
        return None
    if any(d.lower() not in FREE_EMAIL_DOMAINS for d in domains):
        return None
    if re.search(r"https?://|www\.", low):
        return None
    return Signal(
        id="free_email_only",
        title="Free email only",
        severity="medium",
        detail="The only contact is a free email account and no company website is listed.",
        penalty=10,
    )


def _anonymous_employer(text: str, low: str) -> Signal | None:
    if re.search(
        r"our client|a leading (company|firm)|confidential employer|"
        r"employer name withheld|undisclosed (company|employer)",
        low,
    ):
        return Signal(
            id="anonymous_employer",
            title="Anonymous employer",
            severity="high",
            detail="No real company identity. Phrases like our client with no name attached.",
            penalty=18,
        )
    return None


def _monthly_figures(low: str):
    """Yield monthly pay figures found in the text."""
    for m in re.finditer(
        r"(?:\$|USD|AED)\s?([\d,]+)\s*(k)?\s*(?:per month|/month|a month|monthly|p\.m\.)", low
    ):
        num = float(m.group(1).replace(",", ""))
        if m.group(2):
            num *= 1000
        yield num
    for m in re.finditer(
        r"(?:\$|USD|AED)\s?([\d,]+)\s*(k)?\s*(?:per year|/year|a year|yearly|p\.a\.)", low
    ):
        num = float(m.group(1).replace(",", ""))
        if m.group(2):
            num *= 1000
        yield num / 12


def _salary_anomaly(text: str, low: str) -> Signal | None:
    dailies = [
        float(x.replace(",", ""))
        for x in re.findall(r"(?:\$|USD|AED)\s?([\d,]+)\s*(?:per day|/day|a day|daily)", low)
    ]
    if any(d >= 800 for d in dailies):
        return Signal(
            id="salary_anomaly",
            title="Salary anomaly",
            severity="high",
            detail="Daily rates this high are fantasy for advertised roles.",
            penalty=18,
        )
    if "no experience" in low and any(v >= 15000 for v in _monthly_figures(low)):
        return Signal(
            id="salary_anomaly",
            title="Salary anomaly",
            severity="high",
            detail="Five figure monthly pay for a role needing no experience makes no sense.",
            penalty=18,
        )
    return None


def _vague_pay(text: str, low: str) -> Signal | None:
    if re.findall(r"(?:\$|USD|AED|€|£)\s?[\d,]+", low):
        return None
    if re.search(
        r"competitive salar|attractive (package|salary)|lucrative|"
        r"generous (pay|compensation)|earn (big|well)",
        low,
    ):
        return Signal(
            id="vague_pay",
            title="Vague pay",
            severity="low",
            detail="Big talk about competitive packages, zero numbers anywhere.",
            penalty=5,
        )
    return None


def _pressure_language(text: str, low: str) -> Signal | None:
    hits = [
        p
        for p in (
            r"urgent(?:ly)? hiring",
            r"immediate join",
            r"limited slots",
            r"apply immediately",
            r"act now",
            r"hiring immediately",
        )
        if re.search(p, low)
    ]
    if len(hits) >= 2:
        return Signal(
            id="pressure_language",
            title="Pressure language",
            severity="low",
            detail="Urgency stacking. Real roles rarely beg you to hurry.",
            penalty=5,
        )
    return None


def _buzzword_stuffing(text: str, low: str) -> Signal | None:
    hits = [
        p
        for p in (
            r"rockstar",
            r"rock star",
            r"\bninja\b",
            r"\bguru\b",
            r"work hard play hard",
            r"we('re| are) a family",
            r"wear many hats",
        )
        if re.search(p, low)
    ]
    if len(hits) >= 2:
        return Signal(
            id="buzzword_stuffing",
            title="Buzzword stuffing",
            severity="low",
            detail="A posting full of rockstars and ninjas usually means nobody thought about the role.",
            penalty=5,
        )
    return None


def _thin_description(text: str, low: str) -> Signal | None:
    short = len(text.strip()) < 500
    no_sections = not (
        re.search(r"responsib", low) or re.search(r"requirement|qualific", low)
    )
    if short or (len(text.strip()) < 1200 and no_sections):
        return Signal(
            id="thin_description",
            title="Thin description",
            severity="medium",
            detail="The posting says almost nothing about the actual work.",
            penalty=10,
        )
    return None


def _verdict(score: int) -> str:
    if score >= 80:
        return "Legitimate"
    if score >= 55:
        return "Caution"
    if score >= 30:
        return "Suspicious"
    return "Likely ghost"


def analyze(text: str, posted: date | None = None) -> Analysis:
    """Run every rule over the posting and return the scored analysis."""
    low = re.sub(r"\s+", " ", text.lower())
    signals: list[Signal] = []
    for rule in (
        _money_request,
        _too_good_combo,
        _off_platform_contact,
        _free_email_only,
        _anonymous_employer,
        _salary_anomaly,
        _vague_pay,
        _pressure_language,
        _buzzword_stuffing,
        _thin_description,
    ):
        found = rule(text, low)
        if found:
            signals.append(found)
    if posted is not None:
        days = (date.today() - posted).days
        if days > 60:
            signals.append(
                Signal(
                    id="stale_posting",
                    title="Stale posting",
                    severity="medium",
                    detail=f"Posted {days} days ago and still open. Perpetual reposts are a ghost pattern.",
                    penalty=10,
                )
            )
    score = max(0, 100 - sum(s.penalty for s in signals))
    return Analysis(score=score, verdict=_verdict(score), signals=signals)
