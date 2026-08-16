"""Transparent credit calculations. All currency values use source units."""
from __future__ import annotations

from typing import Any


def safe_ratio(numerator: float | None, denominator: float | None, *, require_positive_denominator: bool = True) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    if require_positive_denominator and denominator < 0:
        return None
    return numerator / denominator


def calculate_metrics(period: dict[str, Any]) -> dict[str, Any]:
    """Calculate metrics without hiding negative EBITDA or missing inputs."""
    op_income = period.get("operating_income")
    da = period.get("da")
    ebitda = op_income + da if op_income is not None and da is not None else None
    short_debt = period.get("short_term_debt")
    long_debt = period.get("long_term_debt")
    observed_total = period.get("total_debt")
    debt = observed_total if observed_total is not None else (short_debt + long_debt if short_debt is not None and long_debt is not None else None)
    provenance = dict(period.get("provenance", {}))
    if observed_total is None and debt is not None:
        short_source = provenance.get("short_term_debt", {})
        long_source = provenance.get("long_term_debt", {})
        provenance["total_debt"] = {
            "taxonomy": "calculated",
            "concept": "Short-term debt + long-term debt",
            "form": long_source.get("form") or short_source.get("form"),
            "filed": long_source.get("filed") or short_source.get("filed"),
            "accession": long_source.get("accession") or short_source.get("accession"),
            "unit": "USD",
            "source_url": long_source.get("source_url") or short_source.get("source_url"),
        }
    cash = period.get("cash")
    net_debt = debt - cash if debt is not None and cash is not None else None
    ocf, capex = period.get("operating_cash_flow"), period.get("capex")
    fcf = ocf - capex if ocf is not None and capex is not None else None
    return {
        **period,
        "provenance": provenance,
        "ebitda": ebitda,
        "ebitda_proxy": True,
        "total_debt": debt,
        "total_debt_source": "reported combined debt" if observed_total is not None else "short-term debt + long-term debt" if debt is not None else "unavailable",
        "net_debt": net_debt,
        "free_cash_flow": fcf,
        "debt_ebitda": safe_ratio(debt, ebitda),
        "net_debt_ebitda": safe_ratio(net_debt, ebitda),
        "interest_coverage": safe_ratio(ebitda, period.get("interest_expense")),
        "fcf_debt": safe_ratio(fcf, debt),
        "cash_debt": safe_ratio(cash, debt),
    }


def percent_change(current: float | None, previous: float | None) -> float | None:
    if current is None or previous is None or previous == 0:
        return None
    return (current - previous) / abs(previous)
