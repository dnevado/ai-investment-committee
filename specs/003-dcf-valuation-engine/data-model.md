# Phase 1 Data Model: Deterministic DCF Valuation Engine

Four entities (two input, two output), all Pydantic v2 models under `aic.dcf`. All
monetary fields are `Money` (from `aic.domain`); rates and counts are plain `Decimal`.
Canonical serialized form: `model_dump()` / `model_validate()`, matching 002-domain-model.

## ForecastYear (input line item)

| Field | Type | Required | Notes |
|---|---|---|---|
| `revenue` | `Money` | Yes | |
| `depreciation_and_amortization` | `Money` | Yes | |
| `capital_expenditure` | `Money` | Yes | |
| `change_in_net_working_capital` | `Money` | Yes | |

One entry per explicit forecast year. No identifier — position within
`DCFAssumptions.forecast` (1-indexed) *is* the "year" used in FR-008's discounting
formula.

## DCFAssumptions (input bundle)

| Field | Type | Required | Notes |
|---|---|---|---|
| `forecast` | `list[ForecastYear]` | Yes, min length 1 | FR-016 |
| `operating_margin` | `Decimal` | Yes | Constant across the whole forecast (FR-002) |
| `tax_rate` | `Decimal` | Yes | Constant; bounded to [0, 1] (spec Assumptions) |
| `wacc` | `Decimal` | Yes | Must be strictly positive (FR-015) |
| `terminal_growth_rate` | `Decimal` | Yes | No independent bound beyond FR-014 |
| `cash` | `Money` | Yes | |
| `debt` | `Money` | Yes | |
| `shares_outstanding` | `Decimal` | Yes | Must be strictly positive (FR-017) |

**Validation** (all enforced at construction — FR-014–FR-020):

- `wacc` SHALL be strictly greater than `terminal_growth_rate` (FR-014).
- `wacc` SHALL be strictly greater than 0 (FR-015).
- `tax_rate` SHALL be within `[0, 1]`.
- `forecast` SHALL contain at least one entry (FR-016; also expressed as `min_length=1`).
- `shares_outstanding` SHALL be strictly greater than 0 (FR-017).
- Every `Money` value across `forecast` (all four fields, every year), `cash`, and
  `debt` SHALL share one common `currency` — a mismatch is rejected explicitly (FR-020),
  mirroring `FinancialSnapshot`'s cross-metric currency-consistency validator.
- No field may be omitted (FR-018) — standard Pydantic required-field behavior.

## YearResult (output line item)

| Field | Type | Notes |
|---|---|---|
| `year` | `int` | 1-indexed forecast year number |
| `fcff` | `Money` | FR-007 |
| `pv_fcff` | `Money` | FR-008; rounded to 2dp, round-half-up (FR-022) |

## DCFResult (output bundle)

| Field | Type | Notes |
|---|---|---|
| `per_year` | `list[YearResult]` | One entry per forecast year, in order |
| `terminal_value` | `Money` | FR-009; rounded to 2dp |
| `pv_terminal_value` | `Money` | FR-010; rounded to 2dp |
| `enterprise_value` | `Money` | FR-011; rounded to 2dp |
| `equity_value` | `Money` | FR-012; rounded to 2dp |
| `implied_value_per_share` | `Money` | FR-013; rounded to 2dp |

`DCFResult` carries no identifier of its own — it is a pure, unnamed calculation output.
Identity/metadata (a `valuation_id`, `confidence`, evidence references) is only added
when converting to a `ValuationResult` via the `to_valuation_result()` adapter
(research.md), which is a separate step outside `compute_dcf`.

## Computation (not a stored field — the `compute_dcf` behavior)

```text
for year, item in enumerate(forecast, start=1):
    ebit   = item.revenue * operating_margin
    nopat  = ebit * (1 - tax_rate)
    fcff   = nopat + item.d_and_a - item.capex - item.change_in_nwc
    pv_fcff = fcff / (1 + wacc) ** year
    # (fcff, pv_fcff) become one YearResult; unrounded values carried forward internally

fcff_final = last year's unrounded fcff
terminal_value = fcff_final * (1 + terminal_growth_rate) / (wacc - terminal_growth_rate)
pv_terminal_value = terminal_value / (1 + wacc) ** N

enterprise_value = sum(unrounded pv_fcff for every year) + unrounded pv_terminal_value
equity_value = enterprise_value + cash - debt
implied_value_per_share = equity_value / shares_outstanding

# Only now: round every reported value to 2dp (round-half-up) and construct DCFResult.
```

Every input value in this pipeline is guaranteed non-`None` and currency-consistent
before `compute_dcf` runs (enforced by `DCFAssumptions`'s own validators); `compute_dcf`
performs one final `is_finite()` check on every computed value before returning
`DCFResult`, satisfying FR-019 defensively even though the upstream validation should
make a non-finite result unreachable in practice.

## Relationship to `ValuationResult` (002-domain-model)

```text
DCFResult.implied_value_per_share ──▶ ValuationResult.estimated_value
                                       (via to_valuation_result() adapter;
                                        valuation_id/confidence/evidence refs
                                        supplied by the caller, not derived
                                        from the DCF calculation itself)
```
