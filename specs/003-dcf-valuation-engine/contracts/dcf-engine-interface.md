# Contract: `aic.dcf` Package Public Interface

This feature's only "interface" is the Python import surface `aic.dcf` exposes to
future consumers (a future valuation agent/workflow, tests). There is no network API,
CLI, or UI in scope.

## Import contract

```python
from aic.dcf import (
    ForecastYear,
    DCFAssumptions,
    YearResult,
    DCFResult,
    compute_dcf,
    to_valuation_result,
)
```

- Every name above MUST be importable directly from `aic.dcf`.
- Importing `aic.dcf` MUST succeed with no network access, no file I/O, and no
  environment-variable reads (FR-023, FR-024).

## Construction contract (`DCFAssumptions`)

- Constructing `DCFAssumptions` with valid data MUST succeed and return a fully typed
  instance.
- Constructing `DCFAssumptions` with any of the following MUST raise
  `pydantic.ValidationError`, with no `compute_dcf` call ever able to proceed:
  - `wacc` not strictly greater than `terminal_growth_rate` (FR-014)
  - `wacc` not strictly positive (FR-015)
  - `forecast` empty (FR-016)
  - `shares_outstanding` not strictly positive (FR-017)
  - any required field missing (FR-018)
  - monetary fields (across `forecast`, `cash`, `debt`) not sharing one currency
    (FR-020)

## Calculation contract (`compute_dcf`)

```python
def compute_dcf(assumptions: DCFAssumptions) -> DCFResult: ...
```

- Pure function: no I/O, no global state, no randomness (FR-023, FR-025).
- Given the same `DCFAssumptions`, MUST return an equal `DCFResult` every time
  (`compute_dcf(a).model_dump() == compute_dcf(a).model_dump()` for any valid `a`) —
  determinism (FR-025, SC-005).
- MUST implement exactly the formulas in spec.md FR-005–FR-013 (EBIT, NOPAT, FCFF,
  PV(FCFF), Terminal Value, PV(Terminal Value), Enterprise Value, Equity Value, Implied
  Value Per Share).
- MUST round every value placed into the returned `DCFResult` to 2 decimal places using
  round-half-up, computed from unrounded intermediate values (FR-021, FR-022).
- Given the spec's documented Reference Case inputs, MUST return the documented
  Reference Case outputs exactly (SC-001).
- MUST raise an explicit error (not return a `DCFResult` containing NaN/Infinity) if any
  computed value is non-finite (FR-019).

## Conversion contract (`to_valuation_result`)

```python
def to_valuation_result(
    result: DCFResult,
    *,
    valuation_id: UUID,
    valuation_date: date,
    confidence: float,
    method: str = "DCF (FCFF)",
    assumption_evidence_refs: list[UUID] = [],
) -> ValuationResult: ...
```

- MUST set `ValuationResult.estimated_value` from `result.implied_value_per_share`
  losslessly (same `Money` amount and currency) — FR-026.
- MUST NOT perform any additional financial computation — it is a pure structural
  mapping, not a second calculation step.

## Non-goals of this contract

- No CLI entry point is defined by this feature.
- No network-facing API is defined by this feature.
- No persistence, repository, service, or agent symbol is exported by `aic.dcf`.
- No comparable-company, precedent-transaction, terminal-multiple, Monte Carlo,
  probabilistic, or FX-conversion logic is exported by `aic.dcf`.
