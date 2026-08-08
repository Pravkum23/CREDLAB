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


def build_issuer(meta: dict, payload: dict) -> dict:
    periods = [calculate_metrics(p.to_dict()) for p in normalize_company_facts(payload)]
    if not periods:
        return {**meta, "country": "US", "periods": [], "trend": "UNAVAILABLE", "signals": [], "limitations": ["No comparable annual SEC facts were normalized."]}
    current, previous = periods[-1], periods[-2] if len(periods) > 1 else None
    trend, signals = classify(current, previous)
    current["yoy_leverage"] = percent_change(current.get("debt_ebitda"), previous.get("debt_ebitda") if previous else None)
    current["yoy_coverage"] = percent_change(current.get("interest_coverage"), previous.get("interest_coverage") if previous else None)
    current["yoy_fcf"] = percent_change(current.get("free_cash_flow"), previous.get("free_cash_flow") if previous else None)
    return {**meta, "country": "US", "periods": periods, "latest": current, "trend": trend,
            "signals": [s.to_dict() for s in signals], "bands": bands(current), "key_question": key_question(current, trend),
            "limitations": ["EBITDA is a proxy: operating income plus reported D&A."]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--strict", action="store_true", help="Fail if any issuer cannot be fetched")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    user_agent = os.getenv("SEC_USER_AGENT", "CREDLAB open-research credlab@example.com")
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
    output = {"generated_at": datetime.now(UTC).isoformat(), "source": "SEC EDGAR Company Facts API",
              "methodology": "Observed annual 10-K facts; EBITDA proxy = operating income + D&A; FCF = CFO - capex.",
              "issuer_count": len(issuers), "issuers": issuers, "failures": failures}
    target = ROOT / "web" / "data" / "credit.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2), encoding="utf-8")
    LOG.info("Wrote %s issuers to %s", len(issuers), target)
    return 0 if issuers or not args.strict else 1


if __name__ == "__main__":
    raise SystemExit(main())

