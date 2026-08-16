# Public-data validation log

This log records the V1 manual review set. Values are produced from cached SEC Company Facts observations and remain traceable in `web/data/credit.json`. Validation confirms that the displayed value, concept, period, filing date, and calculation chain agree with the source payload; it does not replace full filing analysis.

| Issuer | Period | Filed | Accession | Core coverage | Review finding |
|---|---|---|---|---:|---|
| Microsoft | 2026-06-30 | 2026-07-29 | `0001193125-26-323660` | 100% | All eight core inputs available; total debt calculated from disclosed short- and long-term debt facts. |
| Verizon | 2025-12-31 | 2026-02-17 | `0000732712-26-000007` | 88% | Leverage and coverage supported; normalized capex unavailable, so FCF remains N/A. |
| Boeing | 2025-12-31 | 2026-01-30 | `0001628280-26-004357` | 88% | High proxy leverage and negative calculated FCF coexist with improving coverage; the UI preserves the mixed evidence. |
| Ford | 2025-12-31 | 2026-02-11 | `0000037996-26-000015` | 75% | Coverage is supported; total debt and normalized capex remain unavailable, so leverage and FCF remain N/A. |
| Intel | 2025-12-27 | 2026-01-23 | `0000050863-26-000011` | 88% | Negative FCF is supported; missing comparable D&A prevents EBITDA-based leverage and coverage. |

## Controls performed

1. Confirmed every reviewed observed fact retains its US-GAAP concept and SEC accession.
2. Confirmed duration facts select the latest filed observation closest to one fiscal year rather than a cumulative multi-year value.
3. Recomputed EBITDA proxy, total debt, net debt, FCF, leverage, coverage, FCF/debt, and cash/debt from displayed inputs.
4. Confirmed unsupported results remain `N/A` in both the dossier and scenario engine.
5. Confirmed heuristic labels expose their component evidence and are described as research signals, not ratings.

## Known methodology limits

- Company Facts can omit issuer-specific extension concepts that are visible in the filing.
- EBITDA is a consistent proxy, not issuer-adjusted EBITDA.
- Autos with captive-finance operations and utilities need sector-specific refinements.
- A high completeness percentage measures input coverage only; it is not a reliability guarantee or credit-quality assessment.

