"""Normalize common US-GAAP concepts from heterogeneous SEC XBRL tags."""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, asdict, field
from datetime import date
from typing import Any

TAGS = {
    "revenue": ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet"),
    "operating_income": ("OperatingIncomeLoss",),
    "da": ("DepreciationDepletionAndAmortization", "DepreciationAndAmortization", "Depreciation", "DepreciationDepletionAndAmortizationPropertyPlantAndEquipment"),
    "interest_expense": ("InterestExpenseNonOperating", "InterestExpenseNonoperating", "InterestExpense", "InterestExpenseDebt", "InterestAndDebtExpense"),
    "cash": ("CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"),
    "current_assets": ("AssetsCurrent",),
    "current_liabilities": ("LiabilitiesCurrent",),
    "short_term_debt": ("DebtCurrent", "LongTermDebtCurrent", "LongTermDebtAndCapitalLeaseObligationsCurrent", "ShortTermBorrowings"),
    "long_term_debt": ("LongTermDebtNoncurrent", "LongTermDebtAndCapitalLeaseObligations", "LongTermDebt"),
    "total_debt": ("DebtLongtermAndShorttermCombinedAmount", "LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities", "DebtAndCapitalLeaseObligations"),
    "operating_cash_flow": ("NetCashProvidedByUsedInOperatingActivities",),
    "capex": ("PaymentsToAcquirePropertyPlantAndEquipment",),
}


@dataclass(slots=True)
class FinancialPeriod:
    period: str
    form: str
    filed: str
    revenue: float | None = None
    operating_income: float | None = None
    da: float | None = None
    interest_expense: float | None = None
    cash: float | None = None
    current_assets: float | None = None
    current_liabilities: float | None = None
    short_term_debt: float | None = None
    long_term_debt: float | None = None
    total_debt: float | None = None
    operating_cash_flow: float | None = None
    capex: float | None = None
    source_url: str | None = None
    provenance: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _annual_entries(concept: dict[str, Any]) -> list[dict[str, Any]]:
    units = concept.get("units", {})
    entries = units.get("USD", next(iter(units.values()), []))
    return [e for e in entries if e.get("form") in {"10-K", "10-K/A"} and e.get("fp") == "FY"]


def _pick(entries: Iterable[dict[str, Any]], period: str) -> dict[str, Any] | None:
    matches = [e for e in entries if e.get("end") == period]
    if not matches:
        return None

    def rank(entry: dict[str, Any]) -> tuple[str, int]:
        """Prefer the latest filing and, for duration facts, a one-year span."""
        duration_distance = 10_000
        if entry.get("start") and entry.get("end"):
            try:
                span = (date.fromisoformat(entry["end"]) - date.fromisoformat(entry["start"])).days
                duration_distance = abs(span - 365)
            except ValueError:
                pass
        return entry.get("filed", ""), -duration_distance

    return max(matches, key=rank)


def normalize_company_facts(payload: dict[str, Any], years: int = 5) -> list[FinancialPeriod]:
    """Return latest annual periods; missing concepts remain None, never estimated."""
    facts = payload.get("facts", {}).get("us-gaap", {})
    by_metric: dict[str, list[dict[str, Any]]] = {}
    tags_used: dict[str, str | None] = {}
    all_periods: set[str] = set()
    for metric, candidates in TAGS.items():
        entries: list[dict[str, Any]] = []
        for tag in candidates:
            if tag in facts:
                entries = _annual_entries(facts[tag])
                if entries:
                    tags_used[metric] = tag
                    break
        tags_used.setdefault(metric, None)
        by_metric[metric] = entries
        all_periods.update(e["end"] for e in entries if e.get("end"))
    periods = sorted(all_periods, reverse=True)[:years]
    output: list[FinancialPeriod] = []
    cik = str(payload.get("cik", "")).zfill(10)
    for period in sorted(periods):
        selected = {metric: _pick(entries, period) for metric, entries in by_metric.items()}
        reference = next((entry for entry in selected.values() if entry), {})
        row = FinancialPeriod(period=period, form=reference.get("form", "10-K"), filed=reference.get("filed", ""))
        for metric, entry in selected.items():
            setattr(row, metric, float(entry["val"]) if entry and entry.get("val") is not None else None)
            if entry:
                accession = entry.get("accn", "")
                accession_path = accession.replace("-", "")
                row.provenance[metric] = {
                    "taxonomy": "us-gaap",
                    "concept": tags_used[metric],
                    "form": entry.get("form"),
                    "filed": entry.get("filed"),
                    "accession": accession,
                    "unit": "USD",
                    "source_url": f"https://www.sec.gov/Archives/edgar/data/{int(cik or 0)}/{accession_path}/" if accession_path else None,
                }
        accession = reference.get("accn", "").replace("-", "")
        row.source_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik or 0)}/{accession}/" if accession else None
        output.append(row)
    return output
