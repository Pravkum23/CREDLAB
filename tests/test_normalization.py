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

