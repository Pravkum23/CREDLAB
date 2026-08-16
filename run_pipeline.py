"""Refresh SEC data and build the GitHub Pages dataset."""
from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path

from credlab.credit.metrics import calculate_metrics, percent_change
from credlab.credit.trends import classify
from credlab.data.sec import SecClient
from credlab.normalization.xbrl import normalize_company_facts
from credlab.research.diagnosis import bands, key_question

ROOT = Path(__file__).resolve().parent
LOG = logging.getLogger("credlab.pipeline")
CORE_FACTS = ("revenue", "operating_income", "da", "interest_expense", "cash", "total_debt", "operating_cash_flow", "capex")


def build_issuer(meta: dict, payload: dict) -> dict:
    periods = [calculate_metrics(p.to_dict()) for p in normalize_company_facts(payload)]
    if not periods:
        return {**meta, "country": "US", "periods": [], "trend": "UNAVAILABLE", "signals": [], "limitations": ["No comparable annual SEC facts were normalized."]}
    current, previous = periods[-1], periods[-2] if len(periods) > 1 else None
    trend, signals = classify(current, previous)
    current["yoy_leverage"] = percent_change(current.get("debt_ebitda"), previous.get("debt_ebitda") if previous else None)
    current["yoy_coverage"] = percent_change(current.get("interest_coverage"), previous.get("interest_coverage") if previous else None)
    current["yoy_fcf"] = percent_change(current.get("free_cash_flow"), previous.get("free_cash_flow") if previous else None)
    observed = sum(current.get(name) is not None for name in CORE_FACTS)
    completeness = round(observed / len(CORE_FACTS) * 100)
    confidence = "Complete" if completeness == 100 else "Substantial" if completeness >= 75 else "Partial"
    metric_methods = {
        "ebitda": {"type": "calculated", "formula": "Operating income + reported D&A", "inputs": ["operating_income", "da"]},
        "total_debt": {"type": "observed or calculated", "formula": current.get("total_debt_source"), "inputs": ["total_debt", "short_term_debt", "long_term_debt"]},
        "net_debt": {"type": "calculated", "formula": "Total debt - cash", "inputs": ["total_debt", "cash"]},
        "free_cash_flow": {"type": "calculated", "formula": "Operating cash flow - capital expenditure", "inputs": ["operating_cash_flow", "capex"]},
        "debt_ebitda": {"type": "calculated", "formula": "Total debt / EBITDA proxy", "inputs": ["total_debt", "ebitda"]},
        "interest_coverage": {"type": "calculated", "formula": "EBITDA proxy / interest expense", "inputs": ["ebitda", "interest_expense"]},
        "fcf_debt": {"type": "calculated", "formula": "Free cash flow / total debt", "inputs": ["free_cash_flow", "total_debt"]},
    }
    return {**meta, "country": "US", "periods": periods, "latest": current, "trend": trend,
            "signals": [s.to_dict() for s in signals], "bands": bands(current), "key_question": key_question(current, trend),
            "data_quality": {"completeness": completeness, "confidence": confidence, "observed_core_facts": observed, "expected_core_facts": len(CORE_FACTS)},
            "metric_methods": metric_methods,
            "limitations": ["EBITDA is a proxy: operating income plus reported D&A.", "Company Facts tags vary by issuer; unavailable facts are not estimated."]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--strict", action="store_true", help="Fail if any issuer cannot be fetched")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    user_agent = os.getenv("SEC_USER_AGENT")
    if not user_agent:
        parser.error("SEC_USER_AGENT is required (example: 'CREDLAB your-name you@example.com')")
    client = SecClient(user_agent, ROOT / "data" / "cache")
    universe = json.loads((ROOT / "config" / "universe.json").read_text(encoding="utf-8"))[: args.limit]
    issuers, failures = [], []
    for meta in universe:
        try:
            issuers.append(build_issuer(meta, client.company_facts(meta["cik"], args.refresh)))
        except RuntimeError as exc:
            LOG.warning("%s", exc)
            failures.append({"ticker": meta["ticker"], "error": str(exc)})
            if args.strict:
                raise
    output = {"schema_version": "1.1", "methodology_version": "CREDLAB 0.1.0", "generated_at": datetime.now(UTC).isoformat(), "source": "SEC EDGAR Company Facts API",
              "methodology": "Observed annual 10-K facts; EBITDA proxy = operating income + D&A; FCF = CFO - capex.",
              "issuer_count": len(issuers), "issuers": issuers, "failures": failures}
    target = ROOT / "web" / "data" / "credit.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2), encoding="utf-8")
    LOG.info("Wrote %s issuers to %s", len(issuers), target)
    return 0 if issuers or not args.strict else 1


if __name__ == "__main__":
    raise SystemExit(main())
