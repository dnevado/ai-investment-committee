# Contract: `aic.dcf.compute_dcf` Plausibility Guard

This feature's "interface" is a behavioral addition to the existing `compute_dcf` function's
public contract. No new module, class, or importable symbol is added.

## Existing signature (unchanged)

```python
def compute_dcf(assumptions: DCFAssumptions) -> DCFResult: ...
```

## New behavior

- MUST raise `ValueError` — and MUST NOT return a `DCFResult` — if the terminal forecast
  year's computed FCFF (before rounding) is less than or equal to zero (FR-001).
  - The error message MUST state that the terminal-year FCFF check failed and MUST include
    the computed FCFF value (FR-003).
- MUST raise `ValueError` — and MUST NOT return a `DCFResult` — if the computed enterprise
  value (before rounding) is less than or equal to zero (FR-002).
  - The error message MUST state that the enterprise-value check failed and MUST include
    the computed enterprise value (FR-003).
- Both checks run after all arithmetic currently performed by `compute_dcf` and before
  `DCFResult` construction — no partial/invalid `DCFResult` is ever constructed or returned
  (FR-009).
- MUST NOT change the FCFF, terminal value, enterprise value, equity value, or implied
  value per share formulas themselves for any input that passes both checks — every
  existing passing test's numeric expectations MUST be unaffected.
- MUST NOT reject a negative FCFF in a non-terminal forecast year (unchanged from 003).
- MUST NOT reject a negative `equity_value` or `implied_value_per_share` (unchanged from
  003 — only `enterprise_value` and terminal-year FCFF are checked).

## Caller impact

- `aic.workflow.run_investment_workflow` (009) calls `compute_dcf` as its first step,
  before any LLM call. No orchestrator code change is required: the existing
  "no exception is caught or suppressed" contract (009) already propagates this new
  `ValueError` to the caller, satisfying FR-004 for free.
- `scripts/mvp_validation.py` and `scripts/mvp_amazon_validation.py` are unmanaged manual
  scripts; a rejection surfaces as an uncaught `ValueError` traceback, which is acceptable
  (no test coverage requirement for scripts).

## Non-goals of this contract

- No new exception type (`ValueError` reused, per research.md Decision 2).
- No change to `DCFAssumptions`'s existing construction-time validators (`wacc` vs
  `terminal_growth_rate`, currency consistency) — this guard is a separate,
  result-level check.
- No CLI, network-facing API, or LangGraph node introduced.
