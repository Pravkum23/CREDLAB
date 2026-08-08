"""Documented CREDLAB research heuristics; these are not rating criteria."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class Signal:
    metric: str
    direction: str
    detail: str
    severity: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def classify(current: dict[str, Any], previous: dict[str, Any] | None) -> tuple[str, list[Signal]]:
    """Classify direction from explicit changes and absolute stress indicators."""
    signals: list[Signal] = []
    leverage = current.get("debt_ebitda")
    coverage = current.get("interest_coverage")
    fcf = current.get("free_cash_flow")
    if leverage is not None and leverage >= 5:
        signals.append(Signal("Leverage", "up", f"Debt / EBITDA is high at {leverage:.1f}x", 2))
    if coverage is not None and coverage < 2:
        signals.append(Signal("Coverage", "down", f"Interest coverage is weak at {coverage:.1f}x", 2))
    if fcf is not None and fcf < 0:
        signals.append(Signal("Free cash flow", "down", "Free cash flow is negative", 2))
    if previous:
        prev_lev, prev_cov, prev_fcf = previous.get("debt_ebitda"), previous.get("interest_coverage"), previous.get("free_cash_flow")
        if leverage is not None and prev_lev is not None and leverage - prev_lev > 0.3:
            signals.append(Signal("Leverage", "up", f"Leverage rose {leverage - prev_lev:.1f}x year over year", 1))
        elif leverage is not None and prev_lev is not None and prev_lev - leverage > 0.3:
            signals.append(Signal("Leverage", "down", f"Leverage fell {prev_lev - leverage:.1f}x year over year", -1))
        if coverage is not None and prev_cov is not None and coverage < prev_cov * 0.8:
            signals.append(Signal("Coverage", "down", "Interest coverage fell more than 20%", 1))
        elif coverage is not None and prev_cov is not None and coverage > prev_cov * 1.2:
            signals.append(Signal("Coverage", "up", "Interest coverage improved more than 20%", -1))
        if fcf is not None and prev_fcf is not None and fcf < prev_fcf:
            signals.append(Signal("Free cash flow", "down", "Free cash flow declined year over year", 1))
        elif fcf is not None and prev_fcf is not None and fcf > prev_fcf:
            signals.append(Signal("Free cash flow", "up", "Free cash flow improved year over year", -1))
    score = sum(s.severity for s in signals)
    critical = sum(1 for s in signals if s.severity == 2)
    label = "STRESS WATCH" if critical >= 2 or score >= 4 else "DETERIORATING" if score >= 2 else "IMPROVING" if score <= -2 else "STABLE"
    return label, signals

