"""Signal definitions for the Mirage rules engine."""
from dataclasses import dataclass


@dataclass
class Signal:
    """One finding from the rules engine."""

    id: str
    title: str
    severity: str  # critical, high, medium, or low
    detail: str
    penalty: int


SEVERITIES = ("critical", "high", "medium", "low")
