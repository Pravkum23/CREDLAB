from credlab.normalization.xbrl import normalize_company_facts


def concept(tag, values):
    return {tag: {"units": {"USD": values}}}


def test_latest_filing_wins_without_estimation():
    entry = {"end": "2025-12-31", "form": "10-K", "fp": "FY", "filed": "2026-02-01", "val": 100, "accn": "1-2"}
    amended = {**entry, "form": "10-K/A", "filed": "2026-03-01", "val": 110}
    payload = {"cik": 1, "facts": {"us-gaap": concept("Revenues", [entry, amended])}}
    rows = normalize_company_facts(payload)
    assert rows[0].revenue == 110
    assert rows[0].cash is None
    assert rows[0].provenance["revenue"]["concept"] == "Revenues"
    assert rows[0].provenance["revenue"]["filed"] == "2026-03-01"


def test_one_year_duration_wins_over_cumulative_fact():
    annual = {"start": "2025-01-01", "end": "2025-12-31", "form": "10-K", "fp": "FY", "filed": "2026-02-01", "val": 100, "accn": "1-2"}
    cumulative = {**annual, "start": "2023-01-01", "val": 290}
    payload = {"cik": 1, "facts": {"us-gaap": concept("Revenues", [cumulative, annual])}}
    assert normalize_company_facts(payload)[0].revenue == 100
