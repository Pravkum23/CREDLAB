# CREDLAB — Open Credit Intelligence

> Can we reproduce parts of an institutional corporate-credit research workflow using only public information?

CREDLAB is an open research experiment that turns public SEC filings into an explainable corporate-credit workflow: **Discover → Investigate → Diagnose → Stress → Form Thesis**. It is deliberately not a ratings model. Every displayed conclusion is backed by an observed filing fact, a documented calculation, and an explicit research heuristic.

## The four-screen MVP

- **Credit Radar** — screen 50 recognizable US non-financial issuers, filter the evidence matrix, and use the leverage/coverage map to identify investigation candidates.
- **Issuer Dossier** — review five annual periods, constructive and weakening evidence, research bands, and a calculated key question.
- **Credit MRI** — a screenshot-ready diagnostic of operating trend, financial risk, liquidity, and available market context.
- **Scenario Lab** — apply Base, Bull, or Stress assumptions and see debt-service capacity recalculate immediately. Missing inputs stay `N/A`.

## Methodology

The refresh pipeline downloads SEC Company Facts, caches the unmodified JSON locally, selects annual `10-K`/`10-K/A` observations, maps common US-GAAP concepts, and emits a static site dataset. An amended filing wins only when it has a later filed date for the same period.

Observed facts and calculated fields are kept separate. No missing values are estimated.

| Metric | Formula |
|---|---|
| EBITDA proxy | Operating income + reported depreciation & amortization |
| Total debt | Reported combined debt; otherwise short-term debt + long-term debt when both exist |
| Net debt | Total debt − cash |
| Free cash flow | Operating cash flow − capital expenditure |
| Debt / EBITDA | Total debt ÷ EBITDA proxy |
| Net debt / EBITDA | Net debt ÷ EBITDA proxy |
| Interest coverage | EBITDA proxy ÷ interest expense |
| FCF / Debt | Free cash flow ÷ total debt |
| Cash / Debt | Cash ÷ total debt |

Negative or zero EBITDA does not produce a leverage multiple. Zero or unavailable denominators return `N/A`.

### Trend heuristics

`IMPROVING`, `STABLE`, `DETERIORATING`, and `STRESS WATCH` are CREDLAB research heuristics—not rating categories. The rules combine transparent signals such as leverage moving by more than 0.3x, coverage changing by more than 20%, weakening FCF, leverage above 5x, coverage below 2x, and negative FCF. `STRESS WATCH` requires multiple critical indicators or a sufficiently broad set of weakening signals. See [`credlab/credit/trends.py`](credlab/credit/trends.py).

## Run locally

Python 3.11+ is required.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# Identify your application to the SEC with a real project contact.
# PowerShell: $env:SEC_USER_AGENT="CREDLAB your-name you@example.com"
# bash: export SEC_USER_AGENT="CREDLAB your-name you@example.com"
python run_pipeline.py --refresh
python -m http.server 8000 --directory web
```

Open `http://localhost:8000`. One command can refresh and rebuild the site:

```bash
make refresh
```

The committed `web/data/credit.json` is a reproducible public-data snapshot for a working first visit. Raw SEC cache files are intentionally excluded from Git.

## Tests

```bash
python -m pytest
```

Tests use synthetic facts and do not require network access. They cover formulas, missing/negative denominators, amended-filing selection, trend classification, and scenario recalculation.

## Data sources and limitations

- Primary source: [SEC EDGAR Company Facts API](https://www.sec.gov/edgar/sec-api-documentation).
- The 50-name universe excludes banks and insurers because they need a different methodology.
- XBRL tags and disclosure practice vary materially. A field stays unavailable when the normalizer cannot support it defensibly.
- EBITDA is a consistent proxy, not company-reported adjusted EBITDA. It excludes issuer-defined adjustments.
- SEC Company Facts can contain restatements, dimensional facts, and fiscal-calendar differences. CREDLAB preserves filing period and filed date, but this MVP is not a substitute for reading the filing.
- Market signals are marked unavailable in V1 unless a reliable secondary provider is added.
- Autos with captive-finance operations and utilities merit sector-specific refinements in later versions.

## Architecture

```text
config/universe.json       50-issuer non-financial universe
credlab/data/              cached SEC provider
credlab/normalization/     XBRL concept mappings
credlab/credit/            metrics and transparent trend rules
credlab/research/          bands and evidence-derived questions
credlab/scenarios/         deterministic stress engine
web/                       static four-screen frontend
tests/                     network-free calculation tests
run_pipeline.py            refresh + site dataset build
```

GitHub Pages serves the `web/` artifact through the included workflow. CI separately installs the project and runs the test suite.

## Responsible use

**Educational/open research only. Not investment advice. Not a credit rating.** CREDLAB does not reproduce an agency methodology or issue an official credit opinion. Validate all facts against source filings before relying on them.

