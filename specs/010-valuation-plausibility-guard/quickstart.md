# Quickstart: Valuation Plausibility Guard

## Prerequisites

- Repo dependencies installed (`uv sync` or equivalent — see repo root for the configured
  package manager).
- No OpenAI/network credentials are required for the automated validation below (see
  contracts/dcf-plausibility-guard.md — this feature only touches `aic.dcf`).

## Automated validation (no network)

```sh
pytest tests/unit/dcf/ -v
```

Expected outcomes:

- `test_engine.py::test_negative_fcff_year_is_allowed` (rewritten) passes: a multi-year
  forecast with a negative *interim* year and a positive terminal year still succeeds.
- A new `test_engine.py` rejection test passes: a single/terminal-year forecast whose FCFF
  is non-positive raises `ValueError` mentioning "terminal" and the FCFF figure — no
  `DCFResult` is returned.
- A new `test_engine.py` rejection test passes: assumptions producing a non-positive
  enterprise value (with a positive terminal FCFF) raise `ValueError` mentioning
  "enterprise value" — no `DCFResult` is returned.
- All pre-existing `test_engine.py`/`test_assumptions.py` cases not touched by
  research.md Decision 1 still pass unmodified (in particular
  `test_negative_equity_value_and_implied_value_per_share_are_allowed` and
  `test_negative_terminal_growth_rate_is_allowed`).
- `test_amazon_reference_case.py` (new) passes: the rebalanced Amazon reference dataset's
  assumptions produce a `DCFResult` with strictly positive `enterprise_value`,
  `equity_value`, and `implied_value_per_share`.

Then confirm the rest of the suite is unaffected:

```sh
pytest
ruff check .
mypy src
```

Expected: same pass count as before this feature plus the new tests, no ruff/mypy errors.

## Manual end-to-end validation (real OpenAI call — optional, costs API credits)

```sh
uv run python scripts/mvp_amazon_validation.py
```

Expected outcomes (differs from the pre-fix run):

- The printed `Enterprise Value`, `Equity Value`, and `Value / Share` are all strictly
  positive (previously: -$351.5B / -$381.4B / -$35.21).
- The script proceeds past the DCF summary and attempts `generate_thesis` using the
  configured `AIC_OPENAI_API_KEY` (`.env`). A real network call is made at this point —
  confirm this is intended before running.
- If the underlying LLM again references an evidence_id not present in the 15-item
  `evidence` list, that is a separate, pre-existing behavior (FR-005 of feature 004's
  evidence-traceability guard) unrelated to this feature's scope — not a regression to
  chase here.

## Rejection-path smoke check (manual, optional)

To directly observe the guard firing, temporarily set `capital_expenditure` back to the
pre-fix flat ~18.4%-of-revenue values in a scratch script (or reuse the new
`test_amazon_reference_case.py` fixture with capex substituted) and re-run `compute_dcf` —
expect an immediate `ValueError` naming the terminal-year FCFF, with no further stages
attempted.
