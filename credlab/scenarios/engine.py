"""Deterministic credit scenario engine."""
from __future__ import annotations

from typing import Any
from credlab.credit.metrics import safe_ratio


def run_scenario(base: dict[str, Any], assumptions: dict[str, float]) -> dict[str, float | None]:
    revenue_base = base.get("revenue")
    revenue = revenue_base * (1 + assumptions.get("revenue_growth", 0)) if revenue_base is not None else None
    margin = assumptions.get("ebitda_margin", safe_ratio(base.get("ebitda"), base.get("revenue"), require_positive_denominator=False) or 0)
    ebitda = revenue * margin if revenue is not None else None
    interest = assumptions.get("interest_expense", base.get("interest_expense"))
    capex = assumptions.get("capex", base.get("capex"))
    debt = assumptions.get("debt", base.get("total_debt"))
    cash = assumptions.get("cash", base.get("cash"))
    ocf_margin = safe_ratio(base.get("operating_cash_flow"), base.get("revenue"), require_positive_denominator=False)
    ocf = revenue * ocf_margin if revenue is not None and ocf_margin is not None else None
    fcf = ocf - capex if ocf is not None and capex is not None else None
    net_debt = debt - cash if debt is not None and cash is not None else None
    return {"revenue": revenue, "ebitda": ebitda, "free_cash_flow": fcf, "total_debt": debt, "net_debt": net_debt,
            "debt_ebitda": safe_ratio(debt, ebitda), "net_debt_ebitda": safe_ratio(net_debt, ebitda),
            "interest_coverage": safe_ratio(ebitda, interest), "fcf_debt": safe_ratio(fcf, debt)}
