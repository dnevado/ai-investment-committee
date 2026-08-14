# Data Model: Valuation Plausibility Guard

No new domain entity or Pydantic model is introduced. This feature adds a computed-result
invariant to an existing entity and formalizes a test fixture.

## `DCFResult` (existing — `aic.dcf.result.DCFResult`, unchanged shape)

| Field | Type | Notes |
|---|---|---|
| `per_year` | `list[YearResult]` | unchanged |
| `terminal_value` | `Money` | unchanged |
| `pv_terminal_value` | `Money` | unchanged |
| `enterprise_value` | `Money` | unchanged |
| `equity_value` | `Money` | unchanged |
| `implied_value_per_share` | `Money` | unchanged |

**New invariant** (enforced in `compute_dcf`, not in the Pydantic model itself, since it
depends on values computed from `DCFAssumptions` rather than being checkable from
`DCFAssumptions` alone):

- A `DCFResult` is only ever constructed and returned if:
  1. the terminal forecast year's FCFF (`per_year[-1].fcff`, pre-rounding) is strictly
     positive, **and**
  2. `enterprise_value` (pre-rounding) is strictly positive.
- If either check fails, `compute_dcf` raises `ValueError` and no `DCFResult` instance is
  constructed. This is a precondition on construction, not a field-level `Field(...)`
  constraint, because it depends on the interaction of multiple assumption inputs
  (operating margin, tax rate, per-year capex/D&A/NWC, WACC, terminal growth), not on any
  single field in isolation.

**Unchanged invariants** (still true, still allowed, per feature 003 — not touched by this
feature):
- `equity_value` and `implied_value_per_share` MAY be negative (debt exceeding enterprise
  value + cash remains a valid, reportable outcome).
- `terminal_growth_rate` MAY be negative (a declining perpetuity), as long as it stays below
  `wacc` (enforced separately, at `DCFAssumptions` construction time, unchanged).
- An *interim* (non-terminal) forecast year's FCFF MAY be negative.

## Reference Dataset (Amazon) — test/script fixture, not a new domain type

A fixed set of existing domain model instances (`Company`, `FinancialSnapshot`, `Evidence`,
`DCFAssumptions`/`ForecastYear`) representing Amazon's FY2025 actuals plus an internally
consistent (i.e., guard-passing) 3-year forecast. Lives in two places with the same
underlying figures:

- `scripts/mvp_amazon_validation.py` — manual, real-provider validation script (existing
  file, capex assumption corrected per research.md Decision 3).
- `tests/unit/dcf/test_amazon_reference_case.py` — new, no-network automated regression
  test asserting `compute_dcf` succeeds and returns a strictly positive Enterprise Value,
  Equity Value, and Implied Value Per Share for this dataset. This test only exercises
  `DCFAssumptions`/`compute_dcf` (already network-free); it does not construct a provider or
  call any LLM-facing generator, since FR-005/FR-007/SC-002 are scoped to the DCF layer.

No relationship changes to existing entities (`Company`, `Evidence`, `FinancialSnapshot`,
`DCFAssumptions`, `ForecastYear` all reused exactly as defined in features 002/003).
