from credlab.credit.metrics import calculate_metrics, percent_change, safe_ratio


def sample():
    return {"revenue": 1000.0, "operating_income": 180.0, "da": 20.0, "interest_expense": 40.0,
            "cash": 100.0, "short_term_debt": 50.0, "long_term_debt": 450.0,
            "operating_cash_flow": 150.0, "capex": 50.0}


def test_credit_formulas():
    result = calculate_metrics(sample())
    assert result["ebitda"] == 200
    assert result["total_debt"] == 500
    assert result["net_debt"] == 400
    assert result["free_cash_flow"] == 100
    assert result["debt_ebitda"] == 2.5
    assert result["interest_coverage"] == 5
    assert result["fcf_debt"] == .2


def test_missing_and_negative_denominators_are_visible():
    assert safe_ratio(5, None) is None
    assert safe_ratio(5, 0) is None
    assert safe_ratio(5, -2) is None
    assert percent_change(2, 0) is None

