from credlab.credit.trends import classify


def test_stress_watch_requires_multiple_critical_signals():
    label, evidence = classify({"debt_ebitda": 6, "interest_coverage": 1.2, "free_cash_flow": -10}, None)
    assert label == "STRESS WATCH"
    assert len(evidence) == 3


def test_improvement_is_evidence_based():
    current = {"debt_ebitda": 2.0, "interest_coverage": 7.0, "free_cash_flow": 150}
    prior = {"debt_ebitda": 3.0, "interest_coverage": 4.0, "free_cash_flow": 100}
    assert classify(current, prior)[0] == "IMPROVING"

