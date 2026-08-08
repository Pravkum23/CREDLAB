"""Generate bounded analyst language from calculated evidence only."""
from __future__ import annotations

from typing import Any


def bands(metrics: dict[str, Any]) -> dict[str, str]:
    lev, cov, cash = metrics.get("debt_ebitda"), metrics.get("interest_coverage"), metrics.get("cash_debt")
    return {
        "leverage": "Unavailable" if lev is None else "Low" if lev < 2 else "Moderate" if lev < 3.5 else "Elevated" if lev < 5 else "High",
        "coverage": "Unavailable" if cov is None else "Strong" if cov >= 6 else "Adequate" if cov >= 2 else "Weak",
        "liquidity": "Unavailable" if cash is None else "Strong" if cash >= .4 else "Adequate" if cash >= .15 else "Weak",
    }


def key_question(metrics: dict[str, Any], trend: str) -> str:
    if metrics.get("free_cash_flow") is not None and metrics["free_cash_flow"] < 0:
        return "Can free cash flow recover enough to support debt reduction and refinancing needs?"
    if metrics.get("interest_coverage") is not None and metrics["interest_coverage"] < 2:
        return "Can operating earnings rebuild debt-service capacity before refinancing pressure rises?"
    if metrics.get("debt_ebitda") is not None and metrics["debt_ebitda"] >= 4:
        return "What path can management credibly deliver to reduce elevated leverage?"
    if trend == "DETERIORATING":
        return "Are recent weakening signals temporary, or the start of a sustained credit deterioration?"
    return "Can the issuer preserve cash generation while funding its strategic priorities?"

