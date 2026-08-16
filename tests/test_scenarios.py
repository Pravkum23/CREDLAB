from credlab.scenarios.engine import run_scenario


def test_scenario_recalculates_capacity():
    base = {"revenue": 1000, "ebitda": 200, "operating_cash_flow": 150, "interest_expense": 40,
            "capex": 50, "total_debt": 500, "cash": 100}
    result = run_scenario(base, {"revenue_growth": -.1, "ebitda_margin": .15, "interest_expense": 60,
                                  "capex": 70, "debt": 600, "cash": 50})
    assert result["ebitda"] == 135
    assert result["free_cash_flow"] == 65
    assert round(result["debt_ebitda"], 2) == 4.44
    assert result["interest_coverage"] == 2.25

